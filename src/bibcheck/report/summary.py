from collections import Counter
from pathlib import Path

from bibcheck.graph.traverse import Graph, Node


STATUS_LABELS = {
    "verified": "Verified",
    "verified_fuzzy": "Verified (fuzzy match)",
    "low_confidence": "Low confidence",
    "not_indexed": "Not indexed",
    "suspected_hallucination": "Suspected hallucination (no match)",
}


def markdown(graph: Graph) -> str:
    input_nodes = graph.nodes
    input_total = graph.input_references or len(input_nodes)
    input_found = sum(_has_candidate(node) for node in input_nodes)
    lines = [
        "# Bibliography Verification Report",
        "",
        "This report is the human-readable result of the bibliography check. It identifies references that were matched in the consulted indexes and highlights entries that need manual review.",
        "",
        "## Executive Summary",
        "",
        f"- **Original references:** {input_total}",
        f"- **Original references checked:** {len(input_nodes)}",
        f"- **Original references with a candidate work found:** {_ratio(input_found, input_total)}",
        f"- **Network requests:** {graph.requests}",
        f"- **Run complete:** {'No - the run stopped before checking all queued references.' if graph.partial else 'Yes'}",
        "",
    ]
    if graph.partial:
        lines += [
            "> **Important:** This is a partial result. Some references may not have been checked because the request limit was reached. Do not interpret an unlisted reference as verified or missing.",
            "",
        ]

    lines += [
        "### Overall Results",
        "",
        "The table below uses **checked nodes** as its denominator. Nodes are deduplicated references in the citation graph, so this number can differ from the number of entries in the original bibliography.",
        "",
        "| Status | Count | Share of checked nodes |",
        "| --- | ---: | ---: |",
    ]
    counts = Counter(node.resolution.status.value for node in graph.nodes)
    for status in _ordered_statuses(counts):
        lines.append(f"| {_status_label(status)} | {counts[status]} | {_percent(counts[status], len(graph.nodes))} |")

    lines += [
        "",
        "## How to Read the Results",
        "",
        "### Statuses",
        "",
        "| Status | Meaning | Recommended action |",
        "| --- | --- | --- |",
        "| Verified | A reliable exact identifier match was found. | Usually no existence check is needed; still review the citation details for accuracy. |",
        "| Verified (fuzzy match) | The metadata was similar enough to an indexed work to pass the configured threshold. | Confirm that the title, authors, year, and subject are the intended work. |",
        "| Low confidence | The citation is incomplete or a possible match was too weak to accept automatically. | Compare the original citation with the candidate work manually. |",
        "| Not indexed | No result was available in the relevant indexes. | Search another catalogue or the publisher manually. |",
        "| Suspected hallucination (no match) | No candidate was returned by the consulted sources. | Treat as a priority for manual investigation, not as proof of fabrication. |",
        "",
        "### Confidence Memo",
        "",
        "Confidence is an evidence score for the automated comparison; it is not a probability that the cited work is real.",
        "",
        "- An exact DOI match receives **1.00**.",
        "- For a fuzzy comparison, the title similarity is calculated first. The candidate is accepted only when the title score reaches the configured threshold, at least one author overlaps, and the publication years differ by no more than one year.",
        "- An accepted fuzzy match reports its title similarity score as confidence.",
        "- If a candidate exists but is not accepted, the best available score is retained and the status is `low_confidence`.",
        "- Missing title, authors, or year produces `low_confidence` with confidence **0.00** and no external lookup.",
        "- If no candidate is returned, the status is `suspected_hallucination` with confidence **0.00**. This means 'not found in the consulted sources', not 'proven invented'.",
        "",
        "## Reference Details",
        "",
    ]

    for status in _ordered_statuses(counts):
        status_nodes = [node for node in graph.nodes if node.resolution.status.value == status]
        lines += [
            f"### {_status_label(status)} ({len(status_nodes)})",
            "",
            "| ID | Cited reference | Confidence | Candidate work | Evidence / next step |",
            "| --- | --- | ---: | --- | --- |",
        ]
        for node in status_nodes:
            lines.append(_node_row(node))
        lines.append("")

    lines += [
        "## Important Limitations",
        "",
        "- A successful lookup verifies that the metadata resembles an indexed work; it does not verify the claims made in the paper.",
        "- Index coverage varies by discipline, publisher, and publication type. Government reports, protocols, legal documents, and older works may be absent from Crossref or OpenAlex.",
        "- For uncertain entries, use the full original citation shown in the table and inspect `graph.json` for lookup queries and source responses.",
        "",
    ]
    return "\n".join(lines)


def write_summary(graph: Graph, path: str | Path) -> None:
    Path(path).write_text(markdown(graph), encoding="utf-8")


def _has_candidate(node: Node) -> bool:
    return node.resolution.work is not None


def _ratio(value: int, total: int) -> str:
    return f"{value} / {total} ({value / total:.1%})" if total else "0 / 0 (n/a)"


def _percent(value: int, total: int) -> str:
    return f"{value / total:.1%}" if total else "n/a"


def _ordered_statuses(counts: Counter) -> list[str]:
    order = ["verified", "verified_fuzzy", "low_confidence", "not_indexed", "suspected_hallucination"]
    return [status for status in order if status in counts]


def _status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status.replace("_", " ").title())


def _node_row(node: Node) -> str:
    reference = node.reference
    resolution = node.resolution
    work = resolution.work
    cited_title = reference.title or "Title not extracted"
    cited_authors = ", ".join(reference.authors) or "Authors not extracted"
    cited = f"**{_cell(cited_title)}**<br>{_cell(cited_authors)}"
    if reference.year is not None:
        cited += f"<br>{reference.year}"
    cited += f"<br><small>Original: {_cell(_compact(reference.raw_text))}</small>"

    if work:
        candidate = f"**{_cell(work.title or 'Title unavailable')}**<br>{_cell(_authors(work.authors))}"
        if work.year is not None:
            candidate += f"<br>{work.year}"
        candidate += f"<br><small>Source: {_cell(work.source or 'source unavailable')}</small>"
        if work.doi:
            candidate += f"<br>DOI: {_cell(work.doi)}"
        if work.url:
            candidate += f"<br><small>[link]({_link(work.url)})</small>"
    else:
        candidate = "No candidate work found"

    return f"| `{_cell(node.id)}` | {cited} | `{resolution.confidence:.2f}` | {candidate} | {_cell(_reason(node))} |"


def _reason(node: Node) -> str:
    status = node.resolution.status.value
    if status == "verified":
        return "Exact identifier match. No further existence check is usually needed."
    if status == "verified_fuzzy":
        return "Accepted fuzzy match. Confirm that the candidate is the intended work."
    if status == "low_confidence":
        if node.resolution.work:
            return "Candidate found, but metadata was incomplete or below the acceptance threshold. Review manually."
        return "Required metadata was missing, so no reliable comparison was possible."
    if status == "not_indexed":
        return "Not available in the relevant indexes. Search another catalogue."
    return "No candidate in the consulted sources. Investigate manually; this is not proof of fabrication."


def _authors(authors: list[str]) -> str:
    return ", ".join(authors) if authors else "Authors unavailable"


def _compact(value: str) -> str:
    return " ".join(value.split())


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _link(value: str) -> str:
    return value.replace(")", "%29").replace("(", "%28").replace(" ", "%20")
