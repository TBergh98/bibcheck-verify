from pathlib import Path

import pymupdf

from bibcheck.ingest.text import parse_text
from bibcheck.resolve.base import Reference


def parse_pdf(path: str | Path) -> list[Reference]:
    document = pymupdf.open(path)
    text = "\n".join(page.get_text() for page in document)
    return parse_text(text)
