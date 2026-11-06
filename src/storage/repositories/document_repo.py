"""Document and Block Repository for ResearchIDE."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import hashlib
from src.storage.database import DatabaseManager


@dataclass
class DocumentRecord:
    id: str
    relative_path: str
    title: str
    doc_type: str
    content_hash: str
    created_at: str = ""
    updated_at: str = ""


class DocumentRepository:
    """Manages document entries and canonical blocks in project.db."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    relative_path TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_blocks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    block_type TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    raw_latex TEXT NOT NULL,
                    source_start_line INTEGER NOT NULL,
                    source_start_col INTEGER NOT NULL,
                    source_end_line INTEGER NOT NULL,
                    source_end_col INTEGER NOT NULL,
                    metadata_json TEXT
                );
                """
            )

    @staticmethod
    def compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def register_document(self, doc_id: str, relative_path: str, title: str, doc_type: str, content: str) -> DocumentRecord:
        """Register or update a document record."""
        content_hash = self.compute_hash(content)
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, relative_path, title, doc_type, content_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(relative_path) DO UPDATE SET
                    title = excluded.title,
                    doc_type = excluded.doc_type,
                    content_hash = excluded.content_hash,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (doc_id, relative_path, title, doc_type, content_hash),
            )
        return self.get_document_by_path(relative_path)  # type: ignore

    def get_document_by_path(self, relative_path: str) -> Optional[DocumentRecord]:
        row = self.db.fetch_one("SELECT * FROM documents WHERE relative_path = ?;", (relative_path,))
        if not row:
            return None
        return DocumentRecord(
            id=row["id"],
            relative_path=row["relative_path"],
            title=row["title"],
            doc_type=row["doc_type"],
            content_hash=row["content_hash"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def list_documents(self) -> List[DocumentRecord]:
        rows = self.db.fetch_all("SELECT * FROM documents ORDER BY updated_at DESC;")
        return [
            DocumentRecord(
                id=r["id"],
                relative_path=r["relative_path"],
                title=r["title"],
                doc_type=r["doc_type"],
                content_hash=r["content_hash"],
                created_at=str(r["created_at"]),
                updated_at=str(r["updated_at"]),
            )
            for r in rows
        ]

    def delete_document(self, doc_id: str) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?;", (doc_id,))

