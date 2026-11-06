"""Project Explorer Tree Widget for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Signal, QDir, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeView,
    QLabel,
    QMenu,
    QMessageBox,
    QFileSystemModel,
)
import subprocess


class ProjectExplorer(QWidget):
    """Hierarchical project tree view for active workspace files."""

    file_selected = Signal(str)  # absolute path of double-clicked file
    new_file_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_root: Path | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        self.title_label = QLabel("PROJECT EXPLORER")
        self.title_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #888899; padding: 4px;")
        layout.addWidget(self.title_label)

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        # Hide Size, Type, Date Modified columns
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.doubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self.tree)

    def set_project_root(self, root_path: Path | str) -> None:
        """Root the explorer tree at the active project directory."""
        self.project_root = Path(root_path).resolve()
        idx = self.model.setRootPath(str(self.project_root))
        self.tree.setRootIndex(idx)
        self.title_label.setText(f"PROJECT: {self.project_root.name.upper()}")

    def _on_item_double_clicked(self, index) -> None:
        file_path = self.model.filePath(index)
        if Path(file_path).is_file():
            self.file_selected.emit(file_path)

    def _on_context_menu(self, position) -> None:
        index = self.tree.indexAt(position)
        menu = QMenu(self)

        action_new = menu.addAction("Add New Document...")
        action_new.triggered.connect(self.new_file_requested.emit)

        if index.isValid():
            target_path = Path(self.model.filePath(index))
            action_reveal = menu.addAction("Reveal in File Explorer")
            action_reveal.triggered.connect(lambda: self._reveal_in_explorer(target_path))

            if target_path != self.project_root:
                action_delete = menu.addAction("Delete File")
                action_delete.triggered.connect(lambda: self._confirm_delete(target_path))

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _reveal_in_explorer(self, path: Path) -> None:
        try:
            if path.is_dir():
                subprocess.run(["explorer", str(path)])
            else:
                subprocess.run(["explorer", f"/select,{str(path)}"])
        except Exception:
            pass

    def _confirm_delete(self, path: Path) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to permanently delete '{path.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete '{path.name}': {e}")
