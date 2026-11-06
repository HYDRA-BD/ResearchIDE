"""Automated Unit Tests for Phase 4: Local AI Engine & Writing Assistant."""
import unittest
import sys
from PySide6.QtWidgets import QApplication

from src.services.resource_monitor import SystemResourceMonitor, ResourceMetrics
from src.services.ai_service import OllamaService, AIPersona, PERSONA_SYSTEM_PROMPTS
from src.ui.ai_panel.ai_assistant_panel import AIAssistantPanel


# Ensure single QApplication instance across test suites
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestPhase4LocalAI(unittest.TestCase):
    """Test suite validating local AI governance, resource monitoring, and permission flows."""

    def setUp(self) -> None:
        self.ollama = OllamaService(host="http://localhost:11434")
        self.monitor = SystemResourceMonitor()

    def test_resource_monitor_query(self) -> None:
        """Verify Windows system memory queries return valid positive numbers."""
        metrics = self.monitor.get_metrics()
        self.assertIsInstance(metrics, ResourceMetrics)
        self.assertGreater(metrics.total_ram_gb, 0)
        self.assertGreaterEqual(metrics.available_ram_gb, 0)
        self.assertGreaterEqual(metrics.ram_load_percent, 0)
        self.assertLessEqual(metrics.ram_load_percent, 100)
        # Headroom safe flag logic
        self.assertTrue(metrics.is_gpu_headroom_safe)

    def test_persona_system_prompts_coverage(self) -> None:
        """Verify each academic persona has an authoritative and distinct system prompt."""
        for persona in AIPersona:
            self.assertIn(persona, PERSONA_SYSTEM_PROMPTS)
            prompt = PERSONA_SYSTEM_PROMPTS[persona]
            self.assertGreater(len(prompt), 30)

        # Check persona specifics
        self.assertIn("LaTeX", PERSONA_SYSTEM_PROMPTS[AIPersona.LATEX_ENGINEER])
        self.assertIn("scholarly", PERSONA_SYSTEM_PROMPTS[AIPersona.ACADEMIC_WRITER])
        self.assertIn("mathematical", PERSONA_SYSTEM_PROMPTS[AIPersona.MATH_REASONER].lower())

    def test_ollama_single_model_policy(self) -> None:
        """Verify single resident model policy switches models safely."""
        self.ollama.current_model = "qwen2.5:14b"
        switched_models = []
        self.ollama.model_switched.connect(switched_models.append)

        # Switch to llama3.1:8b
        res = self.ollama.switch_model("llama3.1:8b")
        self.assertTrue(res)
        self.assertEqual(self.ollama.current_model, "llama3.1:8b")
        self.assertEqual(switched_models, ["llama3.1:8b"])

    def test_project_context_packaging(self) -> None:
        """Verify project context packager bounds context and combines manuscript and error text."""
        context = self.ollama.build_project_context(
            active_tex_content=r"\section{Cosmology} We study the universe.",
            diagnostics_text="! Undefined control sequence on line 42",
            references_text="@article{einstein1915, title={Relativity}}",
            user_notes="Verify tensor equation index placement",
        )

        self.assertIn("--- ACTIVE MANUSCRIPT EXCERPT ---", context)
        self.assertIn(r"\section{Cosmology}", context)
        self.assertIn("--- RECENT COMPILER ERRORS ---", context)
        self.assertIn("! Undefined control sequence", context)
        self.assertIn("--- PROJECT BIBTEX REFERENCES ---", context)
        self.assertIn("@article{einstein1915", context)
        self.assertIn("--- USER NOTES ---", context)

    def test_ollama_offline_graceful_handling(self) -> None:
        """Verify that when Ollama is unreachable on host, no exception is raised and status is reported cleanly."""
        # Use an unreachable port
        offline_service = OllamaService(host="http://localhost:59999")
        is_connected, msg = offline_service.check_connection()
        self.assertFalse(is_connected)
        self.assertIn("Ollama unavailable", msg)

        models = offline_service.list_models()
        self.assertEqual(models, [])

    def test_ai_assistant_panel_permission_workflow(self) -> None:
        """Verify AI permission system: user must explicitly accept a suggestion before it is emitted."""
        panel = AIAssistantPanel(ollama_service=self.ollama)

        # Acceptance signal listener
        accepted_payloads = []
        panel.suggestion_accepted.connect(accepted_payloads.append)

        # Initially, action buttons are disabled
        self.assertFalse(panel.btn_accept.isEnabled())
        self.assertFalse(panel.btn_reject.isEnabled())
        self.assertFalse(panel.btn_copy.isEnabled())

        # Simulate completion of draft generation
        draft = r"\section{Methodology}\nWe employ high-precision numerical tensor calculations."
        panel._on_finished(draft)
        panel.response_edit.setPlainText(draft)

        # Action buttons should now be enabled
        self.assertTrue(panel.btn_accept.isEnabled())
        self.assertTrue(panel.btn_reject.isEnabled())
        self.assertTrue(panel.btn_copy.isEnabled())

        # Click accept
        panel._on_accept_suggestion()
        self.assertEqual(len(accepted_payloads), 1)
        self.assertEqual(accepted_payloads[0], draft)

        # After accepting, buttons should be reset
        self.assertFalse(panel.btn_accept.isEnabled())


if __name__ == "__main__":
    unittest.main()
