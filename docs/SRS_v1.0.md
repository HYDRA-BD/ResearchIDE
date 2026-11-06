# Software Requirements Specification (SRS)
## Local AI-Powered LaTeX Research Writing Environment

**Version:** 1.0  
**Platform:** Windows Desktop  
**Application Type:** Fully Local Academic Research Software  
**Primary Development Language:** Python  
**GUI Framework:** PySide6  
**AI Runtime:** Ollama  
**Development Environment:** Google Antigravity IDE

---

# 1. Product Vision

Develop a comprehensive, locally operated academic research writing environment that combines the familiarity of Microsoft Word, the technical capabilities of a LaTeX IDE, and AI-powered research assistance.

The application should allow researchers to write academic documents visually without needing to manually write LaTeX code. LaTeX source should be generated and maintained in the background.

Users must also be able to switch to a source-code editing environment and access a compiled PDF preview.

The application should support the academic research lifecycle, from literature management and manuscript preparation to publication submission.

## 1.1 Core Objectives

1. Provide a Word-like academic writing experience.
2. Maintain synchronized visual, LaTeX and PDF editing modes.
3. Provide completely local AI assistance through Ollama.
4. Support academic research and literature review workflows.
5. Manage citations, references and publication templates.
6. Compile LaTeX documents locally.
7. Provide research project organization and document history.
8. Protect research documents through autosave and recovery.
9. Operate without external AI APIs or cloud AI services.

# 2. Target Environment

| Component | Requirement |
|---|---|
| Operating system | Windows 10/11 |
| Processor | Ryzen 5 5600G-class or better |
| RAM | 16 GB baseline |
| GPU | NVIDIA RTX 3060 12 GB |
| Storage | Local SSD |
| Programming language | Python |
| GUI | PySide6 |
| AI runtime | Ollama |
| Database | Local database |
| Distribution | Windows installer |

The application must be designed to operate efficiently within the available hardware resources.

# 3. Functional Requirements

## FR-01: Document Editing Environment

The application shall provide three synchronized editing modes:

- Visual Word-like editor.
- LaTeX source editor.
- Compiled PDF preview.

Users shall be able to switch between these modes on demand.

The visual editor shall support:
- Text editing and formatting.
- Headings and academic styles.
- Paragraph formatting.
- Tables and figures.
- Equations.
- Captions and cross-references.
- Page layout and numbering.
- Headers and footers.
- Table of contents.
- Find and replace.

Right-click navigation shall allow users to move between corresponding visual and LaTeX representations.

## FR-02: LaTeX Compilation

The application shall support local compilation using:

- PDFLaTeX.
- XeLaTeX.
- LuaLaTeX.
- BibTeX.
- Biber.

Additional requirements:
- Automatic compilation.
- Configurable compilation delay.
- Compilation logs.
- Error diagnostics.
- Build profiles.
- SyncTeX navigation.
- Previous successful PDF preservation after failed builds.

## FR-03: Academic Templates

Users shall be able to create documents using:

- Research article templates.
- Conference paper templates.
- Systematic reviews.
- Literature reviews.
- Theses and dissertations.

The application shall support publisher and organization templates, including IEEE, Springer Nature, Elsevier, ACM, Wiley and APA.

Users shall be able to select an exact journal, conference or university template.

Templates shall be downloadable and cached locally for offline reuse. Existing projects must retain their original template version.

## FR-04: Literature Review Intelligence

The application shall provide AI-assisted literature analysis.

Capabilities:
- Compare research objectives.
- Compare methodologies.
- Compare datasets.
- Compare experimental results.
- Identify limitations.
- Identify research gaps.
- Detect contradictory findings.
- Generate literature matrices.
- Help organize logically connected literature reviews.
- Trace extracted findings to their source papers and relevant passages.

## FR-05: Academic Writing Intelligence

The AI shall be capable of generating complete draft sections, including:

