"""Academic Publication Template Profiles & Migrator for ResearchIDE.

Supports official publisher styles (IEEE, ACM, Springer, Elsevier, APA)
and non-destructively migrates manuscripts between formatting profiles.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from src.utils.logger import app_logger


@dataclass
class PublicationTemplate:
    """Metadata and LaTeX configuration for an academic publisher template."""
    key: str
    name: str
    publisher: str
    documentclass: str
    column_count: int = 1
    max_pages: Optional[int] = None
    abstract_word_limit: int = 250
    required_packages: List[str] = field(default_factory=list)
    bibstyle: str = "plain"
    required_sections: List[str] = field(default_factory=list)
    description: str = ""


# Master Catalog of Publication Templates
PUBLISHER_TEMPLATES: Dict[str, PublicationTemplate] = {
    "ieee_trans": PublicationTemplate(
        key="ieee_trans",
        name="IEEE Transactions & Conferences",
        publisher="IEEE",
        documentclass=r"\documentclass[journal,10pt,twocolumn]{IEEEtran}",
        column_count=2,
        max_pages=10,
        abstract_word_limit=200,
        required_packages=["amsmath", "cite", "graphicx", "tabularx"],
        bibstyle="IEEEtran",
        required_sections=["Introduction", "Related Work", "Methodology", "Results", "Conclusion", "References"],
        description="Standard 2-column layout for IEEE Transactions, Journals, and Conferences.",
    ),
    "acm_sigconf": PublicationTemplate(
        key="acm_sigconf",
        name="ACM Conference Proceedings (acmart)",
        publisher="ACM",
        documentclass=r"\documentclass[sigconf,screen]{acmart}",
        column_count=2,
        max_pages=12,
        abstract_word_limit=250,
        required_packages=["amsmath", "graphicx", "booktabs"],
        bibstyle="ACM-Reference-Format",
        required_sections=["Introduction", "Background", "Design", "Evaluation", "Discussion", "Conclusion"],
        description="Standard double-column template for ACM flagship conferences and workshops.",
    ),
    "springer_sn": PublicationTemplate(
        key="springer_sn",
        name="Springer Nature (sn-jnl)",
        publisher="Springer Nature",
        documentclass=r"\documentclass[default,sn-mathphys-num]{sn-jnl}",
        column_count=1,
        max_pages=25,
        abstract_word_limit=250,
        required_packages=["amsmath", "graphicx", "bm"],
        bibstyle="sn-mathphys-num",
        required_sections=["Introduction", "Methods", "Results", "Discussion", "Conclusion"],
        description="Standard single-column submission style for Springer Nature journals.",
    ),
    "elsevier_cas": PublicationTemplate(
        key="elsevier_cas",
        name="Elsevier Standard (elsarticle)",
        publisher="Elsevier",
        documentclass=r"\documentclass[preprint,12pt]{elsarticle}",
        column_count=1,
        max_pages=30,
        abstract_word_limit=300,
        required_packages=["amsmath", "amssymb", "graphicx"],
        bibstyle="elsarticle-num",
        required_sections=["Introduction", "Material and Methods", "Results and Discussion", "Conclusion"],
        description="Standard Elsevier manuscript format suitable for peer-review submissions.",
    ),
    "general_article": PublicationTemplate(
        key="general_article",
        name="General Academic Preprint (article)",
        publisher="Independent / arXiv",
        documentclass=r"\documentclass[11pt,a4paper]{article}",
        column_count=1,
        max_pages=None,
        abstract_word_limit=350,
        required_packages=["amsmath", "amssymb", "graphicx", "hyperref"],
        bibstyle="plain",
        required_sections=["Introduction", "Conclusion"],
        description="Clean, portable LaTeX article layout for preprints, theses, and technical reports.",
    ),
}


class TemplateMigrator:
    """Non-destructively migrates manuscripts between publication template profiles."""

    @classmethod
    def apply_template(cls, raw_latex: str, target_template_key: str) -> str:
        """Switch manuscript documentclass and header packages without disturbing content."""
        template = PUBLISHER_TEMPLATES.get(target_template_key)
        if not template:
            app_logger.warning(f"Template '{target_template_key}' not found; preserving original.")
            return raw_latex

        # 1. Replace or insert \documentclass
        doc_class_re = re.compile(r"\\documentclass(\[[^\]]*\])?\{[^}]+\}")
        if doc_class_re.search(raw_latex):
            updated_latex = doc_class_re.sub(lambda _: template.documentclass, raw_latex, count=1)
        else:
            updated_latex = f"{template.documentclass}\n{raw_latex}"

        # 2. Ensure required packages exist in preamble
        begin_doc_pos = updated_latex.find(r"\begin{document}")
        if begin_doc_pos != -1:
            preamble = updated_latex[:begin_doc_pos]
            body = updated_latex[begin_doc_pos:]

            for pkg in template.required_packages:
                pkg_pattern = rf"\\usepackage(\[[^\]]*\])?\{{{pkg}\}}"
                if not re.search(pkg_pattern, preamble):
                    preamble += f"\\usepackage{{{pkg}}}\n"

            # 3. Update \bibliographystyle if present in body
            bibstyle_re = re.compile(r"\\bibliographystyle\{[^}]+\}")
            if bibstyle_re.search(body):
                body = bibstyle_re.sub(lambda _: f"\\bibliographystyle{{{template.bibstyle}}}", body)

            return preamble + body

        return updated_latex
