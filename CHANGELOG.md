# CHANGELOG
## ResearchIDE: Version and Milestone History

All notable changes to the ResearchIDE project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Phase 7 / v1.0.0 Release Candidate: Reliability, Performance & Windows Release] - 2026-11-06

### Added
- **Crash Recovery & Unclean Exit Protection:**
  - Implemented `DocumentRecoveryService` (`src/services/recovery_service.py`) generating timestamped pre-mutation snapshots in `.researchide/snapshots/` and tracking unclean exits.
  - Implemented automatic recovery detection and safe one-click restoration of unpersisted work.
- **Document Revision Checkpoint & Rollback System:**
  - Implemented `RevisionManager` (`src/services/revision_service.py`) maintaining content-hashed document revision checkpoints inside `.researchide/revisions/`.
  - Implemented unified line-by-line diff calculation between arbitrary revision timestamps and the active manuscript.
  - Implemented non-destructive revision rollback with automatic pre-rollback safety snapshots.
  - Implemented interactive `RevisionDialog` (`src/ui/dialogs/revision_dialog.py`) with side-by-side revision selection, diff preview, and one-click rollback.
- **System Health & Hardware Diagnostics:**
  - Implemented `SystemDiagnosticsService` (`src/services/diagnostics_service.py`) executing full-stack environment verification:
    - Host CPU, Win32 RAM, and RTX 3060 VRAM metrics.
    - MiKTeX / TeX Live compiler binary validation (`pdflatex`, `xelatex`, `lualatex`, `bibtex`, `synctex`).
    - Local Ollama runtime connectivity and model registry check.
    - SQLite database integrity check via `PRAGMA integrity_check`.
- **Windows Packaging & Installer Setup:**
  - Authored PyInstaller build specification (`packaging/ResearchIDE.spec`) configured for PySide6, QtWebEngine, QtPdf, and SymPy.
  - Authored Inno Setup 6 installer wizard script (`packaging/installer.iss`) with Windows desktop shortcuts, file associations (`.tex`, `.bib`), and clean uninstallation.
- **Academic Release Documentation:**
  - Created `docs/USER_MANUAL.md`: End-to-end user manual covering installation, project setup, visual editing, AI writing assistance, and compilation.
  - Created `docs/TROUBLESHOOTING.md`: Diagnostic guide covering MiKTeX PATH issues, Ollama offline errors, and VRAM management.
  - Created `docs/OFFLINE_OPERATION_GUIDE.md`: Zero-internet airgap verification guide detailing local model caches and offline library management.
- **Automated Test Suite:**
  - Added 5 unit tests in `tests/test_phase7_release_and_reliability.py` verifying recovery snapshots, revision checkpointing, diff/restore lifecycles, diagnostics reporting, and 100% offline workflow execution (50/50 tests passing total).

---

## [Phase 6: Academic Templates and Publication Preparation] - 2026-11-06

### Added
- **Publisher Template Catalog:**
  - Implemented `PublicationTemplate` registry (`src/services/template_service.py`) supporting IEEE Transactions (`IEEEtran`), ACM SIGCONF (`acmart`), Springer Nature (`sn-jnl`), Elsevier (`elsarticle`), and General Preprint (`article`).
  - Implemented `TemplateMigrator` for non-destructive manuscript profile switching that preserves all manuscript text, equations, citations, and figures.
- **Publication Compliance Auditor:**
  - Implemented `PublicationComplianceAuditor` (`src/services/compliance_auditor.py`) checking abstract word limits, publisher-required sections, figure/table captions, and in-text citation consistency.
  - Implemented structured `ComplianceReport` separating automated checks from manual editorial advisories.
- **Submission Package Bundler:**
  - Implemented `SubmissionBundler` (`src/services/submission_bundler.py`) packaging LaTeX sources, compiled PDFs, BibTeX databases, assets, and auto-generated `SUBMISSION_CHECKLIST.md` into clean ZIP archives.
- **Submission Dialog & Ribbon Integration:**
  - Implemented `SubmissionDialog` (`src/ui/dialogs/submission_dialog.py`) providing an interactive publication prep workflow directly from the Ribbon toolbar.
- **Automated Test Suite:**
  - Added 5 unit tests in `tests/test_phase6_publication.py` validating template profiles, migration safety, compliance audits, violation detection, and ZIP packaging (45/45 tests passing total).

---

## [Phase 5: Research Intelligence and Literature Management] - 2026-11-06

### Added
- **Research PDF Ingestion & Extraction Engine:**
  - Implemented `PDFExtractorService` (`src/services/literature_service.py`) using `pypdf` for page-by-page text extraction, DOI discovery, publication year heuristics, and reference scanning.
  - Implemented strict source grounding via `EvidenceSnippet` linking extracted claims to exact file names and 1-indexed page numbers.
- **Reference & Citation Manager:**
  - Implemented `ReferenceManager` (`src/services/reference_service.py`) supporting BibTeX, RIS, and CSL JSON import and export.
  - Implemented multi-style in-text citation formatting (LaTeX `\cite`, IEEE `[#]`, APA `(Author, Year)`).
