import re
from pathlib import Path

import bibtexparser

from bibcheck.resolve.base import Reference, extract_doi


def parse_bibtex(path: str | Path) -> list[Reference]:
    with open(path, encoding="utf-8") as stream:
        database = bibtexparser.load(stream)
    return [_entry_to_reference(entry) for entry in database.entries]


def _entry_to_reference(entry: dict[str, str]) -> Reference:
    raw = " ".join(f"{key}={value}" for key, value in entry.items())
    doi = extract_doi(entry.get("doi", "")) if entry.get("doi") else extract_doi(raw)
    authors = [part.strip() for part in re.split(r"\s+and\s+", entry.get("author", ""), flags=re.I) if part.strip()]
    year = _year(entry.get("year", ""))
    return Reference(raw_text=raw, title=_clean(entry.get("title", "")), authors=authors,
                     year=year, doi_if_present=doi, venue=_clean(entry.get("journal") or entry.get("booktitle", "")))


def _year(value: str) -> int | None:
    match = re.search(r"\b(\d{4})\b", value)
    return int(match.group(1)) if match else None


def _clean(value: str) -> str:
    return re.sub(r"[{}]", "", value or "").strip()