- Abstract.
- Introduction.
- Literature review.
- Methodology.
- Results.
- Discussion.
- Conclusion.

Generated material must remain editable.

The AI must not fabricate research findings, experimental results, methodologies or references.

AI-generated content must be presented for user review before application to the manuscript.

## FR-06: AI Writing Detection

The application shall provide basic document-level AI-writing detection.

It shall:
- Produce estimated AI-writing likelihood.
- Explain uncertainty.
- Display limitations and possible false positives.

Plagiarism detection and external text-similarity database integration are excluded from this version.

## FR-07: Citation and Reference Intelligence

The application shall support:

- Manual reference creation.
- Automatic reference import.
- BibTeX.
- DOI metadata retrieval.
- RIS.
- CSL JSON.
- In-text citation insertion.
- Automatic bibliography generation.
- IEEE, APA, Springer, Elsevier, ACM and other citation styles.
- Reference recommendations based on manuscript context.
- Citation-style conversion when templates change.

## FR-08: Local AI System

All AI inference shall operate locally through Ollama.

External AI APIs and cloud AI inference are prohibited.

The system shall support specialized models for:

- Academic writing.
- LaTeX assistance.
- Research analysis.
- Mathematical reasoning.
- Programming assistance.
- Embeddings and semantic retrieval.

Only one model shall be loaded at a time.

Users shall be able to:
- Detect existing Ollama models.
- Import compatible local models.
- Assign models to specific tasks.
- Select models manually.
- Remove installed models.

AI responses shall prioritize quality and reasoning depth over speed.

## FR-09: AI Interaction and Permissions

The AI shall use a command-based natural-language interface.

It shall understand the active document and relevant project context.

AI actions shall remain suggestion-based.

The AI must never modify a manuscript automatically without explicit user approval.

## FR-10: Mathematical Editor

The visual equation editor shall support:

- Fractions.
- Nested fractions.
- Superscripts and subscripts.
- Square roots and radicals.
- Greek symbols.
- Mathematical operators.
- Summations.
- Integrals.

Equations shall be converted into LaTeX automatically.

## FR-11: Figures and Tables

The application shall support:

- Image insertion.
- Resizing and cropping.
- Figure positioning.
- Drag-and-drop.
- Table editing.
- Captions.
- Automatic numbering.
- Cross-references.
- SVG, PNG, JPEG and PDF graphics.
- TikZ diagrams.
- Research charts.
- Publication-quality figure formatting.
- Centralized figure management.

## FR-12: Research Project Management

The application shall support structured research projects.

Each project may contain:
- Manuscripts.
- PDF research papers.
- References.
- Literature reviews.
- Figures.
- Tables.
- Notes.
- Datasets.
- Tasks.
- Milestones.
- Publication targets.
- Submission records.

Project-specific AI context shall be maintained.

## FR-13: PDF Processing

The application shall provide:

- PDF viewing.
- Text extraction.
- Heading extraction.
- Reference extraction.
- Metadata extraction.
- Table extraction.
- Figure extraction.
- Equation extraction.
- Document structure extraction.

## FR-14: Dataset Management

The application shall provide:
- Dataset storage.
- CSV and Excel previews.
- Dataset metadata.
- Basic dataset organization.

Advanced experiment tracking and dataset versioning are not mandatory in v1.0.

## FR-15: Version History

The application shall provide automatic document revision history.

Users shall be able to access previous saved revisions.

Git-style branching and merging are not required.

## FR-16: Search and Productivity

The application shall provide:
- Basic find and replace.
- Advanced search within documents and projects.

Global semantic search across the entire research library is not mandatory in v1.0.

## FR-17: Interface and Customization

The interface shall use an adaptive hybrid design combining:

- Word-style ribbon.
- Research project navigation.
- IDE-style editing panels.
- LaTeX source editor.
- PDF preview.
- Research workspace.

Light and dark themes shall be supported.

The interface shall use a predefined layout rather than requiring extensive user customization.

