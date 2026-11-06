"""Automated Unit Tests for Phase 7: Reliability, Performance & Windows Release."""
import unittest
import tempfile
import sqlite3
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.services.recovery_service import DocumentRecoveryService, RecoverySnapshot
from src.services.revision_service import RevisionManager, RevisionItem
from src.services.diagnostics_service import SystemDiagnosticsService, SystemDiagnosticReport
from src.core.parser import LaTeXDocumentParser
from src.core.sync_bridge import SyncBridge
from src.services.compliance_auditor import PublicationComplianceAuditor
from src.services.submission_bundler import SubmissionBundler
from src.services.literature_service import ExtractedPaper, PDFExtractorService
from src.services.literature_matrix import LiteratureMatrixGenerator
from src.storage.file_manager import FileManager


# Ensure single QApplication instance across test suites
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestPhase7ReleaseAndReliability(unittest.TestCase):
    """Test suite validating autosave, crash recovery, revision history, diagnostics, and offline operation."""

    def test_recovery_service_snapshot_lifecycle(self) -> None:
        """Verify saving, detecting, and clearing crash recovery snapshots."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_dir = Path(tmp_dir) / "RecoveryProj"
            proj_dir.mkdir()
            doc_file = proj_dir / "manuscript.tex"
            doc_file.write_text("% original saved content", encoding="utf-8")

            # 1. Save uncommitted working snapshot
            uncommitted_text = "% unsaved experimental changes\n\\section{New Idea}"
            snap_path = DocumentRecoveryService.save_snapshot(proj_dir, doc_file, uncommitted_text)
            self.assertTrue(snap_path.exists())

            # 2. Detect unrecovered snapshots
            snapshots = DocumentRecoveryService.detect_unrecovered_snapshots(proj_dir)
            self.assertEqual(len(snapshots), 1)
            snap = snapshots[0]
            self.assertEqual(snap.content, uncommitted_text)
            self.assertGreater(snap.timestamp, 0)

            # 3. Clean up snapshot on manual save
            DocumentRecoveryService.clear_snapshot(proj_dir, doc_file)
            remaining = DocumentRecoveryService.detect_unrecovered_snapshots(proj_dir)
            self.assertEqual(len(remaining), 0)

    def test_revision_manager_create_and_list(self) -> None:
        """Verify recording document revision checkpoints and listing history."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_dir = Path(tmp_dir) / "RevisionProj"
            proj_dir.mkdir()
            doc_file = proj_dir / "draft.tex"
            doc_file.write_text("Version 1 content", encoding="utf-8")

            # Record Revision 1
            rev1 = RevisionManager.create_revision(proj_dir, doc_file, "Version 1 content", label="Initial Draft")
            self.assertTrue(rev1.revision_id.startswith("rev_"))
            self.assertEqual(rev1.file_name, "draft.tex")

            # Record Revision 2
            rev2 = RevisionManager.create_revision(proj_dir, doc_file, "Version 2 content with revisions", label="Major Revision")

            # List revisions
            revs = RevisionManager.list_revisions(proj_dir, doc_file)
            self.assertEqual(len(revs), 2)
            # Newest first
            self.assertEqual(revs[0].revision_id, rev2.revision_id)
            self.assertEqual(revs[1].revision_id, rev1.revision_id)

    def test_revision_manager_diff_and_restore(self) -> None:
        """Verify generating line diffs and rolling back document to a previous revision."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_dir = Path(tmp_dir) / "DiffProj"
            proj_dir.mkdir()
            doc_file = proj_dir / "paper.tex"

            v1_text = "\\section{Intro}\nInitial line 1\nLine 2\n"
            doc_file.write_text(v1_text, encoding="utf-8")
            rev1 = RevisionManager.create_revision(proj_dir, doc_file, v1_text, label="V1")

            v2_text = "\\section{Intro}\nModified line 1\nLine 2\nAdded line 3\n"
            doc_file.write_text(v2_text, encoding="utf-8")
            rev2 = RevisionManager.create_revision(proj_dir, doc_file, v2_text, label="V2")

            # Test line diff
            diff = RevisionManager.compare_revisions(rev1.content, rev2.content)
            self.assertIn("-Initial line 1", diff)
            self.assertIn("+Modified line 1", diff)
            self.assertIn("+Added line 3", diff)

            # Test restoring V1
            restored = RevisionManager.restore_revision(proj_dir, doc_file, rev1.revision_id)
            self.assertEqual(restored, v1_text)
            self.assertEqual(doc_file.read_text(encoding="utf-8"), v1_text)

    def test_system_diagnostics_service_report(self) -> None:
        """Verify system diagnostics runs environment checks and PRAGMA integrity."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = Path(tmp_dir) / "diag_test.db"
            conn = sqlite3.connect(str(db_file))
            conn.execute("CREATE TABLE test (id INT);")
            conn.commit()
            conn.close()

            report = SystemDiagnosticsService.run_diagnostics(db_path=db_file)
            self.assertIsInstance(report, SystemDiagnosticReport)
            self.assertIn("Windows", report.os_info)
            self.assertIn("RAM:", report.hardware_summary)
            self.assertIn("PRAGMA integrity_check: ok", report.database_integrity)

            text_report = SystemDiagnosticsService.export_report_text(report)
            self.assertIn("ResearchIDE System Diagnostics", text_report)
            self.assertIn("Operating System:", text_report)

    def test_offline_full_pipeline_verification(self) -> None:
        """Verify the complete academic writing pipeline operates 100% locally with zero internet access."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_dir = Path(tmp_dir) / "OfflineStudy"
            proj_dir.mkdir()

            # 1. Create and write manuscript
            tex_file = proj_dir / "manuscript.tex"
            tex_content = (
                r"\documentclass{article}" "\n"
                r"\title{Offline Computing}" "\n"
                r"\begin{document}" "\n"
                r"\begin{abstract}" "\n"
                "This study examines local-first academic research systems.\n"
                r"\end{abstract}" "\n"
                r"\section{Introduction}" "\n"
                "We operate entirely offline.\n"
                r"\begin{equation}" "\n"
                "E = mc^2\n"
                r"\end{equation}" "\n"
                r"\section{Methodology}" "\n"
                "Local AST and CST parsing.\n"
                r"\section{Results}" "\n"
                "Instantaneous execution.\n"
                r"\section{Conclusion}" "\n"
                "Final offline remarks.\n"
                r"\bibliography{refs}" "\n"
                r"\end{document}" "\n"
            )
            tex_file.write_text(tex_content, encoding="utf-8")

            # 2. CST parsing and bidirectional sync bridge
            bridge = SyncBridge()
            doc = bridge.load_from_latex(tex_content)
            self.assertEqual(doc.title, "Offline Computing")
            self.assertGreater(len(doc.blocks), 4)

            # 3. Grounded evidence extraction from local research paper
            paper = ExtractedPaper(
                paper_id="off-1",
                file_path=Path("local_paper.pdf"),
                title="Air-Gapped Systems",
                pages=[(1, "The objective of this study is air-gapped security. Evaluated on local clusters. Results demonstrate zero packet leakage.")],
            )
            evidence = PDFExtractorService.find_evidence(paper, "air-gapped security")
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0].page_number, 1)

            # 4. Comparative literature matrix
            matrix = LiteratureMatrixGenerator.generate_matrix([paper])
            self.assertEqual(len(matrix), 1)
            latex_tbl = LiteratureMatrixGenerator.to_latex_table(matrix)
            self.assertIn(r"\begin{table*}", latex_tbl)

            # 5. Publication compliance auditor
            report = PublicationComplianceAuditor.audit_manuscript(tex_content, "ieee_trans")
            self.assertTrue(report.is_compliant)

            # 6. Submission package bundling
            zip_out = proj_dir / "submission.zip"
            SubmissionBundler.create_submission_package(
                project_dir=proj_dir,
                main_tex_file=tex_file,
                compiled_pdf_file=None,
                output_zip_path=zip_out,
                compliance_report=report,
            )
            self.assertTrue(zip_out.exists())


if __name__ == "__main__":
    unittest.main()
