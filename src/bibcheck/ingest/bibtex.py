from pathlib import Path

import bibtexparser

from bibcheck.resolve.base import Reference


def parse_bibtex(path: str | Path) -> list[Reference]:
    with open(path, encoding="utf-8") as stream:
        database = bibtexparser.load(stream)
    return [_entry_to_reference(entry) for entry in database.entries]


def _entry_to_reference(entry: dict[str, str]) -> Reference:
    raw = " ".join(f"{key}={value}" for key, value in entry.items())
    return Reference(raw_text=raw)
