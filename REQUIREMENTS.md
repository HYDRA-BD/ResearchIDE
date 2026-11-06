# REQUIREMENTS SPECIFICATION
## ResearchIDE: Master Functional and Non-Functional Requirements
**Document Version:** 1.0.0  
**Status:** Baseline Specification  

---

## 1. Functional Requirements (FR)

### FR-01: Desktop Workspace & Presentation
- **FR-01.1:** Professional Windows desktop interface built with PySide6 featuring an Office-style Ribbon toolbar (Home, Insert, Layout, References, Review, View, AI tabs).
- **FR-01.2:** Dockable, adjustable multi-panel layout supporting split views (Visual Editor | LaTeX Source | PDF Preview).
- **FR-01.3:** Navigation sidebar including Project Explorer, Document Outline, and Literature Library.
- **FR-01.4:** High-DPI support, Light and Dark academic color themes.

### FR-02: Canonical Document & Visual Editing
- **FR-02.1:** Word-style visual document editing for standard academic structures: headings (1–4), paragraphs, lists, standard equations, figures, tables, and citations.
- **FR-02.2:** Strict dual-representation architecture: maintaining a canonical semantic model while synchronizing with the raw LaTeX source.
- **FR-02.3:** Lossless preservation of unsupported constructs (custom macros, preambles, TikZ environments, complex packages) via Opaque Verbatim Blocks.
- **FR-02.4:** Two-way position mapping: clicking a visual element navigates to its corresponding range in the LaTeX source and vice-versa.

### FR-03: LaTeX Source Editing & Compilation Engine
- **FR-03.1:** Full-featured LaTeX code editor with syntax highlighting, line numbers, code folding, auto-indentation, and bracket matching.
- **FR-03.2:** Automatic detection of installed TeX distributions (MiKTeX and TeX Live).
- **FR-03.3:** Multi-engine support: PDFLaTeX, XeLaTeX, LuaLaTeX, with BibTeX and Biber bibliography generation.
- **FR-03.4:** Asynchronous background compilation with configurable debounce and process cancellation.
- **FR-03.5:** Structured compilation error/warning parser highlighting file, line, and message.
- **FR-03.6:** High-DPI PDF preview with bidirectional SyncTeX navigation (Source $\leftrightarrow$ PDF).

### FR-04: Local AI Research Assistant (Ollama)
- **FR-04.1:** Direct local HTTP integration with Ollama (`localhost:11434`) with zero cloud dependencies.
- **FR-04.2:** Single-model resident execution policy; safe unloading/reloading when switching models.
- **FR-04.3:** Command-based natural language interface (e.g., explain errors, rewrite paragraphs academically, summarize sections).
- **FR-04.4:** Strict project-level context isolation; preventing cross-project memory contamination.
- **FR-04.5:** Mandatory AI permission gate: AI modifications are presented as interactive diffs/suggestions requiring explicit user approval before mutating files.

### FR-05: Research Intelligence & Literature Management
- **FR-05.1:** Local research PDF repository supporting drag-and-drop ingestion into projects.
- **FR-05.2:** PDF text, metadata, and reference extraction.
- **FR-05.3:** Grounded claim traceability: linking claims to original PDF, page number, and text passages.
- **FR-05.4:** Complete reference manager with BibTeX and RIS import/export, and in-text citation auto-completion.
- **FR-05.5:** Anti-hallucination policy: AI is strictly prohibited from fabricating citations or references.

### FR-06: Mathematical & Scientific Verification
- **FR-06.1:** Integration with SymPy for symbolic algebra simplification and derivation validation.
- **FR-06.2:** Two-tier verification: symbolic CAS equivalence checking with fallback to 50-digit high-precision numerical falsification via `mpmath`.
- **FR-06.3:** Visual verification badges in the document editor (Verified, Conjectured, Disproved).

### FR-07: Academic Templates & Publication Preparation
- **FR-07.1:** Support for major publisher templates (IEEE, Springer, Elsevier, ACM, Nature).
- **FR-07.2:** Automated submission compliance checker (word counts, margins, required sections, reference formats).
- **FR-07.3:** Clean export of submission bundles (final compiled PDF, packaged LaTeX source, figures, and checklist).

### FR-08: Revision History & Disaster Recovery
- **FR-08.1:** Configurable autosave and automatic pre-mutation snapshots before any AI action.
- **FR-08.2:** Local revision timeline allowing comparison and one-click rollback.
- **FR-08.3:** Crash recovery restoring unsaved document states after unexpected termination.

---

## 2. Non-Functional Requirements (NFR)

- **NFR-01 (Offline Guarantee):** 100% of core writing, compiling, AI assistance, and literature search features must function with the network interface disconnected.
- **NFR-02 (RAM Budget):** Base application idling memory must not exceed 400 MB RAM; active compilation + UI must not exceed 1.2 GB RAM.
- **NFR-03 (VRAM Budget):** GPU VRAM allocation must strictly remain below 10.0 GB, leaving at least 2.0 GB headroom on the 12 GB RTX 3060.
- **NFR-04 (Compilation Speed):** Incremental LaTeX compilation turnaround must be under 2.0 seconds for standard papers.
- **NFR-05 (Data Integrity):** Zero silent loss of user data or LaTeX source code under any circumstance.

