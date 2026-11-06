"""Source Coordinate and Position Mapping for ResearchIDE.

Provides bidirectional navigation between visual blocks and LaTeX source positions.
"""

from __future__ import annotations
from typing import Optional
from src.core.document import CanonicalBlock, CanonicalDocument, SourceRange


class SourceMapper:
    """Manages coordinate translations between visual blocks and LaTeX source."""

    def __init__(self, doc: CanonicalDocument) -> None:
        self.doc = doc

    def get_range_for_block(self, block_id: str) -> Optional[SourceRange]:
        """Lookup the source coordinate range for a given visual block ID."""
        block = self.doc.get_block_by_id(block_id)
        if block:
            return block.source_range
        return None

    def get_block_at_position(self, line: int, col: int) -> Optional[CanonicalBlock]:
        """Find the canonical block containing the given (line, col) in source."""
        for block in self.doc.blocks:
            if block.source_range and block.source_range.contains_position(line, col):
                return block
        return None

    def get_block_at_byte_offset(self, byte_offset: int) -> Optional[CanonicalBlock]:
        """Find the canonical block containing the given 0-indexed byte offset."""
        for block in self.doc.blocks:
            if block.source_range:
                if block.source_range.start_byte <= byte_offset <= block.source_range.end_byte:
                    return block
        return None

