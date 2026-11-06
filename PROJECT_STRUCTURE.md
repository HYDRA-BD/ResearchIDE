# PROJECT STRUCTURE SPECIFICATION
## ResearchIDE: Directory Layout and Module Architecture
**Document Version:** 1.0.0  
**Language:** Python 3.11+ / PySide6  

---

```text
D:/ResearchIDE/
├── docs/                             # Architectural Specifications and SRS
│   ├── SRS_v1.0.md                   # Master SRS (Preserved intact)
│   ├── ARCHITECTURE.md               # Master System Architecture
│   ├── DATABASE_DESIGN.md            # SQLite Schema & Migration Design
│   ├── TECHNICAL_DECISIONS.md        # Technology & Library Evaluation
│   ├── PROJECT_STRUCTURE.md          # Repository & Module Directory Layout
│   ├── DEPENDENCY_REGISTER.md        # Third-party Dependencies & Licenses
│   ├── SYSTEM_COMPONENT_DIAGRAM.md   # UML & Component Flow Diagrams
│   ├── DATA_FLOW_DIAGRAM.md          # Data Ingestion & Sync Pipelines
│   └── DOCUMENT_SYNCHRONIZATION_DESIGN.md # Detailed CST/AST Sync Engine
├── planning/                         # Roadmap & Phase Plans
│   ├── DEVELOPMENT_ROADMAP.md        # Master 8-Phase Roadmap
│   └── PHASE_0_IMPLEMENTATION_PLAN.md# Phase 0 Execution Plan
├── prompts/                          # Master Prompt Library (Authoritative)
│   ├── MASTER_INSTRUCTIONS.md        # Permanent Development Rules
│   ├── PHASE_00_ARCHITECTURE.md      # Phase 0 Instructions
│   ├── PHASE_01_FOUNDATION.md        # Phase 1 Instructions
│   ├── PHASE_02_LATEX_ENGINE.md      # Phase 2 Instructions
│   ├── PHASE_03_VISUAL_EDITOR.md     # Phase 3 Instructions
│   ├── PHASE_04_LOCAL_AI.md          # Phase 4 Instructions
│   ├── PHASE_05_RESEARCH_INTELLIGENCE.md # Phase 5 Instructions
│   ├── PHASE_06_PUBLICATION.md       # Phase 6 Instructions
│   └── PHASE_07_RELEASE.md           # Phase 7 Instructions
├── src/                              # Application Source Code
│   ├── __init__.py
│   ├── core/                         # Core Document Model & Synchronization
│   │   ├── __init__.py
│   │   ├── document.py               # Canonical Document Model (Blocks & Inlines)
│   │   ├── serializer.py             # Model-to-LaTeX Serializer
│   │   ├── parser.py                 # LaTeX-to-Model CST Parser
│   │   ├── sync_engine.py            # Bidirectional Synchronizer
│   │   └── source_mapper.py          # Line/Column & Byte-Range Coordinate Mapper
│   ├── ui/                           # PySide6 Desktop Interface Layer
│   │   ├── __init__.py
│   │   ├── main_window.py            # QMainWindow Container
│   │   ├── ribbon/                   # Office-Style Ribbon Bar & Category Tabs
│   │   ├── workspace/                # Docking Area, Splitters, and Document Tabs
│   │   ├── editors/                  # Visual Canvas & LaTeX Source Editors
│   │   ├── viewer/                   # PDF.js / QWebEngine PDF Viewer
│   │   ├── ai_panel/                 # Contextual AI Chat & Suggestion Diff Panel
│   │   ├── explorer/                 # Project File Tree & Outline View
│   │   └── dialogs/                  # Settings, New Project, and Template Dialogs
│   ├── services/                     # Background Services & Daemons
│   │   ├── __init__.py
│   │   ├── latex_service.py          # MiKTeX / TeX Live Compiler Runner & Log Parser
│   │   ├── ai_service.py             # Ollama Gateway Client & Streaming Handler
│   │   ├── literature_service.py     # PDF Text/Metadata Extractor & Ref Manager
│   │   ├── math_service.py           # SymPy CAS & Numerical Verification Engine
│   │   └── template_service.py       # Publication Formatter & Submission Checker
│   ├── storage/                      # SQLite Persistence & File Management
│   │   ├── __init__.py
│   │   ├── database.py               # SQLite Connection Pool & Migrations
│   │   ├── repositories/             # Typed Repositories (Projects, Docs, Refs)
│   │   └── file_manager.py           # Atomic File Operations & Snapshot Manager
│   └── utils/                        # Logging, Config, and Helper Utilities
│       ├── __init__.py
│       ├── config.py                 # Application Configuration Loader
│       ├── logger.py                 # Structured Rotating File Logger
│       └── synctex.py                # SyncTeX Coordinate Parser
├── tests/                            # Comprehensive Automated Test Suites
│   ├── __init__.py
│   ├── unit/                         # Unit Tests for Model, Serializer, Parser
│   │   ├── test_document_model.py
│   │   ├── test_serializer.py
│   │   └── test_parser.py
│   ├── integration/                  # Integration Tests (Compiler, DB, Sync)
│   │   ├── test_latex_compiler.py
│   │   ├── test_database.py
│   │   └── test_document_sync.py
│   └── fixtures/                     # Test LaTeX Documents & BibTeX Samples
│       ├── sample_simple.tex
│       ├── sample_complex_macros.tex
│       └── sample_references.bib
├── CHANGELOG.md                      # Release & Modification History
├── DEVELOPMENT_STATUS.md             # Live Development Status Tracker
├── REQUIREMENTS.md                   # Functional & Non-Functional Requirements
├── PROJECT_MASTER.md                 # Master Architecture Summary
├── TESTING_REPORT.md                 # Test Execution Results
└── README.md                         # Project Introduction & Setup Guide
```

