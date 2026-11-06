# CHANGELOG
## ResearchIDE: Version and Milestone History

All notable changes to the ResearchIDE project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
