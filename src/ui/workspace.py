"""Multi-Document Split-View Workspace Manager for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QSplitter,
    QMessageBox,
)
from src.ui.editors.code_editor import CodeEditor
from src.ui.viewer.pdf_viewer import PDFViewerWidget
from src.storage.file_manager import FileManager
from src.utils.logger import app_logger


class DocumentTab(QWidget):
    """Represents an active document editor tab."""

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

        # Code Editor with Line Numbers & Highlighting
        self.editor = CodeEditor(self.file_path, self)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor)

    def load_content(self) -> None:
        try:
            content = FileManager.read_text(self.file_path)
            self.editor.setPlainText(content)
            self.is_dirty = False
            self.content_changed.emit(False)
        except Exception as e:
            app_logger.error(f"Failed to load file '{self.file_path}': {e}")
            self.editor.setPlainText(f"% Error reading file: {e}")

    def save_content(self) -> bool:
        try:
            content = self.editor.toPlainText()
            FileManager.atomic_write(self.file_path, content)
            self.is_dirty = False
            self.content_changed.emit(False)
            app_logger.info(f"Saved document '{self.file_path.name}'")
            return True
        except Exception as e:
            app_logger.error(f"Failed saving file '{self.file_path}': {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save file: {e}")
            return False

    def _on_text_changed(self) -> None:
        if not self.is_dirty:
            self.is_dirty = True
            self.content_changed.emit(True)


class DocumentWorkspace(QWidget):
    """Split-view workspace managing multi-file editors alongside synchronized PDF preview."""

    document_dirty_changed = Signal(str, bool)  # path, is_dirty
    synctex_inverse_requested = Signal(int, float, float)  # page, x, y

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.open_tabs: Dict[str, DocumentTab] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Horizontal Splitter: Left = Editor Tabs, Right = PDF Viewer
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Container: Document Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # Right Container: PDF Viewer
        self.pdf_viewer = PDFViewerWidget(self)
        self.pdf_viewer.synctex_jump_requested.connect(self.synctex_inverse_requested.emit)

        self.splitter.addWidget(self.tabs)
        self.splitter.addWidget(self.pdf_viewer)
        self.splitter.setSizes([700, 600])

        main_layout.addWidget(self.splitter)

    def open_document(self, file_path: Path | str) -> DocumentTab:
        """Open or focus a document tab."""
        path = Path(file_path).resolve()
        norm_key = str(path)

        if norm_key in self.open_tabs:
            tab = self.open_tabs[norm_key]
            self.tabs.setCurrentWidget(tab)
            return tab

        tab = DocumentTab(path, self)
        tab.content_changed.connect(lambda dirty: self._update_tab_title(norm_key, dirty))
        self.open_tabs[norm_key] = tab
        idx = self.tabs.addTab(tab, path.name)
        self.tabs.setCurrentIndex(idx)
        return tab

    def get_current_editor(self) -> Optional[CodeEditor]:
        """Return the active CodeEditor instance."""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, DocumentTab):
            return current_tab.editor
        return None

    def get_current_tab(self) -> Optional[DocumentTab]:
        current = self.tabs.currentWidget()
        return current if isinstance(current, DocumentTab) else None

    def save_current_document(self) -> bool:
        tab = self.get_current_tab()
        if tab:
            return tab.save_content()
        return False

    def save_all_documents(self) -> None:
        for tab in self.open_tabs.values():
            if tab.is_dirty:
                tab.save_content()

    def close_tab(self, index: int) -> None:
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

    # --- View Mode Controls ---

    def set_split_mode(self, mode: str) -> None:
        """Configure layout visibility: 'split', 'editor_only', 'pdf_only'."""
        if mode == "editor_only":
            self.tabs.show()
            self.pdf_viewer.hide()
        elif mode == "pdf_only":
            self.tabs.hide()
            self.pdf_viewer.show()
        else:  # 'split'
            self.tabs.show()
            self.pdf_viewer.show()
            self.splitter.setSizes([700, 600])

    def load_pdf(self, pdf_path: Path | str) -> bool:
        """Forward PDF reload to the embedded viewer."""
        return self.pdf_viewer.load_pdf(pdf_path)

    def navigate_to_line(self, file_name: str, line_number: int) -> None:
        """Jump to specified line in the matching open editor tab."""
        for norm_key, tab in self.open_tabs.items():
            if tab.file_path.name == file_name or tab.file_path.stem == Path(file_name).stem:
                self.tabs.setCurrentWidget(tab)
                tab.editor.go_to_line(line_number)
                return

        # If file is not open, current tab editor is focused
        editor = self.get_current_editor()
        if editor:
            editor.go_to_line(line_number)
