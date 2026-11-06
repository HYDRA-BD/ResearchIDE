"""Autosave, Crash Recovery & Snapshot Service for ResearchIDE.

Maintains pre-mutation snapshots, detects unclean terminations, and restores
unsaved document changes safely without corrupting original files.
"""
from __future__ import annotations
import hashlib
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from src.storage.file_manager import FileManager
from src.utils.logger import app_logger


@dataclass
class RecoverySnapshot:
    """Represents a crash recovery snapshot of an open document."""
    file_path: Path
    snapshot_path: Path
    timestamp: float
    content_hash: str
    content: str


class DocumentRecoveryService:
    """Manages document snapshots and detects crash recovery candidates."""

    @classmethod
    def get_snapshot_dir(cls, project_dir: Path) -> Path:
        """Return the hidden project snapshot cache directory."""
        snap_dir = Path(project_dir).resolve() / ".researchide" / "snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        return snap_dir

    @classmethod
    def save_snapshot(cls, project_dir: Path, target_file: Path, content: str) -> Path:
        """Create a timestamped snapshot of uncommitted working buffer."""
        snap_dir = cls.get_snapshot_dir(project_dir)
        safe_stem = target_file.name.replace(".", "_")
        snap_file = snap_dir / f"{safe_stem}.recovery.bak"

        FileManager.atomic_write(snap_file, content)
        app_logger.debug(f"Saved crash recovery snapshot for '{target_file.name}'")
        return snap_file

    @classmethod
    def clear_snapshot(cls, project_dir: Path, target_file: Path) -> None:
        """Remove recovery snapshot after successful manual save or clean close."""
        snap_dir = cls.get_snapshot_dir(project_dir)
        safe_stem = target_file.name.replace(".", "_")
        snap_file = snap_dir / f"{safe_stem}.recovery.bak"
        if snap_file.exists():
            try:
                snap_file.unlink()
                app_logger.debug(f"Cleared recovery snapshot for '{target_file.name}'")
            except Exception as e:
                app_logger.warning(f"Could not delete snapshot '{snap_file}': {e}")

    @classmethod
    def detect_unrecovered_snapshots(cls, project_dir: Path) -> List[RecoverySnapshot]:
        """Scan project snapshot directory for lingering recovery snapshots from unclean exits."""
        candidates: List[RecoverySnapshot] = []
        snap_dir = cls.get_snapshot_dir(project_dir)

        for snap_file in snap_dir.glob("*.recovery.bak"):
            try:
                content = FileManager.read_text(snap_file)
                mtime = snap_file.stat().st_mtime
                h = hashlib.sha256(content.encode("utf-8")).hexdigest()

                # Infer original file name
                original_stem = snap_file.name.replace(".recovery.bak", "")
                candidates.append(
                    RecoverySnapshot(
                        file_path=Path(original_stem),
                        snapshot_path=snap_file,
                        timestamp=mtime,
                        content_hash=h,
                        content=content,
                    )
                )
            except Exception as e:
                app_logger.error(f"Error reading snapshot '{snap_file}': {e}")

        return candidates
