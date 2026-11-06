"""LaTeX Document Parser for ResearchIDE.

Parses LaTeX source text into a CanonicalDocument CST, accurately computing
source ranges and categorizing unsupported constructs as OpaqueLaTeXBlock.
"""

from __future__ import annotations
import re
import uuid
from typing import List, Tuple, Optional
from src.core.document import (
    BlockType,
    SourceRange,
    CanonicalBlock,
    CanonicalDocument,
    SectionBlock,
    ParagraphBlock,
    EquationBlock,
    OpaqueLaTeXBlock,
)


class LaTeXDocumentParser:
    """Parses raw LaTeX strings into structured CanonicalDocument representations."""

    # Regex patterns for semantic elements
    SECTION_RE = re.compile(
        r"^\\(?P<cmd>section|subsection|subsubsection|paragraph)\*?\{(?P<title>[^}]+)\}",
        re.MULTILINE
    )
    EQUATION_ENV_RE = re.compile(
        r"\\begin\{(?P<env>equation|align|gather|displaymath)\*?\}(?P<content>.*?)\\end\{(?P=env)\*?\}",
        re.DOTALL
    )
    OPAQUE_ENV_RE = re.compile(
        r"\\begin\{(?P<env>tikzpicture|pgfplots|circuitikz|lstlisting|verbatim|minted|[a-zA-Z0-9_\*]+)\}(?P<content>.*?)\\end\{(?P=env)\}",
        re.DOTALL
    )
    CUSTOM_MACRO_RE = re.compile(
        r"\\(newcommand|renewcommand|providecommand|def)\*?(\\[a-zA-Z]+|\{[^\}]+\})",
    )

    def __init__(self) -> None:
        self.supported_math_envs = {"equation", "align", "gather", "displaymath"}

    def _compute_line_col_offsets(self, text: str) -> list[int]:
        """Compute the character index where each line begins (0-indexed)."""
        offsets = [0]
        for i, char in enumerate(text):
            if char == "\n":
                offsets.append(i + 1)
        return offsets

    def _offset_to_line_col(self, offset: int, line_offsets: list[int]) -> Tuple[int, int]:
        """Convert a 0-indexed byte/char offset into 1-indexed (line, col)."""
        # Binary search for the line index
        low, high = 0, len(line_offsets) - 1
        line_idx = 0
        while low <= high:
            mid = (low + high) // 2
            if line_offsets[mid] <= offset:
                line_idx = mid
                low = mid + 1
            else:
                high = mid - 1
        line = line_idx + 1
        col = (offset - line_offsets[line_idx]) + 1
        return line, col

    def _create_source_range(
        self, start_offset: int, end_offset: int, line_offsets: list[int]
    ) -> SourceRange:
        """Create a SourceRange object from start and end offsets."""
        start_line, start_col = self._offset_to_line_col(start_offset, line_offsets)
        end_line, end_col = self._offset_to_line_col(end_offset, line_offsets)
        return SourceRange(
            start_line=start_line,
            start_col=start_col,
            end_line=end_line,
            end_col=end_col,
            start_byte=start_offset,
            end_byte=end_offset,
        )

    def parse(self, text: str) -> CanonicalDocument:
        """Parse complete LaTeX source text into a CanonicalDocument."""
        doc = CanonicalDocument()
        line_offsets = self._compute_line_col_offsets(text)

        # 1. Preamble and Postamble Extraction
        begin_doc_match = re.search(r"\\begin\{document\}", text)
        end_doc_match = re.search(r"\\end\{document\}", text)

        body_start = 0
        body_end = len(text)

        if begin_doc_match:
            body_start = begin_doc_match.end()
            doc.preamble = text[:body_start]
        else:
            doc.preamble = "\\documentclass{article}\n\\begin{document}\n"

        if end_doc_match:
            body_end = end_doc_match.start()
            doc.postamble = text[body_end:]
        else:
            doc.postamble = "\n\\end{document}\n"

        body_text = text[body_start:body_end]
        body_base_offset = body_start

        # 2. Tokenize and segment body text into blocks
        blocks: List[CanonicalBlock] = []

        # Split body by double newlines or block-level constructs
        cursor = 0
        body_len = len(body_text)

        while cursor < body_len:
            # Skip leading whitespace/newlines
            while cursor < body_len and body_text[cursor].isspace():
                cursor += 1
            if cursor >= body_len:
                break

            current_slice = body_text[cursor:]
            abs_start = body_base_offset + cursor

            # Check 1: Hierarchical Section Heading
            sec_match = self.SECTION_RE.match(current_slice)
            if sec_match:
                cmd = sec_match.group("cmd")
                title = sec_match.group("title").strip()
                match_len = sec_match.end()
                abs_end = abs_start + match_len

                level = 1
                if cmd == "subsection":
                    level = 2
                elif cmd == "subsubsection":
                    level = 3
                elif cmd == "paragraph":
                    level = 4

                raw_latex = body_text[cursor : cursor + match_len]
                sr = self._create_source_range(abs_start, abs_end, line_offsets)
                sec_block = SectionBlock(
                    id=str(uuid.uuid4()),
                    source_range=sr,
                    raw_latex=raw_latex,
                    level=level,
                    title=title,
                )
                blocks.append(sec_block)
                cursor += match_len
                continue

            # Check 2: Math Environment (\begin{equation}...)
            eq_match = self.EQUATION_ENV_RE.match(current_slice)
            if eq_match:
                env_name = eq_match.group("env")
                raw_content = eq_match.group("content")
                match_len = eq_match.end()
                abs_end = abs_start + match_len

                # Extract label if present
                label_match = re.search(r"\\label\{([^}]+)\}", raw_content)
                label = label_match.group(1) if label_match else None
                cleaned_math = re.sub(r"\\label\{[^}]+\}", "", raw_content).strip()

                raw_latex = body_text[cursor : cursor + match_len]
                sr = self._create_source_range(abs_start, abs_end, line_offsets)
                eq_block = EquationBlock(
                    id=str(uuid.uuid4()),
                    source_range=sr,
                    raw_latex=raw_latex,
                    math_content=cleaned_math,
                    env_name=env_name,
                    label=label,
                )
                blocks.append(eq_block)
                cursor += match_len
                continue

            # Check 3: Opaque Environment (e.g. tikzpicture, verbatim, custom)
            opaque_env_match = self.OPAQUE_ENV_RE.match(current_slice)
            if opaque_env_match and opaque_env_match.group("env") not in self.supported_math_envs:
                match_len = opaque_env_match.end()
                abs_end = abs_start + match_len
                raw_latex = body_text[cursor : cursor + match_len]
                sr = self._create_source_range(abs_start, abs_end, line_offsets)
                opaque_block = OpaqueLaTeXBlock(
                    id=str(uuid.uuid4()),
                    source_range=sr,
                    raw_latex=raw_latex,
                    reason=f"environment_{opaque_env_match.group('env')}",
                )
                blocks.append(opaque_block)
                cursor += match_len
                continue

            # Check 4: Custom Macro Definition (\newcommand, \def, etc.)
            macro_match = self.CUSTOM_MACRO_RE.match(current_slice)
            if macro_match:
                # Consume line or until matching brace
                line_end = current_slice.find("\n")
                if line_end == -1:
                    line_end = len(current_slice)
                match_len = line_end
                abs_end = abs_start + match_len
                raw_latex = body_text[cursor : cursor + match_len]
                sr = self._create_source_range(abs_start, abs_end, line_offsets)
                opaque_block = OpaqueLaTeXBlock(
                    id=str(uuid.uuid4()),
                    source_range=sr,
                    raw_latex=raw_latex,
                    reason="custom_macro_definition",
                )
                blocks.append(opaque_block)
                cursor += match_len
                continue

            # Check 5: Standard Paragraph (consume up to next blank line or next special construct)
            para_end = 0
            while para_end < len(current_slice):
                sub = current_slice[para_end:]
                # Stop if blank line
                if sub.startswith("\n\n") or sub.startswith("\r\n\r\n"):
                    break
                # Stop if next line begins a section or environment
                if sub.startswith("\n\\section") or sub.startswith("\n\\subsection") or sub.startswith("\n\\begin{"):
                    break
                para_end += 1

            raw_latex = current_slice[:para_end].strip()
            match_len = para_end
            abs_end = abs_start + match_len

            if raw_latex:
                sr = self._create_source_range(abs_start, abs_end, line_offsets)
                # If paragraph contains unsupported raw TeX primitives, tag or keep as paragraph
                para_block = ParagraphBlock(
                    id=str(uuid.uuid4()),
                    source_range=sr,
                    raw_latex=raw_latex,
                    text=raw_latex,
                )
                blocks.append(para_block)

            cursor += match_len

        doc.blocks = blocks
        return doc

