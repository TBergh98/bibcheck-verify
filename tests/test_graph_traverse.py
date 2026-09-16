from bibcheck.graph.cache import Cache
from bibcheck.graph.traverse import verify_references
from bibcheck.resolve.base import Reference
from bibcheck.resolve.base import Lookup, Work
from bibcheck.resolve.crossref import CrossrefResolver
from bibcheck.resolve.http import ApiClient
from bibcheck.resolve.openalex import OpenAlexResolver
from bibcheck.graph.traverse import _resolve
from bibcheck.resolve.llm import MetadataSuggestion


def test_incomplete_reference_is_kept_without_requests(tmp_path):
    client = ApiClient(max_requests=1)
    graph = verify_references([Reference("raw", title="Only title")], 1, ["openalex"], .85,
                              Cache(str(tmp_path / "cache.db")), OpenAlexResolver(client), CrossrefResolver(client))
    assert graph.nodes[0].resolution.status.value == "low_confidence"
    assert client.requests == 0


def test_request_budget_returns_partial_graph(tmp_path):
    client = ApiClient(max_requests=0)
    reference = Reference("raw", "A Paper", ["Jane Doe"], 2020)
    graph = verify_references([reference], 1, ["openalex"], .85,
                              Cache(str(tmp_path / "cache.db")), OpenAlexResolver(client), CrossrefResolver(client))
    assert graph.partial is True
    assert graph.nodes == []


def test_exact_doi_is_resolved_before_metadata_validation():
    class StubCrossref:
        def resolve_doi(self, reference):
            work = Work(title="A Paper", doi=reference.doi_if_present, year=2020)
            return Lookup("crossref", reference.doi_if_present, work, 1.0, True)

    reference = Reference("raw", doi_if_present="10.3390/v12040366")
    resolution = _resolve(reference, ["crossref"], .85, None, StubCrossref())

    assert resolution.status.value == "verified"
    assert resolution.work.title == "A Paper"

def test_llm_fallback_fills_missing_metadata_before_lookup(tmp_path):
    class StubExtractor:
        def extract_batch(self, references):
            assert len(references) == 1
            return [MetadataSuggestion("0", "A Paper", ["Jane Doe"], 2020, queries=["A Paper Jane Doe 2020"])]

    class StubOpenAlex:
        client = ApiClient(max_requests=1)

        def search(self, reference):
            assert reference.title == "A Paper"
            assert reference.metadata_source == "llm"
            return Lookup("openalex", reference.query_candidates[0], Work("A Paper", ["Jane Doe"], 2020))

    reference = Reference("raw")
    graph = verify_references([reference], 0, ["openalex"], .85, Cache(str(tmp_path / "cache.db")),
                              StubOpenAlex(), CrossrefResolver(ApiClient(max_requests=0)), StubExtractor())

    assert graph.nodes[0].resolution.status.value == "verified_fuzzy"
    assert graph.nodes[0].resolution.llm_fallback_used is True
