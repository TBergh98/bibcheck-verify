import json

import httpx
import pytest

from bibcheck.resolve.base import Reference
from bibcheck.resolve.llm import HttpMetadataExtractor, LlmConfig, LlmExtractionError, load_metadata_file


@pytest.mark.parametrize(
    ("provider", "payload"),
    [
        ("openai", {"choices": [{"message": {"content": '{"items": [{"reference_id": "0", "title": "A Paper", "authors": ["Jane Doe"], "year": 2020, "doi": null, "venue": "Journal", "queries": ["A Paper Jane Doe 2020"]}]}'}}]}),
        ("anthropic", {"content": [{"text": '{"items": [{"reference_id": "0", "title": "A Paper", "authors": ["Jane Doe"], "year": 2020, "doi": null, "venue": "Journal", "queries": ["A Paper Jane Doe 2020"]}]}' }]}),
        ("gemini", {"candidates": [{"content": {"parts": [{"text": '{"items": [{"reference_id": "0", "title": "A Paper", "authors": ["Jane Doe"], "year": 2020, "doi": null, "venue": "Journal", "queries": ["A Paper Jane Doe 2020"]}]}' }]}}]}),
    ],
)
def test_extract_batch_parses_provider_response(provider, payload):
    def handler(request):
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    extractor = HttpMetadataExtractor(LlmConfig(provider, "secret", "model", endpoint="https://llm.test"), client)

    result = extractor.extract_batch([Reference("raw")])

    assert result[0].title == "A Paper"
    assert result[0].authors == ["Jane Doe"]
    assert result[0].queries == ["A Paper Jane Doe 2020"]


def test_extract_batch_rejects_missing_reference_result():
    payload = {"choices": [{"message": {"content": json.dumps({"items": []})}}]}
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)))
    extractor = HttpMetadataExtractor(LlmConfig("openai", "secret", "model"), client)

    with pytest.raises(LlmExtractionError):
        extractor.extract_batch([Reference("raw")])


def test_load_metadata_file_requires_one_item_per_reference(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps({"items": [{"reference_id": "0", "title": "A Paper", "authors": [],
                                            "year": 2020, "doi": None, "venue": "", "queries": []}]}), encoding="utf-8")

    result = load_metadata_file(path, 1)

    assert result[0].title == "A Paper"


def test_load_metadata_file_rejects_invalid_shape(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(LlmExtractionError):
        load_metadata_file(path, 1)
