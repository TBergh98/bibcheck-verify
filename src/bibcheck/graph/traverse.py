from dataclasses import asdict, dataclass, field

from bibcheck.resolve.base import Reference, Resolution, VerificationStatus, Work
from bibcheck.resolve.crossref import CrossrefResolver
from bibcheck.resolve.fuzzy_match import compare
from bibcheck.resolve.http import RequestBudgetExceeded
from bibcheck.resolve.llm import LlmExtractionError, MetadataExtractor, apply_suggestion
from bibcheck.resolve.openalex import OpenAlexResolver

from .cache import Cache


@dataclass(slots=True)
class Node:
    id: str
    depth: int
    reference: Reference
    resolution: Resolution


@dataclass(slots=True)
class Edge:
    source: str
    target: str


@dataclass(slots=True)
class Graph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    partial: bool = False
    requests: int = 0
    input_references: int = 0


def verify_references(references: list[Reference], depth: int, sources: list[str], threshold: float,
                      cache: Cache, openalex: OpenAlexResolver, crossref: CrossrefResolver,
                      extractor: MetadataExtractor | None = None) -> Graph:
    graph = Graph(input_references=len(references))
    _extract_missing_metadata(references, extractor)
    queue = [(reference, 0, "root") for reference in references]
    seen: set[str] = set()
    while queue:
        reference, level, parent = queue.pop(0)
        key = reference.key or reference.raw_text.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            cached = cache.get(key)
            refresh_doi = (cached is not None and reference.doi_if_present
                           and cached.status == VerificationStatus.LOW_CONFIDENCE
                           and cached.work is None)
            resolution = _resolve(reference, sources, threshold, openalex, crossref) if refresh_doi else (
                cached or _resolve(reference, sources, threshold, openalex, crossref)
            )
        except RequestBudgetExceeded:
            graph.partial = True
            break
        cache.put(key, resolution)
        node_id = f"{level}:{len(graph.nodes)}"
        graph.nodes.append(Node(node_id, level, reference, resolution))
        if parent != "root":
            graph.edges.append(Edge(parent, node_id))
        if level >= depth or resolution.status not in (VerificationStatus.VERIFIED, VerificationStatus.VERIFIED_FUZZY) or not resolution.work:
            continue
        for cited in _children(resolution.work):
            queue.append((cited, level + 1, node_id))
    graph.requests = openalex.client.requests + crossref.client.requests
    return graph


def _resolve(reference: Reference, sources: list[str], threshold: float, openalex: OpenAlexResolver, crossref: CrossrefResolver) -> Resolution:
    lookups = []
    if reference.doi_if_present and "crossref" in sources:
        lookup = crossref.resolve_doi(reference)
        lookups.append(lookup)
        if lookup.exact_doi and lookup.matched:
            return Resolution(reference, VerificationStatus.VERIFIED, 1.0, lookup.matched, lookups,
                              reference.metadata_source == "llm")
    if not reference.title or not reference.authors or reference.year is None:
        return Resolution(reference, VerificationStatus.LOW_CONFIDENCE, lookups=lookups)
    for source in sources:
        lookup = openalex.search(reference) if source == "openalex" else crossref.search(reference)
        lookups.append(lookup)
        if lookup.matched:
            match = compare(reference, lookup.matched, threshold)
            lookup.confidence = match.score
            if match.accepted:
                return Resolution(reference, VerificationStatus.VERIFIED_FUZZY, match.score, lookup.matched, lookups,
                                  reference.metadata_source == "llm")
    if any(lookup.matched for lookup in lookups):
        return Resolution(reference, VerificationStatus.LOW_CONFIDENCE, max(item.confidence for item in lookups), lookups[-1].matched, lookups,
                          reference.metadata_source == "llm")
    return Resolution(reference, VerificationStatus.SUSPECTED_HALLUCINATION, 0.0, None, lookups,
                      reference.metadata_source == "llm")


def _extract_missing_metadata(references: list[Reference], extractor: MetadataExtractor | None) -> None:
    if extractor is None:
        return
    pending = [reference for reference in references if not reference.doi_if_present and
               (not reference.title or not reference.authors or reference.year is None)]
    if not pending:
        return
    try:
        suggestions = extractor.extract_batch(pending)
    except (LlmExtractionError, RuntimeError):
        return
    for reference, suggestion in zip(pending, suggestions):
        apply_suggestion(reference, suggestion)


def _children(work: Work) -> list[Reference]:
    return [Reference(raw_text=identifier, title=identifier, authors=["openalex"], year=work.year) for identifier in work.referenced_works]


def graph_to_dict(graph: Graph) -> dict:
    return {"partial": graph.partial, "requests": graph.requests, "input_references": graph.input_references,
            "nodes": [{"id": node.id, "depth": node.depth, "reference": asdict(node.reference),
                       "status": node.resolution.status.value, "confidence": node.resolution.confidence,
                       "work": asdict(node.resolution.work) if node.resolution.work else None,
                       "lookups": [asdict(item) for item in node.resolution.lookups],
                       "llm_fallback_used": node.resolution.llm_fallback_used} for node in graph.nodes],
            "edges": [asdict(edge) for edge in graph.edges]}
