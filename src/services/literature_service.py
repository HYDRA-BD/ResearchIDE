"""Local Research PDF Extraction & Evidence Traceability Service for ResearchIDE.

Extracts text, metadata, and per-page content chunks using PyPDF.
Ensures every extracted research claim is grounded in an exact page snippet.
"""
from __future__ import annotations
import re
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import pypdf
from src.utils.logger import app_logger


@dataclass
class EvidenceSnippet:
    """Verifiable snippet linking an extracted scientific claim to its source page."""
    snippet_id: str
    paper_id: str
    file_name: str
    page_number: int  # 1-indexed
    quote: str
    section_context: str = ""

    def __str__(self) -> str:
        return f"[{self.file_name}, p. {self.page_number}]: \"{self.quote}\""


@dataclass
class ExtractedPaper:
    """Structured representation of an imported academic research paper."""
    paper_id: str
    file_path: Path
    title: str = "Untitled Paper"
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: str = ""
    pages: List[Tuple[int, str]] = field(default_factory=list)  # (page_num, page_text)
    extracted_references: List[str] = field(default_factory=list)

    @property
    def total_pages(self) -> int:
        return len(self.pages)


class PDFExtractorService:
    """Extracts text, metadata, and references from local research PDFs."""

    DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
    YEAR_PATTERN = re.compile(r"\b(19\d\d|20\d\d)\b")

    @classmethod
    def extract_from_pdf(cls, pdf_path: Path) -> ExtractedPaper:
        """Parse a local PDF file and extract pages, metadata, and evidence."""
        pdf_path = Path(pdf_path).resolve()
        paper_id = str(uuid.uuid4())
        paper = ExtractedPaper(paper_id=paper_id, file_path=pdf_path)

        if not pdf_path.exists():
            app_logger.warning(f"PDF file '{pdf_path}' does not exist.")
            return paper

        try:
            reader = pypdf.PdfReader(str(pdf_path))
            # 1. Read metadata dictionary if present
            meta = reader.metadata or {}
            doc_title = meta.get("/Title")
            if doc_title and doc_title.strip() and not doc_title.strip().startswith("untitled"):
                paper.title = str(doc_title).strip()
            else:
                paper.title = pdf_path.stem.replace("_", " ").title()

            doc_author = meta.get("/Author")
            if doc_author and str(doc_author).strip():
                paper.authors = [str(doc_author).strip()]

            # 2. Extract page-by-page text
            full_text_accum = []
            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    app_logger.debug(f"Failed extracting text from page {page_num}: {e}")
                    text = ""

                paper.pages.append((page_num, text))
                full_text_accum.append(text)

            combined_text = "\n".join(full_text_accum)

            # 3. Extract DOI from text if not in metadata
            doi_match = cls.DOI_PATTERN.search(combined_text)
            if doi_match:
                paper.doi = doi_match.group(0)

            # 4. Extract publication year heuristic
            year_matches = cls.YEAR_PATTERN.findall(combined_text[:2000])
            if year_matches:
                paper.year = int(year_matches[0])

            # 5. Extract Abstract snippet heuristic
            abstract_match = re.search(
                r"(?i)\babstract[:\s\n]+(.*?)(?=\b(introduction|keywords|index terms|1\.\s+introduction)\b)",
                combined_text[:5000],
                re.DOTALL,
            )
            if abstract_match:
                raw_abs = abstract_match.group(1).strip()
                paper.abstract = re.sub(r"\s+", " ", raw_abs)

            # 6. Extract references list heuristic from last pages
            refs_match = re.search(r"(?i)\breferences\b\s*\n+(.*)", combined_text, re.DOTALL)
            if refs_match:
                raw_refs = refs_match.group(1).strip()
                ref_entries = re.split(r"\n(?=\[\d+\]|\d+\.\s+)", raw_refs)
                paper.extracted_references = [re.sub(r"\s+", " ", r).strip() for r in ref_entries[:30] if r.strip()]

            app_logger.info(
                f"Successfully parsed PDF '{pdf_path.name}': {paper.total_pages} pages, DOI: {paper.doi}"
            )
            return paper

        except Exception as e:
            app_logger.error(f"Error parsing PDF '{pdf_path.name}': {e}")
            return paper

    @classmethod
    def find_evidence(cls, paper: ExtractedPaper, query: str, max_snippets: int = 5) -> List[EvidenceSnippet]:
        """Search page text for evidence matching a query or claim.
        
        Guarantees strict source grounding: returns exact sentence snippets with page numbers.
        """
        snippets: List[EvidenceSnippet] = []
        clean_query = query.lower().strip()
        query_words = [w for w in clean_query.split() if len(w) > 3]

        if not query_words:
            return snippets

        for page_num, text in paper.pages:
            # Split page text into sentences
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
                sent_clean = sentence.strip()
                if len(sent_clean) < 30:
                    continue

                sent_lower = sent_clean.lower()
                # Score sentence by query word hits
                hits = sum(1 for w in query_words if w in sent_lower)
                if hits >= 2 or (len(query_words) == 1 and hits == 1):
                    snippet = EvidenceSnippet(
                        snippet_id=str(uuid.uuid4())[:8],
                        paper_id=paper.paper_id,
                        file_name=paper.file_path.name,
                        page_number=page_num,
                        quote=sent_clean,
                        section_context=f"Page {page_num}",
                    )
                    snippets.append(snippet)
                    if len(snippets) >= max_snippets:
                        return snippets

        return snippets
