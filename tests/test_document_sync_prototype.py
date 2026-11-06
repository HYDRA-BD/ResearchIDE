"""Automated Test Suite for Phase 0 Document Synchronization Prototype.

Validates:
1. Structured canonical document creation and serialization.
2. Lossless round-trip parsing of supported elements.
3. Safe preservation of unsupported LaTeX constructs (TikZ, macros).
4. Accurate bidirectional source-position mapping.
5. Non-destructive surgical range replacement during visual edits.
6. Mutation rejection on protected opaque blocks.
"""

import unittest
from src.core.document import (
    BlockType,
    CanonicalDocument,
    SectionBlock,
    ParagraphBlock,
    EquationBlock,
    OpaqueLaTeXBlock,
)
from src.core.parser import LaTeXDocumentParser
from src.core.serializer import LaTeXDocumentSerializer
from src.core.source_mapper import SourceMapper
from src.core.sync_engine import DocumentSyncEngine


class TestDocumentSyncPrototype(unittest.TestCase):
    """Test suite validating canonical document modeling and bidirectional synchronization."""

    def setUp(self) -> None:
        self.parser = LaTeXDocumentParser()
        self.serializer = LaTeXDocumentSerializer()
        self.sync_engine = DocumentSyncEngine()

    def test_document_creation_and_serialization(self) -> None:
        """Test building a structured canonical document and serializing to valid LaTeX."""
        doc = CanonicalDocument(title="Test Manuscript")
        doc.blocks = [
            SectionBlock(id="sec-1", level=1, title="Introduction"),
            ParagraphBlock(id="p-1", text="This is the first sentence of the paper."),
            EquationBlock(id="eq-1", math_content="E = mc^2", env_name="equation", label="eq:einstein"),
        ]

        serialized = self.serializer.serialize_document(doc)
        self.assertIn("\\documentclass{article}", serialized)
        self.assertIn("\\begin{document}", serialized)
        self.assertIn("\\section{Introduction}", serialized)
        self.assertIn("This is the first sentence of the paper.", serialized)
        self.assertIn("\\begin{equation}", serialized)
        self.assertIn("E = mc^2", serialized)
        self.assertIn("\\label{eq:einstein}", serialized)
        self.assertIn("\\end{document}", serialized)

    def test_latex_parsing_supported_constructs(self) -> None:
        """Test parsing supported LaTeX into semantic blocks with accurate metadata."""
        raw_latex = (
            "\\documentclass{article}\n"
            "\\begin{document}\n\n"
            "\\section{Methodology}\n\n"
            "We propose a novel framework for offline research.\n\n"
            "\\begin{equation}\n"
            "\\label{eq:navier}\n"
            "\\nabla \\cdot \\mathbf{u} = 0\n"
            "\\end{equation}\n\n"
            "\\end{document}\n"
        )

        doc = self.parser.parse(raw_latex)
        self.assertEqual(len(doc.blocks), 3)

        # 1. Section Block
        sec_block = doc.blocks[0]
        self.assertIsInstance(sec_block, SectionBlock)
        self.assertEqual(sec_block.title, "Methodology")
        self.assertEqual(sec_block.level, 1)

        # 2. Paragraph Block
        para_block = doc.blocks[1]
        self.assertIsInstance(para_block, ParagraphBlock)
        self.assertIn("We propose a novel framework", para_block.text)

        # 3. Equation Block
        eq_block = doc.blocks[2]
        self.assertIsInstance(eq_block, EquationBlock)
        self.assertIn("\\nabla \\cdot \\mathbf{u} = 0", eq_block.math_content)
        self.assertEqual(eq_block.label, "eq:navier")

    def test_preservation_of_unsupported_opaque_constructs(self) -> None:
        """Test that custom macros and TikZ diagrams are isolated into OpaqueLaTeXBlocks."""
        raw_latex = (
            "\\documentclass{article}\n"
            "\\usepackage{tikz}\n"
            "\\begin{document}\n\n"
            "\\newcommand{\\R}{\\mathbb{R}}\n\n"
            "\\section{Complex Architecture}\n\n"
            "\\begin{tikzpicture}\n"
            "\\draw (0,0) circle (1cm);\n"
            "\\node at (0,0) {Center};\n"
            "\\end{tikzpicture}\n\n"
            "Final concluding remarks.\n\n"
            "\\end{document}\n"
        )

        doc = self.parser.parse(raw_latex)
        self.assertEqual(len(doc.blocks), 4)

        # Block 0: Custom macro
        self.assertIsInstance(doc.blocks[0], OpaqueLaTeXBlock)
        self.assertTrue(doc.blocks[0].is_opaque)
        self.assertIn("\\newcommand{\\R}{\\mathbb{R}}", doc.blocks[0].raw_latex)

        # Block 1: Section
        self.assertIsInstance(doc.blocks[1], SectionBlock)
        self.assertEqual(doc.blocks[1].title, "Complex Architecture")

        # Block 2: TikZ environment
        self.assertIsInstance(doc.blocks[2], OpaqueLaTeXBlock)
        self.assertTrue(doc.blocks[2].is_opaque)
        self.assertIn("\\draw (0,0) circle (1cm);", doc.blocks[2].raw_latex)

        # Block 3: Final Paragraph
        self.assertIsInstance(doc.blocks[3], ParagraphBlock)
        self.assertEqual(doc.blocks[3].text, "Final concluding remarks.")

        # Serialize back and verify 100% byte fidelity on opaque blocks
        reserialized = self.serializer.serialize_document(doc)
        self.assertIn("\\newcommand{\\R}{\\mathbb{R}}", reserialized)
        self.assertIn("\\begin{tikzpicture}\n\\draw (0,0) circle (1cm);\n\\node at (0,0) {Center};\n\\end{tikzpicture}", reserialized)

    def test_source_position_mapping(self) -> None:
        """Test bidirectional coordinate translation between blocks and source cursor lines."""
        raw_latex = (
            "\\documentclass{article}\n"  # Line 1
            "\\begin{document}\n\n"       # Line 2, 3
            "\\section{First Section}\n\n"# Line 4, 5
            "Line six text paragraph.\n\n"# Line 6, 7
            "\\end{document}\n"           # Line 8
        )

        doc = self.parser.parse(raw_latex)
        mapper = SourceMapper(doc)

        sec_block = doc.blocks[0]
        sr = mapper.get_range_for_block(sec_block.id)
        self.assertIsNotNone(sr)
        self.assertEqual(sr.start_line, 4)

        # Query cursor position on line 4, col 5 (inside \section)
        found_block = mapper.get_block_at_position(line=4, col=5)
        self.assertIsNotNone(found_block)
        self.assertEqual(found_block.id, sec_block.id)

        # Query cursor position on line 6, col 10 (inside paragraph)
        para_block = mapper.get_block_at_position(line=6, col=10)
        self.assertIsNotNone(para_block)
        self.assertIsInstance(para_block, ParagraphBlock)
        self.assertEqual(para_block.text, "Line six text paragraph.")

    def test_surgical_range_patching(self) -> None:
        """Test visually editing a section title patches raw text without touching opaque blocks."""
        raw_latex = (
            "\\documentclass{article}\n"
            "\\begin{document}\n\n"
            "\\section{Original Title}\n\n"
            "\\begin{tikzpicture}\n"
            "\\draw[red] (0,0) -- (1,1);\n"
            "\\end{tikzpicture}\n\n"
            "\\end{document}\n"
        )

        doc = self.parser.parse(raw_latex)
        sec_block = doc.blocks[0]
        tikz_block = doc.blocks[1]
        original_tikz_latex = tikz_block.raw_latex

        # Apply surgical patch to section title
        updated_doc, patched_source = self.sync_engine.patch_block(
            doc=doc,
            raw_source=raw_latex,
            block_id=sec_block.id,
            new_content="Updated Title for Publication",
        )

        # Verify that section title was replaced
        self.assertIn("\\section{Updated Title for Publication}", patched_source)
        self.assertNotIn("Original Title", patched_source)

        # Verify that the opaque TikZ block is byte-for-byte identical
        self.assertIn(original_tikz_latex, patched_source)
        self.assertEqual(updated_doc.blocks[1].raw_latex, original_tikz_latex)

    def test_opaque_mutation_protection(self) -> None:
        """Test that attempting to visually mutate an opaque block raises an error."""
        raw_latex = (
            "\\documentclass{article}\n"
            "\\begin{document}\n\n"
            "\\begin{tikzpicture}\n"
            "\\draw (0,0) -- (1,1);\n"
            "\\end{tikzpicture}\n\n"
            "\\end{document}\n"
        )

        doc = self.parser.parse(raw_latex)
        opaque_block = doc.blocks[0]
        self.assertTrue(opaque_block.is_opaque)

        # Attempting visual mutation must raise ValueError
        with self.assertRaises(ValueError):
            self.sync_engine.patch_block(
                doc=doc,
                raw_source=raw_latex,
                block_id=opaque_block.id,
                new_content="Corrupted Visual Content",
            )


if __name__ == "__main__":
    unittest.main()

