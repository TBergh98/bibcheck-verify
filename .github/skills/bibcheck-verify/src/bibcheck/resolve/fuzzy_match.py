from dataclasses import dataclass

from rapidfuzz.fuzz import ratio

from .base import Reference, Work, normalize_title


@dataclass(frozen=True, slots=True)
class Match:
    accepted: bool
    score: float
    title_score: float
    author_overlap: bool
    year_close: bool


def compare(reference: Reference, work: Work, threshold: float = 0.85) -> Match:
    title_score = ratio(normalize_title(reference.title), normalize_title(work.title)) / 100
    cited_authors = set().union(*(_author_keys(author) for author in reference.authors)) if reference.authors else set()
    result_authors = set().union(*(_author_keys(author) for author in work.authors)) if work.authors else set()
    author_overlap = bool(cited_authors and result_authors and cited_authors & result_authors)
    year_close = reference.year is not None and work.year is not None and abs(reference.year - work.year) <= 1
    accepted = title_score >= threshold and author_overlap and year_close
    return Match(accepted, title_score if accepted else min(title_score, 0.84), title_score, author_overlap, year_close)


def _author_keys(value: str) -> set[str]:
    value = value.lower().replace("{", "").replace("}", "")
    parts = value.split()
    if "," in value:
        family = value.split(",", 1)[0]
    else:
        family = parts[-1] if parts else ""
    keys = {"".join(char for char in family if char.isalnum())}
    if len(parts) >= 2 and "," not in value:
        keys.add("".join(char for char in " ".join(parts[-2:]) if char.isalnum()))
    return {key for key in keys if key}
