# ResearchIDE
> **Offline AI-Powered Academic Research & LaTeX Environment**

ResearchIDE is a local-first Windows desktop application combining a Microsoft Word-inspired visual document editor, native LaTeX source editing, local compiler integration (MiKTeX/TeX Live), high-DPI PDF preview with bidirectional SyncTeX navigation, local AI assistance via Ollama, and evidence-grounded literature management.

---

## Key Features

- **Local-First & Fully Offline:** Zero cloud dependencies. All writing, compilation, local LLM inference, and literature search operate 100% on your workstation.
- **Academic Source Preservation:** Concrete Syntax Tree (CST) architecture ensures arbitrary LaTeX macros, preamble configurations, comments, and TikZ packages are preserved without silent corruption.
- **Office-Style Ribbon Interface:** Clean, modern PySide6 desktop interface with Dark and Light academic themes.
- **Hardware-Aware Local AI:** Integrates with local Ollama daemon targeting the NVIDIA RTX 3060 12GB VRAM under a strict single-model resident policy.
- **Mathematical & Symbolic Verification:** Built-in SymPy symbolic algebra verification and 50-digit numerical falsification (`mpmath`).
- **Traceable Literature Intelligence:** Grounded claims linked to local research PDFs by page number and coordinate bounding boxes.

---

## Target Hardware & Technology Stack

- **Operating System:** Windows 10/11 (64-bit)
- **Host Spec Target:** AMD Ryzen 5 5600G | NVIDIA RTX 3060 12GB | 16 GB RAM | 1 TB NVMe
- **Language:** Python 3.11+
- **GUI Framework:** PySide6 (Qt 6.12+)
- **Storage:** SQLite 3 in WAL mode with FTS5 Full-Text Search
- **LaTeX Engine:** MiKTeX / TeX Live (`pdflatex`, `xelatex`, `lualatex`, `bibtex`, `synctex`)
- **AI Inference:** Ollama Local Runtime (`localhost:11434`)

---

## Repository Structure

```text
ResearchIDE/
├── docs/                 # Specifications & Architectural Evaluations
│   ├── SRS_v1.0.md       # Master Software Requirements Specification
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── FEASIBILITY_AND_RISK_ANALYSIS.md
│   └── ARCHITECTURAL_DECISIONS.md
├── src/                  # Application Source Code
│   ├── core/             # Canonical Document Model & Sync Engine
│   ├── ui/               # PySide6 Desktop Interface (Ribbon, Workspace, Dashboard)
│   ├── storage/          # SQLite DB Manager & Repositories
│   └── utils/            # Logging and Configuration
├── tests/                # Automated Test Suites
├── ARCHITECTURE.md       # Master System Architecture
├── DATABASE_DESIGN.md    # Relational Database Schema
├── DEVELOPMENT_ROADMAP.md# 8-Phase Development Roadmap
├── DEVELOPMENT_STATUS.md # Current Phase Status Tracker
└── TESTING_REPORT.md     # Test Execution Report
```

---

## Quick Start

### 1. Requirements
- Python 3.11+
- MiKTeX or TeX Live installed on system
- Local Ollama daemon (optional for AI features)

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/HYDRA-BD/ResearchIDE.git
cd ResearchIDE

# Install dependencies
pip install PySide6 pydantic sympy mpmath numpy scipy matplotlib pypdf httpx
```

### 3. Run Automated Tests
```bash
python -m unittest discover -s tests -v
```

### 4. Launch Desktop Application
```bash
python src/main.py
```

---

## Development Status

- [x] **Phase 0: System Architecture & Technical Prototype** (Complete)
- [x] **Phase 1: Application Foundation & PySide6 Desktop Shell** (Complete)
- [x] **Phase 2: LaTeX Source Editor, Compiler Daemon & PDF Preview** (Complete)
- [x] **Phase 3: Visual Document Editor & Bidirectional Synchronization** (Complete)
- [x] **Phase 4: Local AI Engine & Academic Writing Assistant** (Complete)
- [x] **Phase 5: Research Intelligence & Literature Management** (Complete)
- [x] **Phase 6: Academic Templates & Publication Preparation** (Complete)
- [x] **Phase 7: Reliability, Performance & Windows Installer** (Complete — v1.0.0 Release Candidate)

See [`DEVELOPMENT_STATUS.md`](DEVELOPMENT_STATUS.md) for live progress.

