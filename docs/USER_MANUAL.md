# RESEARCHIDE USER MANUAL
## Comprehensive Operational Guide for Academic Researchers
**Version:** 1.0.0  
**Target Platform:** Windows 10/11 64-bit  

---

## 1. Introduction & Overview
ResearchIDE is an offline-first academic desktop environment designed specifically for scholarly authoring, literature analysis, and LaTeX manuscript preparation. It combines:
- Word-inspired visual document authoring.
- Full LaTeX code editing with instant line numbers, bracket matching, and autocompletion.
- Local compiler integration with MiKTeX or TeX Live.
- Interactive high-DPI PDF preview with bidirectional SyncTeX navigation.
- Local AI writing and error analysis powered by Ollama.
- Grounded literature management linking claims to exact PDF page snippets.
- Publication preparation with automated compliance audits (IEEE, ACM, Springer, Elsevier).

---

## 2. Getting Started

### 2.1 Launching the Application
Launch the application via the desktop shortcut or terminal:
```bash
python src/main.py
```

### 2.2 Creating a Project
1. On the Home Dashboard, click **New Research Project**.
2. Choose a project directory, enter the title, and choose a starter template.
3. The application scaffolds:
   - `src/` (LaTeX source files, starting with `main.tex`)
   - `literature/` (Research PDFs)
   - `assets/` (Figures, plots, and diagrams)
   - `notes/` (User research notes)
   - `.researchide/` (Local SQLite database and recovery checkpoints)

---

## 3. Manuscript Authoring

### 3.1 Multi-Mode Editor Views
Each document tab includes an editor mode toolbar:
- **Visual Mode:** Word-style manuscript canvas with formatted headings, paragraphs, and rendered math equations.
- **LaTeX Source Mode:** Full-featured code editor with syntax highlighting, line numbers, error indicators, and autocomplete.
- **Side-by-Side Split:** Side-by-side editing where visual changes surgically patch source text in real-time.

### 3.2 Inserting Academic Elements
Use the Ribbon **Insert** tab:
- **Section / Subsection:** Inserts structured hierarchical headings.
- **Equation:** Inserts `\begin{equation} ... \end{equation}` math blocks.
- **Figure:** Inserts float environments with captions and cross-reference labels.
- **Table:** Inserts structured tabular environments.
- **Citation:** Inserts in-text `\cite{...}` keys.

---

## 4. Local AI Writing Assistant

### 4.1 Connecting Local Ollama
1. Open the **AI Research Assistant** panel on the right sidebar.
2. Ensure the local Ollama daemon is active (`ollama serve`).
3. Click **🔄 Refresh** to detect installed models (e.g. `qwen2.5:14b`, `llama3.1:8b`).

### 4.2 Specialist Personas & Permission Gate
- Select a persona: *Academic Writer*, *LaTeX Engineer*, *Research Analyst*, or *Mathematical Reasoner*.
- Click a Quick Academic Command (e.g. *Explain Error*, *Rewrite Formal*, *Draft Method*).
- **Mandatory Approval:** Generated drafts are presented in a read-only preview. Review the draft and click **Accept & Apply** to insert it, or **Discard** to reject it. AI suggestions never alter your manuscript without your explicit confirmation.

---

## 5. Literature & Reference Management

### 5.1 Ingesting Research Papers
1. Open the **Literature & References** dock panel.
2. In the **Library** tab, click **Import PDF...** to extract text, publication year, and DOI.
3. Use the **Traceable Evidence Search** to locate verified sentences and page numbers matching specific research claims.

### 5.2 Reference Management
1. In the **References** tab, import existing `.bib` or `.ris` files.
2. Select any reference and click **Insert \cite** to place the citation key at your cursor position in the manuscript.

### 5.3 Comparative Literature Matrix
1. In the **Matrix** tab, click **Generate Matrix**.
2. ResearchIDE extracts Research Objectives, Methodologies, Datasets, and Key Results across all imported papers into a comparative matrix.
3. Export directly to Markdown or LaTeX table format.

---

## 6. Publication Preparation & Submission

1. On the Ribbon bar, click **Submission Packager**.
2. Select your target publisher profile (*IEEE Transactions*, *ACM SIGCONF*, *Springer Nature*, *Elsevier*).
3. Click **Run Compliance Audit** to check word limits, required sections, and figure/table captions.
4. Click **Export Complete Submission Bundle (.zip)** to generate a complete, reproducible submission archive containing your `.tex` source, `.bib` files, compiled PDF, figures, and an automated checklist.
