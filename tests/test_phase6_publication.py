"""Automated Unit Tests for Phase 6: Academic Templates & Publication Preparation."""
import unittest
import tempfile
import zipfile
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.services.template_service import PUBLISHER_TEMPLATES, TemplateMigrator
from src.services.compliance_auditor import PublicationComplianceAuditor, ComplianceReport
from src.services.submission_bundler import SubmissionBundler
from src.ui.dialogs.submission_dialog import SubmissionDialog


# Ensure single QApplication instance across test suites
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


SAMPLE_ARTICLE = r"""\documentclass{article}
\usepackage{amsmath}

\title{Neural Operator Foundations}
\author{Ada Lovelace}

\begin{document}
\maketitle

\begin{abstract}
This study presents a novel neural operator architecture for solving partial differential equations in continuum mechanics.
\end{abstract}

\section{Introduction}
Neural operators have emerged as an expressive framework for scientific machine learning.

\begin{equation}
\mathcal{L}(u) = f(x)
\end{equation}

\begin{figure}[htbp]
\centering
\caption{Model Architecture Diagram}
\label{fig:arch}
\end{figure}

\section{Methodology}
We formulate the Fourier neural operator over Sobolev spaces.

\section{Results}
Our empirical evaluations demonstrate sub-millisecond inference.

\section{Conclusion}
The proposed formulation scales effectively.

\bibliographystyle{plain}
\bibliography{references}

\end{document}
"""


class TestPhase6Publication(unittest.TestCase):
    """Test suite validating template profiles, migration safety, compliance audits, and packaging."""

    def test_template_catalog_profiles(self) -> None:
        """Verify master template profiles (IEEE, ACM, Springer, Elsevier) exist with valid constraints."""
        expected_keys = ["ieee_trans", "acm_sigconf", "springer_sn", "elsevier_cas", "general_article"]
        for key in expected_keys:
            self.assertIn(key, PUBLISHER_TEMPLATES)
            tpl = PUBLISHER_TEMPLATES[key]
            self.assertTrue(tpl.documentclass.startswith(r"\documentclass"))
            self.assertGreater(tpl.abstract_word_limit, 50)
            self.assertGreater(len(tpl.required_sections), 0)

    def test_template_migrator_preserves_content(self) -> None:
        """Verify switching template modifies documentclass while preserving all manuscript content."""
        # Migrate to IEEE Transactions
        ieee_tex = TemplateMigrator.apply_template(SAMPLE_ARTICLE, "ieee_trans")
        self.assertIn("IEEEtran", ieee_tex)
        self.assertIn(r"\usepackage{cite}", ieee_tex)
        self.assertIn(r"\usepackage{tabularx}", ieee_tex)
        self.assertIn("IEEEtran", ieee_tex)

        # Content preservation
        self.assertIn("Neural Operator Foundations", ieee_tex)
        self.assertIn(r"\section{Introduction}", ieee_tex)
        self.assertIn(r"\mathcal{L}(u) = f(x)", ieee_tex)
        self.assertIn(r"\section{Methodology}", ieee_tex)
        self.assertIn(r"\section{Results}", ieee_tex)
        self.assertIn(r"\section{Conclusion}", ieee_tex)

        # Migrate to ACM
        acm_tex = TemplateMigrator.apply_template(ieee_tex, "acm_sigconf")
        self.assertIn("acmart", acm_tex)
        self.assertIn(r"\usepackage{booktabs}", acm_tex)
        self.assertIn("ACM-Reference-Format", acm_tex)
        self.assertIn(r"\section{Introduction}", acm_tex)

    def test_compliance_auditor_clean_manuscript(self) -> None:
        """Verify compliant manuscript passes all rule-based checks."""
        report = PublicationComplianceAuditor.audit_manuscript(
            SAMPLE_ARTICLE,
            template_key="ieee_trans",
            bib_source="",
        )
        self.assertIsInstance(report, ComplianceReport)
        self.assertTrue(report.is_compliant)
        self.assertEqual(len(report.failed_checks), 0)
        self.assertGreater(report.estimated_word_count, 40)
        self.assertGreater(report.abstract_word_count, 10)

    def test_compliance_auditor_detects_violations(self) -> None:
        """Verify auditor catches missing abstract, missing figure caption, and missing required sections."""
        bad_latex = r"""\documentclass{article}
\begin{document}
\section{Random Thoughts}
No abstract or required sections here.

\begin{figure}
\includegraphics{fig.png}
\end{figure}

\cite{ghost_citation_key}
\end{document}
"""
        report = PublicationComplianceAuditor.audit_manuscript(
            bad_latex,
            template_key="ieee_trans",
            bib_source="@article{other_key, title={Test}}",
        )
        self.assertFalse(report.is_compliant)
        self.assertGreater(len(report.failed_checks), 0)

        failures = " ".join(report.failed_checks)
        self.assertIn("Missing required \\begin{abstract}", failures)
        self.assertIn("missing a \\caption", failures)
        self.assertIn("Unresolved citations", failures)

    def test_submission_bundler_zip_creation(self) -> None:
        """Verify bundling packages source, PDF, bibtex, assets, and checklist into a ZIP."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_dir = Path(tmp_dir) / "TestProject"
            proj_dir.mkdir()

            tex_file = proj_dir / "main.tex"
            tex_file.write_text(SAMPLE_ARTICLE, encoding="utf-8")

            pdf_file = proj_dir / "main.pdf"
            pdf_file.write_text("%PDF-1.4 dummy pdf content", encoding="utf-8")

            bib_file = proj_dir / "references.bib"
            bib_file.write_text("@article{key, title={A}}", encoding="utf-8")

            assets_dir = proj_dir / "assets"
            assets_dir.mkdir()
            fig_file = assets_dir / "diagram.png"
            fig_file.write_bytes(b"\x89PNG\r\n\x1a\n...")

            zip_output = proj_dir / "submission_bundle.zip"

            report = PublicationComplianceAuditor.audit_manuscript(SAMPLE_ARTICLE, "ieee_trans")
            out_zip = SubmissionBundler.create_submission_package(
                project_dir=proj_dir,
                main_tex_file=tex_file,
                compiled_pdf_file=pdf_file,
                output_zip_path=zip_output,
                compliance_report=report,
            )

            self.assertTrue(out_zip.exists())

            # Inspect contents
            with zipfile.ZipFile(out_zip, "r") as zf:
                namelist = zf.namelist()
                self.assertIn("main.tex", namelist)
                self.assertIn("main.pdf", namelist)
                self.assertIn("references.bib", namelist)
                self.assertIn("assets/diagram.png", namelist)
                self.assertIn("SUBMISSION_CHECKLIST.md", namelist)

                checklist = zf.read("SUBMISSION_CHECKLIST.md").decode("utf-8")
                self.assertIn("ACADEMIC SUBMISSION CHECKLIST", checklist)
                self.assertIn("IEEE Transactions & Conferences", checklist)


if __name__ == "__main__":
    unittest.main()
