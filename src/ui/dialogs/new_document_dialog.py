"""New Document Creation Dialog for ResearchIDE."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
)


class NewDocumentDialog(QDialog):
    """Dialog allowing users to add a new file to an existing project."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add New Project Document")
        self.setFixedWidth(420)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("File Name (e.g. methods.tex, literature_review.md):"))
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("section_methodology.tex")
        layout.addWidget(self.filename_input)

        layout.addWidget(QLabel("Document Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "LaTeX Section (src/sections/)",
            "Root LaTeX File (src/)",
            "Research Notes (notes/)",
            "BibTeX Bibliography (src/)",
        ])
        layout.addWidget(self.category_combo)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_create = QPushButton("Add Document")
        btn_create.setProperty("class", "PrimaryBtn")
        btn_create.clicked.connect(self._validate)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_create)
        layout.addLayout(btn_layout)

    def _validate(self) -> None:
        name = self.filename_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please specify a valid file name.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "filename": self.filename_input.text().strip(),
            "category": self.category_combo.currentText(),
        }

