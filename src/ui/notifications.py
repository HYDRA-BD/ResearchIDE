"""Notification Toast System for ResearchIDE."""
from __future__ import annotations
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame


class NotificationToast(QFrame):
    """Temporary non-modal notification banner."""

    def __init__(self, message: str, level: str = "info", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        colors = {
            "info": ("#2563eb", "#ffffff"),
            "success": ("#16a34a", "#ffffff"),
            "warning": ("#d97706", "#ffffff"),
            "error": ("#dc2626", "#ffffff"),
        }
        bg, fg = colors.get(level, ("#2563eb", "#ffffff"))

        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; color: {fg}; border-radius: 6px; padding: 8px 16px; font-weight: 500; font-size: 13px; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        label = QLabel(message)
        label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(label)

        # Auto-dismiss after 3.5 seconds
        QTimer.singleShot(3500, self.deleteLater)