## FR-18: Security and Recovery

The application shall provide:
- Autosave.
- Automatic backups.
- Crash recovery.
- Restoration of saved documents.
- Protection against unsaved document loss.

Advanced encryption and scheduled multi-location backups are not mandatory in v1.0.

## FR-19: Submission Preparation

The application shall support:
- Final PDF generation.
- LaTeX source package export.
- Page-limit verification.
- Margin and font-size verification.
- Template formatting checks.
- Title page preparation.
- Abstract and keyword management.
- Supplementary material organization.
- Submission checklist generation.

## FR-20: Diagnostics

The application shall provide:
- Detailed error messages.
- Compiler diagnostics.
- Crash reports.
- Diagnostic tools.
- Troubleshooting guidance.

## FR-21: Performance Management

The application shall monitor and manage:
- RAM consumption.
- VRAM consumption.
- CPU utilization.
- GPU utilization.
- Background tasks.
- AI model loading and unloading.

Adaptive performance optimization and configurable resource limits shall be supported.

## FR-22: Application Distribution

The application shall be distributed through a standard Windows installer.

It shall provide:
- Installation wizard.
- Start Menu entry.
- Desktop shortcut.
- Local storage configuration.
- Uninstallation.

Application updates shall be manual.

# 4. Non-Functional Requirements

## NFR-01: Offline Operation

Core editing, compilation, local AI inference and project management must function without an internet connection.

Internet access may be used for:
- Downloading templates.
- Retrieving DOI metadata.
- Acquiring external research resources.

These online features must not be required for core offline operation.

## NFR-02: Data Privacy

Research documents and AI processing shall remain local.

No cloud AI processing shall be used.

## NFR-03: Reliability

Autosave, backup and recovery mechanisms must minimize the risk of research-data loss.

## NFR-04: Performance

The application shall be optimized for 16 GB RAM and 12 GB VRAM.

It shall avoid unnecessary simultaneous model execution.

## NFR-05: Maintainability

The software shall use modular architecture with clearly separated subsystems.

## NFR-06: Extensibility

New AI models, document templates, citation styles and research features should be addable without redesigning the entire application.

# 5. Technical Constraints

The following constraints must guide architecture design:

1. PySide6 is the primary GUI framework.
2. Python is the primary development language.
3. Ollama is the primary AI inference runtime.
4. Only one AI model is loaded at a time.
5. AI must operate locally.
6. LaTeX compilation must operate locally.
7. Windows is the initial target platform.
8. The application must support a standard installer.
9. The application is designed for one user.

# 6. Important Engineering Considerations

The visual editor and LaTeX source editor must share a structured document representation.

The application should use a semantic document model with mappings between visual elements and LaTeX source ranges.

Arbitrary LaTeX packages, custom macros and unsupported environments may not always be representable visually. Such content must remain accessible through source-code mode without being silently destroyed.

AI-generated content must be staged for approval rather than automatically inserted.

The local AI system must manage model memory carefully because the target hardware has limited VRAM and system RAM.

# 7. Initial Acceptance Criteria

The first release shall be considered functionally acceptable when:

1. A user can create and save a research document.
2. The document can be edited in visual mode.
3. The corresponding LaTeX source can be inspected and edited.
4. The document can be compiled into a PDF locally.
5. Basic visual-to-source navigation works.
6. An installed Ollama model can assist with writing and LaTeX.
7. AI suggestions require user approval.
8. References can be inserted and bibliographies generated.
9. Figures, tables and equations can be inserted.
10. Research PDFs can be imported and processed.
11. Projects can be organized locally.
12. Autosave and crash recovery work.
13. The application can operate offline for its core functions.

# 8. Development Strategy

The application shall be developed incrementally.

The development team must establish the document architecture, data model, synchronization strategy and local execution environment before implementing the complete feature set.

Each development phase must produce a testable, working application.

No phase shall be considered complete merely because its interface has been implemented; its underlying functionality must also be tested.