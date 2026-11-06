"""New Project Creation Dialog for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QComboBox,
    QMessageBox,
)


class NewProjectDialog(QDialog):
    """Dialog allowing users to initialize a new research project."""

    def __init__(self, default_parent_dir: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create New Research Project")
        self.setFixedWidth(520)
        self.default_parent_dir = default_parent_dir
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Project Name
        layout.addWidget(QLabel("Project Name (Required):"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Quantum_Turbulence_Study")
        layout.addWidget(self.name_input)

        # 2. Location
        layout.addWidget(QLabel("Parent Directory:"))
        loc_layout = QHBoxLayout()
        self.loc_input = QLineEdit(self.default_parent_dir)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_dir)
        loc_layout.addWidget(self.loc_input)
        loc_layout.addWidget(btn_browse)
        layout.addLayout(loc_layout)

        # 3. Starter Template
        layout.addWidget(QLabel("Starter Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "Standard Academic Article (pdflatex)",
            "IEEE Conference / Journal",
            "ACM Two-Column Format",
            "Springer Nature LNCS",
            "Blank Research Workspace",
        ])
        layout.addWidget(self.template_combo)

        # 4. Description
        layout.addWidget(QLabel("Project Description / Abstract (Optional):"))
        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(80)
        self.desc_input.setPlaceholderText("Brief summary of research questions or methodology...")
        layout.addWidget(self.desc_input)

        # 5. Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        self.btn_create = QPushButton("Create Project")
        self.btn_create.setProperty("class", "PrimaryBtn")
        self.btn_create.clicked.connect(self._validate_and_accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_create)
        layout.addLayout(btn_layout)

    def _browse_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select Parent Folder", self.loc_input.text())
        if chosen:
            self.loc_input.setText(chosen)

    def _validate_and_accept(self) -> None:
        name = self.name_input.text().strip()
        loc = self.loc_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid project name.")
            return
        if not loc or not Path(loc).exists():
            QMessageBox.warning(self, "Invalid Directory", "The selected parent directory does not exist.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "parent_dir": self.loc_input.text().strip(),
            "template": self.template_combo.currentText(),
            "description": self.desc_input.toPlainText().strip(),
        }

