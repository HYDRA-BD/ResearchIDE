"""Automated Unit Tests for Phase 5: Research Intelligence & Literature Management."""
import unittest
import tempfile
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
import pypdf

from src.services.reference_service import ReferenceManager, ReferenceItem
from src.services.literature_service import PDFExtractorService, ExtractedPaper, EvidenceSnippet
from src.services.literature_matrix import LiteratureMatrixGenerator, MatrixRow
from src.services.dataset_service import DatasetService, DatasetSummary
from src.ui.literature_panel import LiteraturePanel


# Ensure single QApplication instance across test suites
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


SAMPLE_BIBTEX = r"""@article{vaswani2017attention,
  title = {Attention Is All You Need},
  author = {Ashish Vaswani and Noam Shazeer and Niki Parmar and Jakob Uszkoreit},
  journal = {Advances in Neural Information Processing Systems},
  volume = {30},
  year = {2017},
  doi = {10.5555/3295222.3295349}
}

@inproceedings{he2016deep,
  title = {Deep Residual Learning for Image Recognition},
  author = {Kaiming He and Xiangyu Zhang and Shaoqing Ren and Jian Sun},
  booktitle = {IEEE Conference on Computer Vision and Pattern Recognition},
  year = {2016},
  pages = {770--778}
}
"""

SAMPLE_RIS = """TY  - JOUR
ID  - einstein1905electrodynamics
TI  - On the Electrodynamics of Moving Bodies
AU  - Albert Einstein
PY  - 1905
JO  - Annalen der Physik
DO  - 10.1002/andp.19053221004
ER  - 
"""


