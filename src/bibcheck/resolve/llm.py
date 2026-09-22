from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Protocol

import httpx

from .base import Reference, extract_doi


@dataclass(slots=True)
class MetadataSuggestion:
    reference_id: str
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    venue: str = ""
    queries: list[str] = field(default_factory=list)


class MetadataExtractor(Protocol):
    def extract_batch(self, references: list[Reference]) -> list[MetadataSuggestion]: ...


class LlmExtractionError(RuntimeError):
    pass


def apply_suggestion(reference: Reference, suggestion: MetadataSuggestion, source: str = "llm") -> None:
    reference.title = suggestion.title
    reference.authors = suggestion.authors
    reference.year = suggestion.year
    reference.doi_if_present = suggestion.doi
    reference.venue = suggestion.venue
    reference.query_candidates = list(dict.fromkeys(suggestion.queries))
    reference.metadata_source = source


def load_metadata_file(path: str | Path, expected: int) -> list[MetadataSuggestion]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return _parse_suggestions(json.dumps(payload), expected)
    except (OSError, UnicodeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LlmExtractionError(f"cannot read metadata file: {path}") from exc


@dataclass(slots=True)
class LlmConfig:
    provider: str
    api_key: str
    model: str
    timeout: float = 30.0
    endpoint: str | None = None


class HttpMetadataExtractor:
    def __init__(self, config: LlmConfig, client: httpx.Client | None = None):
        self.config = config
        self.client = client or httpx.Client(timeout=config.timeout)

    def extract_batch(self, references: list[Reference]) -> list[MetadataSuggestion]:
        if not references:
            return []
        endpoint, options = self._request(references)
        response = self.client.post(endpoint, **options)
        response.raise_for_status()
        return _parse_suggestions(_response_text(self.config.provider, response.json()), len(references))

    def _request(self, references: list[Reference]) -> tuple[str, dict[str, Any]]:
        prompt = _prompt(references)
        provider = self.config.provider.lower()
        if provider == "openai":
            endpoint = self.config.endpoint or "https://api.openai.com/v1/chat/completions"
            return endpoint, {
                "headers": {"Authorization": f"Bearer {self.config.api_key}"},
                "json": {"model": self.config.model, "temperature": 0, "response_format": {"type": "json_object"},
                         "messages": [{"role": "system", "content": _SYSTEM_PROMPT}, {"role": "user", "content": prompt}]},
            }
        if provider in {"anthropic", "claude"}:
            endpoint = self.config.endpoint or "https://api.anthropic.com/v1/messages"
            return endpoint, {
                "headers": {"x-api-key": self.config.api_key, "anthropic-version": "2023-06-01"},
                "json": {"model": self.config.model, "max_tokens": 4096, "temperature": 0,
                         "system": _SYSTEM_PROMPT, "messages": [{"role": "user", "content": prompt}]},
            }
        if provider in {"gemini", "google"}:
            endpoint = self.config.endpoint or f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent"
            return endpoint, {
                "params": {"key": self.config.api_key},
                "json": {"generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
                         "systemInstruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
                         "contents": [{"role": "user", "parts": [{"text": prompt}]}]},
            }
        raise LlmExtractionError(f"unsupported LLM provider: {self.config.provider}")


_SYSTEM_PROMPT = """Extract bibliographic metadata from each citation. Return JSON only with an 'items' array.
Each item must contain reference_id, title, authors, year, doi, venue, and queries.
Use only information present in the citation. Use an empty string/list or null when unknown.
reference_id must be copied exactly. queries must contain useful search strings, never invented identifiers."""


def _prompt(references: list[Reference]) -> str:
    items = [{"reference_id": str(index), "citation": reference.raw_text} for index, reference in enumerate(references)]
    return json.dumps({"references": items}, ensure_ascii=True)


def _response_text(provider: str, payload: dict[str, Any]) -> str:
    provider = provider.lower()
    if provider == "openai":
        return payload["choices"][0]["message"]["content"]
    if provider in {"anthropic", "claude"}:
        return payload["content"][0]["text"]
    if provider in {"gemini", "google"}:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    raise LlmExtractionError(f"unsupported LLM provider: {provider}")


def _parse_suggestions(text: str, expected: int) -> list[MetadataSuggestion]:
    try:
        payload = json.loads(text)
        items = payload["items"]
        if not isinstance(items, list):
            raise TypeError("items is not an array")
        suggestions = [_suggestion(item) for item in items]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LlmExtractionError("LLM returned invalid metadata JSON") from exc
    ids = [item.reference_id for item in suggestions]
    expected_ids = [str(index) for index in range(expected)]
    if len(suggestions) != expected or ids != expected_ids:
        raise LlmExtractionError("LLM response does not contain exactly one item per reference")
    return suggestions


def _suggestion(item: Any) -> MetadataSuggestion:
    if not isinstance(item, dict) or not isinstance(item.get("reference_id"), str):
        raise TypeError("invalid suggestion")
    year = item.get("year")
    if year is not None and not isinstance(year, int):
        raise TypeError("year is not an integer")
    authors = item.get("authors", [])
    queries = item.get("queries", [])
    if not isinstance(authors, list) or not all(isinstance(value, str) for value in authors):
        raise TypeError("authors is not a string array")
    if not isinstance(queries, list) or not all(isinstance(value, str) for value in queries):
        raise TypeError("queries is not a string array")
    doi = item.get("doi")
    if doi is not None and not isinstance(doi, str):
        raise TypeError("doi is not a string")
    return MetadataSuggestion(
        reference_id=item["reference_id"], title=_string(item.get("title")), authors=authors,
        year=year, doi=extract_doi(doi or ""), venue=_string(item.get("venue")), queries=queries,
    )


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""
