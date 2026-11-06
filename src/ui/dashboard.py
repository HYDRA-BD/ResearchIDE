"""Home Dashboard Widget for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
)


class HomeDashboard(QWidget):
    """Initial landing dashboard displayed when no project is active."""

    new_project_requested = Signal()
    open_project_requested = Signal()
    open_recent_requested = Signal(str)  # Project path
    settings_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QLabel("ResearchIDE")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #4daafc;")
        subtitle = QLabel("Offline AI-Powered Academic Research & LaTeX Writing Environment")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        layout.addWidget(header)
        layout.addWidget(subtitle)

        # 2. Quick Action Cards
        action_bar = QHBoxLayout()
        action_bar.setSpacing(12)

        btn_new = QPushButton("📄 New Research Project")
        btn_new.setProperty("class", "PrimaryBtn")
        btn_new.setFixedHeight(44)
        btn_new.clicked.connect(self.new_project_requested.emit)

        btn_open = QPushButton("📂 Open Project Folder...")
        btn_open.setFixedHeight(44)
        btn_open.clicked.connect(self.open_project_requested.emit)

        btn_settings = QPushButton("⚙️ Preferences")
        btn_settings.setFixedHeight(44)
        btn_settings.clicked.connect(self.settings_requested.emit)

        action_bar.addWidget(btn_new)
        action_bar.addWidget(btn_open)
        action_bar.addWidget(btn_settings)
        action_bar.addStretch()
        layout.addLayout(action_bar)

        # Horizontal separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #2a2a34;")
        layout.addWidget(line)

        # 3. Recent Projects Table
        recents_header = QLabel("Recent Research Projects")
        recents_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #e2e8f0;")
        layout.addWidget(recents_header)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Project Name", "Workspace Location", "Last Opened"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

    def set_recent_projects(self, projects: List[Dict[str, str]]) -> None:
        """Populate the table with recent projects."""
        self.table.setRowCount(len(projects))
        for row_idx, p in enumerate(projects):
            name_item = QTableWidgetItem(str(p["name"]))
            path_item = QTableWidgetItem(str(p["path"]))
            time_item = QTableWidgetItem(str(p["last_opened"]))

            name_item.setData(Qt.ItemDataRole.UserRole, str(p["path"]))
            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, path_item)
            self.table.setItem(row_idx, 2, time_item)

    def _on_row_double_clicked(self, row: int, col: int) -> None:
        item = self.table.item(row, 0)
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path and Path(path).exists():
                self.open_recent_requested.emit(path)
