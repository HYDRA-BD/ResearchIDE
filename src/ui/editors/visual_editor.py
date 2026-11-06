"""Visual Document Editor Widget powered by PySide6 QWebEngineView and QWebChannel."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from src.core.sync_bridge import SyncBridge
from src.core.document import BlockType
from src.utils.logger import app_logger


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ResearchIDE Visual Canvas</title>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<style>
  :root {
    --bg-page: #f8f9fa;
    --bg-canvas: #ffffff;
    --text-primary: #1a1a1a;
    --text-muted: #5f6368;
    --border-color: #dadce0;
    --accent: #1a73e8;
    --opaque-bg: #f1f3f4;
    --opaque-border: #d2e3fc;
    --opaque-text: #174ea6;
    --font-serif: "Times New Roman", Times, "Cambria", Georgia, serif;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-mono: "Consolas", "Courier New", monospace;
  }

  body.dark-theme {
    --bg-page: #18191a;
    --bg-canvas: #242526;
    --text-primary: #e4e6eb;
    --text-muted: #b0b3b8;
    --border-color: #3e4042;
    --accent: #4da3ff;
    --opaque-bg: #2d3748;
    --opaque-border: #4a5568;
    --opaque-text: #90cdf4;
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    padding: 30px 15px;
    background-color: var(--bg-page);
    font-family: var(--font-serif);
    color: var(--text-primary);
    transition: background-color 0.2s, color 0.2s;
  }

  #document-container {
    max-width: 820px;
    margin: 0 auto;
    background: var(--bg-canvas);
    padding: 60px 70px;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 2px 8px rgba(0,0,0,0.06);
    border: 1px solid var(--border-color);
    min-height: 90vh;
  }

  .doc-title {
    text-align: center;
    font-size: 26px;
    font-weight: bold;
    margin-bottom: 35px;
    font-family: var(--font-sans);
  }

  .block-wrapper {
    position: relative;
    margin: 12px 0;
    padding: 6px 10px;
    border-radius: 4px;
    transition: background 0.15s, outline 0.15s;
    outline: 2px solid transparent;
  }

  .block-wrapper:hover {
    outline: 1px dashed var(--accent);
  }

  .block-wrapper.active-block {
    outline: 2px solid var(--accent);
    background-color: rgba(26, 115, 232, 0.04);
  }

  /* Headings */
  .heading-1 {
    font-size: 20px;
    font-weight: bold;
    margin-top: 28px;
    margin-bottom: 12px;
    font-family: var(--font-sans);
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 6px;
  }
  .heading-2 {
    font-size: 16px;
    font-weight: bold;
    margin-top: 22px;
    margin-bottom: 10px;
    font-family: var(--font-sans);
  }
  .heading-3 {
    font-size: 14px;
    font-weight: bold;
    font-style: italic;
    margin-top: 16px;
    margin-bottom: 8px;
    font-family: var(--font-sans);
  }

  /* Paragraphs */
  .paragraph-block {
    font-size: 15px;
    line-height: 1.65;
    text-align: justify;
    text-indent: 1.5em;
    min-height: 24px;
  }

  /* Equations */
  .equation-block {
    font-family: var(--font-serif);
    font-style: italic;
    text-align: center;
    padding: 16px;
    margin: 16px 0;
    background: rgba(0,0,0,0.02);
    border-radius: 4px;
    font-size: 17px;
    border: 1px solid var(--border-color);
  }

  /* Tables */
  .table-block {
    margin: 18px 0;
    text-align: center;
  }
  .table-block table {
    margin: 0 auto;
    border-collapse: collapse;
    width: 90%;
  }
  .table-block th, .table-block td {
    border: 1px solid var(--border-color);
    padding: 8px 12px;
    font-size: 14px;
  }
  .table-block th {
    background: rgba(0,0,0,0.04);
    font-family: var(--font-sans);
    font-weight: 600;
  }

  /* Figures */
  .figure-block {
    text-align: center;
    margin: 24px 0;
    padding: 20px;
    border: 1px dashed var(--border-color);
    border-radius: 4px;
  }
  .figure-caption {
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 8px;
    font-style: italic;
  }

  /* Opaque LaTeX Pills */
  .opaque-pill {
    background-color: var(--opaque-bg);
    border: 1px solid var(--opaque-border);
    color: var(--opaque-text);
    padding: 10px 14px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 12px;
    user-select: none;
    cursor: not-allowed;
    white-space: pre-wrap;
    word-break: break-all;
    position: relative;
  }

  .opaque-pill-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
    background: var(--opaque-border);
    padding: 2px 6px;
    border-radius: 3px;
    margin-bottom: 6px;
  }

  .opaque-hint {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
    font-family: var(--font-sans);
  }

  [contenteditable="true"]:focus {
    outline: none;
  }
</style>
</head>
<body>
<div id="document-container">
  <div id="doc-title" class="doc-title">Document Title</div>
  <div id="blocks-container"></div>
</div>

<script>
let bridge = null;
let currentBlocks = [];
let debounceTimer = null;

// Initialize WebChannel connection to PySide6
new QWebChannel(qt.webChannelTransport, function (channel) {
  bridge = channel.objects.bridge;
  if (bridge) {
    bridge.webCanvasReady();
  }
});

function renderDocument(docData) {
  currentBlocks = docData.blocks || [];
  document.getElementById('doc-title').innerText = docData.title || "Untitled Manuscript";
  const container = document.getElementById('blocks-container');
  container.innerHTML = "";

  currentBlocks.forEach(block => {
    const wrapper = document.createElement('div');
    wrapper.className = 'block-wrapper';
    wrapper.id = 'block-' + block.id;
    wrapper.dataset.blockId = block.id;

    wrapper.addEventListener('click', (e) => {
      document.querySelectorAll('.block-wrapper').forEach(el => el.classList.remove('active-block'));
      wrapper.classList.add('active-block');
      if (bridge) {
        bridge.blockClicked(block.id);
      }
    });

    if (block.is_opaque) {
      wrapper.innerHTML = `
        <div class="opaque-pill">
          <div class="opaque-pill-badge">🔒 OPAQUE LATEX (${block.env_name || 'MACRO/TIKZ'})</div>
          <div>${escapeHtml(block.raw_latex)}</div>
          <div class="opaque-hint">Protected block. Click to view or edit in Source Mode.</div>
        </div>
      `;
    } else if (block.type === 'heading') {
      const level = block.level || 1;
      const el = document.createElement('div');
      el.className = `heading-${level}`;
      el.contentEditable = "true";
      el.innerText = block.title || "";
      el.addEventListener('input', () => onBlockInput(block.id, el.innerText));
      wrapper.appendChild(el);
    } else if (block.type === 'paragraph') {
      const el = document.createElement('div');
      el.className = 'paragraph-block';
      el.contentEditable = "true";
      el.innerText = block.text || "";
      el.addEventListener('input', () => onBlockInput(block.id, el.innerText));
      wrapper.appendChild(el);
    } else if (block.type === 'equation') {
      const el = document.createElement('div');
      el.className = 'equation-block';
      el.contentEditable = "true";
      el.innerText = block.latex || "";
      el.addEventListener('input', () => onBlockInput(block.id, el.innerText));
      wrapper.appendChild(el);
    } else if (block.type === 'table') {
      wrapper.innerHTML = `
        <div class="table-block">
          <table>
            <thead>
              <tr><th>Header 1</th><th>Header 2</th></tr>
            </thead>
            <tbody>
              <tr><td>Data 1</td><td>Data 2</td></tr>
              <tr><td>Data 3</td><td>Data 4</td></tr>
            </tbody>
          </table>
        </div>
      `;
    } else if (block.type === 'figure') {
      wrapper.innerHTML = `
        <div class="figure-block">
          <div style="font-size:32px;">🖼️</div>
          <div class="figure-caption">Figure: LaTeX Figure Anchor</div>
        </div>
      `;
    } else {
      const el = document.createElement('div');
      el.className = 'paragraph-block';
      el.contentEditable = "true";
      el.innerText = block.raw_latex || "";
      el.addEventListener('input', () => onBlockInput(block.id, el.innerText));
      wrapper.appendChild(el);
    }

    container.appendChild(wrapper);
  });
}

function onBlockInput(blockId, text) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    if (bridge) {
      bridge.blockContentChanged(blockId, text);
    }
  }, 250);
}

function scrollToBlock(blockId) {
  const el = document.getElementById('block-' + blockId);
  if (el) {
    document.querySelectorAll('.block-wrapper').forEach(b => b.classList.remove('active-block'));
    el.classList.add('active-block');
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function setTheme(isDark) {
  if (isDark) {
    document.body.classList.add('dark-theme');
  } else {
    document.body.classList.remove('dark-theme');
  }
}

function escapeHtml(text) {
  const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
  return text.replace(/[&<>"']/g, m => map[m]);
}
</script>
</body>
</html>
"""


