"""Bidirectional Synchronization Bridge between Canonical Document CST and Visual/Source Editors."""
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal, Slot
from src.core.document import (
    CanonicalDocument,
    CanonicalBlock,
    BlockType,
    SectionBlock,
    ParagraphBlock,
    EquationBlock,
    OpaqueLaTeXBlock,
    SourceRange,
)
from src.core.parser import LaTeXDocumentParser
from src.core.serializer import LaTeXDocumentSerializer
from src.core.sync_engine import DocumentSyncEngine
from src.core.source_mapper import SourceMapper
from src.utils.logger import app_logger


class SyncBridge(QObject):
    """Orchestrates bidirectional synchronization between LaTeX source and visual document representations.
    
    Guarantees:
    1. Zero data loss for unsupported macros / TikZ (isolated in OpaqueLaTeXBlock).
    2. Surgical in-place patching of edited blocks without touching untouched blocks or preambles.
    3. Loop prevention with synchronization guard flags.
    """

    # Signals emitted when synchronization updates occur
    source_patched = Signal(str)  # Emits full patched LaTeX source
    visual_model_updated = Signal(dict)  # Emits serialized document dict for web canvas
    block_selected = Signal(str, int, int)  # block_id, start_line, end_line
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.current_document: Optional[CanonicalDocument] = None
        self.raw_latex: str = ""
        self._is_syncing: bool = False

    def load_from_latex(self, latex_source: str) -> CanonicalDocument:
        """Parse raw LaTeX source into canonical CST model and prepare sync state."""
        self.raw_latex = latex_source
        self.current_document = LaTeXDocumentParser.parse(latex_source)
        app_logger.debug(
            f"SyncBridge parsed document '{self.current_document.title}' with "
            f"{len(self.current_document.blocks)} blocks."
        )
        return self.current_document

    def get_document_as_dict(self) -> Dict[str, Any]:
        """Convert current document model to a JSON-serializable dictionary for the visual editor."""
        if not self.current_document:
            return {"title": "Untitled", "blocks": [], "preamble": ""}

        blocks_data = []
        for block in self.current_document.blocks:
            item: Dict[str, Any] = {
                "id": block.id,
                "type": block.block_type.value,
                "raw_latex": block.raw_latex,
                "is_opaque": block.is_opaque,
                "start_line": block.source_range.start_line,
                "end_line": block.source_range.end_line,
            }

            if isinstance(block, SectionBlock):
                item["title"] = block.title
                item["level"] = block.level
            elif isinstance(block, ParagraphBlock):
                item["text"] = block.text
            elif isinstance(block, EquationBlock):
                item["latex"] = block.math_content
                item["env_name"] = block.env_name
            elif isinstance(block, OpaqueLaTeXBlock):
                item["env_name"] = block.metadata.get("env", "tikzpicture")
            else:
                item["content"] = block.raw_latex

            blocks_data.append(item)

        return {
            "title": self.current_document.title,
            "blocks": blocks_data,
            "preamble": self.current_document.preamble,
        }

    def apply_visual_block_update(self, block_id: str, new_content: str) -> bool:
        """Apply a visual edit to a canonical block and surgically patch the LaTeX buffer.
        
        Returns True if successful, False if blocked (e.g. attempting to mutate opaque block).
        """
        if self._is_syncing or not self.current_document:
            return False

        block = self.current_document.get_block_by_id(block_id)
        if not block:
            app_logger.warning(f"SyncBridge: block '{block_id}' not found for update.")
            return False

        if block.is_opaque:
            msg = f"Cannot visually mutate opaque LaTeX block '{block_id}'. Modify via source mode."
            app_logger.warning(msg)
            self.error_occurred.emit(msg)
            return False

        try:
            self._is_syncing = True

            # Surgically patch raw LaTeX without re-serializing untouched blocks
            self.current_document, self.raw_latex = DocumentSyncEngine.patch_block(
                self.current_document,
                self.raw_latex,
                block_id,
                new_content,
            )

            self.source_patched.emit(self.raw_latex)
            return True

        except Exception as e:
            app_logger.error(f"SyncBridge: Failed applying visual update to '{block_id}': {e}")
            self.error_occurred.emit(str(e))
            return False
        finally:
            self._is_syncing = False

    def insert_block_after(self, target_block_id: Optional[str], block_type: BlockType, content: str = "") -> bool:
        """Insert a new semantic block into the document and update source."""
        if self._is_syncing or not self.current_document:
            return False

        try:
            self._is_syncing = True

            # Construct LaTeX for new block
            if block_type == BlockType.SECTION:
                latex_fragment = f"\n\\section{{{content or 'New Section'}}}\n"
            elif block_type == BlockType.PARAGRAPH:
                latex_fragment = f"\n\n{content or 'Type paragraph text here...'}\n"
            elif block_type == BlockType.EQUATION:
                latex_fragment = f"\n\\begin{{equation}}\n{content or 'E = mc^2'}\n\\end{{equation}}\n"
            elif block_type == BlockType.TABLE:
                latex_fragment = (
                    "\n\\begin{table}[htbp]\n"
                    "\\centering\n"
                    "\\caption{Sample Table}\n"
                    "\\begin{tabular}{|c|c|}\n"
                    "\\hline\n"
                    "Header 1 & Header 2 \\\\\n"
                    "\\hline\n"
                    "Value 1 & Value 2 \\\\\n"
                    "\\hline\n"
                    "\\end{tabular}\n"
                    "\\end{table}\n"
                )
            elif block_type == BlockType.FIGURE:
                latex_fragment = (
                    "\n\\begin{figure}[htbp]\n"
                    "\\centering\n"
                    "\\caption{Sample Figure Caption}\n"
                    "\\label{fig:sample}\n"
                    "\\end{figure}\n"
                )
            else:
                latex_fragment = f"\n{content}\n"

            if target_block_id:
                target = self.current_document.get_block_by_id(target_block_id)
                insert_pos = target.source_range.end_byte if target else len(self.raw_latex)
            else:
                # Insert before \end{document} if present
                doc_end = self.raw_latex.rfind(r"\end{document}")
                insert_pos = doc_end if doc_end != -1 else len(self.raw_latex)

            self.raw_latex = (
                self.raw_latex[:insert_pos] + latex_fragment + self.raw_latex[insert_pos:]
            )

            # Re-parse to rebuild block tree and source coordinates
            self.current_document = LaTeXDocumentParser.parse(self.raw_latex)
            self.source_patched.emit(self.raw_latex)
            self.visual_model_updated.emit(self.get_document_as_dict())
            return True

        except Exception as e:
            app_logger.error(f"SyncBridge: Failed inserting block: {e}")
            self.error_occurred.emit(str(e))
            return False
        finally:
            self._is_syncing = False

    def find_block_at_line(self, line_number: int) -> Optional[CanonicalBlock]:
        """Lookup canonical block enclosing given source line number (1-based)."""
        if not self.current_document:
            return None
        return SourceMapper.find_block_at_line(self.current_document, line_number)
