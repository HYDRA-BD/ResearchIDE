"""Settings Dialog for ResearchIDE Configuration."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QFormLayout,
)
from src.utils.config import AppSettings


class SettingsDialog(QDialog):
    """Preferences and configuration dialog."""

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ResearchIDE Preferences")
        self.setFixedSize(580, 440)
        self.settings = settings
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_appearance_tab(), "Appearance")
        self.tabs.addTab(self._create_general_tab(), "General & Storage")
        self.tabs.addTab(self._create_compiler_tab(), "LaTeX Compiler")
        self.tabs.addTab(self._create_ai_tab(), "Local AI (Ollama)")
        self.tabs.addTab(self._create_performance_tab(), "Performance")

        main_layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save Preferences")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.clicked.connect(self._save_and_accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        main_layout.addLayout(btn_layout)

    def _create_appearance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.settings.appearance.theme)
        layout.addRow("Color Theme:", self.theme_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        self.font_size_spin.setValue(self.settings.appearance.font_size)
        layout.addRow("Base Font Size (pt):", self.font_size_spin)

        self.font_family_input = QLineEdit(self.settings.appearance.editor_font_family)
        layout.addRow("Editor Font Family:", self.font_family_input)
        return widget

    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)

        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit(self.settings.default_project_dir)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_default_dir)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(btn_browse)
        layout.addRow("Default Projects Folder:", dir_layout)

        self.autosave_check = QCheckBox("Enable Background Autosave")
        self.autosave_check.setChecked(self.settings.autosave_enabled)
        layout.addRow("Autosave:", self.autosave_check)

        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(10, 600)
        self.autosave_interval.setValue(self.settings.autosave_interval_seconds)
        layout.addRow("Autosave Interval (seconds):", self.autosave_interval)
        return widget

    def _create_compiler_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["pdflatex", "xelatex", "lualatex"])
        self.engine_combo.setCurrentText(self.settings.compiler.active_engine)
        layout.addRow("Default LaTeX Engine:", self.engine_combo)

        bin_layout = QHBoxLayout()
        self.bin_input = QLineEdit(self.settings.compiler.custom_bin_path)
        btn_bin_browse = QPushButton("Browse...")
        btn_bin_browse.clicked.connect(self._browse_compiler_bin)
        bin_layout.addWidget(self.bin_input)
        bin_layout.addWidget(btn_bin_browse)
        layout.addRow("TeX Binaries Directory:", bin_layout)

        self.auto_compile_check = QCheckBox("Automatically compile on save")
        self.auto_compile_check.setChecked(self.settings.compiler.auto_compile_on_save)
        layout.addRow("Build Automation:", self.auto_compile_check)

        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(200, 5000)
        self.debounce_spin.setValue(self.settings.compiler.debounce_ms)
        layout.addRow("Compile Debounce (ms):", self.debounce_spin)
        return widget

    def _create_ai_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)

        self.ai_host_input = QLineEdit(self.settings.ai.ollama_host)
        layout.addRow("Ollama Endpoint:", self.ai_host_input)

        self.ai_model_input = QLineEdit(self.settings.ai.active_model)
        layout.addRow("Active Model Tag:", self.ai_model_input)

        self.ai_context_spin = QSpinBox()
        self.ai_context_spin.setRange(2048, 65536)
        self.ai_context_spin.setSingleStep(2048)
        self.ai_context_spin.setValue(self.settings.ai.context_length)
        layout.addRow("Context Length (Tokens):", self.ai_context_spin)
        return widget

    def _create_performance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 12)
        self.threads_spin.setValue(self.settings.performance.max_worker_threads)
        layout.addRow("Max Background Worker Threads:", self.threads_spin)

        self.throttle_check = QCheckBox("Throttle background indexing during editing")
        self.throttle_check.setChecked(self.settings.performance.throttle_background_indexing)
        layout.addRow("Resource Governor:", self.throttle_check)
        return widget

    def _browse_default_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select Projects Folder", self.dir_input.text())
        if chosen:
            self.dir_input.setText(chosen)

    def _browse_compiler_bin(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select TeX Bin Folder", self.bin_input.text())
        if chosen:
            self.bin_input.setText(chosen)

    def _save_and_accept(self) -> None:
        self.settings.appearance.theme = self.theme_combo.currentText()
        self.settings.appearance.font_size = self.font_size_spin.value()
        self.settings.appearance.editor_font_family = self.font_family_input.text().strip()

        self.settings.default_project_dir = self.dir_input.text().strip()
        self.settings.autosave_enabled = self.autosave_check.isChecked()
        self.settings.autosave_interval_seconds = self.autosave_interval.value()

        self.settings.compiler.active_engine = self.engine_combo.currentText()
        self.settings.compiler.custom_bin_path = self.bin_input.text().strip()
        self.settings.compiler.auto_compile_on_save = self.auto_compile_check.isChecked()
        self.settings.compiler.debounce_ms = self.debounce_spin.value()

        self.settings.ai.ollama_host = self.ai_host_input.text().strip()
        self.settings.ai.active_model = self.ai_model_input.text().strip()
        self.settings.ai.context_length = self.ai_context_spin.value()

        self.settings.performance.max_worker_threads = self.threads_spin.value()
        self.settings.performance.throttle_background_indexing = self.throttle_check.isChecked()

        self.accept()

