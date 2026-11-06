"""Canonical Semantic Document Model for ResearchIDE.

Defines the structured representations of academic documents, their blocks,
and exact source coordinate mappings for bidirectional synchronization.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class BlockType(str, Enum):
    """Categorization of canonical document blocks."""
    SECTION = "section"
    PARAGRAPH = "paragraph"
    EQUATION = "equation"
    FIGURE = "figure"
    TABLE = "table"
    OPAQUE_LATEX = "opaque_latex"


@dataclass(frozen=True)
class SourceRange:
    """Represents an exact 1-indexed line/column and 0-indexed byte span in raw text."""
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    start_byte: int
    end_byte: int

    def contains_position(self, line: int, col: int) -> bool:
        """Check if a given (line, col) cursor position falls within this range."""
        if line < self.start_line or line > self.end_line:
            return False
        if line == self.start_line and col < self.start_col:
            return False
        if line == self.end_line and col > self.end_col:
            return False
        return True


@dataclass
class CanonicalBlock:
    """Base class for all semantic blocks in a document."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    block_type: BlockType = BlockType.PARAGRAPH
    source_range: Optional[SourceRange] = None
    raw_latex: str = ""
    is_opaque: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SectionBlock(CanonicalBlock):
    """Represents a hierarchical document heading (\section, \subsection, etc.)."""
    level: int = 1  # 1: section, 2: subsection, 3: subsubsection
    title: str = ""
    block_type: BlockType = BlockType.SECTION


@dataclass
class ParagraphBlock(CanonicalBlock):
    """Represents a prose paragraph with text content."""
    text: str = ""
    block_type: BlockType = BlockType.PARAGRAPH


@dataclass
class EquationBlock(CanonicalBlock):
    """Represents a mathematical equation or formula block."""
    math_content: str = ""
    env_name: str = "equation"  # equation, align, gather, displaymath
    label: Optional[str] = None
    is_verified: bool = False
    block_type: BlockType = BlockType.EQUATION


@dataclass
class OpaqueLaTeXBlock(CanonicalBlock):
    """Represents unsupported or protected LaTeX code preserved verbatim."""
    reason: str = "unsupported_construct"
    block_type: BlockType = BlockType.OPAQUE_LATEX
    is_opaque: bool = True


@dataclass
class CanonicalDocument:
    """Represents a complete academic document with metadata and ordered blocks."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Document"
    preamble: str = "\\documentclass{article}\n\\usepackage{amsmath}\n"
    postamble: str = "\\end{document}\n"
    blocks: List[CanonicalBlock] = field(default_factory=list)

    def get_block_by_id(self, block_id: str) -> Optional[CanonicalBlock]:
        """Lookup a block by its unique identifier."""
        for block in self.blocks:
            if block.id == block_id:
                return block
        return None
