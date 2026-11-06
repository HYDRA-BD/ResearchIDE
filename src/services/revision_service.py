"""Document Revision History & Diff Tracking for ResearchIDE.

Maintains automatic local version checkpoints, generates unified line diffs,
and safely rolls back manuscripts without full Git version control complexity.
"""
from __future__ import annotations
import difflib
import hashlib
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from src.storage.file_manager import FileManager
from src.utils.logger import app_logger


@dataclass
class RevisionItem:
    """Represents a historical saved revision checkpoint of a document."""
    revision_id: str
    file_name: str
    timestamp: float
    formatted_time: str
    byte_size: int
    content_hash: str
    summary_label: str = ""
    content: str = ""


class RevisionManager:
    """Manages document revisions inside `.researchide/revisions/`."""

    @classmethod
    def get_revisions_dir(cls, project_dir: Path) -> Path:
        """Return the hidden revisions directory for a project."""
        rev_dir = Path(project_dir).resolve() / ".researchide" / "revisions"
        rev_dir.mkdir(parents=True, exist_ok=True)
        return rev_dir

    @classmethod
    def create_revision(
        cls,
        project_dir: Path,
        file_path: Path,
        content: str,
        label: str = "Manual Save",
    ) -> RevisionItem:
        """Record a new revision checkpoint for a given document."""
        rev_dir = cls.get_revisions_dir(project_dir)
        ts = time.time()
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        rev_id = f"rev_{int(ts)}_{h}"

        safe_stem = file_path.name.replace(".", "_")
        file_rev_dir = rev_dir / safe_stem
        file_rev_dir.mkdir(parents=True, exist_ok=True)

        rev_file = file_rev_dir / f"{rev_id}.txt"
        FileManager.atomic_write(rev_file, content)

        # Update metadata index
        meta_file = file_rev_dir / "index.json"
        index_data = []
        if meta_file.exists():
            try:
                index_data = json.loads(FileManager.read_text(meta_file))
            except Exception:
                index_data = []

        item = RevisionItem(
            revision_id=rev_id,
            file_name=file_path.name,
            timestamp=ts,
            formatted_time=formatted_time,
            byte_size=len(content.encode("utf-8")),
            content_hash=h,
            summary_label=label,
            content=content,
        )

        index_data.append({
            "revision_id": rev_id,
            "file_name": file_path.name,
            "timestamp": ts,
            "formatted_time": formatted_time,
            "byte_size": item.byte_size,
            "content_hash": h,
            "summary_label": label,
        })

        FileManager.atomic_write(meta_file, json.dumps(index_data, indent=2))
        app_logger.info(f"Recorded revision '{rev_id}' for '{file_path.name}'")
        return item

    @classmethod
    def list_revisions(cls, project_dir: Path, file_path: Path) -> List[RevisionItem]:
        """Retrieve list of all revisions recorded for a file."""
        rev_dir = cls.get_revisions_dir(project_dir)
        safe_stem = file_path.name.replace(".", "_")
        file_rev_dir = rev_dir / safe_stem
        meta_file = file_rev_dir / "index.json"

        if not meta_file.exists():
            return []

        try:
            index_data = json.loads(FileManager.read_text(meta_file))
            results: List[RevisionItem] = []
            for d in reversed(index_data):  # newest first
                rev_file = file_rev_dir / f"{d['revision_id']}.txt"
                content = FileManager.read_text(rev_file) if rev_file.exists() else ""
                results.append(
                    RevisionItem(
                        revision_id=d["revision_id"],
                        file_name=d["file_name"],
                        timestamp=d["timestamp"],
                        formatted_time=d["formatted_time"],
                        byte_size=d["byte_size"],
                        content_hash=d["content_hash"],
                        summary_label=d.get("summary_label", ""),
                        content=content,
                    )
                )
            return results
        except Exception as e:
            app_logger.error(f"Error reading revisions index: {e}")
            return []

    @classmethod
    def compare_revisions(cls, content_a: str, content_b: str, label_a: str = "Old", label_b: str = "New") -> str:
        """Produce unified line diff comparing two text versions."""
        lines_a = content_a.splitlines(keepends=True)
        lines_b = content_b.splitlines(keepends=True)
        diff = difflib.unified_diff(lines_a, lines_b, fromfile=label_a, tofile=label_b)
        return "".join(diff)

    @classmethod
    def restore_revision(cls, project_dir: Path, file_path: Path, revision_id: str) -> Optional[str]:
        """Restore document file to specified historical revision content."""
        rev_dir = cls.get_revisions_dir(project_dir)
        safe_stem = file_path.name.replace(".", "_")
        rev_file = rev_dir / safe_stem / f"{revision_id}.txt"

        if not rev_file.exists():
            app_logger.warning(f"Revision file '{rev_file}' not found.")
            return None

        content = FileManager.read_text(rev_file)
        # Create a pre-restore safety revision first
        cls.create_revision(project_dir, file_path, FileManager.read_text(file_path), label=f"Pre-restore ({revision_id})")
        # Overwrite file
        FileManager.atomic_write(file_path, content)
        app_logger.info(f"Restored '{file_path.name}' to revision '{revision_id}'")
        return content