class TestPhase5ResearchIntelligence(unittest.TestCase):
    """Test suite validating literature intelligence, reference management, evidence traceability, and datasets."""

    def test_bibtex_parsing_and_serialization(self) -> None:
        """Verify BibTeX parsing extracts authors, titles, years, and exports cleanly."""
        items = ReferenceManager.parse_bibtex(SAMPLE_BIBTEX)
        self.assertEqual(len(items), 2)

        v_item = items[0]
        self.assertEqual(v_item.key, "vaswani2017attention")
        self.assertEqual(v_item.title, "Attention Is All You Need")
        self.assertEqual(v_item.year, 2017)
        self.assertEqual(len(v_item.authors), 4)
        self.assertEqual(v_item.authors[0], "Ashish Vaswani")
        self.assertEqual(v_item.author_display, "Ashish Vaswani et al.")
        self.assertEqual(v_item.doi, "10.5555/3295222.3295349")

        # Test citation formatters
        cite_latex = ReferenceManager.format_citation(v_item, style="latex")
        self.assertEqual(cite_latex, r"\cite{vaswani2017attention}")

        cite_ieee = ReferenceManager.format_citation(v_item, style="ieee", index=3)
        self.assertEqual(cite_ieee, "[3]")

        cite_apa = ReferenceManager.format_citation(v_item, style="apa")
        self.assertEqual(cite_apa, "(Ashish Vaswani et al., 2017)")

        # Test export
        exported_bib = ReferenceManager.export_bibtex(items)
        self.assertIn("@article{vaswani2017attention,", exported_bib)
        self.assertIn("@inproceedings{he2016deep,", exported_bib)

    def test_ris_parsing_and_csl_export(self) -> None:
        """Verify RIS parsing and CSL JSON generation."""
        items = ReferenceManager.parse_ris(SAMPLE_RIS)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.key, "einstein1905electrodynamics")
        self.assertEqual(item.title, "On the Electrodynamics of Moving Bodies")
        self.assertEqual(item.year, 1905)
        self.assertEqual(item.authors, ["Albert Einstein"])
        self.assertEqual(item.doi, "10.1002/andp.19053221004")

        # CSL JSON
        csl = ReferenceManager.export_csl_json(items)
        self.assertIn("einstein1905electrodynamics", csl)
        self.assertIn("Albert Einstein", csl)

    def test_pdf_extraction_and_grounded_evidence(self) -> None:
        """Verify PDF text extraction and search for evidence grounded in specific pages."""
        # Create a synthetic 2-page PDF
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "quantum_mechanics.pdf"
            writer = pypdf.PdfWriter()

            # Page 1
            writer.add_blank_page(width=612, height=792)
            # Page 2
            writer.add_blank_page(width=612, height=792)
            with open(pdf_path, "wb") as f:
                writer.write(f)

            # Manually mock paper content for extraction testing
            paper = ExtractedPaper(
                paper_id="paper-001",
                file_path=pdf_path,
                title="Quantum Geometry Principles",
                authors=["N. Bohr", "W. Heisenberg"],
                year=1927,
                pages=[
                    (1, "In this work, we propose a matrix mechanics formulation for atomic spectra. The matrix formulation demonstrates complete consistency."),
                    (2, "Experimental results demonstrate that atomic energy levels agree with observed spectral lines with high precision."),
                ],
            )

            # Test finding grounded evidence for query
            snippets = PDFExtractorService.find_evidence(paper, "atomic spectra matrix formulation")
            self.assertGreater(len(snippets), 0)
            self.assertEqual(snippets[0].page_number, 1)
            self.assertIn("matrix mechanics formulation", snippets[0].quote)
            self.assertEqual(snippets[0].file_name, "quantum_mechanics.pdf")

    def test_literature_matrix_generation(self) -> None:
        """Verify compiling literature matrix rows and exporting to Markdown and LaTeX."""
        paper1 = ExtractedPaper(
            paper_id="p1",
            file_path=Path("paper1.pdf"),
            title="Transformer Architecture",
            authors=["A. Vaswani"],
            year=2017,
            abstract="In this work, we propose the Transformer based on self-attention.",
            pages=[(1, "The objective of this study is to replace recurrent neural networks with attention mechanisms. Evaluated on WMT 2014 English-to-German dataset. Results demonstrate BLEU score improvements.")],
        )

        matrix_rows = LiteratureMatrixGenerator.generate_matrix([paper1])
        self.assertEqual(len(matrix_rows), 1)
        row = matrix_rows[0]
        self.assertEqual(row.title, "Transformer Architecture")
        self.assertEqual(row.year, "2017")

        # Markdown Table export
        md_table = LiteratureMatrixGenerator.to_markdown(matrix_rows)
        self.assertIn("| Paper / Authors | Year |", md_table)
        self.assertIn("Transformer Architecture", md_table)

        # LaTeX Table export
        latex_table = LiteratureMatrixGenerator.to_latex_table(matrix_rows)
        self.assertIn(r"\begin{table*}[htbp]", latex_table)
        self.assertIn(r"\begin{tabularx}", latex_table)
        self.assertIn("Transformer Architecture", latex_table)

    def test_dataset_csv_inspection(self) -> None:
        """Verify DatasetService parses CSV files and produces accurate statistics."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "experiment_data.csv"
            csv_path.write_text(
                "trial_id,voltage,temperature,status\n"
                "1,3.3,25.4,OK\n"
                "2,3.4,26.1,OK\n"
                "3,3.2,28.5,FAIL\n"
                "4,3.5,24.9,OK\n",
                encoding="utf-8",
            )

            summary = DatasetService.inspect_csv(csv_path)
            self.assertEqual(summary.file_name, "experiment_data.csv")
            self.assertEqual(summary.row_count, 4)
            self.assertEqual(summary.col_count, 4)

            # Check column types and counts
            col_names = [c.name for c in summary.columns]
            self.assertEqual(col_names, ["trial_id", "voltage", "temperature", "status"])

            trial_col = next(c for c in summary.columns if c.name == "trial_id")
            self.assertEqual(trial_col.dtype, "integer")
            self.assertEqual(trial_col.min_val, 1)
            self.assertEqual(trial_col.max_val, 4)

            status_col = next(c for c in summary.columns if c.name == "status")
            self.assertEqual(status_col.dtype, "string")
            self.assertEqual(status_col.unique_count, 2)

    def test_literature_panel_ui(self) -> None:
        """Verify LiteraturePanel initializes with all 4 tabs and handles reference filtering."""
        panel = LiteraturePanel()
        self.assertEqual(panel.tabs.count(), 4)

        # Add references to panel and test filtering
        items = ReferenceManager.parse_bibtex(SAMPLE_BIBTEX)
        panel.references.extend(items)
        panel._refresh_refs_table()
        self.assertEqual(panel.refs_table.rowCount(), 2)

        # Filter by "Vaswani"
        panel._filter_references("Vaswani")
        self.assertEqual(panel.refs_table.rowCount(), 1)

        # Reset filter
        panel._filter_references("")
        self.assertEqual(panel.refs_table.rowCount(), 2)


if __name__ == "__main__":
    unittest.main()
