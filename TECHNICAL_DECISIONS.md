# TECHNICAL DECISIONS RECORD
## ResearchIDE: Framework Choices, Library Evaluations & Trade-offs
**Document Version:** 1.0.0  
**Date:** 6 November 2026  

---

## 1. Core Framework & Language Decisions

### 1.1 Language: Python 3.11+
- **Rationale:** Python provides native interoperability with the scientific computing and AI ecosystem (SymPy, NumPy, PyPDF, Ollama clients) without cross-language binding friction.
- **Enforcement:** Strict type annotations (`from __future__ import annotations`, `typing`), Pydantic models for data contracts, and automated validation via `pytest` and `ruff`.

### 1.2 GUI Framework: PySide6 (Qt for Python 6.7+)
- **Rationale:** Official Qt framework for Python, LGPLv3 compliant for desktop applications, high-performance C++ backend under the hood, native Windows 10/11 styling, rock-solid thread synchronization (`QThread`, `QObject.moveToThread`), and advanced components (`QWebEngineView`, `QDockWidget`, `QPlainTextEdit`).
- **Alternative Rejected:** Tkinter (too primitive for commercial-grade IDEs), PyQt6 (GPL commercial license friction), Electron (excessive RAM consumption on 16GB host).

---

## 2. Library Selection Matrix & Technical Evaluations

| Subsystem | Selected Library | Alternatives Evaluated | Selection Rationale & Trade-off |
|---|---|---|---|
| **Visual Document Editor** | **QWebEngineView + TipTap/ProseMirror** | Native `QTextEdit`, `QTextDocument` | `QTextEdit` supports very limited HTML/CSS subsets and lacks modern collaborative node-based block models. TipTap/ProseMirror in `QWebEngineView` allows modern Word-like paginated editing while communicating with Python via `QWebChannel`. |
| **LaTeX Source Editor** | **Custom `QPlainTextEdit` with `QSyntaxHighlighter`** | `QScintilla`, Embedded Monaco Editor | A native PySide6 `QPlainTextEdit` with custom asynchronous regex syntax highlighter provides sub-millisecond typing latency and zero WebEngine overhead for code editing. |
| **PDF Preview** | **QWebEngineView + PDF.js** | `PySide6.QtPdf`, `poppler-qt5` | PDF.js delivers identical cross-platform rendering, smooth continuous high-DPI zoom, and rich DOM-level SyncTeX coordinate highlighting via JavaScript hooks. |
| **PDF Extraction** | **`pypdf` + `pdfplumber`** | `fitz` (PyMuPDF / AGPL) | PyMuPDF carries viral AGPL license risks. `pypdf` (BSD) combined with `pdfplumber` (MIT) allows non-restrictive licensing with robust layout extraction. |
| **LaTeX Parsing** | **`pylatexenc` + Custom CST AST** | `tree-sitter-latex`, `plasTeX` | `pylatexenc` is pure Python, lightweight, and excels at extracting macros, equations, and text environments without compilation dependencies on Windows. |
| **Bibliographic Parser** | **`bibtexparser` (v2+)** | `pybtex` | `bibtexparser` v2 offers superior performance, preserves comments and raw BibTeX strings, and handles malformed academic entries gracefully. |
| **Mathematical CAS** | **`sympy` + `mpmath`** | Z3, SageMath | SymPy is the gold standard Python symbolic mathematics engine; `mpmath` handles arbitrary-precision numerical falsification. |
| **Local AI Client** | **`httpx` (Async HTTP to Ollama)** | Official `ollama-python` | `httpx` allows full control over connection pools, timeouts, and SSE token streaming directly into Qt signals without third-party wrapper overhead. |
| **Database** | **`sqlite3` (Standard Library)** | SQLAlchemy, Peewee | Standard library `sqlite3` avoids ORM bloat, enables direct `FTS5` virtual table queries, and operates with zero external dependencies. |

---

## 3. License Compliance & Distribution Review

- **PySide6:** LGPLv3. ResearchIDE complies by dynamically linking Qt libraries and allowing user substitution of Qt binaries.
- **Python Dependencies (`pypdf`, `pylatexenc`, `sympy`, `httpx`, `bibtexparser`):** BSD, MIT, and Apache 2.0. Clean for commercial and open academic distribution.
- **No GPL/AGPL Contamination:** PyMuPDF, Ghostscript binaries, or AGPL libraries are strictly excluded from the core dependency tree.

