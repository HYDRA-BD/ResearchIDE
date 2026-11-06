"""Local Hardware and System Resource Monitor for ResearchIDE.

Monitors CPU, System RAM, and NVIDIA GPU VRAM targeting the RTX 3060 12GB
baseline specification without requiring heavy external dependencies.
"""
from __future__ import annotations
import ctypes
import subprocess
import shutil
from dataclasses import dataclass
from typing import Optional
from src.utils.logger import app_logger


@dataclass
class ResourceMetrics:
    """Hardware resource snapshot."""
    total_ram_gb: float
    available_ram_gb: float
    used_ram_gb: float
    ram_load_percent: int
    gpu_total_mb: Optional[float] = None
    gpu_used_mb: Optional[float] = None
    gpu_free_mb: Optional[float] = None
    gpu_name: Optional[str] = None

    @property
    def is_gpu_headroom_safe(self) -> bool:
        """True if working VRAM does not exceed 9.5 GB, preserving 2.5 GB for OS/DWM."""
        if self.gpu_used_mb is None:
            return True
        return self.gpu_used_mb < 9728.0  # 9.5 GB in MB


class SystemResourceMonitor:
    """Monitors system memory and NVIDIA GPU state."""

    class _MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    def __init__(self) -> None:
        self.nvidia_smi_path = shutil.which("nvidia-smi")

    def get_metrics(self) -> ResourceMetrics:
        """Query current RAM and GPU metrics."""
        # Query RAM via Win32 API
        try:
            stat = self._MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(self._MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

            total_ram_gb = stat.ullTotalPhys / (1024 ** 3)
            avail_ram_gb = stat.ullAvailPhys / (1024 ** 3)
            used_ram_gb = total_ram_gb - avail_ram_gb
            load_pct = stat.dwMemoryLoad
        except Exception as e:
            app_logger.warning(f"Failed querying system RAM: {e}")
            total_ram_gb, avail_ram_gb, used_ram_gb, load_pct = 16.0, 8.0, 8.0, 50

        # Query NVIDIA GPU via nvidia-smi if installed
        gpu_total, gpu_used, gpu_free, gpu_name = None, None, None, None
        if self.nvidia_smi_path:
            try:
                cmd = [
                    self.nvidia_smi_path,
                    "--query-gpu=name,memory.total,memory.used,memory.free",
                    "--format=csv,noheader,nounits",
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
                if proc.returncode == 0 and proc.stdout.strip():
                    parts = [p.strip() for p in proc.stdout.strip().split(",")]
                    if len(parts) >= 4:
                        gpu_name = parts[0]
                        gpu_total = float(parts[1])
                        gpu_used = float(parts[2])
                        gpu_free = float(parts[3])
            except Exception as e:
                app_logger.debug(f"nvidia-smi query skipped: {e}")

        return ResourceMetrics(
            total_ram_gb=round(total_ram_gb, 2),
            available_ram_gb=round(avail_ram_gb, 2),
            used_ram_gb=round(used_ram_gb, 2),
            ram_load_percent=load_pct,
            gpu_total_mb=gpu_total,
            gpu_used_mb=gpu_used,
            gpu_free_mb=gpu_free,
            gpu_name=gpu_name,
        )
