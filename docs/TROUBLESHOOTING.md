# RESEARCHIDE TROUBLESHOOTING GUIDE
## Common Diagnostic Scenarios and Resolution Procedures

---

## 1. LaTeX Compilation Issues

### Issue: "No LaTeX compiler found on system"
- **Cause:** Neither MiKTeX nor TeX Live is installed or their bin directory is not on Windows system `PATH`.
- **Resolution:**
  1. Open ResearchIDE **Preferences** (`⚙️ Settings`).
  2. Set **Custom Compiler Directory** to your local binary folder (e.g. `E:\miktex\miktex\bin\x64` or `C:\texlive\2024\bin\windows`).
  3. Click **Save Preferences**. The compiler indicator will update to show detected engines (`pdflatex`, `xelatex`, `lualatex`).

### Issue: "Fatal compilation error: ! LaTeX Error: File `...` not found"
- **Cause:** A required LaTeX package or style file (`.sty`) is missing.
- **Resolution:**
  1. Inspect the **Compilation Diagnostics** panel at the bottom of the window to identify the missing package.
  2. If using MiKTeX, open the MiKTeX Console and install the missing package, or enable "Always install missing packages on-the-fly".
  3. Click **💡 Explain TeX Error** on the Ribbon AI tab for immediate diagnostic explanation.

---

## 2. Local Ollama AI Issues

### Issue: "Ollama status: ● Ollama Offline"
- **Cause:** The Ollama local daemon is not running on `localhost:11434`.
- **Resolution:**
  1. Open a Windows PowerShell or Command Prompt terminal.
  2. Run:
     ```powershell
     ollama serve
     ```
  3. In ResearchIDE, open the AI Assistant dock and click **🔄 Refresh**. The status indicator will turn green (`● Ollama Active`).

### Issue: "High VRAM Warning: VRAM usage exceeds 9.5 GB"
- **Cause:** A large quantized model or concurrent graphics-intensive application is consuming GPU memory.
- **Resolution:**
  1. ResearchIDE enforces a strict Single-Model Resident Policy. Switch to a lighter quantized model (e.g., `qwen2.5:7b-instruct` or `llama3.1:8b-instruct`).
  2. Unload inactive models:
     ```powershell
     ollama stop <model_name>
     ```

---

## 3. Data Integrity & Crash Recovery

### Issue: "Crash recovery: 1 uncommitted snapshot(s) detected"
- **Cause:** Windows unexpectedly restarted or the application terminated abruptly before an explicit save.
- **Resolution:**
  1. Open the project. ResearchIDE will alert you to the uncommitted snapshot.
  2. Open the document tab and click **🕒 Revisions** on the Ribbon toolbar.
  3. Inspect the diff between the recovery snapshot and your last saved file, and click **⏪ Restore This Revision** to recover all lost text.
