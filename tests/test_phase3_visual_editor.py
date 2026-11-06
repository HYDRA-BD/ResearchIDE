"""Automated Unit Tests for Phase 3: Visual Document Editor & Synchronization."""
import unittest
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.core.document import (
    CanonicalDocument,
    BlockType,
    SectionBlock,
    ParagraphBlock,
    EquationBlock,
    OpaqueLaTeXBlock,
)
from src.core.sync_bridge import SyncBridge
from src.ui.editors.visual_editor import VisualEditorWidget
from src.ui.workspace import DocumentTab
from src.storage.file_manager import FileManager


# Ensure single QApplication instance across test suites
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


SAMPLE_LATEX = r"""\documentclass{article}
\usepackage{amsmath}
\usepackage{tikz}
\newcommand{\customR}{\mathbb{R}}

\title{Quantum Geometry}
\author{A. Einstein}

\begin{document}
\maketitle

\section{Introduction}
This is the introductory paragraph establishing mathematical cosmology.

\begin{equation}
R_{\mu\nu} - \frac{1}{2}R g_{\mu\nu} = 8\pi G T_{\mu\nu}
\end{equation}

\begin{tikzpicture}
\draw[thick] (0,0) -- (2,2);
\end{tikzpicture}

\section{Conclusion}
Final remarks on relativity.

\end{document}
"""


class TestPhase3VisualEditor(unittest.TestCase):
    """Test suite validating the visual document editor and bidirectional synchronization bridge."""

    def setUp(self) -> None:
        self.bridge = SyncBridge()

    def test_sync_bridge_latex_loading_and_dict_serialization(self) -> None:
        """Verify LaTeX source is parsed into CST and properly serialized for the WebChannel canvas."""
        doc = self.bridge.load_from_latex(SAMPLE_LATEX)
        self.assertEqual(doc.title, "Quantum Geometry")
        self.assertGreater(len(doc.blocks), 0)

        # Check dictionary serialization for JS canvas
        data = self.bridge.get_document_as_dict()
        self.assertEqual(data["title"], "Quantum Geometry")
        self.assertIn("blocks", data)
        self.assertTrue(len(data["blocks"]) >= 5)

        # Check block types in JSON
        types = [b["type"] for b in data["blocks"]]
        self.assertIn("section", types)
        self.assertIn("paragraph", types)
        self.assertIn("equation", types)
        self.assertIn("opaque_latex", types)

        # Check opaque block properties
        opaque_blocks = [b for b in data["blocks"] if b["is_opaque"]]
        self.assertGreater(len(opaque_blocks), 0)
        self.assertEqual(opaque_blocks[0]["env_name"], "tikzpicture")

    def test_sync_bridge_surgical_visual_update(self) -> None:
        """Verify modifying a visual block surgically patches LaTeX source without touching opaque macros."""
        doc = self.bridge.load_from_latex(SAMPLE_LATEX)

        # Find the introduction section block
        intro_block = next(
            b for b in doc.blocks if isinstance(b, SectionBlock) and b.title == "Introduction"
        )

        patched_sources = []
        self.bridge.source_patched.connect(patched_sources.append)

        # Perform visual update: rename "Introduction" to "Cosmological Foundations"
        success = self.bridge.apply_visual_block_update(intro_block.id, "Cosmological Foundations")
        self.assertTrue(success)
        self.assertEqual(len(patched_sources), 1)

        patched_tex = patched_sources[0]
        self.assertIn(r"\section{Cosmological Foundations}", patched_tex)
        self.assertNotIn(r"\section{Introduction}", patched_tex)

        # Verify TikZ diagram and custom macros remained completely untouched
        self.assertIn(r"\newcommand{\customR}{\mathbb{R}}", patched_tex)
        self.assertIn(r"\begin{tikzpicture}", patched_tex)
        self.assertIn(r"\draw[thick] (0,0) -- (2,2);", patched_tex)
        self.assertIn(r"\section{Conclusion}", patched_tex)

    def test_sync_bridge_opaque_block_mutation_blocked(self) -> None:
        """Verify that attempting to mutate an opaque block visually is rejected with zero data corruption."""
        doc = self.bridge.load_from_latex(SAMPLE_LATEX)
        opaque_block = next(b for b in doc.blocks if b.is_opaque)

        errors = []
        self.bridge.error_occurred.connect(errors.append)

        success = self.bridge.apply_visual_block_update(opaque_block.id, "Corrupted text")
        self.assertFalse(success)
        self.assertEqual(len(errors), 1)
        self.assertIn("Cannot visually mutate opaque LaTeX block", errors[0])

        # Source buffer must not have changed
        self.assertIn(r"\begin{tikzpicture}", self.bridge.raw_latex)

    def test_sync_bridge_insert_academic_blocks(self) -> None:
        """Verify inserting academic elements generates valid LaTeX environments."""
        self.bridge.load_from_latex(SAMPLE_LATEX)

        # Insert a table
        success_table = self.bridge.insert_block_after(None, BlockType.TABLE)
        self.assertTrue(success_table)
        self.assertIn(r"\begin{table}", self.bridge.raw_latex)
        self.assertIn(r"\begin{tabular}", self.bridge.raw_latex)

        # Insert an equation
        success_eq = self.bridge.insert_block_after(None, BlockType.EQUATION, "F = ma")
        self.assertTrue(success_eq)
        self.assertIn("F = ma", self.bridge.raw_latex)

        # Insert a figure
        success_fig = self.bridge.insert_block_after(None, BlockType.FIGURE)
        self.assertTrue(success_fig)
        self.assertIn(r"\begin{figure}", self.bridge.raw_latex)

    def test_sync_bridge_coordinate_mapping(self) -> None:
        """Verify looking up blocks by source line coordinates works accurately."""
        self.bridge.load_from_latex(SAMPLE_LATEX)

        # In SAMPLE_LATEX, line 12 is \section{Introduction}
        block = self.bridge.find_block_at_line(12)
        self.assertIsNotNone(block)
        self.assertIsInstance(block, SectionBlock)
        self.assertEqual(block.title, "Introduction")

    def test_document_tab_mode_switching(self) -> None:
        """Verify DocumentTab initializes visual and code editors and switches view modes."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            tex_file = Path(tmp_dir) / "test.tex"
            tex_file.write_text(SAMPLE_LATEX, encoding="utf-8")

            tab = DocumentTab(tex_file)
            tab.show()
            self.assertIsNotNone(tab.visual_editor)
            self.assertIsNotNone(tab.code_editor)

            # Test Visual Mode
            tab.set_editor_mode("visual")
            self.assertFalse(tab.visual_editor.isHidden())
            self.assertTrue(tab.code_editor.isHidden())

            # Test Source Mode
            tab.set_editor_mode("source")
            self.assertTrue(tab.visual_editor.isHidden())
            self.assertFalse(tab.code_editor.isHidden())

            # Test Split Mode
            tab.set_editor_mode("split")
            self.assertFalse(tab.visual_editor.isHidden())
            self.assertFalse(tab.code_editor.isHidden())


if __name__ == "__main__":
    unittest.main()
