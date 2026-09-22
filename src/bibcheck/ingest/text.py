import re
from pathlib import Path

from bibcheck.resolve.base import Reference


def parse_text(path_or_text: str | Path) -> list[Reference]:
    text = Path(path_or_text).read_text(encoding="utf-8") if isinstance(path_or_text, Path) else path_or_text
    section = _bibliography_section(text)
    entries = _split_entries(section)
    if not entries and section.strip():
        entries = [line.strip() for line in section.splitlines() if line.strip()]
    return [Reference(raw_text=entry) for entry in entries]


def _bibliography_section(text: str) -> str:
    match = re.search(r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:references|bibliography|bibliografia)\s*:?\s*\n(.*)$", text, re.I | re.S)
    return match.group(1) if match else text


def _split_entries(section: str) -> list[str]:
    entries: list[str] = []
    current: list[str] = []
    numbered = False
    for line in section.splitlines():
        numbered_match = re.match(r"^\s*\d+\.\s*(.*)$", line)
        if numbered_match:
            numbered = True
            numbered_content = numbered_match.group(1).strip()
            if not numbered_content:
                continue
            if current:
                entries.append("\n".join(current).strip())
                current = []
            current.append(numbered_content)
            continue

        starts_reference = bool(re.match(
            r"^\s*(?![A-Z]\.\s)[^\W\d_][^\n,]*,", line
        ))
        current_text = "\n".join(current)
        starts_numbered_reference = (
            numbered
            and current
            and re.search(r"\b(?:19|20)\d{2}\b", current_text)
            and not re.match(r"^\s*\w+\s+\d{4},\s+\d+,\s+\d+\s*$", line)
            and (
                re.match(r"^\s*(?:Welfare Quality|Directive|EURCAW|EFSA Panel)", line)
                or (
                    ";" in line[:80]
                    and not re.match(r"^\s*[A-Z]\.\w*;", line)
                    and not re.search(r"\s", line.split(",", 1)[0])
                )
            )
        )
        if current and (starts_reference and _contains_doi_marker(current_text) or starts_numbered_reference):
            entries.append(current_text.strip())
            current = []
        if line.strip():
            current.append(line)
    if current:
        entries.append("\n".join(current).strip())
    return entries


def _contains_doi_marker(text: str) -> bool:
    return bool(re.search(r"\b10\.\d{4,9}/", text, re.I))


