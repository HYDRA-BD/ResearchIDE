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
    QButtonGroup,
    QPushButton,
    QLabel,
    QStackedWidget,
)
from src.ui.editors.code_editor import CodeEditor
from src.ui.editors.visual_editor import VisualEditorWidget
from src.ui.viewer.pdf_viewer import PDFViewerWidget
from src.storage.file_manager import FileManager
from src.core.document import BlockType
from src.utils.logger import app_logger


class DocumentTab(QWidget):
    """Represents an active multi-mode document editor tab supporting Visual, Source, and Split views."""

    content_changed = Signal(bool)  # is_dirty

    def __init__(self, file_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.file_path = Path(file_path).resolve()
        self.is_dirty = False
        self._is_syncing = False

        self._init_ui()
        self.load_content()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Mode Selector Toolbar
        mode_bar = QWidget(self)
        mode_bar.setObjectName("EditorModeBar")
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(6, 4, 6, 4)
        mode_layout.setSpacing(6)

        mode_label = QLabel("Mode:", self)
        mode_label.setStyleSheet("font-weight: 600; color: #666;")
        mode_layout.addWidget(mode_label)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.btn_visual = QPushButton("Visual", self)
        self.btn_visual.setCheckable(True)
        self.btn_visual.setChecked(True)
        self.btn_visual.clicked.connect(lambda: self.set_editor_mode("visual"))
        self.btn_group.addButton(self.btn_visual)
        mode_layout.addWidget(self.btn_visual)

        self.btn_source = QPushButton("LaTeX Source", self)
        self.btn_source.setCheckable(True)
        self.btn_source.clicked.connect(lambda: self.set_editor_mode("source"))
        self.btn_group.addButton(self.btn_source)
        mode_layout.addWidget(self.btn_source)

        self.btn_split = QPushButton("Side-by-Side", self)
        self.btn_split.setCheckable(True)
        self.btn_split.clicked.connect(lambda: self.set_editor_mode("split"))
        self.btn_group.addButton(self.btn_split)
        mode_layout.addWidget(self.btn_split)

        mode_layout.addStretch()
        main_layout.addWidget(mode_bar)

        # Stack/Container for Editors
        self.editor_container = QWidget(self)
        container_layout = QVBoxLayout(self.editor_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Visual Editor
        self.visual_editor = VisualEditorWidget(self)

        # Code Editor
        self.code_editor = CodeEditor(self.file_path, self)

        # Internal Splitter for Side-by-Side (Visual + Source)
        self.internal_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.internal_splitter.addWidget(self.visual_editor)
        self.internal_splitter.addWidget(self.code_editor)
        self.internal_splitter.setSizes([500, 500])

        container_layout.addWidget(self.internal_splitter)
        main_layout.addWidget(self.editor_container)

        # Connect synchronization signals
        self._wire_sync()

        # Start in Visual mode
        self.set_editor_mode("visual")

    def _wire_sync(self) -> None:
        # Visual edits patch CodeEditor text
        self.visual_editor.content_modified.connect(self._on_visual_modified)

        # CodeEditor edits trigger dirty flag
        self.code_editor.textChanged.connect(self._on_source_text_changed)

        # Block focus jumps in source
        self.visual_editor.block_focused.connect(self._on_visual_block_focused)

        # Source cursor movement reflects in visual canvas
        self.code_editor.cursorPositionChanged.connect(self._on_source_cursor_moved)

    def set_editor_mode(self, mode: str) -> None:
        """Switch between 'visual', 'source', and 'split' editor modes."""
        if mode == "visual":
            self.visual_editor.show()
            self.code_editor.hide()
            self.btn_visual.setChecked(True)
            # Sync source changes into visual
            self.visual_editor.load_latex(self.code_editor.toPlainText())
        elif mode == "source":
            self.visual_editor.hide()
            self.code_editor.show()
            self.btn_source.setChecked(True)
        elif mode == "split":
            self.visual_editor.show()
            self.code_editor.show()
            self.internal_splitter.setSizes([500, 500])
            self.btn_split.setChecked(True)
            self.visual_editor.load_latex(self.code_editor.toPlainText())

    def load_content(self) -> None:
        try:
            content = FileManager.read_text(self.file_path)
            self._is_syncing = True
            self.code_editor.setPlainText(content)
            self.visual_editor.load_latex(content)
            self._is_syncing = False
            self.is_dirty = False
            self.content_changed.emit(False)
        except Exception as e:
            app_logger.error(f"Failed to load file '{self.file_path}': {e}")
            self.code_editor.setPlainText(f"% Error reading file: {e}")

    def save_content(self) -> bool:
        try:
            content = self.code_editor.toPlainText()
            FileManager.atomic_write(self.file_path, content)
            self.is_dirty = False
            self.content_changed.emit(False)
            app_logger.info(f"Saved document '{self.file_path.name}'")
            return True
        except Exception as e:
            app_logger.error(f"Failed saving file '{self.file_path}': {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save file: {e}")
            return False

    def _on_visual_modified(self, patched_latex: str) -> None:
        if self._is_syncing:
            return
        self._is_syncing = True
        try:
            # Preserve cursor position if possible
            cursor = self.code_editor.textCursor()
            pos = cursor.position()
            self.code_editor.setPlainText(patched_latex)
            cursor.setPosition(min(pos, len(patched_latex)))
            self.code_editor.setTextCursor(cursor)
            self._mark_dirty()
        finally:
            self._is_syncing = False

    def _on_source_text_changed(self) -> None:
        if self._is_syncing:
            return
        self._mark_dirty()

    def _mark_dirty(self) -> None:
        if not self.is_dirty:
            self.is_dirty = True
            self.content_changed.emit(True)

    def _on_visual_block_focused(self, block_id: str, start_line: int, end_line: int) -> None:
        """Jump source editor cursor to start line of selected block."""
        self.code_editor.go_to_line(start_line)

    def _on_source_cursor_moved(self) -> None:
        if self._is_syncing:
            return
        line = self.code_editor.textCursor().blockNumber() + 1
        self.visual_editor.scroll_to_source_line(line)

    def insert_element(self, block_type: BlockType, content: str = "") -> None:
        """Insert an element into the document."""
        self.visual_editor.insert_element(block_type, content)

    @property
    def editor(self) -> CodeEditor:
        """Convenience accessor for backward-compatibility."""
        return self.code_editor


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
            return current_tab.code_editor
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
                tab.code_editor.go_to_line(line_number)
                return

        editor = self.get_current_editor()
        if editor:
            editor.go_to_line(line_number)

    def insert_element_in_current(self, block_type: BlockType, content: str = "") -> None:
        """Insert element into currently active document tab."""
        tab = self.get_current_tab()
        if tab:
            tab.insert_element(block_type, content)
