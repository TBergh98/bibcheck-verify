from pathlib import Path

from bibcheck.ingest.bibtex import parse_bibtex


def test_bibtex_preserves_entry_without_extracting_metadata(tmp_path: Path):
    path = tmp_path / "refs.bib"
    path.write_text('@article{x, title={A Paper}, author={Doe, Jane}, year={2020}}', encoding="utf-8")
    reference = parse_bibtex(path)[0]
    assert "title=A Paper" in reference.raw_text
    assert reference.title == ""
    assert reference.authors == []
    assert reference.year is None
    assert reference.doi_if_present is None


def test_bibtex_doi_is_left_for_llm_extraction(tmp_path: Path):
    path = tmp_path / "refs.bib"
    path.write_text(
        '@article{x, title={A Paper}, doi={10.1080/ 03079457.2012.680432}}',
        encoding="utf-8",
    )

    reference = parse_bibtex(path)[0]

    assert "10.1080/ 03079457.2012.680432" in reference.raw_text
    assert reference.doi_if_present is None
