"""Project domain entity and project workspace lifecycle management."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict
import uuid
from src.storage.database import DatabaseManager
from src.storage.file_manager import FileManager
from src.storage.repositories.project_repo import ProjectRepository, ProjectMetadata
from src.storage.repositories.document_repo import DocumentRepository
from src.storage.repositories.settings_repo import SettingsRepository
from src.utils.logger import app_logger


class Project:
    """Represents an active, self-contained ResearchIDE research project."""

    def __init__(self, project_path: Path | str) -> None:
        self.path = Path(project_path).resolve()
        self.db_path = self.path / ".researchide" / "project.db"
        self.db = DatabaseManager(self.db_path)
        self.project_repo = ProjectRepository(self.db)
        self.doc_repo = DocumentRepository(self.db)

        # Load metadata
        meta = self.project_repo.get_project_metadata()
        if meta:
            self.id = meta.id
            self.name = meta.name
            self.description = meta.description
        else:
            self.id = str(uuid.uuid4())
            self.name = self.path.name
            self.description = ""
            self.project_repo.init_project_metadata(self.id, self.name, self.description)

    @property
    def src_dir(self) -> Path:
        return self.path / "src"

    @property
    def literature_dir(self) -> Path:
        return self.path / "literature"

    @property
    def notes_dir(self) -> Path:
        return self.path / "notes"

    @property
    def assets_dir(self) -> Path:
        return self.path / "assets"

    @property
    def main_tex_path(self) -> Path:
        return self.src_dir / "main.tex"

    def close(self) -> None:
        """Close project database connection."""
        self.db.close()


class ProjectManager:
    """Manages project creation, opening, deletion, and recent history."""

    def __init__(self, global_db_path: Optional[Path | str] = None) -> None:
        if global_db_path is None:
            global_dir = Path.home() / ".researchide"
            global_dir.mkdir(parents=True, exist_ok=True)
            global_db_path = global_dir / "global.db"

        self.global_db = DatabaseManager(global_db_path)
        self.settings_repo = SettingsRepository(self.global_db)
        self.active_project: Optional[Project] = None

    def create_project(self, parent_dir: Path | str, project_name: str, description: str = "") -> Project:
        """Scaffold and initialize a new project workspace."""
        clean_name = project_name.strip()
        if not clean_name:
            raise ValueError("Project name cannot be empty.")

        target_dir = Path(parent_dir).resolve() / clean_name
        if target_dir.exists() and any(target_dir.iterdir()):
            raise FileExistsError(f"Directory '{target_dir}' already exists and is not empty.")

        # Scaffold directory tree and starter files
        FileManager.scaffold_project(target_dir, clean_name)

        # Initialize Project instance & database
        project = Project(target_dir)
        project.project_repo.init_project_metadata(project.id, clean_name, description)

        # Register initial main.tex in document repository
        if project.main_tex_path.exists():
            main_content = FileManager.read_text(project.main_tex_path)
            project.doc_repo.register_document(
                doc_id=str(uuid.uuid4()),
                relative_path="src/main.tex",
                title="Main Manuscript",
                doc_type="master_tex",
                content=main_content,
            )

        # Track in recent projects
        self.settings_repo.add_recent_project(project.path, clean_name)
        self.active_project = project
        app_logger.info(f"Created and opened project '{clean_name}' at '{target_dir}'")
        return project

    def open_project(self, project_path: Path | str) -> Project:
        """Open an existing project from disk."""
        target_dir = Path(project_path).resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Project directory '{target_dir}' does not exist.")

        # Verify it has .researchide or src/main.tex
        if not (target_dir / ".researchide").exists() and not (target_dir / "src" / "main.tex").exists():
            raise ValueError(f"'{target_dir}' does not appear to be a valid ResearchIDE project.")

        if self.active_project:
            self.close_current_project()

        project = Project(target_dir)
        self.settings_repo.add_recent_project(project.path, project.name)
        self.active_project = project
        app_logger.info(f"Opened project '{project.name}' from '{target_dir}'")
        return project

    def close_current_project(self) -> None:
        """Close active project workspace cleanly."""
        if self.active_project:
            app_logger.info(f"Closing project '{self.active_project.name}'")
            self.active_project.close()
            self.active_project = None

    def rename_project(self, new_name: str) -> Project:
        """Rename the currently active project folder and metadata."""
        if not self.active_project:
            raise RuntimeError("No active project to rename.")

        clean_name = new_name.strip()
        if not clean_name:
            raise ValueError("New project name cannot be empty.")

        old_path = self.active_project.path
        self.active_project.close()

        new_path = FileManager.rename_project_dir(old_path, clean_name)
        self.settings_repo.remove_recent_project(old_path)

        project = Project(new_path)
        project.project_repo.update_project_name(project.id, clean_name)
        project.name = clean_name
        self.settings_repo.add_recent_project(new_path, clean_name)
        self.active_project = project
        return project

    def delete_project(self, project_path: Path | str) -> None:
        """Delete project files and remove from recent projects."""
        target_dir = Path(project_path).resolve()
        if self.active_project and self.active_project.path == target_dir:
            self.close_current_project()

        self.settings_repo.remove_recent_project(target_dir)
        FileManager.delete_project(target_dir)

    def get_recent_projects(self) -> List[Dict[str, str]]:
        """Return recently opened projects."""
        return self.settings_repo.get_recent_projects()

