"""Local AI Engine & Academic Writing Assistant via Ollama for ResearchIDE.

Strictly operates 100% locally with zero cloud API dependencies. Enforces a
single-model VRAM resident policy targeting the NVIDIA RTX 3060 12GB.
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from PySide6.QtCore import QObject, Signal, QThread
from src.utils.logger import app_logger


class AIPersona(str, Enum):
    """Academic AI specialist personas with tailored system prompts."""
    ACADEMIC_WRITER = "Academic Writer"
    LATEX_ENGINEER = "LaTeX Engineer"
    RESEARCH_ANALYST = "Research Analyst"
    MATH_REASONER = "Mathematical Reasoner"
    CODE_ASSISTANT = "Computational Assistant"


PERSONA_SYSTEM_PROMPTS: Dict[AIPersona, str] = {
    AIPersona.ACADEMIC_WRITER: (
        "You are an expert academic research writer. Your task is to produce rigorous, "
        "scholarly prose with clear arguments, logical transitions, and an objective tone. "
        "Avoid conversational pleasantries. Provide ready-to-insert text suitable for peer-reviewed publication."
    ),
    AIPersona.LATEX_ENGINEER: (
        "You are a senior LaTeX engineering specialist. You analyze compilation errors, "
        "diagnose package conflicts, and write robust, compilable LaTeX syntax. When suggesting fixes, "
        "provide the exact corrected LaTeX block and concisely explain the root cause."
    ),
    AIPersona.RESEARCH_ANALYST: (
        "You are a scientific research analyst. You evaluate methodologies, summarize literature, "
        "identify gaps in experimental design, and synthesize findings across papers into structured comparative matrices."
    ),
    AIPersona.MATH_REASONER: (
        "You are a mathematical and symbolic reasoning assistant. You explain mathematical equations, "
        "verify algebraic derivations step-by-step, identify dimension/unit mismatches, and suggest clear notation."
    ),
    AIPersona.CODE_ASSISTANT: (
        "You are a scientific computing assistant. You write clean, vectorized Python code (NumPy, SciPy, Matplotlib) "
        "for academic simulations and data visualizations."
    ),
}


class OllamaInferenceWorker(QThread):
    """Background worker for streaming token generation from local Ollama without blocking UI."""

    chunk_received = Signal(str)       # Emits token as it arrives
    finished = Signal(str)             # Emits complete accumulated text
    error_occurred = Signal(str)       # Emits error description

    def __init__(
        self,
        base_url: str,
        model_name: str,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.3,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.temperature = temperature
        self._is_cancelled = False

    def cancel(self) -> None:
        """Flag cancellation to break out of stream reading."""
        self._is_cancelled = True

    def run(self) -> None:
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": self.prompt,
            "system": self.system_prompt,
            "stream": True,
            "options": {
                "temperature": self.temperature,
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        accumulated = []
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    if self._is_cancelled:
                        app_logger.info("Inference streaming cancelled by user.")
                        break

                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue

                    try:
                        chunk_json = json.loads(line_str)
                        token = chunk_json.get("response", "")
                        if token:
                            accumulated.append(token)
                            self.chunk_received.emit(token)

                        if chunk_json.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

            full_text = "".join(accumulated)
            self.finished.emit(full_text)

        except urllib.error.URLError as e:
            err_msg = f"Ollama connection error: {e}"
            app_logger.error(err_msg)
            self.error_occurred.emit(err_msg)
        except Exception as e:
            err_msg = f"Inference execution failed: {e}"
            app_logger.error(err_msg)
            self.error_occurred.emit(err_msg)


class OllamaService(QObject):
    """Local Ollama client enforcing single-model VRAM governance and contextual boundaries."""

    connection_checked = Signal(bool, str)     # is_connected, status_message
    models_listed = Signal(list)               # list of model name strings
    model_switched = Signal(str)               # active_model_name

    def __init__(self, host: str = "http://localhost:11434", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.host = host.rstrip("/")
        self.current_model: Optional[str] = None
        self._active_worker: Optional[OllamaInferenceWorker] = None

    def check_connection(self) -> Tuple[bool, str]:
        """Verify Ollama daemon is reachable on host."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    self.connection_checked.emit(True, f"Connected ({len(models)} models available)")
                    return True, "Ollama daemon connected."
        except Exception as e:
            msg = f"Ollama unavailable on {self.host} ({e})"
            self.connection_checked.emit(False, msg)
            return False, msg
        return False, "Unknown Ollama status"

    def list_models(self) -> List[str]:
        """Query installed models from Ollama."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    model_names = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    self.models_listed.emit(model_names)
                    if model_names and not self.current_model:
                        self.current_model = model_names[0]
                    return model_names
        except Exception as e:
            app_logger.debug(f"Could not list Ollama models: {e}")
        return []

    def switch_model(self, model_name: str) -> bool:
        """Switch resident model under the strict Single-Model VRAM policy.
        
        1. Cancels active generation if running.
        2. Unloads previous model from GPU VRAM via keep_alive: 0.
        3. Sets new active model.
        """
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.cancel()
            self._active_worker.wait(1000)

        # Unload current model from VRAM if exists
        if self.current_model and self.current_model != model_name:
            self._unload_model(self.current_model)

        self.current_model = model_name
        self.model_switched.emit(model_name)
        app_logger.info(f"Ollama switched active model to '{model_name}'")
        return True

    def _unload_model(self, model_name: str) -> None:
        """Unload specified model from GPU memory by sending keep_alive: 0."""
        try:
            payload = {"model": model_name, "keep_alive": 0}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                pass
            app_logger.info(f"Unloaded model '{model_name}' from VRAM.")
        except Exception as e:
            app_logger.debug(f"Model unload call: {e}")

    def build_project_context(
        self,
        active_tex_content: str = "",
        diagnostics_text: str = "",
        references_text: str = "",
        user_notes: str = "",
    ) -> str:
        """Construct bounded project context for AI requests."""
        parts = []
        if active_tex_content:
            # Truncate to reasonable length to avoid context explosion
            excerpt = active_tex_content[:3000]
            parts.append(f"--- ACTIVE MANUSCRIPT EXCERPT ---\n{excerpt}")
        if diagnostics_text:
            parts.append(f"--- RECENT COMPILER ERRORS ---\n{diagnostics_text}")
        if references_text:
            parts.append(f"--- PROJECT BIBTEX REFERENCES ---\n{references_text[:1500]}")
        if user_notes:
            parts.append(f"--- USER NOTES ---\n{user_notes[:1000]}")

        return "\n\n".join(parts)

    def create_generation_worker(
        self,
        prompt: str,
        persona: AIPersona = AIPersona.ACADEMIC_WRITER,
        context: str = "",
        temperature: float = 0.3,
    ) -> Optional[OllamaInferenceWorker]:
        """Create and configure background worker for streaming inference."""
        if not self.current_model:
            models = self.list_models()
            if models:
                self.current_model = models[0]
            else:
                self.current_model = "qwen2.5:14b"

        system_prompt = PERSONA_SYSTEM_PROMPTS.get(
            persona, PERSONA_SYSTEM_PROMPTS[AIPersona.ACADEMIC_WRITER]
        )

        full_prompt = prompt
        if context:
            full_prompt = f"CONTEXT:\n{context}\n\nUSER REQUEST:\n{prompt}"

        worker = OllamaInferenceWorker(
            base_url=self.host,
            model_name=self.current_model,
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        self._active_worker = worker
        return worker

    def cancel_active_generation(self) -> None:
        """Cancel any ongoing inference."""
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.cancel()