- **Comparative Literature Matrix:**
  - Implemented `LiteratureMatrixGenerator` (`src/services/literature_matrix.py`) compiling structured dimensions (Research Objective, Methodology, Dataset, Key Results, Limitations) into exportable Markdown and LaTeX tables.
- **Dataset Inspector:**
  - Implemented `DatasetService` (`src/services/dataset_service.py`) for CSV/TSV parsing, column type inference (integer, float, string), null count calculation, and data previews.
- **Literature & Reference UI:**
  - Implemented dockable `LiteraturePanel` (`src/ui/literature_panel.py`) featuring *Library*, *References*, *Matrix*, and *Data* tabs with instant citation insertion into active editor tabs.
- **Automated Test Suite:**
  - Added 6 automated tests in `tests/test_phase5_research_intelligence.py` covering BibTeX/RIS/CSL round-trips, grounded evidence search, literature matrix synthesis, and dataset profiling (40/40 tests passing total).

---

## [Phase 4: Local AI Engine and Academic Writing Assistant] - 2026-11-06

### Added
- **Local Ollama Inference Client:**
  - Implemented `OllamaService` (`src/services/ai_service.py`) targeting local endpoint (`localhost:11434`) without external internet/cloud calls.
  - Implemented asynchronous non-blocking token streaming thread (`OllamaInferenceWorker`).
  - Implemented strict Single-Model Resident Policy unloading previous models (`keep_alive: 0`) before loading a new model to enforce the 9.5 GB VRAM ceiling.
  - Implemented five academic system prompt personas (`AIPersona`): Academic Writer, LaTeX Engineer, Research Analyst, Mathematical Reasoner, and Computational Assistant.
  - Implemented project-bounded context packaging extracting active `.tex` excerpts, compiler diagnostic errors, and BibTeX entries.
- **AI Permission System & Assistant Panel:**
  - Implemented dockable `AIAssistantPanel` (`src/ui/ai_panel/ai_assistant_panel.py`) featuring live connection indicator, model selector, persona selector, and streaming output view.
  - Implemented Quick Academic Command buttons (*Explain Error*, *Rewrite Formal*, *Draft Method*, *Explain Math*, *Suggest Cites*).
  - Implemented mandatory user approval controls (*Accept & Apply*, *Discard*, *Copy*) ensuring AI drafts never automatically alter manuscripts without explicit confirmation.
- **Hardware Resource Monitor:**
  - Implemented `SystemResourceMonitor` (`src/services/resource_monitor.py`) querying system RAM via Win32 `GlobalMemoryStatusEx` and NVIDIA GPU VRAM via `nvidia-smi` without heavy third-party dependencies.
- **Automated Test Suite:**
  - Added 6 automated tests in `tests/test_phase4_local_ai.py` validating hardware metric queries, persona prompts, model switching, context packaging, offline fallback, and user approval workflow (34/34 tests passing total).

---

## [Phase 3: Visual Document Editor and Bidirectional Synchronization] - 2026-11-06

### Added
- **Visual Academic Canvas:**
  - Implemented `VisualEditorWidget` (`src/ui/editors/visual_editor.py`) embedding `QWebEngineView` and `QWebChannel`.
  - Rendered academic manuscript layout with editable headings (H1-H3), paragraphs, equation blocks, tabular environments, and figures.
  - Implemented protected opaque code pills (🔒 OPAQUE LATEX) for TikZ graphics, custom macros, and raw preamble directives, preventing visual WYSIWYG corruption.
- **Bidirectional SyncBridge:**
  - Implemented `SyncBridge` (`src/core/sync_bridge.py`) converting visual mutations into surgical byte-range replacements via `DocumentSyncEngine`.
  - Implemented re-entrance guard locks preventing recursive update feedback loops between visual and code editors.
  - Implemented incremental parsing of source edits to refresh visual DOM blocks dynamically.
  - Implemented bidirectional cursor/selection coordinate mapping between visual DOM elements (`data-block-id`) and LaTeX source line ranges.
- **Multi-Mode Editor Workspace:**
  - Enhanced `DocumentTab` (`src/ui/workspace.py`) with mode switcher toolbar supporting *Visual*, *LaTeX Source*, and *Side-by-Side Split* editor layouts.
  - Synchronized text modifications and cursor movements between `VisualEditorWidget` and `CodeEditor`.
- **Ribbon Insert Integration:**
  - Connected *Insert* tab buttons in `RibbonBar` (Section, Equation, Figure, Table, Citation) to insert corresponding LaTeX structures into active documents.
- **Automated Test Suite:**
  - Added 6 automated tests in `tests/test_phase3_visual_editor.py` validating dictionary serialization, surgical visual patching, opaque block protection, academic block insertion, coordinate mapping, and tab mode switching (28/28 tests passing total).

---

## [Phase 2: LaTeX Engine, Compiler and PDF Preview] - 2026-11-06

