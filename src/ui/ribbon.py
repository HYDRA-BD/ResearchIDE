"""Office-Inspired Ribbon Toolbar for ResearchIDE."""
from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QLabel,
    QGroupBox,
)


class RibbonBar(QFrame):
    """Office-style ribbon toolbar with categorized academic tabs."""

    # Action signals
    new_project_clicked = Signal()
    open_project_clicked = Signal()
    save_document_clicked = Signal()
    compile_clicked = Signal()
    settings_clicked = Signal()
    new_document_clicked = Signal()
    view_mode_changed = Signal(str)  # 'split', 'editor_only', 'pdf_only'
    forward_sync_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("RibbonContainer")
        self.setFixedHeight(115)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 4)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("RibbonTabs")

        # Create Ribbon Tabs
        self.home_tab = self._create_home_tab()
        self.insert_tab = self._create_insert_tab()
        self.references_tab = self._create_references_tab()
        self.view_tab = self._create_view_tab()
        self.ai_tab = self._create_ai_tab()

        self.tab_widget.addTab(self.home_tab, "Home")
        self.tab_widget.addTab(self.insert_tab, "Insert")
        self.tab_widget.addTab(self.references_tab, "References")
        self.tab_widget.addTab(self.view_tab, "View")
        self.tab_widget.addTab(self.ai_tab, "AI Assistant")

        main_layout.addWidget(self.tab_widget)

    def _create_group(self, title: str) -> tuple[QGroupBox, QHBoxLayout]:
        group = QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-size: 10px; color: #888899; border: 1px solid #2a2a34; border-radius: 4px; margin-top: 10px; padding: 2px; } QGroupBox::title { subcontrol-origin: margin; left: 6px; top: 0px; }")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(4)
        return group, layout

    def _create_home_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(6, 2, 6, 2)
        tab_layout.setSpacing(8)

        # 1. Project Management Group
        proj_group, proj_layout = self._create_group("Project")
        btn_new_proj = QPushButton("📄 New Project")
        btn_new_proj.setProperty("class", "RibbonBtn")
        btn_new_proj.clicked.connect(self.new_project_clicked.emit)

        btn_open_proj = QPushButton("📂 Open Project")
        btn_open_proj.setProperty("class", "RibbonBtn")
        btn_open_proj.clicked.connect(self.open_project_clicked.emit)

        btn_save = QPushButton("💾 Save")
        btn_save.setProperty("class", "RibbonBtn")
        btn_save.clicked.connect(self.save_document_clicked.emit)

        proj_layout.addWidget(btn_new_proj)
        proj_layout.addWidget(btn_open_proj)
        proj_layout.addWidget(btn_save)
        tab_layout.addWidget(proj_group)

        # 2. Document Group
        doc_group, doc_layout = self._create_group("Document")
        btn_new_doc = QPushButton("➕ Add File")
        btn_new_doc.setProperty("class", "RibbonBtn")
        btn_new_doc.clicked.connect(self.new_document_clicked.emit)

        btn_compile = QPushButton("⚙️ Compile PDF")
        btn_compile.setProperty("class", "RibbonBtn")
        btn_compile.setStyleSheet("font-weight: bold; color: #4daafc;")
        btn_compile.clicked.connect(self.compile_clicked.emit)

        doc_layout.addWidget(btn_new_doc)
        doc_layout.addWidget(btn_compile)
        tab_layout.addWidget(doc_group)

        # 3. Preferences Group
        pref_group, pref_layout = self._create_group("Preferences")
        btn_settings = QPushButton("⚙️ Settings")
        btn_settings.setProperty("class", "RibbonBtn")
        btn_settings.clicked.connect(self.settings_clicked.emit)

        pref_layout.addWidget(btn_settings)
        tab_layout.addWidget(pref_group)

        tab_layout.addStretch()
        return tab

    def _create_insert_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(6, 2, 6, 2)
        tab_layout.setSpacing(8)

        struct_group, struct_layout = self._create_group("Academic Structure")
        btn_sec = QPushButton("📑 Section")
        btn_sec.setProperty("class", "RibbonBtn")
        btn_eq = QPushButton("∑ Equation")
        btn_eq.setProperty("class", "RibbonBtn")
        btn_fig = QPushButton("🖼️ Figure")
        btn_fig.setProperty("class", "RibbonBtn")
        btn_tbl = QPushButton("📊 Table")
        btn_tbl.setProperty("class", "RibbonBtn")

        struct_layout.addWidget(btn_sec)
        struct_layout.addWidget(btn_eq)
        struct_layout.addWidget(btn_fig)
        struct_layout.addWidget(btn_tbl)
        tab_layout.addWidget(struct_group)

        tab_layout.addStretch()
        return tab

    def _create_references_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(6, 2, 6, 2)

        ref_group, ref_layout = self._create_group("Citations & BibTeX")
        btn_cite = QPushButton("📖 Insert Citation")
        btn_cite.setProperty("class", "RibbonBtn")
        btn_import_bib = QPushButton("📥 Import .bib")
        btn_import_bib.setProperty("class", "RibbonBtn")
        btn_verify_cites = QPushButton("🔍 Verify Citations")
        btn_verify_cites.setProperty("class", "RibbonBtn")

        ref_layout.addWidget(btn_cite)
        ref_layout.addWidget(btn_import_bib)
        ref_layout.addWidget(btn_verify_cites)
        tab_layout.addWidget(ref_group)

        tab_layout.addStretch()
        return tab

    def _create_view_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(6, 2, 6, 2)

        view_group, view_layout = self._create_group("Layout Modes")
        btn_split = QPushButton("🔀 Split View")
        btn_split.setProperty("class", "RibbonBtn")
        btn_split.clicked.connect(lambda: self.view_mode_changed.emit("split"))

        btn_editor_only = QPushButton("📝 Editor Only")
        btn_editor_only.setProperty("class", "RibbonBtn")
        btn_editor_only.clicked.connect(lambda: self.view_mode_changed.emit("editor_only"))

        btn_pdf_only = QPushButton("📄 PDF Only")
        btn_pdf_only.setProperty("class", "RibbonBtn")
        btn_pdf_only.clicked.connect(lambda: self.view_mode_changed.emit("pdf_only"))

        btn_sync = QPushButton("🎯 Sync to PDF")
        btn_sync.setProperty("class", "RibbonBtn")
        btn_sync.clicked.connect(self.forward_sync_clicked.emit)

        view_layout.addWidget(btn_split)
        view_layout.addWidget(btn_editor_only)
        view_layout.addWidget(btn_pdf_only)
        view_layout.addWidget(btn_sync)
        tab_layout.addWidget(view_group)

        tab_layout.addStretch()
        return tab

    def _create_ai_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(6, 2, 6, 2)

        ai_group, ai_layout = self._create_group("Local AI (Ollama)")
        btn_rewrite = QPushButton("✍️ Academic Rewrite")
        btn_rewrite.setProperty("class", "RibbonBtn")
        btn_explain = QPushButton("💡 Explain TeX Error")
        btn_explain.setProperty("class", "RibbonBtn")
        btn_math = QPushButton("📐 Verify Math (SymPy)")
        btn_math.setProperty("class", "RibbonBtn")

        ai_layout.addWidget(btn_rewrite)
        ai_layout.addWidget(btn_explain)
        ai_layout.addWidget(btn_math)
        tab_layout.addWidget(ai_group)

        tab_layout.addStretch()
        return tab

