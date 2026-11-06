# PHASE 0 — SYSTEM ARCHITECTURE AND TECHNICAL FOUNDATION

Read the Master Development Instructions.

Your task is to design the complete technical architecture of the Local AI-Powered LaTeX Research Environment.

Do not attempt to implement the entire application in this phase.

## 1. Repository inspection

Inspect the current workspace.

If it is empty, establish a clean project repository.

If existing files exist, inspect them before modifying anything.

## 2. Architecture design

Design a modular architecture containing:

A. Desktop application layer
- PySide6.
- Main window.
- Navigation.
- Workspace management.
- Dialogs and notifications.

B. Document engine
- Canonical document representation.
- Document schema.
- Paragraphs and headings.
- Tables and figures.
- Equations.
- Citations.
- Metadata.
- Document serialization.

C. LaTeX engine
- LaTeX parser and serializer.
- Source editor integration.
- Compilation service.
- Build profiles.
- PDF generation.
- SyncTeX support.

D. AI subsystem
- Ollama integration.
- Model discovery.
- Model loading and unloading.
- Prompt management.
- Task-specific AI interfaces.
- Context management.

E. Research subsystem
- PDF extraction.
- Literature analysis.
- Reference management.
- Dataset management.

F. Storage subsystem
- SQLite.
- Project storage.
- Document storage.
- Revision history.
- Autosave and backup.

G. Publication subsystem
- Templates.
- Journal and conference profiles.
- Formatting verification.
- Submission preparation.

## 3. Critical architectural requirement: Document synchronization

Design a canonical semantic document model.

The visual editor, LaTeX source editor and PDF preview must represent the same underlying document.

Define how the system will handle:

- Visual-to-LaTeX conversion.
- LaTeX-to-visual conversion.
- Source position mapping.
- Selection synchronization.
- Unsupported LaTeX constructs.
- Custom commands.
- Package-specific environments.
- Compilation errors.
- Document identity and formatting preservation.

Do not assume that arbitrary LaTeX can be perfectly converted into editable visual content.

Use an explicit unsupported-content fallback mechanism.

Design source mappings so that clicking a visual block can navigate to its corresponding source range, and vice versa.

## 4. Technical stack evaluation

Evaluate appropriate libraries for:

- PySide6 interface.
- Rich text editing.
- Code editing.
- PDF viewing.
- PDF text extraction.
- OCR.
- LaTeX parsing.
- LaTeX compilation.
- Bibliographic metadata.
- Local AI integration.
- Data previews.
- Charts and diagrams.
- Database access.

Prefer mature, maintained libraries.

Document licensing considerations.

Do not select dependencies merely because they are popular.

## 5. Database design

Design SQLite schemas for:

- Projects.
- Documents.
- Document blocks.
- References.
- Citations.
- Templates.
- Figures.
- Tables.
- Datasets.
- AI configurations.
- Revision history.
- Application settings.
- Backup metadata.

Define relationships, indexes and migration strategy.

## 6. Security and data integrity

Design:
- Atomic document saving.
- Autosave.
- Backup.
- Recovery.
- Database integrity checks.
- File-path validation.
- Safe handling of external LaTeX commands.
- Protection against accidental project deletion.

## 7. Hardware-aware design

Optimize the architecture for:

- 16 GB system RAM.
- 12 GB GPU VRAM.
- Single-model AI loading.
- Local inference.
- CPU fallback.
- Background task management.

## 8. Development deliverables

Create:

1. ARCHITECTURE.md
2. DATABASE_DESIGN.md
3. TECHNICAL_DECISIONS.md
4. DEVELOPMENT_ROADMAP.md
5. PROJECT_STRUCTURE.md
6. DEPENDENCY_REGISTER.md
7. SYSTEM_COMPONENT_DIAGRAM.md
8. DATA_FLOW_DIAGRAM.md
9. DOCUMENT_SYNCHRONIZATION_DESIGN.md

Create a practical project directory structure.

## 9. Technical prototype

Build a small isolated prototype to validate the most important architectural risk:

- Create a structured document.
- Serialize supported elements into LaTeX.
- Parse supported LaTeX back into the document representation.
- Preserve unsupported source constructs safely.
- Demonstrate source-position mapping.

Do not build the complete visual editor yet.

## 10. Completion report

Explain:

- Final proposed architecture.
- Important technology choices.
- Known limitations.
- Major risks.
- Dependency requirements.
- Prototype results.
- Recommended implementation sequence.

Wait for approval before proceeding to Phase 1.