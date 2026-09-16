from pathlib import Path
import os

import typer
from dotenv import load_dotenv

from bibcheck.graph.cache import Cache
from bibcheck.graph.traverse import verify_references
from bibcheck.ingest import parse_bibtex, parse_pdf, parse_text
from bibcheck.report.json_graph import write_json
from bibcheck.report.summary import write_summary
from bibcheck.resolve.crossref import CrossrefResolver
from bibcheck.resolve.http import ApiClient
from bibcheck.resolve.openalex import OpenAlexResolver
from bibcheck.resolve.llm import HttpMetadataExtractor, LlmConfig, LlmExtractionError, apply_suggestion, load_metadata_file

app = typer.Typer(no_args_is_help=True)
load_dotenv()


@app.command()
def version() -> None:
    typer.echo("bibcheck 0.1.0")


@app.command("verify")
def verify(input_file: Path, depth: int = typer.Option(0, min=0), sources: str = typer.Option("openalex,crossref"),
           confidence_threshold: float = typer.Option(0.85, min=0.0, max=1.0),
           max_requests: int = typer.Option(2000, min=0), output_dir: Path = typer.Option(Path("./bibcheck-results")),
           mailto: str | None = typer.Option(None),
           llm_provider: str | None = typer.Option(None, envvar="BIBCHECK_LLM_PROVIDER"),
           llm_model: str | None = typer.Option(None, envvar="BIBCHECK_LLM_MODEL"),
           metadata_file: Path | None = typer.Option(None, help="JSON metadata produced by a skill or another extractor.")) -> None:
    if not input_file.is_file():
        raise typer.BadParameter(f"input file not found: {input_file}")
    suffix = input_file.suffix.lower()
    references = parse_bibtex(input_file) if suffix == ".bib" else parse_pdf(input_file) if suffix == ".pdf" else parse_text(input_file)
    selected = [source.strip() for source in sources.split(",") if source.strip() in {"openalex", "crossref"}]
    if not selected:
        raise typer.BadParameter("sources must contain openalex or crossref")
    output_dir.mkdir(parents=True, exist_ok=True)
    client = ApiClient(max_requests=max_requests, mailto=mailto)
    cache = Cache(str(output_dir / "cache.sqlite3"))
    if metadata_file:
        if llm_provider:
            raise typer.BadParameter("use either --metadata-file or --llm-provider, not both")
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
