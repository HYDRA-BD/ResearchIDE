# PHASE 5 — RESEARCH INTELLIGENCE AND LITERATURE MANAGEMENT

Implement the research-processing subsystem.

All extracted research information must remain traceable to its source.

## 1. Research PDF library

Support importing local research PDFs into projects.

Store:
- Original PDF.
- Filename.
- Title.
- Authors.
- Publication year.
- DOI.
- Abstract.
- Journal or conference.
- Keywords.

## 2. PDF processing

Extract:
- Text.
- Headings.
- References.
- Metadata.
- Tables.
- Figures.
- Equations.
- Document structure.

Use OCR where required by the approved architecture.

Preserve original PDFs.

Do not assume every PDF can be perfectly parsed.

## 3. Literature analysis

Support:
- Paper summarization.
- Research objective extraction.
- Methodology extraction.
- Dataset extraction.
- Result extraction.
- Limitation extraction.
- Comparison between papers.
- Literature matrix generation.
- Research gap identification.
- Contradiction detection.

## 4. Traceability

Every extracted research claim must link to:
- Original paper.
- Page number.
- Relevant passage, where available.

Never present an AI-generated interpretation as a direct quotation.

## 5. Reference management

Implement:
- Manual reference creation.
- BibTeX import/export.
- RIS import/export.
- CSL JSON support.
- DOI metadata retrieval when online.
- In-text citation insertion.
- Bibliography generation.
- Citation style selection.

Support common academic styles.

## 6. Citation recommendations

Allow AI to recommend references from the active project library.

Recommendations must identify the source and explain relevance.

Never fabricate DOI numbers, publication details or references.

## 7. Dataset management

Implement:
- Dataset file storage.
- CSV preview.
- Excel preview.
- Metadata management.
- Dataset organization.
- Basic data inspection.

Do not implement advanced experiment tracking or complex machine-learning pipelines in this phase.

## 8. Testing

Test:
- PDF imports.
- Metadata extraction.
- Reference extraction.
- Tables and figures.
- Scanned PDF handling.
- Citation import/export.
- Source traceability.
- Literature matrix generation.
- Dataset previews.

## 9. Completion

A user must be able to import research papers, inspect extracted information, compare papers, manage references and generate literature-review drafts with source traceability.