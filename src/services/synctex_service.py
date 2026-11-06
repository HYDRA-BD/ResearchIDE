"""SyncTeX Bidirectional Synchronization Service for ResearchIDE.

Provides forward (Source -> PDF) and inverse (PDF -> Source) navigation
using local synctex binaries and gzip record parsing.
"""

from __future__ import annotations
import gzip
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
from src.utils.logger import app_logger


@dataclass
class SyncTeXPDFLocation:
    """PDF coordinates corresponding to a source line."""
    page: int
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0


@dataclass
class SyncTeXSourceLocation:
    """Source file coordinates corresponding to a PDF click."""
    file_path: Path
    line: int
    column: int = 1


class SyncTeXService:
    """Handles bidirectional synchronization between LaTeX source and compiled PDF."""

    def __init__(self, synctex_bin_path: Optional[Path | str] = None) -> None:
        self.synctex_bin = Path(synctex_bin_path) if synctex_bin_path else None

    def forward_sync(
        self,
        source_file: Path | str,
        line: int,
        column: int,
        pdf_path: Path | str,
    ) -> Optional[SyncTeXPDFLocation]:
        """Map source file line/col to PDF page coordinates."""
        source = Path(source_file).resolve()
        pdf = Path(pdf_path).resolve()
        synctex_gz = pdf.with_suffix(".synctex.gz")

        if not pdf.exists():
            return None

        # 1. Try synctex CLI if binary path is provided or available
        if self.synctex_bin and self.synctex_bin.exists():
            cmd = [
                str(self.synctex_bin),
                "view",
                "-i", f"{line}:{column}:{str(source)}",
                "-o", str(pdf),
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                output = res.stdout
                page_match = re.search(r"Page:(\d+)", output)
                x_match = re.search(r"x:([0-9\.]+)", output)
                y_match = re.search(r"y:([0-9\.]+)", output)
                if page_match and x_match and y_match:
                    return SyncTeXPDFLocation(
                        page=int(page_match.group(1)) - 1,  # 0-indexed page for QtPdf
                        x=float(x_match.group(1)),
                        y=float(y_match.group(1)),
                    )
            except Exception as e:
                app_logger.warning(f"synctex.exe forward sync failed: {e}")

        # 2. Pure-Python Gzip parser fallback
        if synctex_gz.exists():
            return self._parse_forward_from_gz(synctex_gz, source.name, line)

        # Fallback to page 0
        return SyncTeXPDFLocation(page=0, x=0.0, y=0.0)

    def inverse_sync(
        self,
        pdf_path: Path | str,
        page: int,
        x: float,
        y: float,
    ) -> Optional[SyncTeXSourceLocation]:
        """Map PDF click coordinates back to source file and line."""
        pdf = Path(pdf_path).resolve()
        synctex_gz = pdf.with_suffix(".synctex.gz")

        if not pdf.exists():
            return None

        # 1. Try synctex CLI if binary path is provided or available
        if self.synctex_bin and self.synctex_bin.exists():
            # synctex tool expects 1-indexed page
            cmd = [
                str(self.synctex_bin),
                "edit",
                "-o", f"{page + 1}:{x}:{y}:{str(pdf)}",
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                output = res.stdout
                input_match = re.search(r"Input:(.*?)$", output, re.MULTILINE)
                line_match = re.search(r"Line:(\d+)", output)
                col_match = re.search(r"Column:(\d+)", output)
                if input_match and line_match:
                    return SyncTeXSourceLocation(
                        file_path=Path(input_match.group(1).strip()),
                        line=int(line_match.group(1)),
                        column=int(col_match.group(1)) if col_match else 1,
                    )
            except Exception as e:
                app_logger.warning(f"synctex.exe inverse sync failed: {e}")

        # 2. Pure-Python Gzip parser fallback
        if synctex_gz.exists():
            return self._parse_inverse_from_gz(synctex_gz, page + 1)

        return None

    def _parse_forward_from_gz(self, synctex_gz: Path, filename: str, target_line: int) -> Optional[SyncTeXPDFLocation]:
        """Parse gzipped SyncTeX record file to find nearest page coordinate."""
        try:
            with gzip.open(synctex_gz, "rt", encoding="utf-8", errors="replace") as f:
                current_page = 1
                for line in f:
                    if line.startswith("{"):
                        # Beginning of page block, e.g. {1
                        try:
                            current_page = int(line[1:].strip())
                        except ValueError:
                            pass
                    elif line.startswith("x") or line.startswith("k"):
                        # Record format: x<tag>,<line>:<x>,<y>:<w>,<h>
                        parts = line.split(":")
                        if len(parts) >= 2:
                            tag_line = parts[0][1:].split(",")
                            if len(tag_line) == 2:
                                rec_line = int(tag_line[1])
                                if abs(rec_line - target_line) <= 2:
                                    coords = parts[1].split(",")
                                    x_val = float(coords[0]) if len(coords) > 0 else 0.0
                                    y_val = float(coords[1]) if len(coords) > 1 else 0.0
                                    return SyncTeXPDFLocation(
                                        page=max(0, current_page - 1),
                                        x=x_val / 65536.0,  # convert scaled points to points
                                        y=y_val / 65536.0,
                                    )
        except Exception as e:
            app_logger.error(f"Error parsing synctex.gz: {e}")
        return SyncTeXPDFLocation(page=0, x=0.0, y=0.0)

    def _parse_inverse_from_gz(self, synctex_gz: Path, page_1based: int) -> Optional[SyncTeXSourceLocation]:
        """Parse gzipped SyncTeX record file to find nearest line for a given page."""
        try:
            with gzip.open(synctex_gz, "rt", encoding="utf-8", errors="replace") as f:
                input_files = {}
                in_target_page = False
                for line in f:
                    if line.startswith("Input:"):
                        # Format: Input:1:main.tex
                        parts = line.strip().split(":", 2)
                        if len(parts) == 3:
                            input_files[parts[1]] = Path(parts[2])
                    elif line.startswith(f"{{{page_1based}"):
                        in_target_page = True
                    elif line.startswith("}") and in_target_page:
                        break
                    elif in_target_page and (line.startswith("x") or line.startswith("k")):
                        parts = line.split(":")
                        if len(parts) >= 2:
                            tag_line = parts[0][1:].split(",")
                            if len(tag_line) == 2:
                                file_tag = tag_line[0]
                                rec_line = int(tag_line[1])
                                target_file = input_files.get(file_tag, synctex_gz.parent / "main.tex")
                                return SyncTeXSourceLocation(
                                    file_path=target_file,
                                    line=rec_line,
                                )
        except Exception as e:
            app_logger.error(f"Error in inverse parsing synctex.gz: {e}")
        return None

