# OFFLINE OPERATION & AIR-GAPPED WORKFLOW GUIDE
## Operating ResearchIDE in Disconnected and High-Security Environments

---

## 1. Zero Cloud Dependency Architecture
ResearchIDE is engineered from the ground up for strict local-first autonomy:
- **No Cloud API Requirements:** Document editing, Concrete Syntax Tree parsing, LaTeX compilation, vector indexing, and AI inference execute 100% locally on your workstation.
- **Air-Gapped Operation:** All features operate identically whether connected to the internet or completely air-gapped.

---

## 2. Setting Up an Air-Gapped Workstation

### 2.1 Pre-Requisite Local Assets
Before disconnecting from external networks, ensure the following are installed locally:
1. **Python 3.11+ Runtime:** Installed to standard local path.
2. **Local TeX Distribution:** MiKTeX or TeX Live installed with complete academic package sets (`amsmath`, `graphicx`, `tabularx`, `cite`, `booktabs`, `IEEEtran`, `acmart`, `sn-jnl`, `elsarticle`).
3. **Local Ollama Executable:** Downloaded and installed from `ollama.com`.
4. **Quantized Model Weights:** Pull desired academic models into local storage:
   ```powershell
   ollama pull qwen2.5:14b
   ollama pull llama3.1:8b
   ```

---

## 3. Verifying Fully Disconnected Operation

To verify that your installation operates without internet:
1. Disconnect Wi-Fi and Ethernet on your Windows workstation.
2. Launch ResearchIDE: `python src/main.py`.
3. Verify that:
   - Creating, opening, and saving projects succeeds.
   - LaTeX compilation (`Ctrl+B`) compiles PDF via local `pdflatex.exe`.
   - PDF preview and SyncTeX navigation operate normally.
   - Local AI Assistant streams responses from local Ollama daemon.
   - PDF text extraction, evidence search, and literature matrices function cleanly.
   - Packaging submission bundles exports `.zip` archives.
4. Optional features that gracefully notify when offline:
   - DOI online metadata lookups (reports network unavailable without crashing).
