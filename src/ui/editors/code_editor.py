"""Professional Code Editor with Line Numbers, Bracket Matching, and Search."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Set
from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import (
    QColor,
    QPainter,
    QTextFormat,
    QTextCursor,
    QKeyEvent,
    QFont,
    QKeySequence,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QWidget,
    QPlainTextEdit,
    QTextEdit,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QLabel,
    QFrame,
    QCompleter,
)
from src.ui.editors.latex_highlighter import LaTeXHighlighter


class LineNumberArea(QWidget):
    """Side gutter widget displaying line numbers."""

    def __init__(self, editor: CodeEditor) -> None:
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.code_editor.line_number_area_paint_event(event)


class SearchReplaceBar(QFrame):
    """Inline search and replace floating toolbar."""

    find_next_requested = Signal(str, bool)  # text, match_case
    find_prev_requested = Signal(str, bool)
    replace_requested = Signal(str, str, bool)  # find_text, replace_text, match_case
    replace_all_requested = Signal(str, str, bool)
    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SearchReplaceBar")
        self.setStyleSheet(
            "QFrame#SearchReplaceBar { background-color: #22222a; border: 1px solid #363644; border-radius: 6px; padding: 4px; }"
        )
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 4)
        main_layout.setSpacing(4)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        search_row.addWidget(QLabel("Find:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.returnPressed.connect(self._find_next)
        search_row.addWidget(self.search_input)

        btn_next = QPushButton("↓ Next")
        btn_next.clicked.connect(self._find_next)
        btn_prev = QPushButton("↑ Prev")
        btn_prev.clicked.connect(self._find_prev)
        self.case_check = QCheckBox("Match Case")

        search_row.addWidget(btn_next)
        search_row.addWidget(btn_prev)
        search_row.addWidget(self.case_check)

        btn_close = QPushButton("✕")
        btn_close.setFixedWidth(24)
        btn_close.clicked.connect(self.close_requested.emit)
        search_row.addWidget(btn_close)
        main_layout.addLayout(search_row)

        # Replace row
        replace_row = QHBoxLayout()
        replace_row.setSpacing(6)
        replace_row.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        replace_row.addWidget(self.replace_input)

        btn_replace = QPushButton("Replace")
        btn_replace.clicked.connect(self._replace)
        btn_replace_all = QPushButton("Replace All")
        btn_replace_all.clicked.connect(self._replace_all)

        replace_row.addWidget(btn_replace)
        replace_row.addWidget(btn_replace_all)
        main_layout.addLayout(replace_row)

    def _find_next(self) -> None:
        text = self.search_input.text()
        if text:
            self.find_next_requested.emit(text, self.case_check.isChecked())

    def _find_prev(self) -> None:
        text = self.search_input.text()
        if text:
            self.find_prev_requested.emit(text, self.case_check.isChecked())

    def _replace(self) -> None:
        find_text = self.search_input.text()
        replace_text = self.replace_input.text()
        if find_text:
            self.replace_requested.emit(find_text, replace_text, self.case_check.isChecked())

    def _replace_all(self) -> None:
        find_text = self.search_input.text()
        replace_text = self.replace_input.text()
        if find_text:
            self.replace_all_requested.emit(find_text, replace_text, self.case_check.isChecked())


class CodeEditor(QPlainTextEdit):
    """High-performance LaTeX code editor with gutter line numbers, bracket matching, and error indicators."""

    LATEX_KEYWORDS = [
        "\\begin{equation}", "\\end{equation}",
        "\\begin{align}", "\\end{align}",
        "\\begin{figure}", "\\end{figure}",
        "\\begin{table}", "\\end{table}",
        "\\begin{itemize}", "\\end{itemize}",
        "\\begin{enumerate}", "\\end{enumerate}",
        "\\section{}", "\\subsection{}", "\\subsubsection{}",
        "\\cite{}", "\\ref{}", "\\label{}", "\\pageref{}",
        "\\textbf{}", "\\textit{}", "\\underline{}", "\\emph{}",
        "\\usepackage{}", "\\documentclass{}",
        "\\author{}", "\\title{}", "\\date{\\today}",
        "\\includegraphics{}", "\\caption{}",
    ]

    def __init__(self, file_path: Optional[Path | str] = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.file_path = Path(file_path).resolve() if file_path else None
        self.error_lines: Set[int] = set()

        # Typography
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Line Number Gutter
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

        # Syntax Highlighter
        is_bib = self.file_path.suffix.lower() == ".bib" if self.file_path else False
        self.highlighter = LaTeXHighlighter(self.document(), is_bibtex=is_bib, dark_theme=True)

        # Search Bar
        self.search_bar = SearchReplaceBar(self)
        self.search_bar.hide()
        self.search_bar.find_next_requested.connect(self.find_next)
        self.search_bar.find_prev_requested.connect(self.find_previous)
        self.search_bar.replace_requested.connect(self.replace_text)
        self.search_bar.replace_all_requested.connect(self.replace_all_text)
        self.search_bar.close_requested.connect(self.search_bar.hide)

        # Auto-complete
        self.completer = QCompleter(self.LATEX_KEYWORDS, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self._insert_completion)

        self.highlight_current_line()

    # --- Line Number Gutter Implementation ---

    def line_number_area_width(self) -> int:
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 20 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
        if self.search_bar.isVisible():
            sb_width = min(480, cr.width() - 40)
            self.search_bar.setGeometry(cr.right() - sb_width - 20, cr.top() + 10, sb_width, 75)

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#18181e"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_idx = block_number + 1
                number_str = str(line_idx)

                # Error marker in gutter
                if line_idx in self.error_lines:
                    painter.fillRect(0, top, self.line_number_area.width(), self.fontMetrics().height(), QColor("#7f1d1d"))
                    painter.setPen(QColor("#fca5a5"))
                elif block_number == current_line:
                    painter.setPen(QColor("#4daafc"))
                else:
                    painter.setPen(QColor("#52525e"))

                painter.setFont(self.font())
                painter.drawText(
                    0, top, self.line_number_area.width() - 8, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number_str
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # --- Line Highlighting & Error Display ---

    def highlight_current_line(self) -> None:
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#22222a")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        # Highlight compilation error lines
        if self.error_lines:
            block = self.document().begin()
            while block.isValid():
                line_idx = block.blockNumber() + 1
                if line_idx in self.error_lines:
                    err_selection = QTextEdit.ExtraSelection()
                    err_selection.format.setBackground(QColor(127, 29, 29, 90))
                    err_selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                    cursor = QTextCursor(block)
                    err_selection.cursor = cursor
                    extra_selections.append(err_selection)
                block = block.next()

        self.setExtraSelections(extra_selections)

    def set_error_lines(self, lines: list[int]) -> None:
        """Mark line numbers with compilation errors."""
        self.error_lines = set(lines)
        self.line_number_area.update()
        self.highlight_current_line()

    def go_to_line(self, line_number: int) -> None:
        """Move cursor directly to specified 1-based line number."""
        block = self.document().findBlockByLineNumber(line_number - 1)
        if block.isValid():
            cursor = QTextCursor(block)
            self.setTextCursor(cursor)
            self.centerCursor()

    # --- Search and Replace Actions ---

    def toggle_search_bar(self) -> None:
        if self.search_bar.isVisible():
            self.search_bar.hide()
        else:
            selected = self.textCursor().selectedText()
            if selected:
                self.search_bar.search_input.setText(selected)
            cr = self.contentsRect()
            sb_width = min(480, cr.width() - 40)
            self.search_bar.setGeometry(cr.right() - sb_width - 20, cr.top() + 10, sb_width, 75)
            self.search_bar.show()
            self.search_bar.search_input.setFocus()
            self.search_bar.search_input.selectAll()

    def find_next(self, text: str, match_case: bool = False) -> bool:
        flags = QTextDocument.FindFlag(0)
        if match_case:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        found = self.find(text, flags)
        if not found:
            # Wrap around from top
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            found = self.find(text, flags)
        return found

    def find_previous(self, text: str, match_case: bool = False) -> bool:
        flags = QTextDocument.FindFlag.FindBackward
        if match_case:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        found = self.find(text, flags)
        if not found:
            # Wrap around from end
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            found = self.find(text, flags)
        return found

    def replace_text(self, find_text: str, replace_text: str, match_case: bool = False) -> None:
        cursor = self.textCursor()
        if cursor.hasSelection() and (
            (match_case and cursor.selectedText() == find_text)
            or (not match_case and cursor.selectedText().lower() == find_text.lower())
        ):
            cursor.insertText(replace_text)
        self.find_next(find_text, match_case)

    def replace_all_text(self, find_text: str, replace_text: str, match_case: bool = False) -> int:
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)

        count = 0
        while self.find_next(find_text, match_case):
            cur = self.textCursor()
            cur.insertText(replace_text)
            count += 1

        cursor.endEditBlock()
        return count

    # --- Autocomplete & Auto-Indentation ---

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Search Shortcut (Ctrl+F)
        if event.matches(QKeySequence.StandardKey.Find):
            self.toggle_search_bar()
            return

        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                event.ignore()
                return

        # Auto-Indentation on Enter/Return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            current_line = cursor.block().text()
            match = re.match(r"^(\s*)", current_line)
            indent = match.group(1) if match else ""

            if current_line.strip().startswith("\\begin{") or current_line.strip().endswith("{"):
                extra_indent = "  "
            else:
                extra_indent = ""

            super().keyPressEvent(event)
            self.insertPlainText(indent + extra_indent)
            return

        super().keyPressEvent(event)

        # Trigger Completer after typing '\'
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()

        if word.startswith("\\") and len(word) >= 2:
            self.completer.setCompletionPrefix(word)
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

    def _insert_completion(self, completion: str) -> None:
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)
