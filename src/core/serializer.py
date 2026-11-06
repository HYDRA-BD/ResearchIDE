"""LaTeX Document Serializer for ResearchIDE.

Converts canonical semantic document models into valid, compilable LaTeX source code
while preserving opaque verbatim constructs byte-for-byte.
"""

from __future__ import annotations
from src.core.document import (
    BlockType,
    CanonicalBlock,
    CanonicalDocument,
    SectionBlock,
    ParagraphBlock,
    EquationBlock,
    OpaqueLaTeXBlock,
)


class LaTeXDocumentSerializer:
    """Serializes a CanonicalDocument into standard LaTeX source text."""

    SECTION_COMMANDS = {
        1: "\\section",
        2: "\\subsection",
        3: "\\subsubsection",
        4: "\\paragraph",
    }

    def serialize_block(self, block: CanonicalBlock) -> str:
        """Serialize a single canonical block to LaTeX string."""
        if block.is_opaque:
            return block.raw_latex

        if isinstance(block, SectionBlock):
            cmd = self.SECTION_COMMANDS.get(block.level, "\\section")
            return f"{cmd}{{{block.title}}}\n"

        if isinstance(block, ParagraphBlock):
            return f"{block.text}\n"

        if isinstance(block, EquationBlock):
            env = block.env_name or "equation"
            label_part = f"\\label{{{block.label}}}\n" if block.label else ""
            content = block.math_content.strip()
            return f"\\begin{{{env}}}\n{label_part}{content}\n\\end{{{env}}}\n"

        # Fallback to raw latex if available
        return block.raw_latex if block.raw_latex else ""

    def serialize_document(self, doc: CanonicalDocument) -> str:
        """Serialize an entire CanonicalDocument into standard LaTeX source text."""
        parts: list[str] = []

        # 1. Preamble
        preamble = doc.preamble
        if not preamble.strip().endswith("\\begin{document}"):
            if not preamble.endswith("\n"):
                preamble += "\n"
            preamble += "\\begin{document}\n\n"
        parts.append(preamble)

        # 2. Document Body Blocks
        for i, block in enumerate(doc.blocks):
            serialized = self.serialize_block(block)
            parts.append(serialized)
            # Add separation between blocks if not already trailing with double newline
            if not serialized.endswith("\n\n"):
                parts.append("\n")

        # 3. Postamble
        parts.append(doc.postamble)

        return "".join(parts)

