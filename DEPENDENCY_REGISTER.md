# DEPENDENCY REGISTER
## ResearchIDE: Third-Party Dependencies and Licensing
**Document Version:** 1.0.0  
**Python Runtime:** Python 3.11.9 (Installed on System)  

---

## 1. Primary Desktop & GUI Dependencies

| Package | Version Targeted | License | Installation Status | Purpose |
|---|---|---|---|---|
| **PySide6** | $\ge$ 6.7.0 | LGPLv3 | *To be installed* | Core GUI framework: QMainWindow, QDockWidget, QPlainTextEdit, QWebEngineView. |
| **pydantic** | 2.14.2 | MIT | **Installed** | Strongly-typed data validation for documents, schemas, and IPC payloads. |

---

## 2. Document & Scientific Processing Dependencies

| Package | Version Targeted | License | Installation Status | Purpose |
|---|---|---|---|---|
| **sympy** | 1.14.0 | BSD-3-Clause | **Installed** | Symbolic algebra, CAS equation derivation verification. |
| **mpmath** | 1.3.0 | BSD-3-Clause | **Installed** | 50-digit high-precision numerical falsification of math identities. |
| **numpy** | 2.4.6 | BSD-3-Clause | **Installed** | Numerical matrix computation and vector transformations. |
| **scipy** | 1.17.1 | BSD-3-Clause | **Installed** | Scientific computing and optimization routines. |
| **matplotlib** | 3.11.1 | PSF / BSD | **Installed** | Data visualization and PGFPlots rendering daemon. |
| **pypdf** | 6.21.4 | BSD-3-Clause | **Installed** | PDF document parsing, page extraction, and metadata inspection. |
| **pylatexenc** | $\ge$ 2.10 | MIT | *To be installed* | Robust LaTeX string to unicode and macro tokenization. |
| **bibtexparser** | $\ge$ 2.0.0 | MIT | *To be installed* | High-performance BibTeX parsing and serialization. |

---

## 3. Local AI & Networking Dependencies

| Package | Version Targeted | License | Installation Status | Purpose |
|---|---|---|---|---|
| **httpx** | 0.28.1 | BSD-3-Clause | **Installed** | Asynchronous HTTP client for Ollama local streaming API (`127.0.0.1:11434`). |
| **chromadb** | 1.5.9 | Apache-2.0 | **Installed** | Local vector storage engine for semantic paper search. |
| **sentence-transformers** | 6.2.0 | Apache-2.0 | **Installed** | Local embedding models for semantic literature search. |
| **torch** | 2.15.0 | BSD-3-Clause | **Installed** | PyTorch runtime with CUDA acceleration on RTX 3060. |

---

## 4. Development & Testing Dependencies

| Package | Version Targeted | License | Installation Status | Purpose |
|---|---|---|---|---|
| **pytest** | $\ge$ 8.0.0 | MIT | *To be installed* | Automated test execution and assertions. |
| **unittest** | Standard Lib | Python Software License | **Built-in** | Standard test runner for zero-dependency test execution. |
| **sqlite3** | Standard Lib | Public Domain | **Built-in** | Embedded ACID relational database and FTS5 search. |

