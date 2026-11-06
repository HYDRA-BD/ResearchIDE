"""High-DPI PDF Preview Canvas with Continuous Scrolling and SyncTeX Navigation."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QMouseEvent
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSpinBox,
    QLineEdit,
    QFrame,
    QComboBox,
)
from src.utils.logger import app_logger


class InteractivePdfView(QPdfView):
    """Custom QPdfView catching double-clicks and Ctrl+clicks for inverse SyncTeX."""

    synctex_clicked = Signal(int, float, float)  # page, x, y (in PDF points)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._handle_synctex_click(event)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self._handle_synctex_click(event)
        super().mousePressEvent(event)

    def _handle_synctex_click(self, event: QMouseEvent) -> None:
        pos = event.position()
        current_page = self.pageNavigator().currentPage()

        # Approximate coordinate mapping inside viewport
        scale = self.zoomFactor()
        pdf_x = pos.x() / max(0.1, scale)
        pdf_y = pos.y() / max(0.1, scale)

        app_logger.debug(f"SyncTeX click on PDF: page={current_page}, x={pdf_x:.1f}, y={pdf_y:.1f}")
        self.synctex_clicked.emit(current_page, pdf_x, pdf_y)


class PDFViewerWidget(QWidget):
    """Integrated PDF presentation canvas with zoom, navigation, and SyncTeX hooks."""

    synctex_jump_requested = Signal(int, float, float)  # page, x, y

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_pdf_path: Optional[Path] = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Navigation & Zoom Toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        # 2. PDF Document & View
        self.document = QPdfDocument(self)
        self.document.statusChanged.connect(self._on_doc_status_changed)

        self.pdf_view = InteractivePdfView(self)
        self.pdf_view.setDocument(self.document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)  # Continuous scrolling
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_view.synctex_clicked.connect(self.synctex_jump_requested.emit)

        layout.addWidget(self.pdf_view)

        # 3. Search Model
        self.search_model = QPdfSearchModel(self)
        self.search_model.setDocument(self.document)

    def _create_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #1a1a20; border-bottom: 1px solid #282832; padding: 2px 4px; }")
        t_layout = QHBoxLayout(frame)
        t_layout.setContentsMargins(4, 2, 4, 2)
        t_layout.setSpacing(6)

        # Page Navigation
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(28, 26)
        self.btn_prev.clicked.connect(self.previous_page)

        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(1)
        self.page_spin.valueChanged.connect(self._on_spin_page_changed)

        self.page_count_label = QLabel("/ 1")
        self.page_count_label.setStyleSheet("color: #888899; font-size: 11px;")

        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(28, 26)
        self.btn_next.clicked.connect(self.next_page)

        t_layout.addWidget(self.btn_prev)
        t_layout.addWidget(self.page_spin)
        t_layout.addWidget(self.page_count_label)
        t_layout.addWidget(self.btn_next)

        # Zoom Controls
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedSize(28, 26)
        self.btn_zoom_out.clicked.connect(self.zoom_out)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(28, 26)
        self.btn_zoom_in.clicked.connect(self.zoom_in)

        self.zoom_mode_combo = QComboBox()
        self.zoom_mode_combo.addItems(["Fit to Width", "Fit in View", "100%", "150%", "200%"])
        self.zoom_mode_combo.currentIndexChanged.connect(self._on_zoom_mode_changed)

        t_layout.addWidget(self.btn_zoom_out)
        t_layout.addWidget(self.btn_zoom_in)
        t_layout.addWidget(self.zoom_mode_combo)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find in PDF...")
        self.search_input.setFixedWidth(130)
        self.search_input.returnPressed.connect(self._search_text)
        t_layout.addWidget(self.search_input)

        t_layout.addStretch()
        return frame

    def load_pdf(self, pdf_path: Path | str) -> bool:
        """Load and display a compiled PDF."""
        path = Path(pdf_path).resolve()
        if not path.exists():
            app_logger.warning(f"PDF file does not exist: {path}")
            return False

        self.current_pdf_path = path
        old_page = self.pdf_view.pageNavigator().currentPage()

        # Load document
        self.document.load(str(path))
        pages = max(1, self.document.pageCount())
        self.page_spin.setRange(1, pages)
        self.page_count_label.setText(f"/ {pages}")

        # Restore page position if valid
        if old_page < pages:
            self.pdf_view.pageNavigator().jump(old_page, QPointF(), 0)

        app_logger.info(f"Loaded PDF: {path.name} ({pages} pages)")
        return True

    def _on_doc_status_changed(self, status) -> None:
        pages = max(1, self.document.pageCount())
        self.page_spin.setRange(1, pages)
        self.page_count_label.setText(f"/ {pages}")

    def previous_page(self) -> None:
        nav = self.pdf_view.pageNavigator()
        if nav.currentPage() > 0:
            nav.jump(nav.currentPage() - 1, QPointF(), 0)
            self.page_spin.setValue(nav.currentPage() + 1)

    def next_page(self) -> None:
        nav = self.pdf_view.pageNavigator()
        if nav.currentPage() < self.document.pageCount() - 1:
            nav.jump(nav.currentPage() + 1, QPointF(), 0)
            self.page_spin.setValue(nav.currentPage() + 1)

    def _on_spin_page_changed(self, val: int) -> None:
        nav = self.pdf_view.pageNavigator()
        target_page = val - 1
        if target_page != nav.currentPage() and 0 <= target_page < self.document.pageCount():
            nav.jump(target_page, QPointF(), 0)

    def zoom_in(self) -> None:
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * 1.2)

    def zoom_out(self) -> None:
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(max(0.2, self.pdf_view.zoomFactor() / 1.2))

    def _on_zoom_mode_changed(self, idx: int) -> None:
        if idx == 0:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        elif idx == 1:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        elif idx == 2:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
            self.pdf_view.setZoomFactor(1.0)
        elif idx == 3:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
            self.pdf_view.setZoomFactor(1.5)
        elif idx == 4:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
            self.pdf_view.setZoomFactor(2.0)

    def scroll_to_page_and_point(self, page_0based: int, x: float = 0.0, y: float = 0.0) -> None:
        """Jump and scroll directly to page coordinate for SyncTeX forward sync."""
        if 0 <= page_0based < self.document.pageCount():
            nav = self.pdf_view.pageNavigator()
            nav.jump(page_0based, QPointF(x, y), 0)
            self.page_spin.setValue(page_0based + 1)

    def _search_text(self) -> None:
        query = self.search_input.text().strip()
        if query:
            self.search_model.setSearchString(query)

