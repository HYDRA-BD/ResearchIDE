"""Structured System Diagnostics, Health Reporter & Log Auditor for ResearchIDE.

Gathers hardware metrics, compiler distributions, local Ollama endpoints,
and SQLite database PRAGMA integrity checks into exportable diagnostic reports.
"""
from __future__ import annotations
import platform
import sys
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any
from src.services.resource_monitor import SystemResourceMonitor
from src.services.latex_service import LaTeXCompilerService
from src.services.ai_service import OllamaService
from src.utils.logger import app_logger


@dataclass
class SystemDiagnosticReport:
    """Comprehensive diagnostic snapshot of the workstation environment."""
    os_info: str
    python_version: str
    hardware_summary: str
    latex_distribution_status: str
    ollama_service_status: str
    database_integrity: str
    passed_all: bool
    details: Dict[str, Any] = field(default_factory=dict)


class SystemDiagnosticsService:
    """Runs end-to-end health audits across all subsystems."""

    @classmethod
    def run_diagnostics(
        cls,
        db_path: Optional[Path] = None,
        ollama_host: str = "http://localhost:11434",
    ) -> SystemDiagnosticReport:
        """Execute complete diagnostic evaluation."""
        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        py_ver = sys.version.split()[0]
        details: Dict[str, Any] = {}
        all_passed = True

        # 1. Hardware Metrics
        monitor = SystemResourceMonitor()
        metrics = monitor.get_metrics()
        gpu_str = f"{metrics.gpu_name or 'NVIDIA GPU'} ({metrics.gpu_used_mb or 0:.0f}/{metrics.gpu_total_mb or 0:.0f} MB)" if metrics.gpu_total_mb else "No dedicated GPU detected"
        hw_summary = (
            f"RAM: {metrics.used_ram_gb:.1f}/{metrics.total_ram_gb:.1f} GB ({metrics.ram_load_percent}%) | "
            f"GPU: {gpu_str}"
        )
        details["hardware"] = {
            "ram_total_gb": metrics.total_ram_gb,
            "ram_avail_gb": metrics.available_ram_gb,
            "gpu_name": metrics.gpu_name,
            "gpu_vram_mb": metrics.gpu_total_mb,
            "gpu_safe_headroom": metrics.is_gpu_headroom_safe,
        }

        # 2. LaTeX Distribution Check
        compiler = LaTeXCompilerService()
        engines = compiler.detect_available_engines()
        if engines:
            pdflatex_path = compiler.get_binary_path("pdflatex")
            latex_status = f"Available ({len(engines)} engines: {', '.join(engines)}) at '{pdflatex_path}'"
            details["latex"] = {"status": "ok", "engines": engines, "binary": str(pdflatex_path)}
        else:
            latex_status = "Not detected in PATH or standard MiKTeX/TeX Live directories"
            details["latex"] = {"status": "missing", "engines": []}
            all_passed = False

        # 3. Local Ollama AI Engine Check
        ollama = OllamaService(host=ollama_host)
        is_ollama_ok, ollama_msg = ollama.check_connection()
        if is_ollama_ok:
            models = ollama.list_models()
            ollama_status = f"Connected ({len(models)} models available: {', '.join(models[:3])})"
            details["ollama"] = {"status": "connected", "models": models}
        else:
            ollama_status = f"Offline / Unreachable ({ollama_msg})"
            details["ollama"] = {"status": "offline", "message": ollama_msg}
            # Note: Ollama offline is not a fatal crash, application works offline

        # 4. SQLite Database Integrity Check
        db_status = "No database provided"
        if db_path and Path(db_path).exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                rows = cursor.fetchall()
                conn.close()
                if rows and rows[0][0] == "ok":
                    db_status = "Verified (PRAGMA integrity_check: ok)"
                    details["database"] = {"status": "ok", "path": str(db_path)}
                else:
                    db_status = f"Warning: {rows}"
                    details["database"] = {"status": "corrupt", "result": str(rows)}
                    all_passed = False
            except Exception as e:
                db_status = f"Error: {e}"
                details["database"] = {"status": "error", "error": str(e)}
                all_passed = False

        return SystemDiagnosticReport(
            os_info=os_info,
            python_version=py_ver,
            hardware_summary=hw_summary,
            latex_distribution_status=latex_status,
            ollama_service_status=ollama_status,
            database_integrity=db_status,
            passed_all=all_passed,
            details=details,
        )

    @classmethod
    def export_report_text(cls, report: SystemDiagnosticReport) -> str:
        """Format report as exportable plain text for technical support."""
        return "\n".join([
            "==================================================================",
            "ResearchIDE System Diagnostics & Technical Environment Report",
            "==================================================================",
            f"Operating System:     {report.os_info}",
            f"Python Runtime:       {report.python_version}",
            f"Hardware State:       {report.hardware_summary}",
            f"LaTeX Compiler:       {report.latex_distribution_status}",
            f"Local Ollama AI:      {report.ollama_service_status}",
            f"Database Integrity:   {report.database_integrity}",
            f"Overall Ready Status: {'PASSED' if report.passed_all else 'ATTENTION REQUIRED'}",
            "==================================================================",
        ])
