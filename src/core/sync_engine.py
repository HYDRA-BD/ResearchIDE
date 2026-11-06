"""Bidirectional Document Synchronization Engine for ResearchIDE.

Applies surgical text range replacements to raw LaTeX source without altering
or re-serializing untouched semantic elements or opaque blocks.
"""

from __future__ import annotations
from typing import Tuple
from src.core.document import (
    CanonicalBlock,
    CanonicalDocument,
    SectionBlock,
    ParagraphBlock,
    EquationBlock,
)
from src.core.parser import LaTeXDocumentParser
from src.core.serializer import LaTeXDocumentSerializer


class DocumentSyncEngine:
    """Coordinates non-destructive edits between visual views and raw LaTeX source."""

    def __init__(self) -> None:
        self.parser = LaTeXDocumentParser()
        self.serializer = LaTeXDocumentSerializer()

    def patch_block(
        self,
        doc: CanonicalDocument,
        raw_source: str,
        block_id: str,
        new_content: str,
    ) -> Tuple[CanonicalDocument, str]:
        """Apply a visual edit to a specific block and return updated (doc, patched_source).

        Raises:
            ValueError: If block is not found or block is an OpaqueLaTeXBlock.
        """
        block = doc.get_block_by_id(block_id)
        if not block:
            raise ValueError(f"Block with ID '{block_id}' not found in document.")

        if block.is_opaque:
            raise ValueError(
                f"Block '{block_id}' is protected Opaque LaTeX and cannot be modified via visual editing."
            )

        if not block.source_range:
            raise ValueError(f"Block '{block_id}' does not have source coordinate bounds.")

        # 1. Update the in-memory block object
        if isinstance(block, SectionBlock):
            block.title = new_content
        elif isinstance(block, ParagraphBlock):
            block.text = new_content
        elif isinstance(block, EquationBlock):
            block.math_content = new_content

        # 2. Serialize only this modified block
        replacement_text = self.serializer.serialize_block(block).strip()

        # 3. Surgical slice replacement in raw source text
        start_byte = block.source_range.start_byte
        end_byte = block.source_range.end_byte

        patched_source = (
            raw_source[:start_byte]
            + replacement_text
            + raw_source[end_byte:]
        )

        # 4. Re-parse the patched source to refresh CST coordinates
        updated_doc = self.parser.parse(patched_source)
        return updated_doc, patched_source