### Added
- **LaTeX Source Code Editor:**
  - Implemented `CodeEditor` (`src/ui/editors/code_editor.py`) featuring gutter line numbers (`LineNumberArea`), current line highlighting, auto-indentation on Return, bracket matching, and compilation error indicators.
  - Implemented `LaTeXHighlighter` (`src/ui/editors/latex_highlighter.py`) providing theme-aware syntax highlighting for LaTeX commands, environments, inline/display math, comments, and BibTeX structures.
  - Implemented inline floating search & replace bar (`SearchReplaceBar`) with case matching and replace-all capabilities.
  - Implemented `QCompleter` autocompletion for common LaTeX environments and commands.
- **LaTeX Compilation Daemon & Compiler Management:**
  - Implemented `LaTeXCompilerService` (`src/services/latex_service.py`) auto-discovering local MiKTeX and TeX Live distributions (`pdflatex`, `xelatex`, `lualatex`, `bibtex`, `biber`, `synctex`).
  - Implemented `LaTeXLogParser` converting compilation logs into structured `LaTeXDiagnostic` records with exact line numbers and source snippets.
  - Implemented asynchronous non-blocking compilation worker thread (`CompileWorker`).
  - Implemented previous PDF preservation on failed builds.
- **High-DPI PDF Preview Canvas:**
  - Implemented `PDFViewerWidget` (`src/ui/viewer/pdf_viewer.py`) using `PySide6.QtPdf` and `PySide6.QtPdfWidgets` (`QPdfDocument`, `QPdfView`).
  - Implemented continuous multi-page scrolling mode, page navigation controls, zoom controls (Fit to Width, Fit in View, 100%, 150%, 200%), and text search.
- **Bidirectional SyncTeX Navigation:**
  - Implemented `SyncTeXService` (`src/services/synctex_service.py`) supporting forward synchronization (Source -> PDF) and inverse synchronization (PDF click -> Source line).
  - Wired interactive double-click and Ctrl+click in PDF viewer to jump code editor to matching LaTeX line.
- **Diagnostics Panel & Split View:**
  - Implemented dockable `DiagnosticsPanel` (`src/ui/diagnostics_panel.py`) with clickable issue navigation and raw build logs.
  - Implemented split view in `DocumentWorkspace` (LaTeX editor on left, PDF preview on right) with toggleable layout modes (*Split*, *Editor Only*, *PDF Only*).
- **Automated Test Suite:**
  - Added 7 comprehensive unit tests in `tests/test_phase2_latex_engine.py` (22/22 tests passing total).

---

## [Phase 1: Application Foundation] - 2026-11-06

### Added
- **PySide6 Desktop Application Core:**
  - Implemented `MainWindow` with Office-style Ribbon toolbar (`RibbonBar`), dockable Project Explorer (`ProjectExplorer`), multi-document tabbed workspace (`DocumentWorkspace`), and status bar.
  - Implemented consistent academic design system with Dark and Light QSS themes (`theme.py`).
  - Implemented `HomeDashboard` for initial workspace landing and recent project navigation.
  - Implemented interactive dialogs: `NewProjectDialog`, `SettingsDialog`, `NewDocumentDialog`.
  - Implemented temporary notification toast system (`NotificationToast`).
- **Storage Subsystem:**
  - Implemented thread-safe `DatabaseManager` with WAL mode, foreign keys, transaction context management, and PRAGMA integrity verification.
  - Implemented `SettingsRepository` for application preferences and recent projects tracking.
  - Implemented `ProjectRepository` for project metadata stored in `.researchide/project.db`.
  - Implemented `DocumentRepository` for document tracking and content hashes.
  - Implemented `FileManager` with atomic file writes (`atomic_write`) and path traversal security jailing (`validate_path_within_project`).
- **Project Domain Layer:**
  - Implemented `Project` and `ProjectManager` handling project creation, scaffolding, opening, renaming, closing, and deletion.
- **Automated Test Suite:**
  - Implemented and verified 9 unit and integration tests in `tests/test_phase1_foundation.py` with 100% pass rate.

---

## [Phase 0: Architecture & Foundation] - 2026-11-06

### Added
- Master System Architecture specification (`ARCHITECTURE.md`).
- SQLite Database Schema and Migration design (`DATABASE_DESIGN.md`).
- Technical Decision Records and library evaluation (`TECHNICAL_DECISIONS.md`).
- Master 8-Phase Development Roadmap (`DEVELOPMENT_ROADMAP.md`).
- Repository and Module Structure specification (`PROJECT_STRUCTURE.md`).
- Dependency Register and license compliance review (`DEPENDENCY_REGISTER.md`).
- System Component Diagrams (`SYSTEM_COMPONENT_DIAGRAM.md`).
- Data Flow Diagrams (`DATA_FLOW_DIAGRAM.md`).
- Document Synchronization and CST design (`DOCUMENT_SYNCHRONIZATION_DESIGN.md`).
- Live Development Status Tracker (`DEVELOPMENT_STATUS.md`).
- Master Project Specification (`PROJECT_MASTER.md`) and Requirements (`REQUIREMENTS.md`).
- Technical Prototype for Canonical Document Model, Serialization, and CST Parsing (`src/core/`).
- Automated Test Suite with 6 tests passing (`tests/test_document_sync_prototype.py`).
