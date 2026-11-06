"""Syntax Highlighter for LaTeX (.tex, .sty, .cls) and BibTeX (.bib) files."""
from __future__ import annotations
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QTextDocument,
)


class LaTeXHighlighter(QSyntaxHighlighter):
    """Provides high-performance syntax highlighting for LaTeX and BibTeX code."""

    def __init__(self, parent: QTextDocument, is_bibtex: bool = False, dark_theme: bool = True) -> None:
        super().__init__(parent)
        self.is_bibtex = is_bibtex
        self.dark_theme = dark_theme
        self.highlighting_rules: list[tuple[re.Pattern, QTextCharFormat]] = []
        self._init_formats()
        if self.is_bibtex:
            self._init_bibtex_rules()
        else:
            self._init_latex_rules()

    def _init_formats(self) -> None:
        # Theme-aware color palette
        if self.dark_theme:
            self.color_cmd = QColor("#60a5fa")       # Light blue
            self.color_section = QColor("#93c5fd")   # Bold cyan-blue
            self.color_math = QColor("#34d399")      # Green
            self.color_comment = QColor("#6b7280")   # Dim gray
            self.color_cite = QColor("#f472b6")      # Pink/magenta
            self.color_brace = QColor("#fbbf24")     # Amber
            self.color_keyword = QColor("#a78bfa")   # Purple
            self.color_string = QColor("#fca5a5")    # Soft red
        else:
            self.color_cmd = QColor("#0284c7")
            self.color_section = QColor("#1d4ed8")
            self.color_math = QColor("#059669")
            self.color_comment = QColor("#9ca3af")
            self.color_cite = QColor("#db2777")
            self.color_brace = QColor("#d97706")
            self.color_keyword = QColor("#7c3aed")
            self.color_string = QColor("#dc2626")

        # Command Format
        self.cmd_format = QTextCharFormat()
        self.cmd_format.setForeground(self.color_cmd)
        self.cmd_format.setFontWeight(QFont.Weight.Bold)

        # Section Heading Format
        self.section_format = QTextCharFormat()
        self.section_format.setForeground(self.color_section)
        self.section_format.setFontWeight(QFont.Weight.ExtraBold)

        # Math Environment Format
        self.math_format = QTextCharFormat()
        self.math_format.setForeground(self.color_math)

        # Comment Format
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(self.color_comment)
        self.comment_format.setFontItalic(True)

        # Citations / References Format
        self.cite_format = QTextCharFormat()
        self.cite_format.setForeground(self.color_cite)
        self.cite_format.setFontWeight(QFont.Weight.Bold)

        # Delimiters / Braces Format
        self.brace_format = QTextCharFormat()
        self.brace_format.setForeground(self.color_brace)

        # BibTeX Keyword Format
        self.bib_entry_format = QTextCharFormat()
        self.bib_entry_format.setForeground(self.color_keyword)
        self.bib_entry_format.setFontWeight(QFont.Weight.Bold)

        # BibTeX Field Format
        self.bib_field_format = QTextCharFormat()
        self.bib_field_format.setForeground(self.color_cmd)

        # String Format
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(self.color_string)

    def _init_latex_rules(self) -> None:
        """Rules for LaTeX source files (.tex, .sty, .cls)."""
        rules: list[tuple[str, QTextCharFormat]] = [
            # 1. Section Headings
            (r"\\(?:part|chapter|section|subsection|subsubsection|paragraph)\*?\{[^}]*\}", self.section_format),

            # 2. Citations and References
            (r"\\(?:cite|citep|citet|nocite|ref|eqref|pageref|label)\*?\{[^}]*\}", self.cite_format),

            # 3. Environments (\begin{...}, \end{...})
            (r"\\(?:begin|end)\{[^}]*\}", self.cmd_format),

            # 4. Standard LaTeX Commands
            (r"\\[a-zA-Z@]+", self.cmd_format),

            # 5. Math Delimiters ($...$, $$...$$)
            (r"\$\$[^\$]+\$\$", self.math_format),
            (r"\$[^\$\n]+\$", self.math_format),
            (r"\\\(.*?\\\)", self.math_format),
            (r"\\\[.*?\\\]", self.math_format),

            # 6. Braces & Brackets
            (r"[\{\}\[\]\(\)]", self.brace_format),

            # 7. Comments (must be evaluated after commands)
            (r"%.*$", self.comment_format),
        ]

        self.highlighting_rules = [(re.compile(pattern), fmt) for pattern, fmt in rules]

    def _init_bibtex_rules(self) -> None:
        """Rules for BibTeX bibliography files (.bib)."""
        rules: list[tuple[str, QTextCharFormat]] = [
            # Entry Type (e.g. @article, @book)
            (r"@[a-zA-Z]+", self.bib_entry_format),

            # Fields (e.g. author =, title =)
            (r"\b(?:author|title|journal|year|volume|number|pages|month|note|key|booktitle|publisher|editor|edition|series|address|doi|url|isbn|issn)\b\s*=", self.bib_field_format),

            # Braces and equals
            (r"[\{\}\=,]", self.brace_format),

            # Double-quoted strings
            (r'"[^"\n]*"', self.string_format),

            # Comments
            (r"%.*$", self.comment_format),
        ]

        self.highlighting_rules = [(re.compile(pattern, re.IGNORECASE), fmt) for pattern, fmt in rules]

    def highlightBlock(self, text: str) -> None:
        """Apply highlighting rules sequentially to the current text block."""
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)
