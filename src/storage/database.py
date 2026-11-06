"""SQLite Database Manager and Migration System for ResearchIDE.

Implements WAL mode, foreign keys, transaction management, automated migrations,
integrity verification, and connection pooling.
"""

from __future__ import annotations
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Callable
from src.utils.logger import app_logger


class DatabaseError(Exception):
    """Base exception for database failures."""
    pass


class DatabaseManager:
    """Thread-safe SQLite manager supporting project and global database instances."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._ensure_parent_directory()
        self._initialize_connection()

    def _ensure_parent_directory(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            conn.row_factory = sqlite3.Row
            # Enable optimal performance and integrity PRAGMAs
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            self._local.conn = conn
        return self._local.conn

    def _initialize_connection(self) -> None:
        """Verify database accessibility and create migration ledger."""
        with self.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                );
                """
            )

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides an atomic transactional context."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            app_logger.error(f"Transaction failed, rolled back on {self.db_path.name}: {e}")
            raise DatabaseError(f"Database transaction failure: {e}") from e

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        """Execute a query within an immediate transaction."""
        with self.transaction() as conn:
            return conn.execute(sql, params)

    def fetch_one(self, sql: str, params: tuple | dict = ()) -> sqlite3.Row | None:
        """Fetch a single row."""
        conn = self._get_connection()
        cursor = conn.execute(sql, params)
        return cursor.fetchone()

    def fetch_all(self, sql: str, params: tuple | dict = ()) -> List[sqlite3.Row]:
        """Fetch all matching rows."""
        conn = self._get_connection()
        cursor = conn.execute(sql, params)
        return cursor.fetchall()

    def run_integrity_check(self) -> bool:
        """Execute PRAGMA integrity_check to detect corruption."""
        try:
            row = self.fetch_one("PRAGMA integrity_check;")
            if row and row[0] == "ok":
                return True
            app_logger.warning(f"Integrity check returned non-ok: {row[0] if row else 'empty'}")
            return False
        except Exception as e:
            app_logger.error(f"Integrity check failed with error: {e}")
            return False

    def get_current_schema_version(self) -> int:
        """Retrieve highest applied schema migration version."""
        row = self.fetch_one("SELECT MAX(version) FROM schema_migrations;")
        if row and row[0] is not None:
            return int(row[0])
        return 0

    def apply_migrations(self, migrations: List[tuple[int, str, Callable[[sqlite3.Connection], None]]]) -> None:
        """Apply pending migrations sequentially in atomic transactions.

        Args:
            migrations: List of (version, description, migration_callable).
        """
        current_version = self.get_current_schema_version()
        for version, description, func in sorted(migrations, key=lambda m: m[0]):
            if version > current_version:
                app_logger.info(f"Applying migration v{version}: {description} on {self.db_path.name}")
                with self.transaction() as conn:
                    func(conn)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, description) VALUES (?, ?);",
                        (version, description),
                    )
                current_version = version

    def close(self) -> None:
        """Close connection for the current thread."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

