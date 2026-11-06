# PHASE 4 — LOCAL AI ENGINE AND ACADEMIC WRITING ASSISTANT

Implement the local AI subsystem using Ollama.

No external AI API or cloud AI inference is permitted.

## 1. Ollama integration

Implement:
- Ollama installation detection.
- Connection verification.
- Installed-model discovery.
- Model information.
- Model selection.
- Model loading.
- Model unloading.
- Model availability monitoring.
- Model error handling.

The application must work when Ollama is unavailable, without crashing.

## 2. Single-model execution

Only one AI model should be loaded at a time.

When switching models:
1. Stop active inference safely.
2. Unload the previous model.
3. Release resources.
4. Load the requested model.
5. Verify readiness.

Prevent conflicting model operations.

## 3. Model roles

Support configurable model assignments for:

- Academic writing.
- LaTeX assistance.
- Research analysis.
- Mathematical reasoning.
- Programming assistance.

Embeddings should use a separate, explicitly managed workflow if needed. Do not silently violate the single-model policy.

## 4. Command-based AI interface

Implement a natural-language command interface.

Example commands:

- Explain this LaTeX error.
- Rewrite this paragraph academically.
- Generate a methodology draft.
- Compare these research papers.
- Create a literature matrix.
- Explain this equation.
- Suggest relevant citations.
- Improve this abstract.

## 5. Context management

The AI shall access the active project only.

Allow contextual retrieval from:
- Current manuscript.
- Project PDFs.
- Project references.
- Project notes.
- Project figures and relevant metadata.

Respect project boundaries.

Do not automatically access unrelated projects.

## 6. Academic writing assistant

Support:
- Draft generation.
- Grammar improvement.
- Academic tone improvement.
- Paragraph restructuring.
- Abstract drafting.
- Introduction drafting.
- Literature review drafting.
- Methodology drafting.
- Discussion drafting.
- Conclusion drafting.

## 7. AI permission system

All generated material must appear in a suggestion or draft interface.

Provide:
- Preview.
- Compare with original.
- Accept.
- Reject.
- Copy.
- Edit before applying.

Never automatically alter the manuscript.

## 8. LaTeX intelligence

Implement:
- Syntax explanations.
- Error explanations.
- Code suggestions.
- Environment explanations.
- Package guidance.
- LaTeX snippet generation.

## 9. Resource monitoring

Monitor:
- GPU memory.
- System memory.
- CPU usage.
- Model loading status.
- Inference status.

Provide graceful CPU fallback where practical.

## 10. Testing

Test:
- Ollama unavailable.
- Model unavailable.
- Model loading failure.
- Model switching.
- Long-running inference.
- Cancellation.
- Memory exhaustion.
- AI suggestion approval.
- Project-context isolation.

## 11. Completion

The user must be able to use local AI for academic writing and LaTeX assistance without cloud inference.