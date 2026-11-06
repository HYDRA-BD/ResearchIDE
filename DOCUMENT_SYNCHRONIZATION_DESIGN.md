# DOCUMENT SYNCHRONIZATION DESIGN
## ResearchIDE: Concrete Syntax Tree, Semantic Model, and Source Preservation
**Document Version:** 1.0.0  

---

## 1. The LaTeX Bidirectional Problem & Solution

### 1.1 The Theoretical Constraint
LaTeX is a Turing-complete macro language. A pure WYSIWYG editor attempting to convert arbitrary LaTeX into an abstract document model loses comments, macro definitions, whitespace structure, and unsupported environment parameters.

### 1.2 The CST Opaque Block Architecture
ResearchIDE solves this using a **lossless Concrete Syntax Tree (CST) with Opaque Verbatim Anchors**:

```text
Full LaTeX Source (.tex)
  ├── Semantic Node (Supported: \section{Introduction})       --> TipTap Heading1
  ├── Semantic Node (Supported: Standard Paragraph)          --> TipTap Paragraph
  ├── Opaque Node (Unsupported: \newcommand{\R}{\mathbb{R}}) --> Opaque Code Pill (Locked)
  ├── Semantic Node (Supported: \begin{equation} ... \end)   --> TipTap Math Block
  └── Opaque Node (Unsupported: \begin{tikzpicture} ... \end)--> Opaque Code Pill (Locked)
```

---

## 2. Canonical Data Models

### 2.1 Core Block Hierarchy
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    EQUATION = "equation"
    FIGURE = "figure"
    TABLE = "table"
    OPAQUE_LATEX = "opaque_latex"

@dataclass
class SourceRange:
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    start_byte: int
    end_byte: int

@dataclass
class CanonicalBlock:
    id: str
    block_type: BlockType
    raw_latex: str
    source_range: SourceRange
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_opaque: bool = False

@dataclass
class CanonicalDocument:
    id: str
    title: str
    blocks: List[CanonicalBlock] = field(default_factory=list)
    preamble_raw: str = ""
```

---

## 3. Synchronization Algorithms

### 3.1 LaTeX-to-Model Parsing (CST Generation)
1. **Preamble Extraction:** Scan for `\begin{document}`. Everything preceding it is preserved verbatim in `preamble_raw` and marked as opaque.
2. **Body Lexing:** Scan document body sequentially:
   - Match `\section{...}`, `\subsection{...}`, etc. $\to$ `CanonicalBlock(HEADING, level=...)`.
   - Match `\begin{equation}...\end{equation}` or `$$...$$` $\to$ `CanonicalBlock(EQUATION)`.
   - Match standard prose paragraphs separated by blank lines $\to$ `CanonicalBlock(PARAGRAPH)`.
   - Any unknown environment (`\begin{custom}...\end{custom}`), macro definition (`\def`, `\newcommand`), or raw formatting command (`\vspace`, `\noindent`) $\to$ `CanonicalBlock(OPAQUE_LATEX, is_opaque=True)`.
3. **Range Anchoring:** Compute exact 0-indexed byte and line/column ranges for every block.

### 3.2 Visual-to-LaTeX Patching (Surgical Range Replacement)
When a user edits block $B_k$ in the visual editor:
1. Lookup $B_k$ in the active document block registry.
2. If $B_k$ is `OPAQUE_LATEX`, reject visual mutation (editing must occur in source view or side inspector).
3. Serialize only $B_k$ into its new LaTeX representation: $T_{new}$.
4. Compute delta length: $\Delta = \text{len}(T_{new}) - \text{len}(B_k.\text{raw\_latex})$.
5. In the raw `.tex` buffer, slice and replace:
   $$\text{Buffer}_{new} = \text{Buffer}[0 : B_k.\text{start\_byte}] + T_{new} + \text{Buffer}[B_k.\text{end\_byte} :]$$
6. Update downstream blocks: For all $j > k$, offset their byte ranges by $\Delta$.
7. Untouched blocks and opaque blocks are **not re-parsed or re-serialized**, guaranteeing zero formatting or macro degradation.

---

## 4. Two-Way Coordinate Mapping

- **Visual Element to Source Range:** Every visual DOM element carries attribute `data-block-id="{id}"`. Clicking the element dispatches an IPC message with the `block_id`. The source editor moves cursor to `block.source_range.start_line, start_col`.
- **Source Cursor to Visual Element:** When the cursor moves in the source editor at position $(L, C)$, the engine performs binary search over the block list:
  $$\text{Find } B_k \text{ such that } B_k.\text{start\_line} \le L \le B_k.\text{end\_line}$$
  The visual editor scrolls to and highlights DOM node `[data-block-id="B_k.id"]`.

