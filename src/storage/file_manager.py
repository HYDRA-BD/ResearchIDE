"""Safe File Operations and Project Workspace Scaffolding for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
import os
import shutil
import uuid
from src.utils.logger import app_logger


class FileSecurityError(Exception):
    """Raised when a path traversal or out-of-bounds file operation is attempted."""
    pass


class FileManager:
    """Provides atomic file operations, project scaffolding, and safety validation."""

    @staticmethod
    def validate_path_within_project(target_path: Path | str, project_root: Path | str) -> Path:
        """Ensure target path resides strictly within the project boundary.

        Raises:
            FileSecurityError: If path attempts directory traversal outside project.
        """
        root = Path(project_root).resolve()
        target = Path(target_path).resolve()
        try:
            target.relative_to(root)
        except ValueError as e:
            app_logger.error(f"Path traversal blocked: '{target}' is outside '{root}'")
            raise FileSecurityError(f"Access denied: '{target}' is outside project root '{root}'") from e
        return target

    @classmethod
    def atomic_write(cls, target_path: Path | str, content: str | bytes, encoding: str = "utf-8") -> None:
        """Write content to target atomically via temporary swap file."""
        target = Path(target_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        temp_name = f".{target.name}.{uuid.uuid4().hex}.tmp"
        temp_file = target.parent / temp_name

        try:
            if isinstance(content, str):
                with open(temp_file, "w", encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
            else:
                with open(temp_file, "wb") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())

            # Atomic replace on Windows
            temp_file.replace(target)
        except Exception as e:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            app_logger.error(f"Failed atomic write to {target}: {e}")
            raise IOError(f"Atomic write to '{target}' failed: {e}") from e

    @classmethod
    def read_text(cls, target_path: Path | str, encoding: str = "utf-8") -> str:
        """Read full text content safely."""
        target = Path(target_path).resolve()
        if not target.exists():
            raise FileNotFoundError(f"File not found: '{target}'")
        with open(target, "r", encoding=encoding) as f:
            return f.read()

    @classmethod
    def scaffold_project(cls, project_dir: Path | str, project_name: str) -> Path:
        """Create standard ResearchIDE directory tree and starter template files."""
        root = Path(project_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)

        # Standard subdirectories
        subdirs = [
            root / "src",
            root / "src" / "sections",
            root / "literature",
            root / "assets" / "figures",
            root / "assets" / "plots",
            root / "notes",
            root / "data",
            root / ".researchide",
            root / ".researchide" / "snapshots",
            root / ".researchide" / "cache",
        ]
        for d in subdirs:
            d.mkdir(parents=True, exist_ok=True)

        # Starter LaTeX main.tex
        starter_tex = (
            "\\documentclass[11pt,a4paper]{article}\n"
            "\\usepackage{amsmath}\n"
            "\\usepackage{amssymb}\n"
            "\\usepackage{graphicx}\n"
            "\\usepackage{hyperref}\n\n"
            f"\\title{{{project_name}}}\n"
            "\\author{Research Author}\n"
            "\\date{\\today}\n\n"
            "\\begin{document}\n\n"
            "\\maketitle\n\n"
            "\\begin{abstract}\n"
            "This paper introduces the core research objectives and methodologies.\n"
            "\\end{abstract}\n\n"
            "\\section{Introduction}\n"
            "Begin typing your manuscript here.\n\n"
            "\\section{Methodology}\n"
            "Describe the experimental or theoretical framework.\n\n"
            "\\begin{equation}\n"
            "\\label{eq:sample}\n"
            "E = mc^2\n"
            "\\end{equation}\n\n"
            "\\section{Conclusion}\n"
            "Summarize the primary contributions.\n\n"
            "\\end{document}\n"
        )
        cls.atomic_write(root / "src" / "main.tex", starter_tex)

        # Starter bibliography
        starter_bib = (
            "% ResearchIDE Bibliography\n"
            "@article{einstein1905,\n"
            "  author = {Einstein, Albert},\n"
            "  title = {Zur Elektrodynamik bewegter K{\\\"o}rper},\n"
            "  journal = {Annalen der Physik},\n"
            "  year = {1905},\n"
            "  volume = {322},\n"
            "  pages = {891--921}\n"
            "}\n"
        )
        cls.atomic_write(root / "src" / "references.bib", starter_bib)

        # Starter research note
        starter_note = (
            f"# Research Notes: {project_name}\n\n"
            "- Initial project initialized.\n"
            "- Add research papers to literature/ folder.\n"
        )
        cls.atomic_write(root / "notes" / "research_notes.md", starter_note)

        app_logger.info(f"Project scaffolding created at '{root}'")
        return root

    @classmethod
    def delete_project(cls, project_dir: Path | str) -> None:
        """Safely delete project directory."""
        root = Path(project_dir).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Project directory '{root}' does not exist.")
        shutil.rmtree(root)
        app_logger.info(f"Project directory '{root}' deleted successfully.")

    @classmethod
    def rename_project_dir(cls, old_dir: Path | str, new_name: str) -> Path:
        """Rename project folder while keeping same parent directory."""
        old_path = Path(old_dir).resolve()
        new_path = old_path.parent / new_name
        if new_path.exists():
            raise FileExistsError(f"A directory with name '{new_name}' already exists at '{old_path.parent}'")
        old_path.rename(new_path)
        app_logger.info(f"Project renamed from '{old_path.name}' to '{new_name}'")
        return new_path

