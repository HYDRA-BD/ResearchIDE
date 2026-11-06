"""LaTeX Compilation Service and TeX Distribution Manager for ResearchIDE.

Provides asynchronous LaTeX compilation, compiler discovery (MiKTeX and TeX Live),
process management, log parsing, error extraction, and output PDF preservation.
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable
from src.utils.logger import app_logger


@dataclass
class LaTeXDiagnostic:
    """Represents a compiler error, warning, or informational diagnostic message."""
    file_name: str
    line_number: int
    severity: str  # 'error', 'warning', 'info'
    message: str
    source_snippet: str = ""


@dataclass
class CompilationResult:
    """Outcome of a LaTeX compilation run."""
    success: bool
    pdf_path: Optional[Path] = None
    diagnostics: List[LaTeXDiagnostic] = field(default_factory=list)
    log_content: str = ""
    duration_seconds: float = 0.0
    error_summary: str = ""


@dataclass
class TeXDistributionInfo:
    """Metadata regarding an installed TeX distribution on Windows."""
    name: str  # 'MiKTeX' or 'TeX Live'
    bin_dir: Path
    engines_found: List[str] = field(default_factory=list)


class LaTeXLogParser:
    """Extracts structured errors, warnings, and source line numbers from LaTeX log files."""

    ERROR_LINE_RE = re.compile(r"^l\.(\d+)\s*(.*)$")
    GENERIC_ERROR_RE = re.compile(r"^!\s+(.*?)$")
    LATEX_WARNING_LINE_RE = re.compile(r"^LaTeX Warning:\s*(.*?)\s+on input line (\d+)\.", re.MULTILINE)
    GENERIC_WARNING_RE = re.compile(r"^((?:Package|Class|LaTeX)\s+[\w\-]+ Warning:\s*.*?)(?:\n\n|\n[A-Z]|\Z)", re.DOTALL | re.MULTILINE)

    @classmethod
    def parse_log(cls, log_text: str, default_file: str = "main.tex") -> List[LaTeXDiagnostic]:
        """Parse raw compilation log into a list of typed diagnostics."""
        diagnostics: List[LaTeXDiagnostic] = []
        lines = log_text.splitlines()

        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]

            # Detect error indicated by leading '!'
            if line.startswith("!"):
                error_msg = line[1:].strip()
                line_no = 1
                snippet = ""

                # Look forward up to 10 lines for "l.<number> <snippet>"
                for lookahead in range(1, 12):
                    if i + lookahead >= n:
                        break
                    next_line = lines[i + lookahead]
                    match = cls.ERROR_LINE_RE.match(next_line)
                    if match:
                        line_no = int(match.group(1))
                        snippet = match.group(2).strip()
                        break
                    if next_line.startswith("!"):
                        break

                diagnostics.append(
                    LaTeXDiagnostic(
                        file_name=default_file,
                        line_number=line_no,
                        severity="error",
                        message=error_msg,
                        source_snippet=snippet,
                    )
                )

            # Detect explicit LaTeX Warning with line number
            elif "LaTeX Warning:" in line:
                match = cls.LATEX_WARNING_LINE_RE.search(line)
                if match:
                    warn_msg = match.group(1).strip()
                    line_no = int(match.group(2))
                    diagnostics.append(
                        LaTeXDiagnostic(
                            file_name=default_file,
                            line_number=line_no,
                            severity="warning",
                            message=warn_msg,
                        )
                    )
                else:
                    diagnostics.append(
                        LaTeXDiagnostic(
                            file_name=default_file,
                            line_number=1,
                            severity="warning",
                            message=line.replace("LaTeX Warning:", "").strip(),
                        )
                    )

            # Detect Overfull \hbox warnings
            elif line.startswith("Overfull \\hbox") or line.startswith("Underfull \\hbox"):
                line_match = re.search(r"at lines? (\d+)", line)
                line_no = int(line_match.group(1)) if line_match else 1
                diagnostics.append(
                    LaTeXDiagnostic(
                        file_name=default_file,
                        line_number=line_no,
                        severity="warning",
                        message=line.strip(),
                    )
                )

            i += 1

        return diagnostics


class LaTeXCompilerService:
    """Manages local TeX engines, execution queues, and multi-pass builds."""

    STANDARD_MIKTEX_PATHS = [
        Path("E:/miktex/miktex/bin/x64"),
        Path("C:/Program Files/MiKTeX/miktex/bin/x64"),
        Path(os.path.expandvars("%LOCALAPPDATA%/Programs/MiKTeX/miktex/bin/x64")),
    ]

    STANDARD_TEXLIVE_PATHS = [
        Path("C:/texlive/2026/bin/windows"),
        Path("C:/texlive/2025/bin/windows"),
        Path("C:/texlive/2024/bin/windows"),
        Path("C:/texlive/2023/bin/win32"),
    ]

    def __init__(self, custom_bin_dir: Optional[Path | str] = None) -> None:
        self.custom_bin_dir = Path(custom_bin_dir) if custom_bin_dir else None
        self._current_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._is_cancelled = False

    def discover_distributions(self) -> List[TeXDistributionInfo]:
        """Scan system paths and registry for installed TeX distributions."""
        found: List[TeXDistributionInfo] = []

        candidates = []
        if self.custom_bin_dir and self.custom_bin_dir.exists():
            candidates.append(("Custom TeX", self.custom_bin_dir))

        for p in self.STANDARD_MIKTEX_PATHS:
            if p.exists():
                candidates.append(("MiKTeX", p))

        for p in self.STANDARD_TEXLIVE_PATHS:
            if p.exists():
                candidates.append(("TeX Live", p))

        # Check system PATH
        path_env = os.environ.get("PATH", "")
        for item in path_env.split(os.path.pathsep):
            item_path = Path(item)
            if (item_path / "pdflatex.exe").exists():
                candidates.append(("System PATH", item_path))

        seen = set()
        for name, bin_dir in candidates:
            resolved = bin_dir.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)

            engines = []
            for eng in ["pdflatex.exe", "xelatex.exe", "lualatex.exe", "bibtex.exe", "biber.exe", "synctex.exe"]:
                if (resolved / eng).exists():
                    engines.append(eng.replace(".exe", ""))

            if engines:
                found.append(TeXDistributionInfo(name=name, bin_dir=resolved, engines_found=engines))

        return found

    def get_binary_path(self, binary_name: str) -> Optional[Path]:
        """Locate full executable path for an engine."""
        exe_name = binary_name if binary_name.endswith(".exe") else f"{binary_name}.exe"

        # Check custom bin dir first
        if self.custom_bin_dir:
            target = self.custom_bin_dir / exe_name
            if target.exists():
                return target

        # Check discovered distributions
        dists = self.discover_distributions()
        for dist in dists:
            target = dist.bin_dir / exe_name
            if target.exists():
                return target

        # Check standard PATH
        which_path = shutil.which(binary_name)
        if which_path:
            return Path(which_path)

        return None

    def cancel_compilation(self) -> None:
        """Cancel ongoing build process immediately."""
        self._is_cancelled = True
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                app_logger.info("Terminating active LaTeX compilation process.")
                try:
                    self._current_process.terminate()
                    time.sleep(0.2)
                    if self._current_process.poll() is None:
                        self._current_process.kill()
                except Exception as e:
                    app_logger.warning(f"Error killing compiler process: {e}")

    def compile(
        self,
        main_tex_file: Path | str,
        engine: str = "pdflatex",
        run_bibtex: bool = True,
        build_dir: Optional[Path | str] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> CompilationResult:
        """Execute compilation with SyncTeX enabled, preserving previous PDF on failure."""
        start_time = time.time()
        main_path = Path(main_tex_file).resolve()

        if not main_path.exists():
            return CompilationResult(
                success=False,
                duration_seconds=0.0,
                error_summary=f"LaTeX root file not found: {main_path}",
            )

        # Output directory: use specified build_dir or default to project's .researchide/build
        work_dir = main_path.parent
        project_root = work_dir.parent if work_dir.name in ("src", "sections") else work_dir

        if build_dir:
            out_dir = Path(build_dir).resolve()
        else:
            out_dir = project_root / ".researchide" / "build"
        out_dir.mkdir(parents=True, exist_ok=True)

        engine_bin = self.get_binary_path(engine)
        if not engine_bin:
            return CompilationResult(
                success=False,
                duration_seconds=0.0,
                error_summary=f"Compiler engine '{engine}' executable not found. Please verify TeX installation.",
            )

        stem = main_path.stem
        target_pdf = out_dir / f"{stem}.pdf"
        previous_backup_pdf: Optional[Path] = None

        # Backup existing PDF before building to preserve on failure
        if target_pdf.exists():
            backup_name = f".{stem}.backup.pdf"
            previous_backup_pdf = out_dir / backup_name
            try:
                shutil.copy2(target_pdf, previous_backup_pdf)
            except Exception:
                pass

        self._is_cancelled = False
        full_log = []

        def _update_status(msg: str) -> None:
            if status_callback:
                status_callback(msg)
            app_logger.info(f"[LaTeX Build] {msg}")

        # Multi-pass execution pipeline
        passes = [(engine_bin, f"Running {engine} (Pass 1)...")]
        if run_bibtex:
            bibtex_bin = self.get_binary_path("bibtex")
            if bibtex_bin:
                passes.append((bibtex_bin, "Running BibTeX..."))
                passes.append((engine_bin, f"Running {engine} (Pass 2)..."))
                passes.append((engine_bin, f"Running {engine} (Pass 3)..."))

        final_success = True

        for bin_path, desc in passes:
            if self._is_cancelled:
                _update_status("Compilation cancelled by user.")
                final_success = False
                break

            _update_status(desc)

            # Construct arguments safely
            if "bibtex" in bin_path.name.lower():
                # bibtex operates on the aux file stem inside out_dir
                cmd = [str(bin_path), stem]
                exec_cwd = out_dir
            else:
                cmd = [
                    str(bin_path),
                    "-interaction=nonstopmode",
                    "-synctex=1",
                    f"-output-directory={str(out_dir)}",
                    str(main_path),
                ]
                exec_cwd = work_dir

            with self._lock:
                try:
                    self._current_process = subprocess.Popen(
                        cmd,
                        cwd=str(exec_cwd),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                except Exception as e:
                    full_log.append(f"Failed to spawn {bin_path.name}: {e}\n")
                    final_success = False
                    break

            # Stream output
            stdout_data, _ = self._current_process.communicate()
            full_log.append(stdout_data)

            return_code = self._current_process.returncode
            if "bibtex" not in bin_path.name.lower() and return_code != 0:
                # Fatal compiler error in TeX pass
                final_success = False
                break

        duration = time.time() - start_time
        merged_log = "\n".join(full_log)

        # Parse diagnostics from log file in out_dir or stdout
        log_file = out_dir / f"{stem}.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = merged_log
        else:
            log_content = merged_log

        diagnostics = LaTeXLogParser.parse_log(log_content, default_file=main_path.name)
        has_fatal_errors = any(d.severity == "error" for d in diagnostics)

        if not target_pdf.exists() or has_fatal_errors or not final_success:
            # Build failed: restore previous PDF if available
            if previous_backup_pdf and previous_backup_pdf.exists():
                try:
                    shutil.copy2(previous_backup_pdf, target_pdf)
                    _update_status("Build failed: Preserved previously working PDF.")
                except Exception:
                    pass

            return CompilationResult(
                success=False,
                pdf_path=target_pdf if target_pdf.exists() else None,
                diagnostics=diagnostics,
                log_content=log_content,
                duration_seconds=duration,
                error_summary="Compilation encountered errors. Check build log.",
            )

        # Cleanup backup
        if previous_backup_pdf and previous_backup_pdf.exists():
            try:
                previous_backup_pdf.unlink()
            except Exception:
                pass

        _update_status(f"Compilation finished successfully in {duration:.2f}s")
        return CompilationResult(
            success=True,
            pdf_path=target_pdf,
            diagnostics=diagnostics,
            log_content=log_content,
            duration_seconds=duration,
        )
