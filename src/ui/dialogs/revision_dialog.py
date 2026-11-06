"""Document Revision History & Comparison Dialog for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QPushButton,
    QSplitter,
    QMessageBox,
)
from src.services.revision_service import RevisionManager, RevisionItem
from src.storage.file_manager import FileManager


class RevisionHistoryDialog(QDialog):
    """Dialog allowing users to inspect, diff, and restore historical document versions."""

    def __init__(
        self,
        project_dir: Path,
        file_path: Path,
        parent: Optional[QDialog] = None,
    ) -> None:
        super().__init__(parent)
        self.project_dir = Path(project_dir).resolve()
        self.file_path = Path(file_path).resolve()
        self.revisions: List[RevisionItem] = []

        self.setWindowTitle(f"Revision History — {self.file_path.name}")
        self.resize(780, 520)
        self._init_ui()
        self.load_revisions()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Revisions List
        left_widget = QWidget()
        l_layout = QVBoxLayout(left_widget)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.addWidget(QLabel("Saved Checkpoints:"))

        self.rev_list = QListWidget()
        self.rev_list.currentRowChanged.connect(self._on_revision_selected)
        l_layout.addWidget(self.rev_list)
        splitter.addWidget(left_widget)

        # Right: Revision Preview & Diff
        right_widget = QWidget()
        r_layout = QVBoxLayout(right_widget)
        r_layout.setContentsMargins(0, 0, 0, 0)

        self.diff_label = QLabel("Diff vs Current Active File:")
        r_layout.addWidget(self.diff_label)

        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        r_layout.addWidget(self.preview_edit)
        splitter.addWidget(right_widget)

        splitter.setSizes([260, 520])
        layout.addWidget(splitter, 1)

        # Bottom Actions
        action_bar = QHBoxLayout()
        self.btn_restore = QPushButton("⏪ Restore This Revision", self)
        self.btn_restore.setStyleSheet("font-weight: bold; background-color: #d9534f; color: white;")
        self.btn_restore.setEnabled(False)
        self.btn_restore.clicked.connect(self.action_restore)

        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.accept)

        action_bar.addWidget(self.btn_restore)
        action_bar.addStretch()
        action_bar.addWidget(btn_close)
        layout.addLayout(action_bar)

    def load_revisions(self) -> None:
        self.revisions = RevisionManager.list_revisions(self.project_dir, self.file_path)
        self.rev_list.clear()

        if not self.revisions:
            self.preview_edit.setPlainText("No revisions recorded yet. Revisions are created automatically on each save.")
            return

        for rev in self.revisions:
            label = f"{rev.formatted_time} ({rev.byte_size} bytes)"
            if rev.summary_label:
                label += f" - {rev.summary_label}"
            item = QListWidgetItem(label)
            self.rev_list.addItem(item)

        self.rev_list.setCurrentRow(0)

    def _on_revision_selected(self, row: int) -> None:
        if 0 <= row < len(self.revisions):
            rev = self.revisions[row]
            current_content = FileManager.read_text(self.file_path) if self.file_path.exists() else ""
            diff_text = RevisionManager.compare_revisions(
                rev.content,
                current_content,
                label_a=f"Revision {rev.formatted_time}",
                label_b="Current Working File",
            )
            if diff_text:
                self.preview_edit.setPlainText(diff_text)
            else:
                self.preview_edit.setPlainText(f"--- Revision Content ({rev.formatted_time}) ---\n\n" + rev.content)
            self.btn_restore.setEnabled(True)

    def action_restore(self) -> None:
        row = self.rev_list.currentRow()
        if 0 <= row < len(self.revisions):
            rev = self.revisions[row]
            reply = QMessageBox.question(
                self,
                "Confirm Revision Rollback",
                f"Restore '{self.file_path.name}' to revision from {rev.formatted_time}?\n"
                "A safety backup of the current state will be created automatically.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                res = RevisionManager.restore_revision(self.project_dir, self.file_path, rev.revision_id)
                if res is not None:
                    QMessageBox.information(self, "Restored", "Revision restored successfully.")
                    self.accept()
