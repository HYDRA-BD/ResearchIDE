"""Project Repository for ResearchIDE Project Databases."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from src.storage.database import DatabaseManager


@dataclass
class ProjectMetadata:
    id: str
    name: str
    description: str = ""
    active_compiler: str = "pdflatex"
    active_template: str = "default_article"
    created_at: str = ""
    updated_at: str = ""


class ProjectRepository:
    """Manages project-level metadata stored inside .researchide/project.db."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_info (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    active_compiler TEXT DEFAULT 'pdflatex',
                    active_template TEXT DEFAULT 'default_article',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def init_project_metadata(self, project_id: str, name: str, description: str = "") -> ProjectMetadata:
        """Initialize project metadata record."""
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO project_info (id, name, description, active_compiler, active_template, created_at, updated_at)
                VALUES (?, ?, ?, 'pdflatex', 'default_article', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (project_id, name, description),
            )
        return self.get_project_metadata(project_id) or ProjectMetadata(id=project_id, name=name)

    def get_project_metadata(self, project_id: Optional[str] = None) -> Optional[ProjectMetadata]:
        """Fetch project metadata."""
        if project_id:
            row = self.db.fetch_one("SELECT * FROM project_info WHERE id = ?;", (project_id,))
        else:
            row = self.db.fetch_one("SELECT * FROM project_info LIMIT 1;")

        if not row:
            return None

        return ProjectMetadata(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            active_compiler=row["active_compiler"] or "pdflatex",
            active_template=row["active_template"] or "default_article",
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def update_project_name(self, project_id: str, new_name: str) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE project_info SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (new_name, project_id),
            )

    def update_compiler(self, project_id: str, compiler: str) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE project_info SET active_compiler = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (compiler, project_id),
            )

