"""Configuration data models and default application settings for ResearchIDE."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json


@dataclass
class AppearanceSettings:
    theme: str = "dark"  # "dark", "light", "system"
    font_size: int = 12
    ui_scale: float = 1.0
    editor_font_family: str = "Consolas"


@dataclass
class CompilerSettings:
    active_engine: str = "pdflatex"  # "pdflatex", "xelatex", "lualatex"
    custom_bin_path: str = "E:\\miktex\\miktex\\bin\\x64"
    auto_compile_on_save: bool = True
    debounce_ms: int = 1000
    synctex_enabled: bool = True


@dataclass
class AISettings:
    ollama_host: str = "http://127.0.0.1:11434"
    active_model: str = "qwen2.5:14b-instruct-q4_K_M"
    context_length: int = 8192
    temperature: float = 0.2
    auto_unload_timeout_seconds: int = 300


@dataclass
class PDFPreviewSettings:
    default_zoom_mode: str = "fit_width"  # "fit_width", "fit_page", "100%"
    continuous_scroll: bool = True
    highlight_synctex: bool = True


@dataclass
class PerformanceSettings:
    max_worker_threads: int = 4
    throttle_background_indexing: bool = True
    memory_limit_mb: int = 12000


@dataclass
class AppSettings:
    """Master application configuration container."""
    default_project_dir: str = str(Path.home() / "Documents" / "ResearchIDE_Projects")
    autosave_enabled: bool = True
    autosave_interval_seconds: int = 60
    appearance: AppearanceSettings = field(default_factory=AppearanceSettings)
    compiler: CompilerSettings = field(default_factory=CompilerSettings)
    ai: AISettings = field(default_factory=AISettings)
    pdf: PDFPreviewSettings = field(default_factory=PDFPreviewSettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AppSettings:
        appearance_data = data.get("appearance", {})
        compiler_data = data.get("compiler", {})
        ai_data = data.get("ai", {})
        pdf_data = data.get("pdf", {})
        perf_data = data.get("performance", {})

        return cls(
            default_project_dir=data.get(
                "default_project_dir",
                str(Path.home() / "Documents" / "ResearchIDE_Projects"),
            ),
            autosave_enabled=data.get("autosave_enabled", True),
            autosave_interval_seconds=data.get("autosave_interval_seconds", 60),
            appearance=AppearanceSettings(**appearance_data) if appearance_data else AppearanceSettings(),
            compiler=CompilerSettings(**compiler_data) if compiler_data else CompilerSettings(),
            ai=AISettings(**ai_data) if ai_data else AISettings(),
            pdf=PDFPreviewSettings(**pdf_data) if pdf_data else PDFPreviewSettings(),
            performance=PerformanceSettings(**perf_data) if perf_data else PerformanceSettings(),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> AppSettings:
        return cls.from_dict(json.loads(json_str))

