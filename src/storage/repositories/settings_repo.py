"""Settings and Recent Projects Repository for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from src.storage.database import DatabaseManager
from src.utils.config import AppSettings


class SettingsRepository:
    """Handles global preferences and recently opened projects."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recent_projects (
                    project_path TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    last_opened TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def load_settings(self) -> AppSettings:
        """Load complete AppSettings from database, falling back to defaults."""
        row = self.db.fetch_one("SELECT value FROM app_settings WHERE key = 'master_settings';")
        if row and row["value"]:
            try:
                return AppSettings.from_json(row["value"])
            except Exception:
                pass
        return AppSettings()

    def save_settings(self, settings: AppSettings) -> None:
        """Save complete AppSettings object as JSON."""
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES ('master_settings', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (settings.to_json(),),
            )

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve single setting value."""
        row = self.db.fetch_one("SELECT value FROM app_settings WHERE key = ?;", (key,))
        if row:
            try:
                return json.loads(row["value"])
            except Exception:
                return row["value"]
        return default

    def set_setting(self, key: str, value: Any) -> None:
        """Store single setting value."""
        val_str = json.dumps(value) if not isinstance(value, str) else value
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (key, val_str),
            )

    # --- Recent Projects ---

    def add_recent_project(self, project_path: Path | str, project_name: str) -> None:
        """Record or update recently opened project."""
        norm_path = str(Path(project_path).resolve())
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO recent_projects (project_path, project_name, last_opened)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_path) DO UPDATE SET
                    project_name = excluded.project_name,
                    last_opened = CURRENT_TIMESTAMP;
                """,
                (norm_path, project_name),
            )

    def get_recent_projects(self, limit: int = 15) -> List[Dict[str, str]]:
        """Return list of recently opened projects sorted newest first."""
        rows = self.db.fetch_all(
            "SELECT project_path, project_name, last_opened FROM recent_projects ORDER BY last_opened DESC LIMIT ?;",
            (limit,),
        )
        return [
            {
                "path": r["project_path"],
                "name": r["project_name"],
                "last_opened": r["last_opened"],
            }
            for r in rows
        ]

    def remove_recent_project(self, project_path: Path | str) -> None:
        """Remove a project from the recent projects list."""
        norm_path = str(Path(project_path).resolve())
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM recent_projects WHERE project_path = ?;", (norm_path,))

