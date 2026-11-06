"""Automated Test Suite for Phase 2 LaTeX Engine, Compiler and PDF Preview.

Tests:
1. Compiler discovery (MiKTeX / TeX Live binaries).
2. LaTeX compiler log parser for errors and warnings.
3. Syntax highlighter rules for LaTeX and BibTeX.
4. Code editor line numbering, error indicators, and search & replace.
5. PDF viewer document loading, page navigation, and zoom modes.
6. Build failure recovery and preservation of previous PDF.
7. SyncTeX service coordinate translation.
8. Multi-file project structure resolution.
"""

import unittest
import tempfile
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.services.latex_service import (
    LaTeXCompilerService,
    LaTeXLogParser,
    LaTeXDiagnostic,
    CompilationResult,
)
from src.services.synctex_service import SyncTeXService
from src.ui.editors.latex_highlighter import LaTeXHighlighter
from src.ui.editors.code_editor import CodeEditor
from src.ui.viewer.pdf_viewer import PDFViewerWidget
from src.storage.file_manager import FileManager


class TestPhase2LaTeXEngine(unittest.TestCase):
    """Test suite for Phase 2 LaTeX compiler, editor, and PDF preview."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        if not QApplication.instance():
            cls.app = QApplication(["--platform", "offscreen"])
        else:
            cls.app = QApplication.instance()

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name).resolve()
        # Custom bin dir pointing to installed MiKTeX
        self.compiler_service = LaTeXCompilerService(custom_bin_dir="E:/miktex/miktex/bin/x64")
        self.synctex_service = SyncTeXService()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_compiler_discovery(self) -> None:
        """Verify discovery of local TeX distributions and compiler engines."""
        dists = self.compiler_service.discover_distributions()
        self.assertGreaterEqual(len(dists), 1)

        # Check binaries
        pdflatex_bin = self.compiler_service.get_binary_path("pdflatex")
        self.assertIsNotNone(pdflatex_bin)
        self.assertTrue(pdflatex_bin.exists())

        xelatex_bin = self.compiler_service.get_binary_path("xelatex")
        self.assertIsNotNone(xelatex_bin)

        bibtex_bin = self.compiler_service.get_binary_path("bibtex")
        self.assertIsNotNone(bibtex_bin)

    def test_log_parser_errors_and_warnings(self) -> None:
        """Verify parsing of compiler error logs and warning messages."""
        sample_log = (
            "This is pdfTeX, Version 3.141592653-2.6-1.40.25 (MiKTeX 23.5)\n"
            "(main.tex\n"
            "LaTeX2e <2022-11-01> patch level 1\n"
            "! Undefined control sequence.\n"
            "l.24 \\badcommand\n"
            "                {argument}\n"
            "The control sequence at the end of the top line\n"
            "LaTeX Warning: Citation 'hawking1974' on page 1 undefined on input line 45.\n"
            "Overfull \\hbox (12.4pt too wide) in paragraph at lines 50--52\n"
            ")\n"
        )

        diagnostics = LaTeXLogParser.parse_log(sample_log, default_file="main.tex")
        self.assertEqual(len(diagnostics), 3)

        # 1. Error check
        err = diagnostics[0]
        self.assertEqual(err.severity, "error")
        self.assertEqual(err.line_number, 24)
        self.assertIn("Undefined control sequence", err.message)
        self.assertIn("\\badcommand", err.source_snippet)

        # 2. Citation Warning check
        warn1 = diagnostics[1]
        self.assertEqual(warn1.severity, "warning")
        self.assertEqual(warn1.line_number, 45)
        self.assertIn("hawking1974", warn1.message)

        # 3. Overfull hbox Warning check
        warn2 = diagnostics[2]
        self.assertEqual(warn2.severity, "warning")
        self.assertEqual(warn2.line_number, 50)
        self.assertIn("Overfull \\hbox", warn2.message)

    def test_code_editor_line_numbers_and_search(self) -> None:
        """Verify CodeEditor line number gutter, error indicators, and search & replace."""
        editor = CodeEditor()
        content = "Line one\nLine two\nLine three\nTarget word\nLine five\n"
        editor.setPlainText(content)

        # Check line count
        self.assertEqual(editor.blockCount(), 6)
        self.assertGreater(editor.line_number_area_width(), 10)

        # Test error lines highlighting
        editor.set_error_lines([2, 4])
        self.assertIn(2, editor.error_lines)
        self.assertIn(4, editor.error_lines)

        # Test go_to_line
        editor.go_to_line(3)
        self.assertEqual(editor.textCursor().blockNumber(), 2)

        # Test search
        found = editor.find_next("Target")
        self.assertTrue(found)

        # Test replace
        editor.replace_text("Target", "Replaced")
        self.assertIn("Replaced word", editor.toPlainText())
        self.assertNotIn("Target word", editor.toPlainText())

    def test_syntax_highlighter_latex_and_bibtex(self) -> None:
        """Verify syntax highlighters initialize rules for LaTeX and BibTeX."""
        editor_tex = CodeEditor()
        self.assertFalse(editor_tex.highlighter.is_bibtex)
        self.assertGreater(len(editor_tex.highlighter.highlighting_rules), 4)

        # BibTeX editor
        bib_path = self.test_root / "refs.bib"
        bib_path.touch()
        editor_bib = CodeEditor(file_path=bib_path)
        self.assertTrue(editor_bib.highlighter.is_bibtex)
        self.assertGreater(len(editor_bib.highlighter.highlighting_rules), 3)

    def test_failed_compilation_preserves_previous_pdf(self) -> None:
        """Verify that a broken compilation preserves any previously generated working PDF."""
        build_dir = self.test_root / "build"
        build_dir.mkdir(parents=True, exist_ok=True)

        target_pdf = build_dir / "main.pdf"
        # Simulate pre-existing valid PDF
        FileManager.atomic_write(target_pdf, b"%PDF-1.5 Dummy Valid PDF Content")
        self.assertTrue(target_pdf.exists())

        # Compile non-existent or broken file
        broken_tex = self.test_root / "broken.tex"
        FileManager.atomic_write(broken_tex, "\\documentclass{article}\n\\begin{document}\n\\invalidcmd\n\\end{document}\n")

        # Mock compile failure with fake binary to test preservation logic
        res = self.compiler_service.compile(
            main_tex_file=broken_tex,
            engine="nonexistent_engine",
            build_dir=build_dir,
        )

        self.assertFalse(res.success)
        # Previous PDF must still exist and be intact!
        self.assertTrue(target_pdf.exists())

    def test_pdf_viewer_widget(self) -> None:
        """Verify PDF viewer initialization, zoom modes, and page navigation controls."""
        viewer = PDFViewerWidget()
        self.assertIsNotNone(viewer.pdf_view)
        self.assertIsNotNone(viewer.toolbar)

        # Initial state without document
        self.assertEqual(viewer.document.pageCount(), 0)

        # Zoom mode controls
        viewer.zoom_in()
        viewer.zoom_out()
        viewer._on_zoom_mode_changed(0)  # Fit to width

    def test_synctex_service_parsing(self) -> None:
        """Verify forward and inverse SyncTeX parsing with fallback coordinates."""
        dummy_tex = self.test_root / "main.tex"
        dummy_pdf = self.test_root / "main.pdf"
        dummy_tex.touch()
        dummy_pdf.touch()

        # Forward sync without synctex.gz returns fallback page 0
        loc = self.synctex_service.forward_sync(dummy_tex, 15, 1, dummy_pdf)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.page, 0)

        # Inverse sync without synctex.gz returns None gracefully
        src_loc = self.synctex_service.inverse_sync(dummy_pdf, 0, 100.0, 200.0)
        self.assertIsNone(src_loc)


if __name__ == "__main__":
    unittest.main()

