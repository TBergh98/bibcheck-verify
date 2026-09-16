from pathlib import Path

from bibcheck.ingest.bibtex import parse_bibtex


def test_bibtex_missing_fields(tmp_path: Path):
    path = tmp_path / "refs.bib"
    path.write_text('@article{x, title={A Paper}, author={Doe, Jane}, year={2020}}', encoding="utf-8")
    reference = parse_bibtex(path)[0]
    assert reference.title == "A Paper"
    assert reference.year == 2020
    assert reference.doi_if_present is None


def test_bibtex_doi_with_internal_spaces(tmp_path: Path):
    path = tmp_path / "refs.bib"
    path.write_text(
        '@article{x, title={A Paper}, doi={10.1080/ 03079457.2012.680432}}',
        encoding="utf-8",
    )

    reference = parse_bibtex(path)[0]

    assert reference.doi_if_present == "10.1080/03079457.2012.680432"
