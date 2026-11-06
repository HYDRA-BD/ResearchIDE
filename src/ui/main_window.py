"""Main Application Window for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QDockWidget,
    QFileDialog,
    QMessageBox,
    QLabel,
    QInputDialog,
)
from src.core.project import ProjectManager, Project
from src.storage.file_manager import FileManager
from src.ui.theme import get_theme_stylesheet
from src.ui.ribbon import RibbonBar
from src.ui.dashboard import HomeDashboard
from src.ui.explorer import ProjectExplorer
from src.ui.workspace import DocumentWorkspace
from src.ui.notifications import NotificationToast
from src.ui.dialogs.new_project_dialog import NewProjectDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.new_document_dialog import NewDocumentDialog
from src.utils.logger import app_logger


class MainWindow(QMainWindow):
    """Master application window for ResearchIDE desktop suite."""

    def __init__(self, project_manager: Optional[ProjectManager] = None) -> None:
        super().__init__()
        self.setWindowTitle("ResearchIDE — Academic Research & LaTeX Environment")
        self.resize(1366, 850)
        self.setMinimumSize(1024, 600)

        self.project_manager = project_manager or ProjectManager()
        self.settings = self.project_manager.settings_repo.load_settings()

        self._init_ui()
        self._apply_theme()
        self._init_autosave_timer()
        self._refresh_recents()

    def _init_ui(self) -> None:
        self.setObjectName("MainWindow")

        # 1. Central Widget & Stack (Dashboard vs Document Workspace)
        self.central_container = QWidget()
        self.central_container.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_container)

        container_layout = QVBoxLayout(self.central_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Ribbon Toolbar
        self.ribbon = RibbonBar(self)
        self.ribbon.new_project_clicked.connect(self.action_new_project)
        self.ribbon.open_project_clicked.connect(self.action_open_project)
        self.ribbon.save_document_clicked.connect(self.action_save_document)
        self.ribbon.settings_clicked.connect(self.action_open_settings)
        self.ribbon.new_document_clicked.connect(self.action_new_document)
        self.ribbon.compile_clicked.connect(self.action_compile_pdf)
        container_layout.addWidget(self.ribbon)

        # Stacked Central Area
        self.stacked_widget = QStackedWidget()
        self.dashboard = HomeDashboard()
        self.dashboard.new_project_requested.connect(self.action_new_project)
        self.dashboard.open_project_requested.connect(self.action_open_project)
        self.dashboard.open_recent_requested.connect(self.open_project_from_path)
        self.dashboard.settings_requested.connect(self.action_open_settings)

        self.workspace = DocumentWorkspace()
        self.stacked_widget.addWidget(self.dashboard)   # Index 0
        self.stacked_widget.addWidget(self.workspace)   # Index 1
        container_layout.addWidget(self.stacked_widget)

        # 2. Navigation Sidebar Dock (Project Explorer)
        self.dock_explorer = QDockWidget("Project Explorer", self)
        self.dock_explorer.setObjectName("DockProjectExplorer")
        self.dock_explorer.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        self.explorer = ProjectExplorer(self.dock_explorer)
        self.explorer.file_selected.connect(self.action_open_file)
        self.explorer.new_file_requested.connect(self.action_new_document)
        self.dock_explorer.setWidget(self.explorer)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_explorer)
        self.dock_explorer.hide()  # Initially hidden until project is opened

        # 3. Application Menu Bar
        self._build_menu_bar()

        # 4. Status Bar
        self.status_project_label = QLabel("No Project Active")
        self.status_compiler_label = QLabel("Compiler: pdflatex")
        self.status_hw_label = QLabel("GPU: RTX 3060 12GB | RAM: 16GB")
        self.statusBar().addWidget(self.status_project_label, 1)
        self.statusBar().addPermanentWidget(self.status_compiler_label)
        self.statusBar().addPermanentWidget(self.status_hw_label)

    def _build_menu_bar(self) -> None:
        mb = self.menuBar()

        # File Menu
        file_menu = mb.addMenu("&File")

        act_new_proj = QAction("&New Project...", self)
        act_new_proj.setShortcut(QKeySequence.StandardKey.New)
        act_new_proj.triggered.connect(self.action_new_project)
        file_menu.addAction(act_new_proj)

        act_open_proj = QAction("&Open Project...", self)
        act_open_proj.setShortcut(QKeySequence.StandardKey.Open)
        act_open_proj.triggered.connect(self.action_open_project)
        file_menu.addAction(act_open_proj)

        act_save = QAction("&Save", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self.action_save_document)
        file_menu.addAction(act_save)

        file_menu.addSeparator()

        act_close_proj = QAction("&Close Project", self)
        act_close_proj.triggered.connect(self.action_close_project)
        file_menu.addAction(act_close_proj)

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Project Menu
        project_menu = mb.addMenu("&Project")
        act_add_doc = QAction("&Add Document...", self)
        act_add_doc.triggered.connect(self.action_new_document)
        project_menu.addAction(act_add_doc)

        act_rename_proj = QAction("&Rename Project...", self)
        act_rename_proj.triggered.connect(self.action_rename_project)
        project_menu.addAction(act_rename_proj)

        act_delete_proj = QAction("&Delete Project...", self)
        act_delete_proj.triggered.connect(self.action_delete_project)
        project_menu.addAction(act_delete_proj)

        # Settings Menu
        settings_menu = mb.addMenu("&Settings")
        act_prefs = QAction("&Preferences...", self)
        act_prefs.triggered.connect(self.action_open_settings)
        settings_menu.addAction(act_prefs)

    def _apply_theme(self) -> None:
        theme = self.settings.appearance.theme
        qss = get_theme_stylesheet(theme)
        self.setStyleSheet(qss)

    def _refresh_recents(self) -> None:
        recents = self.project_manager.get_recent_projects()
        self.dashboard.set_recent_projects(recents)

    def _init_autosave_timer(self) -> None:
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._on_autosave)
        if self.settings.autosave_enabled:
            interval_ms = max(5000, self.settings.autosave_interval_seconds * 1000)
            self.autosave_timer.start(interval_ms)

    def _on_autosave(self) -> None:
        if self.project_manager.active_project and self.workspace.open_tabs:
            self.workspace.save_all_documents()
            self.statusBar().showMessage("Autosaved project changes", 2000)

    def show_notification(self, message: str, level: str = "info") -> None:
        """Surface non-blocking notification toast."""
        toast = NotificationToast(message, level=level, parent=self)
        toast.move(self.width() - toast.width() - 30, self.height() - toast.height() - 40)
        toast.show()

    # --- Actions ---

    def action_new_project(self) -> None:
        dlg = NewProjectDialog(self.settings.default_project_dir, self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                project = self.project_manager.create_project(
                    parent_dir=data["parent_dir"],
                    project_name=data["name"],
                    description=data["description"],
                )
                self._load_active_project(project)
                self.show_notification(f"Project '{project.name}' initialized.", level="success")
            except Exception as e:
                app_logger.error(f"Project creation failed: {e}")
                QMessageBox.critical(self, "Project Creation Error", str(e))

    def action_open_project(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select Project Folder", self.settings.default_project_dir)
        if chosen:
            self.open_project_from_path(chosen)

    def open_project_from_path(self, project_path: str) -> None:
        try:
            project = self.project_manager.open_project(project_path)
            self._load_active_project(project)
            self.show_notification(f"Project '{project.name}' loaded.", level="info")
        except Exception as e:
            app_logger.error(f"Failed opening project: {e}")
            QMessageBox.critical(self, "Open Error", str(e))

    def _load_active_project(self, project: Project) -> None:
        self.workspace.close_all_tabs()
        self.explorer.set_project_root(project.path)
        self.dock_explorer.show()
        self.stacked_widget.setCurrentIndex(1)  # Show workspace

        self.status_project_label.setText(f"Project: {project.name}")
        self.status_compiler_label.setText(f"Compiler: {self.settings.compiler.active_engine}")

        # Open main.tex by default if it exists
        if project.main_tex_path.exists():
            self.workspace.open_document(project.main_tex_path)

        self._refresh_recents()

    def action_close_project(self) -> None:
        if self.project_manager.active_project:
            self.workspace.close_all_tabs()
            self.project_manager.close_current_project()
            self.dock_explorer.hide()
            self.stacked_widget.setCurrentIndex(0)  # Show dashboard
            self.status_project_label.setText("No Project Active")
            self._refresh_recents()
            self.show_notification("Project closed.", level="info")

    def action_rename_project(self) -> None:
        if not self.project_manager.active_project:
            QMessageBox.information(self, "Rename", "No active project to rename.")
            return

        current_name = self.project_manager.active_project.name
        new_name, ok = QInputDialog.getText(self, "Rename Project", "New Project Name:", text=current_name)
        if ok and new_name.strip():
            try:
                project = self.project_manager.rename_project(new_name.strip())
                self._load_active_project(project)
                self.show_notification(f"Project renamed to '{new_name}'.", level="success")
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", str(e))

    def action_delete_project(self) -> None:
        if not self.project_manager.active_project:
            QMessageBox.information(self, "Delete", "No active project to delete.")
            return

        current_path = self.project_manager.active_project.path
        current_name = self.project_manager.active_project.name

        reply = QMessageBox.question(
            self,
            "Confirm Permanent Deletion",
            f"Are you sure you want to permanently delete the project '{current_name}' and all its files?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.action_close_project()
                self.project_manager.delete_project(current_path)
                self._refresh_recents()
                self.show_notification(f"Project '{current_name}' deleted.", level="warning")
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", str(e))

    def action_new_document(self) -> None:
        if not self.project_manager.active_project:
            QMessageBox.information(self, "No Project", "Please open or create a project first.")
            return

        dlg = NewDocumentDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            filename = data["filename"]
            category = data["category"]

            proj = self.project_manager.active_project
            if "sections" in category:
                target_dir = proj.src_dir / "sections"
            elif "notes" in category:
                target_dir = proj.notes_dir
            else:
                target_dir = proj.src_dir

            target_file = target_dir / filename
            if target_file.exists():
                QMessageBox.warning(self, "File Exists", f"File '{filename}' already exists.")
                return

            try:
                FileManager.atomic_write(target_file, f"% {filename}\n\n")
                self.workspace.open_document(target_file)
                self.show_notification(f"Added document '{filename}'.", level="success")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create document: {e}")

    def action_open_file(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists() and path.is_file():
            self.workspace.open_document(path)

    def action_save_document(self) -> None:
        saved = self.workspace.save_current_document()
        if saved:
            self.statusBar().showMessage("Document saved.", 2500)

    def action_compile_pdf(self) -> None:
        if not self.project_manager.active_project:
            QMessageBox.information(self, "No Project", "No active project to compile.")
            return
        self.workspace.save_all_documents()
        self.statusBar().showMessage("Compilation requested (Phase 2 integration)...", 3000)
        self.show_notification("LaTeX compilation will execute via Phase 2 engine.", level="info")

    def action_open_settings(self) -> None:
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            self.project_manager.settings_repo.save_settings(self.settings)
            self._apply_theme()
            self._init_autosave_timer()
            self.status_compiler_label.setText(f"Compiler: {self.settings.compiler.active_engine}")
            self.show_notification("Preferences saved.", level="success")

    def closeEvent(self, event) -> None:
        """Handle graceful window closure."""
        if any(tab.is_dirty for tab in self.workspace.open_tabs.values()):
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "There are unsaved documents. Save all before exiting?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self.workspace.save_all_documents()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
                return

        self.project_manager.close_current_project()
        event.accept()

