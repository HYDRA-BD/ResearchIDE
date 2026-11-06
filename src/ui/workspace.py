"""Multi-Document Workspace Tab Manager for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QPlainTextEdit,
    QMessageBox,
)
from src.storage.file_manager import FileManager
from src.utils.logger import app_logger


class DocumentTab(QWidget):
    """Represents a single open document in the workspace."""

    content_changed = Signal(bool)  # is_dirty

    def __init__(self, file_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.file_path = Path(file_path).resolve()
        self.is_dirty = False
        self._init_ui()
        self.load_content()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QPlainTextEdit()
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(font)
        self.editor.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.editor)

    def load_content(self) -> None:
        """Read content from disk into editor."""
        try:
            content = FileManager.read_text(self.file_path)
            self.editor.setPlainText(content)
            self.is_dirty = False
            self.content_changed.emit(False)
        except Exception as e:
            app_logger.error(f"Failed to read file '{self.file_path}': {e}")
            self.editor.setPlainText(f"% Error loading file: {e}")

    def save_content(self) -> bool:
        """Write current buffer to disk atomically."""
        try:
            content = self.editor.toPlainText()
            FileManager.atomic_write(self.file_path, content)
            self.is_dirty = False
            self.content_changed.emit(False)
            app_logger.info(f"Saved document '{self.file_path.name}'")
            return True
        except Exception as e:
            app_logger.error(f"Failed saving '{self.file_path}': {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save file: {e}")
            return False

    def _on_text_changed(self) -> None:
        if not self.is_dirty:
            self.is_dirty = True
            self.content_changed.emit(True)


class DocumentWorkspace(QWidget):
    """Tab widget container managing multiple active document editors."""

    document_dirty_changed = Signal(str, bool)  # path, is_dirty

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.open_tabs: Dict[str, DocumentTab] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tabs)

    def open_document(self, file_path: Path | str) -> DocumentTab:
        """Open a file into a new or existing tab."""
        path = Path(file_path).resolve()
        norm_key = str(path)

        if norm_key in self.open_tabs:
            tab = self.open_tabs[norm_key]
            self.tabs.setCurrentWidget(tab)
            return tab

        tab = DocumentTab(path)
        tab.content_changed.connect(lambda dirty: self._update_tab_title(norm_key, dirty))
        self.open_tabs[norm_key] = tab
        idx = self.tabs.addTab(tab, path.name)
        self.tabs.setCurrentIndex(idx)
        return tab

    def save_current_document(self) -> bool:
        """Save currently focused document tab."""
        current = self.tabs.currentWidget()
        if isinstance(current, DocumentTab):
            return current.save_content()
        return False

    def save_all_documents(self) -> None:
        """Save all open document tabs."""
        for tab in self.open_tabs.values():
            if tab.is_dirty:
                tab.save_content()

    def close_tab(self, index: int) -> None:
        """Close tab at given index, prompting if unsaved."""
        widget = self.tabs.widget(index)
        if isinstance(widget, DocumentTab):
            if widget.is_dirty:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"'{widget.file_path.name}' has unsaved changes. Save before closing?",
                    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                )
                if reply == QMessageBox.StandardButton.Save:
                    if not widget.save_content():
                        return
                elif reply == QMessageBox.StandardButton.Cancel:
                    return

            norm_key = str(widget.file_path)
            if norm_key in self.open_tabs:
                del self.open_tabs[norm_key]
            self.tabs.removeTab(index)

    def close_all_tabs(self) -> None:
        """Close all tabs."""
        while self.tabs.count() > 0:
            self.close_tab(0)

    def _update_tab_title(self, norm_key: str, is_dirty: bool) -> None:
        tab = self.open_tabs.get(norm_key)
        if tab:
            idx = self.tabs.indexOf(tab)
            if idx != -1:
                prefix = "* " if is_dirty else ""
                self.tabs.setTabText(idx, f"{prefix}{tab.file_path.name}")
            self.document_dirty_changed.emit(norm_key, is_dirty)

