from bibcheck.graph.traverse import Graph, Node
from bibcheck.report.summary import markdown
from bibcheck.resolve.base import Reference, Resolution, VerificationStatus, Work


def _node(node_id, depth, status, reference, confidence=0.0, work=None):
    return Node(node_id, depth, reference, Resolution(reference, status, confidence, work))


def test_report_explains_results_and_uses_original_input_denominator():
    verified_reference = Reference("Original | citation", "A | Paper", ["Jane Doe"], 2020)
    missing_reference = Reference("Second citation", "Missing Paper", ["John Doe"], 2021)
    graph = Graph(
        nodes=[
            _node("0:0", 0, VerificationStatus.VERIFIED, verified_reference, 1.0,
                  Work("A Paper", ["Jane Doe"], 2020, source="crossref", doi="10.1234/example")),
            _node("0:1", 0, VerificationStatus.SUSPECTED_HALLUCINATION, missing_reference),
        ],
        input_references=3,
        requests=2,
    )

    report = markdown(graph)

    assert "**Original references:** 3" in report
    assert "**Original references with a candidate work found:** 1 / 3 (33.3%)" in report
    assert "Verified (1)" in report
    assert "Suspected hallucination (no match) (1)" in report
    assert "An exact DOI match receives **1.00**" in report
    assert "not 'proven invented'" in report
    assert "A \\| Paper" in report
    assert "10.1234/example" in report


def test_report_shows_low_confidence_reason():
    reference = Reference("Raw citation", "Candidate Paper", ["Author"], 2020)
    candidate = Work("Possible Paper", ["Different Author"], 2022, source="openalex")
    graph = Graph(
        nodes=[_node("0:0", 0, VerificationStatus.LOW_CONFIDENCE, reference, 0.42, candidate),
               _node("0:1", 0, VerificationStatus.VERIFIED_FUZZY, reference, 0.91, candidate)],
        input_references=1,
    )

    report = markdown(graph)

    assert "## Reference Details" in report
    assert "Candidate found, but metadata was incomplete or below the acceptance threshold." in report
    assert "0.42" in report
    assert "Possible Paper" in report


def test_report_warns_when_run_is_partial():
    reference = Reference("Raw citation", "Unfinished Paper", ["Author"], 2020)
    graph = Graph(
        nodes=[_node("0:0", 0, VerificationStatus.LOW_CONFIDENCE, reference)],
        partial=True,
        input_references=2,
    )

    report = markdown(graph)

    assert "**Run complete:** No" in report
    assert "This is a partial result" in report
    assert "0 / 2 (0.0%)" in report
