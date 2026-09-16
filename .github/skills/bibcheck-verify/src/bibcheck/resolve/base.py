from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    VERIFIED_FUZZY = "verified_fuzzy"
    LOW_CONFIDENCE = "low_confidence"
    NOT_INDEXED = "not_indexed"
    SUSPECTED_HALLUCINATION = "suspected_hallucination"


@dataclass(slots=True)
class Reference:
    raw_text: str
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi_if_present: str | None = None
    venue: str = ""
    query_candidates: list[str] = field(default_factory=list)
    metadata_source: str = "parser"

    @property
    def key(self) -> str:
        return normalize_doi(self.doi_if_present) or normalize_title(self.title)


@dataclass(slots=True)
class Work:
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    venue: str = ""
    source: str = ""
    source_id: str | None = None
    url: str | None = None
    referenced_works: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Lookup:
    source: str
    query: str
    matched: Work | None = None
    confidence: float = 0.0
    exact_doi: bool = False
    error: str | None = None


@dataclass(slots=True)
class Resolution:
    reference: Reference
    status: VerificationStatus
    confidence: float = 0.0
    work: Work | None = None
    lookups: list[Lookup] = field(default_factory=list)
    llm_fallback_used: bool = False


def extract_doi(value: str) -> str | None:
    match = re.search(r"10\.\d{4,9}/", value, re.I)
    if not match:
        return None

    allowed = set("-._;()/:0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    candidate: list[str] = []
    index = match.end()
    while index < len(value):
        character = value[index]
        if character in allowed:
            candidate.append(character)
            index += 1
            continue
        if not character.isspace():
            break

        next_index = index
        while next_index < len(value) and value[next_index].isspace():
            next_index += 1
        if next_index >= len(value) or value[next_index] not in allowed:
            break
        if candidate and candidate[-1] == ".":
            continuation = re.match(r"[A-Za-z]+\.", value[next_index:])
            if not continuation:
                break
        next_character = value[next_index]
        continuation = re.match(r"[A-Za-z]+\.", value[next_index:])
        if (candidate and candidate[-1] not in "/-" and next_character.isupper()
            and next_index + 1 < len(value) and value[next_index + 1].islower()
            and not continuation):
            break
        index = next_index

    return normalize_doi(match.group(0) + "".join(candidate))


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    doi = re.sub(r"\s+", "", value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.rstrip(" .;,)") or None


def normalize_title(value: str) -> str:
    return " ".join("".join(char.lower() if char.isalnum() else " " for char in value).split())


def work_to_dict(work: Work | None) -> dict[str, Any] | None:
    if work is None:
        return None
    return {"title": work.title, "authors": work.authors, "year": work.year, "doi": work.doi,
            "venue": work.venue, "source": work.source, "source_id": work.source_id,
            "url": work.url, "referenced_works": work.referenced_works}
