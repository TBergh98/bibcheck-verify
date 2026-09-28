from pathlib import Path

import pytest
import typer

from bibcheck.cli import download_skill


def test_download_skill_writes_skill_file(tmp_path: Path):
    destination = tmp_path / "SKILL.md"

    download_skill(destination, False)

    assert destination.read_text(encoding="utf-8").startswith("---\nname: bibcheck-verify")


def test_download_skill_does_not_overwrite_by_default(tmp_path: Path):
    destination = tmp_path / "SKILL.md"
    destination.write_text("existing", encoding="utf-8")

    with pytest.raises(typer.BadParameter, match="destination already exists"):
        download_skill(destination, False)

    assert destination.read_text(encoding="utf-8") == "existing"

def test_verify_stops_when_sources_are_unreachable(tmp_path: Path, monkeypatch):
    import httpx
    from typer.testing import CliRunner

    from bibcheck.cli import app

    def blocked(url, **kwargs):
        raise httpx.ConnectError("blocked by proxy")

    monkeypatch.setattr(httpx, "get", blocked)
    bibliography = tmp_path / "references.bib"
    bibliography.write_text("@article{a, title={A Paper}, author={Doe, Jane}, year={2020}}\n", encoding="utf-8")
    metadata = tmp_path / "metadata.json"
    metadata.write_text('{"items": [{"reference_id": "0", "title": "A Paper", "authors": ["Jane Doe"], '
                        '"year": 2020, "doi": null, "venue": "", "queries": ["A Paper"]}]}', encoding="utf-8")
    output_dir = tmp_path / "out"

    result = CliRunner().invoke(app, ["verify", str(bibliography), "--metadata-file", str(metadata),
                                      "--output-dir", str(output_dir)])

    assert result.exit_code == 2
    assert "Cannot reach the bibliographic sources" in result.output
    assert not output_dir.exists()
