from bibcheck.graph.cache import Cache
from bibcheck.resolve.base import Lookup, Reference, Resolution, VerificationStatus, Work


def test_cache_round_trip_preserves_lookup_match(tmp_path):
    reference = Reference("raw", "A Paper", ["Jane Doe"], 2020)
    work = Work(title="A Paper", authors=["Jane Doe"], year=2020, source="crossref")
    resolution = Resolution(reference, VerificationStatus.VERIFIED_FUZZY, .95, work,
                            [Lookup("crossref", "A Paper", work, .95)])
    cache = Cache(str(tmp_path / "cache.db"))
    cache.put(reference.key, resolution)
    restored = cache.get(reference.key)
    assert restored is not None
    assert restored.lookups[0].matched.title == "A Paper"