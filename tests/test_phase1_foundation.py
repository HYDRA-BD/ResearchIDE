"""Automated Test Suite for Phase 1 Application Foundation.

Tests:
1. Database initialization, WAL mode, migrations, and integrity verification.
2. Global settings persistence across database instances.
3. Project workspace scaffolding, file creation, and metadata initialization.
4. Project reopening and recent projects tracking.
5. Project renaming and folder renaming consistency.
6. Project deletion and cleanup.
7. Path traversal security validation.
8. Safe atomic file operations.
9. Desktop UI initialization and headless MainWindow startup.
"""

import unittest
import tempfile
import sys
import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.storage.database import DatabaseManager
from src.storage.file_manager import FileManager, FileSecurityError
from src.storage.repositories.settings_repo import SettingsRepository
from src.storage.repositories.project_repo import ProjectRepository
from src.storage.repositories.document_repo import DocumentRepository
from src.core.project import ProjectManager, Project
from src.utils.config import AppSettings
from src.ui.main_window import MainWindow


class TestPhase1Foundation(unittest.TestCase):
    """Test suite validating Phase 1 desktop foundation, storage, and project lifecycle."""

    @classmethod
    def setUpClass(cls) -> None:
        # Initialize headless offscreen QApplication if not already running
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        if not QApplication.instance():
            cls.app = QApplication(["--platform", "offscreen"])
        else:
            cls.app = QApplication.instance()

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name).resolve()
        self.global_db_path = self.test_root / "test_global.db"
        self.project_manager = ProjectManager(global_db_path=self.global_db_path)

    def tearDown(self) -> None:
        if self.project_manager.active_project:
            self.project_manager.close_current_project()
        if hasattr(self.project_manager, "global_db"):
            self.project_manager.global_db.close()
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_database_initialization_and_integrity(self) -> None:
        """Verify SQLite database initialization, WAL mode, and integrity checks."""
        db_path = self.test_root / "test_db.db"
        db = DatabaseManager(db_path)

        # 1. Integrity check
        self.assertTrue(db.run_integrity_check())

        # 2. PRAGMA validation
        journal = db.fetch_one("PRAGMA journal_mode;")
        self.assertEqual(journal[0].lower(), "wal")

        fk = db.fetch_one("PRAGMA foreign_keys;")
        self.assertEqual(fk[0], 1)

        # 3. Transaction handling
        with db.transaction() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);")
            conn.execute("INSERT INTO test_table (name) VALUES ('Test Item');")

        row = db.fetch_one("SELECT name FROM test_table WHERE id = 1;")
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Test Item")
        db.close()

    def test_settings_persistence(self) -> None:
        """Verify global settings are persisted and restored accurately."""
        repo = self.project_manager.settings_repo

        settings = AppSettings()
        settings.appearance.theme = "light"
        settings.appearance.font_size = 14
        settings.compiler.active_engine = "xelatex"
        settings.compiler.custom_bin_path = "C:\\Custom\\TeX"
        settings.ai.active_model = "deepseek-r1:14b"

        # Save to DB
        repo.save_settings(settings)

        # Create new repository instance pointing to same DB and load
        loaded = repo.load_settings()
        self.assertEqual(loaded.appearance.theme, "light")
        self.assertEqual(loaded.appearance.font_size, 14)
        self.assertEqual(loaded.compiler.active_engine, "xelatex")
        self.assertEqual(loaded.compiler.custom_bin_path, "C:\\Custom\\TeX")
        self.assertEqual(loaded.ai.active_model, "deepseek-r1:14b")

    def test_project_creation_and_scaffolding(self) -> None:
        """Verify project scaffolding creates directories and starter files."""
        proj = self.project_manager.create_project(
            parent_dir=self.test_root,
            project_name="AeroAcoustics",
            description="Acoustic analysis in hypersonic flow",
        )

        self.assertEqual(proj.name, "AeroAcoustics")
        self.assertTrue(proj.path.exists())
        self.assertTrue(proj.src_dir.exists())
        self.assertTrue(proj.literature_dir.exists())
        self.assertTrue(proj.notes_dir.exists())
        self.assertTrue(proj.assets_dir.exists())
        self.assertTrue((proj.path / ".researchide" / "project.db").exists())
        self.assertTrue(proj.main_tex_path.exists())

        # Check starter main.tex content
        main_tex = FileManager.read_text(proj.main_tex_path)
        self.assertIn("\\title{AeroAcoustics}", main_tex)
        self.assertIn("\\begin{document}", main_tex)

        # Check starter bibliography
        bib_file = proj.src_dir / "references.bib"
        self.assertTrue(bib_file.exists())
        bib_content = FileManager.read_text(bib_file)
        self.assertIn("@article{einstein1905", bib_content)

        # Check document repository registered main.tex
        docs = proj.doc_repo.list_documents()
        self.assertGreaterEqual(len(docs), 1)
        self.assertEqual(docs[0].relative_path, "src/main.tex")

        # Check recent projects recorded
        recents = self.project_manager.get_recent_projects()
        self.assertEqual(len(recents), 1)
        self.assertEqual(recents[0]["name"], "AeroAcoustics")

    def test_project_reopening(self) -> None:
        """Verify closing a project and reopening restores active metadata."""
        proj = self.project_manager.create_project(
            parent_dir=self.test_root,
            project_name="DarkMatterSim",
            description="N-body simulations",
        )
        proj_path = proj.path
        self.project_manager.close_current_project()
        self.assertIsNone(self.project_manager.active_project)

        # Reopen
        reopened = self.project_manager.open_project(proj_path)
        self.assertEqual(reopened.name, "DarkMatterSim")
        self.assertEqual(reopened.description, "N-body simulations")
        self.assertEqual(self.project_manager.active_project.id, reopened.id)

    def test_project_renaming(self) -> None:
        """Verify renaming updates filesystem folder, recent list, and DB metadata."""
        proj = self.project_manager.create_project(
            parent_dir=self.test_root,
            project_name="OldName",
        )
        renamed = self.project_manager.rename_project("NewName")
        self.assertEqual(renamed.name, "NewName")
        self.assertEqual(renamed.path.name, "NewName")
        self.assertTrue(renamed.path.exists())
        self.assertFalse((self.test_root / "OldName").exists())

        # Check recent projects reflects new name
        recents = self.project_manager.get_recent_projects()
        self.assertEqual(recents[0]["name"], "NewName")

    def test_project_deletion(self) -> None:
        """Verify deleting a project removes files and recent entries."""
        proj = self.project_manager.create_project(
            parent_dir=self.test_root,
            project_name="TempProject",
        )
        proj_path = proj.path
        self.assertTrue(proj_path.exists())

        self.project_manager.delete_project(proj_path)
        self.assertFalse(proj_path.exists())
        self.assertEqual(len(self.project_manager.get_recent_projects()), 0)

    def test_path_traversal_security(self) -> None:
        """Verify FileManager blocks path traversal attempts outside project root."""
        proj = self.project_manager.create_project(
            parent_dir=self.test_root,
            project_name="SecureProject",
        )
        project_root = proj.path

        # Valid subpath
        valid_path = project_root / "src" / "sections" / "intro.tex"
        resolved = FileManager.validate_path_within_project(valid_path, project_root)
        self.assertEqual(resolved, valid_path.resolve())

        # Forbidden traversal outside
        invalid_path = project_root / ".." / "system_file.txt"
        with self.assertRaises(FileSecurityError):
            FileManager.validate_path_within_project(invalid_path, project_root)

    def test_atomic_write_safety(self) -> None:
        """Verify atomic file writes replace content cleanly."""
        target = self.test_root / "atomic_test.txt"
        FileManager.atomic_write(target, "Version 1")
        self.assertEqual(FileManager.read_text(target), "Version 1")

        # Overwrite with Version 2
        FileManager.atomic_write(target, "Version 2 Updated Content")
        self.assertEqual(FileManager.read_text(target), "Version 2 Updated Content")

    def test_desktop_ui_initialization(self) -> None:
        """Verify MainWindow initializes cleanly with Ribbon, Dashboard, and Explorer."""
        window = MainWindow(self.project_manager)
        self.assertIsNotNone(window.ribbon)
        self.assertIsNotNone(window.dashboard)
        self.assertIsNotNone(window.workspace)
        self.assertIsNotNone(window.explorer)

        # Initially shows dashboard (index 0) and hides explorer dock
        self.assertEqual(window.stacked_widget.currentIndex(), 0)
        self.assertTrue(window.dock_explorer.isHidden())

        # Create project through manager and load into UI
        proj = self.project_manager.create_project(
            parent_dir=self.test_root,
            project_name="UIProject",
        )
        window._load_active_project(proj)

        # Stack switches to workspace (index 1) and explorer shows
        self.assertEqual(window.stacked_widget.currentIndex(), 1)
        self.assertFalse(window.dock_explorer.isHidden())
        self.assertIn("UIProject", window.status_project_label.text())

        # Close project
        window.action_close_project()
        self.assertEqual(window.stacked_widget.currentIndex(), 0)
        self.assertTrue(window.dock_explorer.isHidden())

        window.close()


if __name__ == "__main__":
    unittest.main()