class VisualEditorBridge(QObject):
    """Bridge exposed to JavaScript inside QWebEngineView for IPC communication."""

    block_updated = Signal(str, str)  # block_id, new_text
    block_selected = Signal(str)      # block_id
    ready = Signal()

    @Slot()
    def webCanvasReady(self) -> None:
        """Called by JavaScript when the page and QWebChannel are fully initialized."""
        app_logger.debug("VisualEditor web canvas reported ready.")
        self.ready.emit()

    @Slot(str, str)
    def blockContentChanged(self, block_id: str, new_text: str) -> None:
        """Called by JavaScript when the user types in an editable block."""
        self.block_updated.emit(block_id, new_text)

    @Slot(str)
    def blockClicked(self, block_id: str) -> None:
        """Called by JavaScript when a block is clicked/selected."""
        self.block_selected.emit(block_id)


class VisualEditorWidget(QWidget):
    """PySide6 Visual Academic Document Editor using QWebEngineView."""

    content_modified = Signal(str)  # Emits updated LaTeX source
    block_focused = Signal(str, int, int)  # block_id, start_line, end_line

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.sync_bridge = SyncBridge(self)
        self.is_canvas_ready: bool = False
        self._pending_doc_dict: Optional[Dict[str, Any]] = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # WebEngine View
        self.web_view = QWebEngineView(self)
        self.web_channel = QWebChannel(self)
        self.bridge = VisualEditorBridge(self)

        self.web_channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.web_channel)

        # Set HTML content
        self.web_view.setHtml(HTML_TEMPLATE, QUrl("http://localhost/canvas"))
        layout.addWidget(self.web_view)

    def _connect_signals(self) -> None:
        self.bridge.ready.connect(self._on_canvas_ready)
        self.bridge.block_updated.connect(self._on_block_updated)
        self.bridge.block_selected.connect(self._on_block_selected)
        self.sync_bridge.source_patched.connect(self.content_modified.emit)
        self.sync_bridge.visual_model_updated.connect(self._render_model)

    def load_latex(self, latex_source: str) -> None:
        """Load LaTeX source into the synchronizer and render in visual canvas."""
        self.sync_bridge.load_from_latex(latex_source)
        doc_dict = self.sync_bridge.get_document_as_dict()

        if self.is_canvas_ready:
            self._render_model(doc_dict)
        else:
            self._pending_doc_dict = doc_dict

    def _on_canvas_ready(self) -> None:
        self.is_canvas_ready = True
        if self._pending_doc_dict:
            self._render_model(self._pending_doc_dict)
            self._pending_doc_dict = None

    def _render_model(self, doc_dict: Dict[str, Any]) -> None:
        """Transmit document JSON to JavaScript canvas."""
        escaped_json = json.dumps(doc_dict)
        js_code = f"renderDocument({escaped_json});"
        self.web_view.page().runJavaScript(js_code)

    def _on_block_updated(self, block_id: str, new_text: str) -> None:
        """Handle visual text modification from JavaScript."""
        self.sync_bridge.apply_visual_block_update(block_id, new_text)

    def _on_block_selected(self, block_id: str) -> None:
        """Handle block selection in visual editor and emit coordinates for source editor."""
        if not self.sync_bridge.current_document:
            return
        block = self.sync_bridge.current_document.get_block_by_id(block_id)
        if block:
            self.block_focused.emit(
                block.id,
                block.source_range.start_line,
                block.source_range.end_line,
            )

    def scroll_to_source_line(self, line_number: int) -> None:
        """Given a source line number, find and scroll to the matching block in the visual canvas."""
        block = self.sync_bridge.find_block_at_line(line_number)
        if block:
            self.web_view.page().runJavaScript(f"scrollToBlock('{block.id}');")

    def insert_element(self, block_type: BlockType, content: str = "") -> None:
        """Insert a new academic block (heading, paragraph, equation, table, figure)."""
        self.sync_bridge.insert_block_after(None, block_type, content)

    def set_theme(self, is_dark: bool) -> None:
        """Toggle dark or light theme inside the web canvas."""
        flag = "true" if is_dark else "false"
        self.web_view.page().runJavaScript(f"setTheme({flag});")
