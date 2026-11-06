"""Research Intelligence, Literature Library & Reference Manager Panel for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QTextEdit,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QApplication,
)
from src.services.reference_service import ReferenceManager, ReferenceItem
from src.services.literature_service import PDFExtractorService, ExtractedPaper
from src.services.literature_matrix import LiteratureMatrixGenerator, MatrixRow
from src.services.dataset_service import DatasetService, DatasetSummary
from src.utils.logger import app_logger


class LiteraturePanel(QWidget):
    """Multi-tab Research Intelligence dock panel."""

    citation_insert_requested = Signal(str)  # Emits LaTeX citation \cite{key}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.papers: List[ExtractedPaper] = []
        self.references: List[ReferenceItem] = []
        self.matrix_rows: List[MatrixRow] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.tabs = QTabWidget(self)

        # Tab 1: Papers Library
        self.papers_tab = self._create_papers_tab()
        self.tabs.addTab(self.papers_tab, "📚 Library")

        # Tab 2: Reference Manager
        self.refs_tab = self._create_refs_tab()
        self.tabs.addTab(self.refs_tab, "🏷️ References")

        # Tab 3: Literature Matrix
        self.matrix_tab = self._create_matrix_tab()
        self.tabs.addTab(self.matrix_tab, "📊 Matrix")

        # Tab 4: Dataset Inspector
        self.dataset_tab = self._create_dataset_tab()
        self.tabs.addTab(self.dataset_tab, "📈 Data")

        layout.addWidget(self.tabs)

    # --- Tab 1: Papers Library ---

    def _create_papers_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        toolbar = QHBoxLayout()
        btn_import_pdf = QPushButton("➕ Import PDF...", self)
        btn_import_pdf.clicked.connect(self.action_import_pdf)
        toolbar.addWidget(btn_import_pdf)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Papers Table
        self.papers_table = QTableWidget(0, 4)
        self.papers_table.setHorizontalHeaderLabels(["Title", "Year", "DOI", "Pages"])
        self.papers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.papers_table.itemSelectionChanged.connect(self._on_paper_selected)
        splitter.addWidget(self.papers_table)

        # Detail & Evidence Search
        detail_widget = QWidget()
        d_layout = QVBoxLayout(detail_widget)
        d_layout.setContentsMargins(0, 0, 0, 0)

        d_layout.addWidget(QLabel("Traceable Evidence Search (Ground Claims to Pages):"))
        search_box = QHBoxLayout()
        self.evidence_query_input = QLineEdit()
        self.evidence_query_input.setPlaceholderText("Search terms or claim to locate exact paper pages...")
        btn_search_ev = QPushButton("🔍 Find Evidence")
        btn_search_ev.clicked.connect(self._on_search_evidence)
        search_box.addWidget(self.evidence_query_input)
        search_box.addWidget(btn_search_ev)
        d_layout.addLayout(search_box)

        self.paper_detail_text = QTextEdit()
        self.paper_detail_text.setReadOnly(True)
        self.paper_detail_text.setPlaceholderText("Select a paper above to view extracted metadata and grounded evidence.")
        d_layout.addWidget(self.paper_detail_text)

        splitter.addWidget(detail_widget)
        splitter.setSizes([150, 200])
        layout.addWidget(splitter)
        return widget

    # --- Tab 2: References Manager ---

    def _create_refs_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        toolbar = QHBoxLayout()
        btn_import_bib = QPushButton("📥 Import BibTeX", self)
        btn_import_bib.clicked.connect(self.action_import_bibtex)
        btn_export_bib = QPushButton("📤 Export BibTeX", self)
        btn_export_bib.clicked.connect(self.action_export_bibtex)
        btn_cite = QPushButton("📋 Insert \\cite", self)
        btn_cite.setStyleSheet("font-weight: bold; background-color: #1a73e8; color: white;")
        btn_cite.clicked.connect(self.action_insert_selected_citation)

        toolbar.addWidget(btn_import_bib)
        toolbar.addWidget(btn_export_bib)
        toolbar.addWidget(btn_cite)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Filter
        filter_box = QHBoxLayout()
        self.ref_filter_input = QLineEdit()
        self.ref_filter_input.setPlaceholderText("Filter references by author, title, or key...")
        self.ref_filter_input.textChanged.connect(self._filter_references)
        filter_box.addWidget(QLabel("Filter:"))
        filter_box.addWidget(self.ref_filter_input)
        layout.addLayout(filter_box)

        self.refs_table = QTableWidget(0, 4)
        self.refs_table.setHorizontalHeaderLabels(["Cite Key", "Authors", "Year", "Title"])
        self.refs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.refs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.refs_table)
        return widget

    # --- Tab 3: Literature Matrix ---

    def _create_matrix_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        toolbar = QHBoxLayout()
        btn_gen_matrix = QPushButton("⚡ Generate Matrix", self)
        btn_gen_matrix.clicked.connect(self.action_generate_matrix)
        btn_copy_latex = QPushButton("📋 Copy LaTeX Table", self)
        btn_copy_latex.clicked.connect(self.action_copy_matrix_latex)
        btn_copy_md = QPushButton("📋 Copy Markdown", self)
        btn_copy_md.clicked.connect(self.action_copy_matrix_md)

        toolbar.addWidget(btn_gen_matrix)
        toolbar.addWidget(btn_copy_latex)
        toolbar.addWidget(btn_copy_md)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.matrix_table = QTableWidget(0, 5)
        self.matrix_table.setHorizontalHeaderLabels(["Paper", "Year", "Objective", "Methodology", "Key Results"])
        self.matrix_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.matrix_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.matrix_table)
        return widget

    # --- Tab 4: Dataset Inspector ---

    def _create_dataset_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        toolbar = QHBoxLayout()
        btn_open_csv = QPushButton("📁 Inspect CSV/TSV...", self)
        btn_open_csv.clicked.connect(self.action_inspect_csv)
        self.dataset_info_label = QLabel("No dataset loaded.")
        toolbar.addWidget(btn_open_csv)
        toolbar.addWidget(self.dataset_info_label)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Columns Profile Table
        col_group = QGroupBox("Column Statistics")
        cg_layout = QVBoxLayout(col_group)
        self.dataset_cols_table = QTableWidget(0, 6)
        self.dataset_cols_table.setHorizontalHeaderLabels(["Column", "Type", "Non-Null", "Nulls", "Min", "Max"])
        self.dataset_cols_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cg_layout.addWidget(self.dataset_cols_table)
        splitter.addWidget(col_group)

        # Data Preview Table
        preview_group = QGroupBox("Data Preview (First 50 Rows)")
        pg_layout = QVBoxLayout(preview_group)
        self.dataset_preview_table = QTableWidget(0, 0)
        pg_layout.addWidget(self.dataset_preview_table)
        splitter.addWidget(preview_group)

        splitter.setSizes([140, 200])
        layout.addWidget(splitter)
        return widget

    # --- Actions ---

    def action_import_pdf(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Research PDF", "", "PDF Files (*.pdf)")
        if file_path:
            paper = PDFExtractorService.extract_from_pdf(Path(file_path))
            self.papers.append(paper)
            self._refresh_papers_table()

    def _refresh_papers_table(self) -> None:
        self.papers_table.setRowCount(len(self.papers))
        for row, paper in enumerate(self.papers):
            self.papers_table.setItem(row, 0, QTableWidgetItem(paper.title))
            self.papers_table.setItem(row, 1, QTableWidgetItem(str(paper.year or "")))
            self.papers_table.setItem(row, 2, QTableWidgetItem(paper.doi or "None"))
            self.papers_table.setItem(row, 3, QTableWidgetItem(str(paper.total_pages)))

    def _on_paper_selected(self) -> None:
        row = self.papers_table.currentRow()
        if 0 <= row < len(self.papers):
            paper = self.papers[row]
            authors_str = ", ".join(paper.authors) if paper.authors else "Unknown"
            info = [
                f"Title: {paper.title}",
                f"Authors: {authors_str}",
                f"Year: {paper.year or 'n.d.'} | DOI: {paper.doi or 'None'}",
                f"File: {paper.file_path.name} ({paper.total_pages} pages)",
                "",
                "Abstract:",
                paper.abstract or "No abstract extracted.",
            ]
            self.paper_detail_text.setPlainText("\n".join(info))

    def _on_search_evidence(self) -> None:
        row = self.papers_table.currentRow()
        if not (0 <= row < len(self.papers)):
            QMessageBox.information(self, "Evidence Search", "Select a paper from the list first.")
            return

        query = self.evidence_query_input.text().strip()
        if not query:
            return

        paper = self.papers[row]
        snippets = PDFExtractorService.find_evidence(paper, query)
        if not snippets:
            self.paper_detail_text.setPlainText(f"No direct evidence matches found for '{query}' in {paper.file_path.name}.")
            return

        output = [f"Found {len(snippets)} Grounded Evidence Snippets for query: '{query}':\n"]
        for s in snippets:
            output.append(f"📌 Page {s.page_number} ({s.file_name}):\n\"{s.quote}\"\n")

        self.paper_detail_text.setPlainText("\n".join(output))

    def action_import_bibtex(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Import BibTeX File", "", "BibTeX Files (*.bib)")
        if file_path:
            try:
                content = Path(file_path).read_text(encoding="utf-8", errors="replace")
                items = ReferenceManager.parse_bibtex(content)
                self.references.extend(items)
                self._refresh_refs_table()
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import BibTeX: {e}")

    def action_export_bibtex(self) -> None:
        if not self.references:
            QMessageBox.information(self, "Export", "No references to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export BibTeX File", "references.bib", "BibTeX Files (*.bib)")
        if file_path:
            content = ReferenceManager.export_bibtex(self.references)
            Path(file_path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Exported {len(self.references)} references.")

    def action_insert_selected_citation(self) -> None:
        row = self.refs_table.currentRow()
        if 0 <= row < len(self.references):
            item = self.references[row]
            self.citation_insert_requested.emit(f"\\cite{{{item.key}}}")

    def _refresh_refs_table(self, items: Optional[List[ReferenceItem]] = None) -> None:
        display_items = items if items is not None else self.references
        self.refs_table.setRowCount(len(display_items))
        for row, ref in enumerate(display_items):
            self.refs_table.setItem(row, 0, QTableWidgetItem(ref.key))
            self.refs_table.setItem(row, 1, QTableWidgetItem(ref.author_display))
            self.refs_table.setItem(row, 2, QTableWidgetItem(str(ref.year or "")))
            self.refs_table.setItem(row, 3, QTableWidgetItem(ref.title))

    def _filter_references(self, query: str) -> None:
        query = query.lower().strip()
        if not query:
            self._refresh_refs_table()
            return
        filtered = [
            r for r in self.references
            if query in r.key.lower() or query in r.title.lower() or any(query in a.lower() for a in r.authors)
        ]
        self._refresh_refs_table(filtered)

    def action_generate_matrix(self) -> None:
        if not self.papers:
            QMessageBox.information(self, "Matrix Generator", "Import papers into the library first.")
            return

        self.matrix_rows = LiteratureMatrixGenerator.generate_matrix(self.papers)
        self.matrix_table.setRowCount(len(self.matrix_rows))
        for row, mr in enumerate(self.matrix_rows):
            self.matrix_table.setItem(row, 0, QTableWidgetItem(f"{mr.title}\n({mr.authors})"))
            self.matrix_table.setItem(row, 1, QTableWidgetItem(mr.year))
            self.matrix_table.setItem(row, 2, QTableWidgetItem(mr.objective))
            self.matrix_table.setItem(row, 3, QTableWidgetItem(mr.methodology))
            self.matrix_table.setItem(row, 4, QTableWidgetItem(mr.results))

    def action_copy_matrix_latex(self) -> None:
        if not self.matrix_rows:
            self.action_generate_matrix()
        if self.matrix_rows:
            latex = LiteratureMatrixGenerator.to_latex_table(self.matrix_rows)
            QApplication.clipboard().setText(latex)
            QMessageBox.information(self, "Copied", "LaTeX table code copied to clipboard.")

    def action_copy_matrix_md(self) -> None:
        if not self.matrix_rows:
            self.action_generate_matrix()
        if self.matrix_rows:
            md = LiteratureMatrixGenerator.to_markdown(self.matrix_rows)
            QApplication.clipboard().setText(md)
            QMessageBox.information(self, "Copied", "Markdown table copied to clipboard.")

    def action_inspect_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Dataset", "", "CSV / TSV Files (*.csv *.tsv)")
        if file_path:
            summary = DatasetService.inspect_csv(Path(file_path))
            self.dataset_info_label.setText(
                f"File: {summary.file_name} | {summary.row_count} rows, {summary.col_count} columns"
            )

            # Columns summary
            self.dataset_cols_table.setRowCount(len(summary.columns))
            for row, col in enumerate(summary.columns):
                self.dataset_cols_table.setItem(row, 0, QTableWidgetItem(col.name))
                self.dataset_cols_table.setItem(row, 1, QTableWidgetItem(col.dtype))
                self.dataset_cols_table.setItem(row, 2, QTableWidgetItem(str(col.non_null_count)))
                self.dataset_cols_table.setItem(row, 3, QTableWidgetItem(str(col.null_count)))
                self.dataset_cols_table.setItem(row, 4, QTableWidgetItem(str(col.min_val or "")))
                self.dataset_cols_table.setItem(row, 5, QTableWidgetItem(str(col.max_val or "")))

            # Preview rows
            headers = [c.name for c in summary.columns]
            self.dataset_preview_table.setColumnCount(len(headers))
            self.dataset_preview_table.setHorizontalHeaderLabels(headers)
            self.dataset_preview_table.setRowCount(len(summary.preview_rows))

            for r_idx, row_dict in enumerate(summary.preview_rows):
                for c_idx, h in enumerate(headers):
                    val = str(row_dict.get(h, ""))
                    self.dataset_preview_table.setItem(r_idx, c_idx, QTableWidgetItem(val))
