# bibcheck

`bibcheck` is a tool for an initial reproducible check of scientific bibliographies. It compares each reference with metadata indexed by Crossref and OpenAlex and produces a report that helps identify strong matches, possible matches, and references that require manual review.

It does not determine on its own that a citation is fabricated. A reference may be correct but not indexed, or it may be written too incompletely to be recognized. The results are therefore a triage tool, not definitive proof.

## Why it exists

Real bibliographies often come from PDFs, copied text, or documents with missing DOIs and metadata. Checking them one entry at a time is slow; relying on a language model for the judgment, on the other hand, can introduce fabricated details.

`bibcheck` separates these two problems: extracting incomplete metadata can be assisted by a model, while the existence and matching of a work are evaluated by querying external bibliographic sources and comparing the results. This makes both interactive verification with an agent and repeated processing of many bibliographies through scripts, caching, and request limits possible.

## Two ways to use the project

The repository contains two related but distinct components:

1. **The standalone Python package**: the `bibcheck` program can be used from a terminal, script, or pipeline to check many bibliographies. It can also use an LLM provider through an API key as a fallback for extracting missing metadata.
2. **The `bibcheck` skill**: instructions for Hermes Agent, Claude Code, or compatible agents. The agent uses the session model to extract metadata, without a separate LLM API key, and then delegates verification to the Python `bibcheck` command.

The skill does not contain a copy of the program. To use it, first install the Python package and then copy the `.github/skills/bibcheck/` directory to the agent’s local skills directory.

## Package installation

Requirements:

- Python 3.11 o successivo;
- [`uv`](https://docs.astral.sh/uv/).

### From the repository

This is the useful mode during development or before publishing to PyPI:

```powershell
uv tool install .
```

To update the installation after a local change:

```powershell
uv tool install --force .
```

Alternatively, to use the project without installing it globally:

```powershell
uv run bibcheck verify references.bib
```

### From PyPI

Once the package is published, installation will not require downloading the repository:

```powershell
uv tool install bibcheck
```

For a single temporary run:

```powershell
uvx bibcheck verify references.bib
```

PyPI distributes the code and dependencies. It does not automatically receive the user’s bibliographies, reports, or API keys.

## Standalone usage

The command accepts BibTeX, PDF, Markdown, and plain text:

```powershell
bibcheck verify references.bib
bibcheck verify article.pdf
bibcheck verify references.md --output-dir risultati
```

The format is recognized from the extension:

- `.bib`: title, authors, year, DOI, journal, or proceedings are extracted;
- `.pdf`: text is extracted with PyMuPDF;
- other extensions: the file is treated as text or Markdown.

For text and Markdown, the parser looks for a `References`, `Bibliography`, or `Bibliografia` section. If it does not find one, it tries to interpret the entire file as a bibliography. PDF parsing is best effort; whenever possible, a BibTeX file produces more predictable results.

To see all options:

```powershell
bibcheck --help
bibcheck verify --help
```

Example with the main options:

```powershell
bibcheck verify references.bib `
  --depth 1 `
  --sources openalex,crossref `
  --confidence-threshold 0.85 `
  --max-requests 2000 `
  --output-dir risultati `
  --mailto nome@example.org
```

`--depth 0` checks only the provided references. With higher values, it can follow works cited by the verified publications and build a larger graph.

## Usage with a skill

The skill is located in [.github/skills/bibcheck](.github/skills/bibcheck). To install it:

1. install the `bibcheck` command, from the repository with `uv tool install .` or from PyPI with `uv tool install bibcheck` once it is available;
2. copy the entire `.github/skills/bibcheck/` directory to the skills directory supported by your Hermes Agent or Claude Code installation;
3. ask the agent to verify a PDF, Markdown, text, or BibTeX file.

The session model reads the bibliography and creates a temporary file with the title, authors, year, DOI, journal, and search query. The `bibcheck` command reads the original file, applies that metadata, and queries Crossref and OpenAlex. The model proposes metadata; it does not decide whether a publication exists.

This mode does not require `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`. It does require network access to the bibliographic sources, and the `bibcheck` command must be available in the agent’s PATH.

## API keys and LLM fallback

Standalone usage can ask the program to extract incomplete metadata through an LLM provider. This is an optional fallback and does not replace verification against Crossref/OpenAlex.

```powershell
$env:OPENAI_API_KEY = "..."
bibcheck verify references.md --llm-provider openai
```

The `openai`, `anthropic`, and `gemini` providers are supported. Keys must remain in environment variables or a local `.env` file, never in the repository, reports, or metadata JSON file.

## Results

The output directory contains:

- `summary.md`: readable report for manual review;
- `graph.json`: complete details, queries, sources, nodes, edges, and confidence;
- `cache.sqlite3`: local resolution cache.

The main statuses are:

- `verified`: verified match, including through an exact DOI;
- `verified_fuzzy`: match accepted by fuzzy comparison;
- `low_confidence`: possible match that is not sufficiently strong;
- `suspected_hallucination`: no match found in the consulted sources.

`suspected_hallucination` is a triage label, not proof that the reference is fabricated. All uncertain cases require human review.

## Project structure

```text
bibcheck/
├── src/bibcheck/                 # Python package and CLI command
│   ├── cli.py                    # `bibcheck` commands and options
│   ├── ingest/                   # BibTeX, PDF, and text parsers
│   ├── resolve/                  # Crossref, OpenAlex, fuzzy matching, and optional LLM
│   ├── graph/                    # citation graph cache and traversal
│   └── report/                   # Markdown and JSON output
├── tests/                        # automated package tests
├── .github/skills/bibcheck/      # skill for compatible agents
│   ├── SKILL.md                  # agent operating instructions
│   └── README.md                 # manual skill installation
├── pyproject.toml                # metadata, dependencies, and console command
├── uv.lock                       # locked dependency versions
├── .env.example                  # local LLM configuration example
└── README.md                     # this guide
```

The `bibcheck-results*` directories are results from local runs and are not part of the distributed package.

## Development and testing

To prepare the repository environment:

```powershell
uv sync --extra test
uv run python -m pytest
```

The distributable package is built with:

```powershell
uv build
```

Artifacts are created in `dist/`. Before publishing to PyPI, it is advisable to check the wheel contents and test it in a clean environment or on TestPyPI.

## Publishing to PyPI

Publishing is optional and is not required to use the project locally. In summary:

1. create an account on PyPI and, preferably, a project-scoped token;
2. run `uv build`;
3. check the artifacts in `dist/`;
4. upload to TestPyPI first;
5. upload to PyPI using the token, without saving it in versioned files.

The `bibcheck` distribution name must be available on PyPI. The actual upload requires the owner’s credentials and is not performed by this repository.

## Limitations

- verification requires network access;
- Crossref and OpenAlex may have incomplete or differing data;
- the request limit may produce a partial result;
- the cache may reuse previous resolutions;
- no result replaces review of the original bibliography.
