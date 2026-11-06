"""AI Assistant Dockable Panel with Suggestion Diff & Permission Controls."""
from __future__ import annotations
from typing import Optional, Callable
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QPlainTextEdit,
    QTextEdit,
    QSplitter,
    QGroupBox,
    QScrollArea,
    QApplication,
    QMessageBox,
)
from src.services.ai_service import OllamaService, AIPersona, OllamaInferenceWorker
from src.services.resource_monitor import SystemResourceMonitor
from src.utils.logger import app_logger


class AIAssistantPanel(QWidget):
    """Interactive AI Assistant panel with streaming output, diff preview, and permission enforcement."""

    suggestion_accepted = Signal(str)  # Emits text user approved for insertion
    status_updated = Signal(str)

    def __init__(
        self,
        ollama_service: Optional[OllamaService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.ollama = ollama_service or OllamaService()
        self.resource_monitor = SystemResourceMonitor()
        self.current_worker: Optional[OllamaInferenceWorker] = None
        self.context_provider: Optional[Callable[[], str]] = None

        self._init_ui()
        self._connect_signals()
        self._init_hardware_timer()

        # Initial check
        QTimer.singleShot(500, self.check_connection)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 1. Configuration & Connection Header
        cfg_group = QGroupBox("Engine & Persona", self)
        cfg_layout = QVBoxLayout(cfg_group)
        cfg_layout.setContentsMargins(6, 6, 6, 6)
        cfg_layout.setSpacing(6)

        # Status & Refresh Row
        status_row = QHBoxLayout()
        self.status_indicator = QLabel("● Offline", self)
        self.status_indicator.setStyleSheet("color: #e06c75; font-weight: bold;")
        self.btn_refresh = QPushButton("🔄 Refresh", self)
        self.btn_refresh.setFixedHeight(24)
        self.btn_refresh.clicked.connect(self.check_connection)
        status_row.addWidget(self.status_indicator)
        status_row.addStretch()
        status_row.addWidget(self.btn_refresh)
        cfg_layout.addLayout(status_row)

        # Model & Persona Selection Row
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Model:", self))
        self.model_combo = QComboBox(self)
        self.model_combo.setMinimumWidth(120)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        sel_row.addWidget(self.model_combo, 1)

        sel_row.addWidget(QLabel("Persona:", self))
        self.persona_combo = QComboBox(self)
        for persona in AIPersona:
            self.persona_combo.addItem(persona.value, persona)
        sel_row.addWidget(self.persona_combo, 1)

        cfg_layout.addLayout(sel_row)
        layout.addWidget(cfg_group)

        # 2. Quick Command Pills
        cmd_group = QGroupBox("Quick Academic Commands", self)
        cmd_layout = QHBoxLayout(cmd_group)
        cmd_layout.setContentsMargins(4, 4, 4, 4)
        cmd_layout.setSpacing(4)

        commands = [
            ("Explain Error", "Explain this LaTeX compilation error and suggest the exact fix:"),
            ("Rewrite Formal", "Rewrite the selected paragraph to improve academic rigor and flow:"),
            ("Draft Method", "Draft a scholarly Methodology section outline for this research topic:"),
            ("Explain Math", "Explain this mathematical equation and verify its physical dimensions:"),
            ("Suggest Cites", "Suggest relevant academic citations and literature for this context:"),
        ]

        for label, cmd_text in commands:
            btn = QPushButton(label, self)
            btn.setStyleSheet("font-size: 11px; padding: 3px 6px;")
            btn.clicked.connect(lambda _, t=cmd_text: self._apply_quick_command(t))
            cmd_layout.addWidget(btn)

        layout.addWidget(cmd_group)

        # 3. Main Splitter: Top = Prompt Input, Bottom = Response Output
        splitter = QSplitter(Qt.Orientation.Vertical, self)

        # Prompt Input Area
        prompt_container = QWidget(self)
        p_layout = QVBoxLayout(prompt_container)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(4)

        p_layout.addWidget(QLabel("Instruction / Query:", self))
        self.prompt_edit = QPlainTextEdit(self)
        self.prompt_edit.setPlaceholderText("Enter writing request or click a quick command above...")
        self.prompt_edit.setMaximumHeight(110)
        p_layout.addWidget(self.prompt_edit)

        btn_row = QHBoxLayout()
        self.btn_generate = QPushButton("✨ Generate Suggestion", self)
        self.btn_generate.setStyleSheet("font-weight: bold; background-color: #1a73e8; color: white;")
        self.btn_generate.clicked.connect(self.start_generation)
        self.btn_stop = QPushButton("🛑 Stop", self)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_generation)

        btn_row.addWidget(self.btn_generate, 2)
        btn_row.addWidget(self.btn_stop, 1)
        p_layout.addLayout(btn_row)

        splitter.addWidget(prompt_container)

        # Response Output & Suggestion Review Area
        resp_container = QWidget(self)
        r_layout = QVBoxLayout(resp_container)
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(4)

        r_layout.addWidget(QLabel("AI Suggestion Preview (Read-Only until Approved):", self))
        self.response_edit = QTextEdit(self)
        self.response_edit.setReadOnly(True)
        r_layout.addWidget(self.response_edit)

        # Suggestion Action Bar (Permission Controls)
        action_bar = QHBoxLayout()
        self.btn_accept = QPushButton("✅ Accept & Apply", self)
        self.btn_accept.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white;")
        self.btn_accept.setEnabled(False)
        self.btn_accept.clicked.connect(self._on_accept_suggestion)

        self.btn_reject = QPushButton("❌ Discard", self)
        self.btn_reject.setEnabled(False)
        self.btn_reject.clicked.connect(self._on_reject_suggestion)

        self.btn_copy = QPushButton("📋 Copy", self)
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._on_copy_suggestion)

        action_bar.addWidget(self.btn_accept)
        action_bar.addWidget(self.btn_reject)
        action_bar.addWidget(self.btn_copy)
        r_layout.addLayout(action_bar)

        splitter.addWidget(resp_container)
        splitter.setSizes([140, 260])
        layout.addWidget(splitter, 1)

        # 4. Hardware Resource Footer
        self.hw_label = QLabel("RAM: -- | GPU VRAM: --", self)
        self.hw_label.setStyleSheet("color: #777; font-size: 11px;")
        layout.addWidget(self.hw_label)

    def _connect_signals(self) -> None:
        self.ollama.connection_checked.connect(self._on_connection_checked)
        self.ollama.models_listed.connect(self._on_models_listed)

    def _init_hardware_timer(self) -> None:
        self.hw_timer = QTimer(self)
        self.hw_timer.timeout.connect(self._refresh_hardware_metrics)
        self.hw_timer.start(5000)
        self._refresh_hardware_metrics()

    def set_context_provider(self, provider: Callable[[], str]) -> None:
        """Register a callback that packages active manuscript/error context."""
        self.context_provider = provider

    def check_connection(self) -> None:
        """Poll local Ollama status."""
        self.status_indicator.setText("● Connecting...")
        self.status_indicator.setStyleSheet("color: #d19a66; font-weight: bold;")
        self.ollama.check_connection()
        self.ollama.list_models()

    def _on_connection_checked(self, is_connected: bool, message: str) -> None:
        if is_connected:
            self.status_indicator.setText("● Ollama Active")
            self.status_indicator.setStyleSheet("color: #98c379; font-weight: bold;")
        else:
            self.status_indicator.setText("● Ollama Offline")
            self.status_indicator.setStyleSheet("color: #e06c75; font-weight: bold;")
            self.model_combo.clear()
            self.model_combo.addItem("None (Offline)")

    def _on_models_listed(self, models: list) -> None:
        current_sel = self.model_combo.currentText()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        if models:
            for m in models:
                self.model_combo.addItem(m)
            idx = self.model_combo.findText(current_sel)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.addItem("No models found")
        self.model_combo.blockSignals(False)

    def _on_model_changed(self, index: int) -> None:
        model_name = self.model_combo.currentText()
        if model_name and "No models" not in model_name and "None" not in model_name:
            self.ollama.switch_model(model_name)

    def _apply_quick_command(self, cmd_prefix: str) -> None:
        existing = self.prompt_edit.toPlainText().strip()
        if existing and not existing.startswith(cmd_prefix):
            self.prompt_edit.setPlainText(f"{cmd_prefix}\n\n{existing}")
        else:
            self.prompt_edit.setPlainText(cmd_prefix + " ")
        self.prompt_edit.setFocus()

    def start_generation(self) -> None:
        """Start streaming token generation in the background."""
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.information(self, "AI Assistant", "Please enter a prompt or instruction.")
            return

        persona = self.persona_combo.currentData() or AIPersona.ACADEMIC_WRITER

        context = ""
        if self.context_provider:
            try:
                context = self.context_provider()
            except Exception as e:
                app_logger.warning(f"Error packaging AI context: {e}")

        # Check hardware safety headroom
        metrics = self.resource_monitor.get_metrics()
        if not metrics.is_gpu_headroom_safe:
            reply = QMessageBox.question(
                self,
                "High VRAM Usage",
                f"VRAM usage is currently {metrics.gpu_used_mb:.1f} MB (exceeding 9.5 GB safe limit).\n"
                "Continuing may cause driver memory paging. Proceed anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.response_edit.clear()
        self.btn_generate.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_accept.setEnabled(False)
        self.btn_reject.setEnabled(False)
        self.btn_copy.setEnabled(False)

        worker = self.ollama.create_generation_worker(
            prompt=prompt,
            persona=persona,
            context=context,
        )
        if not worker:
            self._on_error("Failed creating generation worker.")
            return

        self.current_worker = worker
        worker.chunk_received.connect(self._on_chunk_received)
        worker.finished.connect(self._on_finished)
        worker.error_occurred.connect(self._on_error)
        worker.start()

    def stop_generation(self) -> None:
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
        self.btn_stop.setEnabled(False)
        self.btn_generate.setEnabled(True)

    def _on_chunk_received(self, chunk: str) -> None:
        self.response_edit.insertPlainText(chunk)
        # Scroll to bottom
        sb = self.response_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_finished(self, full_text: str) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_stop.setEnabled(False)
        has_content = bool(full_text.strip())
        self.btn_accept.setEnabled(has_content)
        self.btn_reject.setEnabled(has_content)
        self.btn_copy.setEnabled(has_content)

    def _on_error(self, err_msg: str) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.response_edit.setPlainText(f"⚠️ {err_msg}")

    def _on_accept_suggestion(self) -> None:
        """User explicitly approved the AI suggestion."""
        text = self.response_edit.toPlainText().strip()
        if text:
            self.suggestion_accepted.emit(text)
            self.response_edit.clear()
            self.btn_accept.setEnabled(False)
            self.btn_reject.setEnabled(False)
            self.btn_copy.setEnabled(False)

    def _on_reject_suggestion(self) -> None:
        """User discarded the suggestion."""
        self.response_edit.clear()
        self.btn_accept.setEnabled(False)
        self.btn_reject.setEnabled(False)
        self.btn_copy.setEnabled(False)

    def _on_copy_suggestion(self) -> None:
        """Copy generated suggestion to clipboard."""
        text = self.response_edit.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)

    def _refresh_hardware_metrics(self) -> None:
        metrics = self.resource_monitor.get_metrics()
        gpu_str = f"GPU: {metrics.gpu_used_mb:.0f}/{metrics.gpu_total_mb:.0f} MB" if metrics.gpu_used_mb else "GPU: Idle"
        self.hw_label.setText(
            f"RAM: {metrics.used_ram_gb:.1f}/{metrics.total_ram_gb:.1f} GB ({metrics.ram_load_percent}%) | {gpu_str}"
        )
