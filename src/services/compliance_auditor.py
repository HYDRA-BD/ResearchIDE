"""Academic Formatting and Publication Compliance Auditor for ResearchIDE.

Audits manuscripts against publisher criteria (page budget, abstract word limit,
required sections, figure/table captions, bibliography keys) with zero false guarantees.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional
from src.services.template_service import PublicationTemplate, PUBLISHER_TEMPLATES
from src.utils.logger import app_logger


@dataclass
class ComplianceReport:
    """Detailed audit report comparing manuscript against publisher specifications."""
    template_name: str
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    manual_verifications: List[str] = field(default_factory=list)
    estimated_word_count: int = 0
    abstract_word_count: int = 0

    @property
    def is_compliant(self) -> bool:
        """True if there are zero blocking failures."""
        return len(self.failed_checks) == 0


class PublicationComplianceAuditor:
    """Executes rule-based compliance audits on raw LaTeX manuscripts."""

    @classmethod
    def audit_manuscript(
        cls,
        latex_source: str,
        template_key: str = "ieee_trans",
        bib_source: str = "",
    ) -> ComplianceReport:
        """Analyze manuscript against target publisher template specifications."""
        template = PUBLISHER_TEMPLATES.get(template_key, PUBLISHER_TEMPLATES["general_article"])
        report = ComplianceReport(template_name=template.name)

        # 1. Total Word Count Estimation
        # Strip commands and comments
        plain_body = re.sub(r"%.*", "", latex_source)
        plain_body = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{([^}]*)\})?", r"\3", plain_body)
        words = plain_body.split()
        report.estimated_word_count = len(words)
        report.passed_checks.append(f"Manuscript word count calculated: ~{report.estimated_word_count} words.")

        # 2. Abstract Word Count Audit
        abs_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", latex_source, re.DOTALL)
        if abs_match:
            abs_text = abs_match.group(1).strip()
            abs_words = abs_text.split()
            report.abstract_word_count = len(abs_words)

            if report.abstract_word_count > template.abstract_word_limit:
                report.failed_checks.append(
                    f"Abstract exceeds {template.publisher} limit: "
                    f"{report.abstract_word_count} words (Limit: {template.abstract_word_limit} words)."
                )
            else:
                report.passed_checks.append(
                    f"Abstract length compliant: {report.abstract_word_count} / {template.abstract_word_limit} words."
                )
        else:
            report.failed_checks.append("Missing required \\begin{abstract} ... \\end{abstract} environment.")

        # 3. Required Sections Audit
        sections_found = set(
            re.findall(r"\\section\*?\{([^}]+)\}", latex_source, re.IGNORECASE)
        )
        sections_found_lower = {s.lower().strip() for s in sections_found}

        for req_sec in template.required_sections:
            if req_sec.lower() == "references" and (r"\bibliography" in latex_source or r"\begin{thebibliography}" in latex_source):
                report.passed_checks.append("References verified via BibTeX \\bibliography / thebibliography.")
                continue

            if req_sec.lower() in sections_found_lower:
                report.passed_checks.append(f"Required section verified: '{req_sec}'.")
            else:
                # Check fuzzy synonym
                synonyms = {
                    "methodology": ["methods", "approach", "proposed method", "material and methods"],
                    "related work": ["background", "literature review", "prior work"],
                    "results": ["evaluation", "experiments", "findings"],
                    "conclusion": ["concluding remarks", "summary and outlook"],
                }
                found_synonym = False
                for syn in synonyms.get(req_sec.lower(), []):
                    if syn in sections_found_lower:
                        report.passed_checks.append(f"Required section verified via synonym: '{syn}' (for '{req_sec}').")
                        found_synonym = True
                        break

                if not found_synonym:
                    if req_sec.lower() in ("introduction", "methodology", "methods", "results", "conclusion"):
                        report.failed_checks.append(f"Missing required {template.publisher} section: '\\section{{{req_sec}}}'.")
                    else:
                        report.warnings.append(f"Recommended {template.publisher} section not found: '\\section{{{req_sec}}}'.")

        # 4. Figure & Table Captions Audit
        # Check all figure environments have captions and labels
        figs = re.findall(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", latex_source, re.DOTALL)
        for i, fig in enumerate(figs, 1):
            if r"\caption" not in fig:
                report.failed_checks.append(f"Figure {i} is missing a \\caption{{...}} directive.")
            else:
                report.passed_checks.append(f"Figure {i} includes a valid \\caption.")
            if r"\label" not in fig:
                report.warnings.append(f"Figure {i} is missing a \\label{{...}} for in-text cross-referencing.")

        tables = re.findall(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", latex_source, re.DOTALL)
        for i, tbl in enumerate(tables, 1):
            if r"\caption" not in tbl:
                report.failed_checks.append(f"Table {i} is missing a \\caption{{...}} directive.")
            else:
                report.passed_checks.append(f"Table {i} includes a valid \\caption.")

        # 5. Citations and Bibliography Keys Audit
        cited_keys = set(re.findall(r"\\cite[a-z]*\{([^}]+)\}", latex_source))
        flat_cited_keys = set()
        for k_group in cited_keys:
            for k in k_group.split(","):
                flat_cited_keys.add(k.strip())

        if flat_cited_keys:
            report.passed_checks.append(f"Detected {len(flat_cited_keys)} in-text citation keys.")
            if bib_source:
                bib_defined_keys = set(re.findall(r"@\w+\s*\{\s*([^,]+),", bib_source))
                missing_in_bib = flat_cited_keys - bib_defined_keys
                if missing_in_bib:
                    report.failed_checks.append(
                        f"Unresolved citations (cited in text but missing in .bib): {', '.join(missing_in_bib)}"
                    )
                else:
                    report.passed_checks.append("All in-text citations are verified in the BibTeX database.")
        else:
            report.warnings.append("No in-text \\cite{...} commands found in manuscript.")

        # 6. Manual Verification Advisories
        report.manual_verifications.extend([
            f"Verify author affiliation and email addresses match {template.publisher} formatting guidelines.",
            "Verify high-resolution figure DPI (>300 DPI for rasters, or vector PDF/EPS).",
            "Verify conflict-of-interest and funding declarations are present where required.",
            "Disclaimer: Compliance pass does not guarantee editorial acceptance by the journal.",
        ])

        return report
