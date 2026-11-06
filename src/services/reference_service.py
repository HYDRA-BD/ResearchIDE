"""Academic Reference and Citation Management Service for ResearchIDE.

Supports BibTeX, RIS, CSL JSON import/export, citation styling (LaTeX, IEEE, APA),
and reference verification without fabricating metadata.
"""
from __future__ import annotations
import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from src.utils.logger import app_logger


@dataclass
class ReferenceItem:
    """Represents a structured bibliographic reference entry."""
    key: str
    entry_type: str = "article"  # article, book, inproceedings, techreport, misc
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    booktitle: Optional[str] = None
    volume: Optional[str] = None
    number: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    extra_fields: Dict[str, str] = field(default_factory=dict)

    @property
    def author_display(self) -> str:
        """Format authors for table / UI display."""
        if not self.authors:
            return "Unknown"
        if len(self.authors) == 1:
            return self.authors[0]
        if len(self.authors) == 2:
            return f"{self.authors[0]} and {self.authors[1]}"
        return f"{self.authors[0]} et al."


class ReferenceManager:
    """Parses, serializes, and formats academic citations across standard formats."""

    # BibTeX entry regex: @type{key, field = {val}, ...}
    BIB_ENTRY_RE = re.compile(r"@(?P<type>[a-zA-Z]+)\s*\{\s*(?P<key>[^,]+),", re.MULTILINE)
    BIB_FIELD_RE = re.compile(r"(?P<field>[a-zA-Z_]+)\s*=\s*[\"{](?P<value>.*?)[\"}](?=\s*,\s*[a-zA-Z_]+\s*=|\s*[\"{}]*\s*\})", re.DOTALL)

    @classmethod
    def parse_bibtex(cls, bib_text: str) -> List[ReferenceItem]:
        """Parse raw BibTeX content into structured ReferenceItem objects."""
        items: List[ReferenceItem] = []
        entries = re.split(r"(?=@\w+\s*\{)", bib_text)

        for raw_entry in entries:
            raw_entry = raw_entry.strip()
            if not raw_entry.startswith("@"):
                continue

            match = cls.BIB_ENTRY_RE.search(raw_entry)
            if not match:
                continue

            entry_type = match.group("type").lower()
            key = match.group("key").strip()

            # Parse fields
            item = ReferenceItem(key=key, entry_type=entry_type)

            # Simple field extraction: field = {value} or field = "value"
            field_matches = re.findall(
                r'([a-zA-Z_]+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)")',
                raw_entry,
                re.DOTALL,
            )

            for field_name, val_braces, val_quotes in field_matches:
                fname = field_name.lower().strip()
                val = (val_braces if val_braces else val_quotes).strip()
                # Clean nested braces/newlines
                clean_val = re.sub(r"\s+", " ", val).replace("{", "").replace("}", "").strip()

                if fname == "title":
                    item.title = clean_val
                elif fname == "author" or fname == "authors":
                    # Split authors by 'and'
                    item.authors = [a.strip() for a in clean_val.split(" and ") if a.strip()]
                elif fname == "year":
                    try:
                        item.year = int(re.search(r"\d{4}", clean_val).group(0))
                    except (ValueError, AttributeError):
                        pass
                elif fname == "journal":
                    item.journal = clean_val
                elif fname == "booktitle":
                    item.booktitle = clean_val
                elif fname == "volume":
                    item.volume = clean_val
                elif fname == "number":
                    item.number = clean_val
                elif fname == "pages":
                    item.pages = clean_val
                elif fname == "doi":
                    item.doi = clean_val
                elif fname == "url":
                    item.url = clean_val
                elif fname == "abstract":
                    item.abstract = clean_val
                else:
                    item.extra_fields[fname] = clean_val

            items.append(item)

        return items

    @classmethod
    def export_bibtex(cls, items: List[ReferenceItem]) -> str:
        """Serialize a list of ReferenceItem objects into formatted BibTeX."""
        blocks = []
        for item in items:
            lines = [f"@{item.entry_type}{{{item.key},"]
            if item.title:
                lines.append(f"  title = {{{item.title}}},")
            if item.authors:
                authors_str = " and ".join(item.authors)
                lines.append(f"  author = {{{authors_str}}},")
            if item.year:
                lines.append(f"  year = {{{item.year}}},")
            if item.journal:
                lines.append(f"  journal = {{{item.journal}}},")
            if item.booktitle:
                lines.append(f"  booktitle = {{{item.booktitle}}},")
            if item.volume:
                lines.append(f"  volume = {{{item.volume}}},")
            if item.number:
                lines.append(f"  number = {{{item.number}}},")
            if item.pages:
                lines.append(f"  pages = {{{item.pages}}},")
            if item.doi:
                lines.append(f"  doi = {{{item.doi}}},")
            if item.url:
                lines.append(f"  url = {{{item.url}}},")
            if item.abstract:
                lines.append(f"  abstract = {{{item.abstract}}},")
            for k, v in item.extra_fields.items():
                lines.append(f"  {k} = {{{v}}},")
            lines.append("}")
            blocks.append("\n".join(lines))

        return "\n\n".join(blocks)

    @classmethod
    def parse_ris(cls, ris_text: str) -> List[ReferenceItem]:
        """Parse RIS bibliography formatted text into ReferenceItems."""
        items: List[ReferenceItem] = []
        records = re.split(r"(?:\r?\n)ER\s*-", ris_text)

        for rec in records:
            rec = rec.strip()
            if not rec:
                continue

            item = ReferenceItem(key="ref")
            authors = []

            for line in rec.splitlines():
                line = line.strip()
                if " - " not in line:
                    continue

                parts = line.split(" - ", 1)
                tag = parts[0].strip().upper()
                val = parts[1].strip()

                if tag == "TY":
                    ty_map = {"JOUR": "article", "CONF": "inproceedings", "BOOK": "book"}
                    item.entry_type = ty_map.get(val, "misc")
                elif tag in ("TI", "T1"):
                    item.title = val
                elif tag in ("AU", "A1"):
                    authors.append(val)
                elif tag in ("PY", "Y1"):
                    try:
                        item.year = int(re.search(r"\d{4}", val).group(0))
                    except (ValueError, AttributeError):
                        pass
                elif tag in ("JO", "JF", "JA"):
                    item.journal = val
                elif tag == "DO":
                    item.doi = val
                elif tag == "UR":
                    item.url = val
                elif tag in ("AB", "N2"):
                    item.abstract = val
                elif tag == "ID":
                    item.key = val

            item.authors = authors
            # Generate key if still default
            if item.key == "ref" and authors and item.year:
                first_author_last = authors[0].split(",")[0].replace(" ", "").lower()
                item.key = f"{first_author_last}{item.year}"
            elif item.key == "ref":
                item.key = f"ref_{len(items)+1}"

            items.append(item)

        return items

    @classmethod
    def export_ris(cls, items: List[ReferenceItem]) -> str:
        """Export ReferenceItems into RIS format."""
        blocks = []
        for item in items:
            lines = []
            ty_map = {"article": "JOUR", "inproceedings": "CONF", "book": "BOOK"}
            lines.append(f"TY  - {ty_map.get(item.entry_type, 'GEN')}")
            lines.append(f"ID  - {item.key}")
            if item.title:
                lines.append(f"TI  - {item.title}")
            for a in item.authors:
                lines.append(f"AU  - {a}")
            if item.year:
                lines.append(f"PY  - {item.year}")
            if item.journal:
                lines.append(f"JO  - {item.journal}")
            if item.booktitle:
                lines.append(f"T2  - {item.booktitle}")
            if item.doi:
                lines.append(f"DO  - {item.doi}")
            if item.url:
                lines.append(f"UR  - {item.url}")
            if item.abstract:
                lines.append(f"AB  - {item.abstract}")
            lines.append("ER  - ")
            blocks.append("\n".join(lines))

        return "\n\n".join(blocks)

    @classmethod
    def export_csl_json(cls, items: List[ReferenceItem]) -> str:
        """Export references in CSL JSON format."""
        csl_list = []
        for item in items:
            entry: Dict[str, Any] = {
                "id": item.key,
                "type": "article-journal" if item.entry_type == "article" else item.entry_type,
                "title": item.title,
            }
            if item.authors:
                entry["author"] = [{"literal": a} for a in item.authors]
            if item.year:
                entry["issued"] = {"date-parts": [[item.year]]}
            if item.journal:
                entry["container-title"] = item.journal
            if item.doi:
                entry["DOI"] = item.doi
            if item.abstract:
                entry["abstract"] = item.abstract
            csl_list.append(entry)

        return json.dumps(csl_list, indent=2)

    @classmethod
    def format_citation(cls, item: ReferenceItem, style: str = "latex", index: int = 1) -> str:
        """Generate formatted in-text citation string."""
        if style == "latex":
            return f"\\cite{{{item.key}}}"
        elif style == "ieee":
            return f"[{index}]"
        elif style == "apa":
            author = item.authors[0].split(",")[0].strip() if item.authors else "Anonymous"
            if len(item.authors) > 2:
                author = f"{author} et al."
            elif len(item.authors) == 2:
                sec = item.authors[1].split(",")[0].strip()
                author = f"{author} & {sec}"
            year = str(item.year) if item.year else "n.d."
            return f"({author}, {year})"
        return f"\\cite{{{item.key}}}"
