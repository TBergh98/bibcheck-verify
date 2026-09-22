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