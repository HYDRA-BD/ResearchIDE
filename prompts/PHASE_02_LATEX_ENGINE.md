# PHASE 2 — LATEX EDITOR, COMPILER AND PDF PREVIEW

Implement a complete local LaTeX development environment.

Follow the existing architecture and preserve Phase 1 functionality.

## 1. LaTeX source editor

Implement a professional code editor with:

- Syntax highlighting.
- Line numbers.
- Code folding.
- Auto indentation.
- Bracket matching.
- Search and replace.
- Basic autocomplete.
- Error indicators.
- Multiple open files.
- .tex and .bib support.

Support project files such as:
- .tex
- .bib
- .cls
- .sty

## 2. Compiler management

Detect installed TeX distributions.

Support:
- TeX Live.
- MiKTeX.

Support engines:
- PDFLaTeX.
- XeLaTeX.
- LuaLaTeX.

Support bibliography tools:
- BibTeX.
- Biber.

Provide compiler configuration and build profiles.

Do not silently install a TeX distribution.

## 3. Compilation engine

Implement:
- Manual compilation.
- Automatic compilation.
- Configurable debounce.
- Compilation status.
- Process management.
- Build logs.
- Error parsing.
- Warning detection.
- Build cancellation.

Prevent concurrent compilation conflicts.

Preserve the previous successful PDF when a new build fails.

## 4. PDF preview

Implement an integrated PDF viewer with:

- Page navigation.
- Zoom.
- Fit-to-width.
- Fit-to-page.
- Text selection where supported.
- Page thumbnails.
- Search.
- Continuous scrolling.

## 5. SyncTeX

Implement forward and inverse synchronization.

- LaTeX source to PDF.
- PDF to LaTeX source.

Use the actual SyncTeX output from the compiler.

## 6. Project structure

Support multi-file LaTeX projects.

Handle:
- Main document.
- Included files.
- Bibliography.
- Images.
- Styles.
- Custom classes.

## 7. Security

Execute compiler processes safely.

Avoid unsafe shell command construction.

Validate paths and manage process termination.

## 8. Testing

Test:
- Minimal LaTeX documents.
- Bibliography compilation.
- Different compiler engines.
- Missing packages.
- Invalid LaTeX.
- Multiple source files.
- Failed compilation recovery.
- SyncTeX navigation.

## 9. Completion

The user must be able to create a LaTeX project, edit source, compile locally and view the resulting PDF.

Do not proceed until these workflows work reliably.