"""Structured Literature Matrix & Comparative Analysis for ResearchIDE.

Compiles comparative research dimensions (Objective, Methodology, Dataset,
Results, Limitations) across imported papers and exports to Markdown and LaTeX tables.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional
from src.services.literature_service import ExtractedPaper, EvidenceSnippet


@dataclass
class MatrixRow:
    """A row in the comparative literature matrix representing one research paper."""
    title: str
    authors: str
    year: str
    objective: str = ""
    methodology: str = ""
    dataset: str = ""
    results: str = ""
    limitations: str = ""
    grounded_evidence: List[EvidenceSnippet] = field(default_factory=list)


class LiteratureMatrixGenerator:
    """Generates structured literature matrices from extracted research papers."""

    @classmethod
    def analyze_paper(cls, paper: ExtractedPaper) -> MatrixRow:
        """Extract comparative dimensions from paper text using academic heuristics."""
        full_text = " ".join(text for _, text in paper.pages)

        # 1. Authors & Year
        authors_str = ", ".join(paper.authors) if paper.authors else "Unknown Authors"
        year_str = str(paper.year) if paper.year else "n.d."

        # 2. Objective / Thesis extraction
        obj_match = re.search(
            r"(?i)\b(this paper presents|in this work, we propose|the objective of this study is|we introduce|we investigate)\s+(.*?)(?=[.!?])",
            full_text,
        )
        objective = obj_match.group(0).strip() if obj_match else (paper.abstract[:150] + "..." if paper.abstract else "Not specified")

        # 3. Methodology extraction
        method_match = re.search(
            r"(?i)\b(methodology|proposed method|our approach|experimental setup)\b[:\s\n]+(.*?)(?=[.!?])",
            full_text,
        )
        method = method_match.group(2).strip() if method_match else "Empirical evaluation"

        # 4. Dataset extraction
        dataset_match = re.search(
            r"(?i)\b(dataset|benchmark|evaluated on|trained on)\b[:\s\n]+(.*?)(?=[.!?])",
            full_text,
        )
        dataset = dataset_match.group(2).strip() if dataset_match else "Standard benchmark"

        # 5. Results extraction
        res_match = re.search(
            r"(?i)\b(results demonstrate|achieves an accuracy of|outperforms|we observe that)\s+(.*?)(?=[.!?])",
            full_text,
        )
        results = res_match.group(0).strip() if res_match else "Significant performance gain"

        # 6. Limitations extraction
        lim_match = re.search(
            r"(?i)\b(limitation|future work|however, our method|computational constraint)\s+(.*?)(?=[.!?])",
            full_text,
        )
        limitations = lim_match.group(0).strip() if lim_match else "Not explicitly stated"

        return MatrixRow(
            title=paper.title,
            authors=authors_str,
            year=year_str,
            objective=objective[:160],
            methodology=method[:140],
            dataset=dataset[:120],
            results=results[:140],
            limitations=limitations[:140],
        )

    @classmethod
    def generate_matrix(cls, papers: List[ExtractedPaper]) -> List[MatrixRow]:
        """Build matrix rows for all papers."""
        return [cls.analyze_paper(p) for p in papers]

    @classmethod
    def to_markdown(cls, rows: List[MatrixRow]) -> str:
        """Export literature matrix as a Markdown table."""
        headers = ["Paper / Authors", "Year", "Research Objective", "Methodology", "Dataset", "Key Results", "Gaps / Limitations"]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for r in rows:
            clean_title = r.title.replace("|", "-")
            clean_authors = r.authors.replace("|", "-")
            row_items = [
                f"**{clean_title}**<br>_{clean_authors}_",
                r.year,
                r.objective.replace("|", "-"),
                r.methodology.replace("|", "-"),
                r.dataset.replace("|", "-"),
                r.results.replace("|", "-"),
                r.limitations.replace("|", "-"),
            ]
            lines.append("| " + " | ".join(row_items) + " |")

        return "\n".join(lines)

    @classmethod
    def to_latex_table(cls, rows: List[MatrixRow]) -> str:
        """Export literature matrix as a professional LaTeX tabularx table."""
        out = [
            r"\begin{table*}[htbp]",
            r"\centering",
            r"\caption{Comparative Synthesis of Related Literature}",
            r"\label{tab:lit_matrix}",
            r"\begin{tabularx}{\textwidth}{|p{3cm}|p{1cm}|X|X|X|}",
            r"\hline",
            r"\textbf{Paper \& Authors} & \textbf{Year} & \textbf{Objective} & \textbf{Methodology} & \textbf{Key Findings} \\",
            r"\hline",
        ]

        for r in rows:
            safe_title = r.title.replace("&", "\\&").replace("%", "\\%")
            safe_obj = r.objective.replace("&", "\\&").replace("%", "\\%")
            safe_method = r.methodology.replace("&", "\\&").replace("%", "\\%")
            safe_results = r.results.replace("&", "\\&").replace("%", "\\%")
            out.append(
                f"{safe_title} & {r.year} & {safe_obj} & {safe_method} & {safe_results} \\\\"
            )
            out.append(r"\hline")

        out.append(r"\end{tabularx}")
        out.append(r"\end{table*}")
        return "\n".join(out)
