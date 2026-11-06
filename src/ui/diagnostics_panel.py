"""Compilation Diagnostics and Error Navigation Panel for ResearchIDE."""
from __future__ import annotations
from typing import List
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPlainTextEdit,
    QLabel,
)
from src.services.latex_service import LaTeXDiagnostic


class DiagnosticsPanel(QWidget):
    """Displays compiler errors, warnings, and raw build logs with line jump navigation."""

    diagnostic_selected = Signal(str, int)  # file_name, line_number

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.tabs = QTabWidget()

        # Tab 1: Structured Diagnostics Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Type", "Line", "File", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self.tabs.addTab(self.table, "Issues (0)")

        # Tab 2: Raw Build Log
        self.raw_log_edit = QPlainTextEdit()
        self.raw_log_edit.setReadOnly(True)
        self.raw_log_edit.setStyleSheet("font-family: Consolas; font-size: 11px;")
        self.tabs.addTab(self.raw_log_edit, "Raw Build Log")

        layout.addWidget(self.tabs)

    def set_diagnostics(self, diagnostics: List[LaTeXDiagnostic], raw_log: str = "") -> None:
        """Populate the table with parsed compiler diagnostics."""
        self.raw_log_edit.setPlainText(raw_log)

        errors = [d for d in diagnostics if d.severity == "error"]
        warnings = [d for d in diagnostics if d.severity == "warning"]
        self.tabs.setTabText(0, f"Issues ({len(errors)} errors, {len(warnings)} warnings)")

        self.table.setRowCount(len(diagnostics))
        for row_idx, d in enumerate(diagnostics):
            type_item = QTableWidgetItem("⛔ Error" if d.severity == "error" else "⚠️ Warning")
            if d.severity == "error":
                type_item.setForeground(QColor("#f87171"))
            else:
                type_item.setForeground(QColor("#fbbf24"))

            line_item = QTableWidgetItem(str(d.line_number))
            file_item = QTableWidgetItem(d.file_name)
            desc_item = QTableWidgetItem(d.message)

            # Store metadata for navigation
            line_item.setData(Qt.ItemDataRole.UserRole, (d.file_name, d.line_number))

            self.table.setItem(row_idx, 0, type_item)
            self.table.setItem(row_idx, 1, line_item)
            self.table.setItem(row_idx, 2, file_item)
            self.table.setItem(row_idx, 3, desc_item)

    def _on_row_double_clicked(self, row: int, col: int) -> None:
        item = self.table.item(row, 1)
        if item:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                file_name, line_no = data
                self.diagnostic_selected.emit(file_name, line_no)

    def clear(self) -> None:
        self.table.setRowCount(0)
        self.raw_log_edit.clear()
        self.tabs.setTabText(0, "Issues (0)")
