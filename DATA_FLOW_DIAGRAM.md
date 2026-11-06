# DATA FLOW DIAGRAMS
## ResearchIDE: Document Sync, Compilation, AI and Literature Pipelines
**Document Version:** 1.0.0  

---

## 1. Document Editing and Synchronization Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Researcher
    participant VE as Visual Canvas (TipTap)
    participant Core as Canonical Sync Engine
    participant SE as LaTeX Source Editor
    participant Disk as Local File (.tex)

    User->>VE: Types or formats text in Visual Mode
    VE->>Core: Emit visual node mutation event
    Core->>Core: Match node ID to CST Source Coordinate [Line, Col]
    Core->>SE: Apply surgical text range replacement
    Core->>Disk: Atomic write via temp file (.tex.tmp -> .tex)
    Core->>Core: Update CST offsets for downstream blocks
```

---

## 2. LaTeX Compilation and SyncTeX Feedback Loop

```mermaid
sequenceDiagram
    autonumber
    participant Core as Core Engine
    participant Daemon as Compilation Daemon
    participant TeX as MiKTeX / TeX Live (pdflatex)
    participant LogParser as TeX Log Parser
    participant PDF as PDF.js Preview Canvas
    participant SE as Source Editor

    Core->>Daemon: Trigger debounced build (after 500ms idle)
    Daemon->>TeX: Spawn process with -synctex=1 in /build cache
    TeX-->>Daemon: Process exits (code, stdout, stderr, synctex.gz)
    Daemon->>LogParser: Feed raw compilation log
    LogParser-->>Core: Structured errors & warnings (file, line, desc)
    alt Compilation Successful
        Daemon->>PDF: Reload generated main.pdf
        User->>PDF: Ctrl+Click on equation in PDF
        PDF->>Core: Query SyncTeX (page 2, x=150, y=340)
        Core->>SE: Scroll & highlight line 124 in main.tex
    else Compilation Failed
        Core->>SE: Display red squiggly underlines on error lines
        Core->>Core: Keep previous valid PDF in preview canvas
    end
```

---

## 3. Local AI Generation and Pre-Mutation Rollback Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Researcher
    participant UI as AI Chat / Ribbon
    participant Core as Core Orchestrator
    participant Ollama as Ollama Daemon (GPU)
    participant Snapshot as Snapshot Store (.researchide/snapshots/)
    participant Disk as Project Files

    User->>UI: Prompt: "Rewrite Section 2 to emphasize methodology"
    UI->>Core: Package active section text + local context
    Core->>Ollama: POST /api/chat (streaming JSON)
    Ollama-->>UI: Stream drafted text suggestions
    User->>UI: Clicks "Preview Diff & Apply"
    Core->>Snapshot: Take atomic snapshot of target section (.zstd)
    Core->>UI: Display interactive Side-by-Side Diff
    alt User Clicks "Accept"
        Core->>Disk: Apply unified diff patch to section.tex
        Core->>Core: Re-parse document CST & update visual editor
    else User Clicks "Reject" or "Undo"
        Core->>Snapshot: Revert file state from snapshot
        Core->>UI: Restore original document buffer
    end
```

---

## 4. Literature Ingestion & Evidence Grounding Pipeline

```mermaid
flowchart TD
    PDFFile["Incoming Research PDF"] --> Ingest["Literature Manager Ingest"]
    Ingest --> TextExtract["pypdf / PDFium Text & Bounding Box Extractor"]
    Ingest --> BibExtract["BibTeX / DOI Metadata Resolver"]
    
    TextExtract --> LayoutSplitter["Two-Column & Heading Segmenter"]
    LayoutSplitter --> ChunkStore["Semantic Chunks [Text, Page, Coords]"]
    
    ChunkStore --> FTS["SQLite FTS5 Full-Text Index"]
    ChunkStore --> Embedding["Ollama / Local Sentence-Transformer"]
    Embedding --> VecStore["Vector Index (Chroma / SQLite)"]
    
    BibExtract --> RefTable["literature_references Table"]
    ChunkStore --> ClaimTable["literature_claims Table"]
```

