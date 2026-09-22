from pathlib import Path
import os
from importlib.resources import files
from importlib.metadata import files as distribution_files

import typer
from dotenv import load_dotenv

from bibcheck.graph.cache import Cache
from bibcheck import __version__
from bibcheck.graph.traverse import verify_references
from bibcheck.ingest import parse_bibtex, parse_pdf, parse_text
from bibcheck.report.json_graph import write_json
from bibcheck.report.summary import write_summary
from bibcheck.resolve.crossref import CrossrefResolver
from bibcheck.resolve.http import ApiClient
from bibcheck.resolve.openalex import OpenAlexResolver
from bibcheck.resolve.llm import HttpMetadataExtractor, LlmConfig, LlmExtractionError, apply_suggestion, load_metadata_file

app = typer.Typer(no_args_is_help=True)
skill_app = typer.Typer(no_args_is_help=True)
app.add_typer(skill_app, name="skill")
load_dotenv()


@app.command()
def version() -> None:
    typer.echo(f"bibcheck-verify {__version__}")


@skill_app.command("download")
def download_skill(output: Path | None = typer.Option(None, "--output", "-o"),
                   force: bool = typer.Option(False, "--force", help="Overwrite an existing file.")) -> None:
    """Copy the skill instructions to the user's download directory."""
    destination = output or _download_directory() / "bibcheck-verify-SKILL.md"
    if destination.exists() and not force:
        raise typer.BadParameter(f"destination already exists: {destination}; use --force to overwrite")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        skill_path = files("bibcheck").joinpath("skill/SKILL.md")
        destination.write_text(skill_path.read_text(encoding="utf-8"), encoding="utf-8")
    except FileNotFoundError:
        source_path = next(
            (file.locate() for file in distribution_files("bibcheck-verify") or []
             if str(file).replace("\\", "/").endswith("bibcheck/skill/SKILL.md")),
            Path(__file__).parents[2] / ".github" / "skills" / "bibcheck-verify" / "SKILL.md",
        )
        if not source_path.is_file():
            raise typer.BadParameter("packaged skill instructions are unavailable") from None
        destination.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    typer.echo(f"Downloaded skill to: {destination}")
    typer.echo("Copy this file as SKILL.md inside your provider's skill directory.")


def _download_directory() -> Path:
    downloads = Path.home() / "Downloads"
    return downloads if downloads.is_dir() else Path.home()


@app.command("verify")
def verify(input_file: Path, depth: int = typer.Option(0, min=0), sources: str = typer.Option("openalex,crossref"),
           confidence_threshold: float = typer.Option(0.85, min=0.0, max=1.0),
           max_requests: int = typer.Option(2000, min=0), output_dir: Path = typer.Option(Path("./bibcheck-verify-results")),
           mailto: str | None = typer.Option(None),
           llm_provider: str | None = typer.Option(None, envvar="BIBCHECK_VERIFY_LLM_PROVIDER"),
           llm_model: str | None = typer.Option(None, envvar="BIBCHECK_VERIFY_LLM_MODEL"),
           metadata_file: Path | None = typer.Option(None, help="JSON metadata produced by a skill or another extractor.")) -> None:
    if not input_file.is_file():
        raise typer.BadParameter(f"input file not found: {input_file}")
    if metadata_file and llm_provider:
        raise typer.BadParameter("use either --metadata-file or --llm-provider, not both")
    if not metadata_file and not llm_provider:
        raise typer.BadParameter("provide either --metadata-file or --llm-provider")
    suffix = input_file.suffix.lower()
    references = parse_bibtex(input_file) if suffix == ".bib" else parse_pdf(input_file) if suffix == ".pdf" else parse_text(input_file)
    selected = [source.strip() for source in sources.split(",") if source.strip() in {"openalex", "crossref"}]
    if not selected:
        raise typer.BadParameter("sources must contain openalex or crossref")
    output_dir.mkdir(parents=True, exist_ok=True)
    client = ApiClient(max_requests=max_requests, mailto=mailto)
    cache = Cache(str(output_dir / "cache.sqlite3"))
    if metadata_file:
        try:
            suggestions = load_metadata_file(metadata_file, len(references))
        except LlmExtractionError as exc:
            raise typer.BadParameter(str(exc)) from exc
        for reference, suggestion in zip(references, suggestions):
            apply_suggestion(reference, suggestion, source="skill")
    extractor = _llm_extractor(llm_provider, llm_model)
    graph = verify_references(references, depth, selected, confidence_threshold, cache,
                              OpenAlexResolver(client), CrossrefResolver(client), extractor)
    write_json(graph, output_dir / "graph.json")
    write_summary(graph, output_dir / "summary.md")
    typer.echo(f"Verified {len(references)} references; wrote {output_dir}")


def _llm_extractor(provider: str | None, model: str | None) -> HttpMetadataExtractor | None:
    if not provider:
        return None
    provider = provider.lower()
    key_names = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "claude": "ANTHROPIC_API_KEY",
                 "gemini": "GEMINI_API_KEY", "google": "GEMINI_API_KEY"}
    api_key = os.getenv(key_names.get(provider, ""))
    if not api_key:
        raise typer.BadParameter(f"missing API key for LLM provider {provider}")
    defaults = {"openai": "gpt-4o-mini", "anthropic": "claude-3-5-haiku-latest", "claude": "claude-3-5-haiku-latest",
                "gemini": "gemini-2.0-flash", "google": "gemini-2.0-flash"}
    return HttpMetadataExtractor(LlmConfig(provider, api_key, model or defaults[provider]))


if __name__ == "__main__":
    app()
