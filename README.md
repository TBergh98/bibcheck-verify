# bibcheck-verify

`bibcheck-verify` is a tool for an initial reproducible check of scientific bibliographies. It compares each reference with metadata indexed by Crossref and OpenAlex and produces a report that helps identify strong matches, possible matches, and references that require manual review.

It does not determine on its own that a citation is fabricated. A reference may be correct but not indexed, or it may be written too incompletely to be recognized. The results are therefore a triage tool, not definitive proof.

## Why it exists

Real bibliographies often come from PDFs, copied text, or documents with missing DOIs and metadata. Checking them one entry at a time is slow; relying on a language model for the judgment, on the other hand, can introduce fabricated details.

`bibcheck-verify` separates these two problems: a model extracts bibliographic metadata from each citation, while the existence and matching of a work are evaluated by querying external bibliographic sources and comparing the results. This makes both interactive verification with an agent and repeated processing of many bibliographies through scripts, caching, and request limits possible.

### Why this matters

The scale of the problem is illustrated by a 2026 audit published in [The Lancet](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(26)00603-3/fulltext). The audit examined 2,471,758 biomedical papers published between January 1, 2023, and February 18, 2026, containing 125,615,773 structured references. Of these references, 97.1 million (77%) carried a PMID and were checked against bibliographic records; references to websites, books, and other grey literature were mostly excluded.

The authors identified 4,046 fabricated references across 2,810 papers. The reported rate increased from approximately one paper in 2,828 in 2023 to one in 458 in 2025, and one in 277 during the first seven weeks of 2026. The fabrication rate rose from about 4 per 10,000 papers in 2023 to 51.3 per 10,000 papers in the fourth quarter of 2025, reaching 56.9 per 10,000 papers in early 2026.

Their system compared claimed reference metadata with records from PubMed and Crossref, then used automated filters, an LLM review step, and additional checks against OpenAlex and Google Scholar. In a masked validation of 500 entries, the system had a reported precision of 91% (Fleiss’ κ = 0.71); the authors explicitly note that this estimates precision, not recall. The study also distinguishes fabricated references from reference errors, such as abbreviated titles that still correspond to a real publication.

This is the problem `bibcheck-verify` is intended to make easier to investigate at a smaller and inspectable scale: verify references against external records, preserve the queries and evidence, and send uncertain cases to human review. Its results should not be interpreted as a replication of the Lancet audit or as definitive proof that an unmatched reference is fabricated.

## Two ways to use the project

The repository contains two related but distinct components:

1. **The standalone Python package**: the `bibcheck-verify` program can be used from a terminal, script, or pipeline to check many bibliographies. Metadata extraction is performed by an LLM provider or by metadata prepared by the compatible skill.
2. **The `bibcheck-verify` skill**: instructions for Hermes Agent, Claude Code, or compatible agents. The agent uses the session model to extract metadata, without a separate LLM API key, and then delegates verification to the Python `bibcheck-verify` command.

The skill does not contain a copy of the program. To use it, first install the Python package and then copy the `.github/skills/bibcheck-verify/` directory to the agent’s local skills directory.

## Package installation

Requirements:

- Python 3.11 o successivo;
- [`uv`](https://docs.astral.sh/uv/).

### From PyPI

This is the recommended option for normal use. It installs the published package without requiring a local copy of the repository:

```powershell
uv tool install bibcheck-verify
```

To update all tools installed with `uv tool install` to the latest versions available on PyPI, from anywhere:

```powershell
uv tool upgrade --all
```

To update only `bibcheck-verify`:

```powershell
uv tool upgrade bibcheck-verify
```

For a single temporary run:

```powershell
uvx bibcheck-verify verify references.bib --metadata-file metadata.json
```

PyPI distributes the code and dependencies. It does not automatically receive the user’s bibliographies, reports, or API keys.

## Standalone usage

The command accepts BibTeX, PDF, Markdown, and plain text:

```powershell
bibcheck-verify verify references.bib
bibcheck-verify verify article.pdf --metadata-file metadata.json
bibcheck-verify verify references.md --llm-provider openai --output-dir risultati
```

The format is recognized from the extension:

- `.bib`: entries are separated and passed to the LLM for metadata extraction;
- `.pdf`: text is extracted with PyMuPDF;
- other extensions: the file is treated as text or Markdown.

For text and Markdown, the parser looks for a `References`, `Bibliography`, or `Bibliografia` section. If it does not find one, it tries to interpret the entire file as a bibliography. For PDFs, it first extracts text, locates the bibliography section, and separates its entries. The LLM is the only component that extracts bibliographic metadata.

One of `--metadata-file` or `--llm-provider` is required. The metadata file must contain one LLM-produced item per citation; the HTTP provider requires its API key in the environment.

To see all options:

```powershell
bibcheck-verify --help
bibcheck-verify verify --help
```

Example with the main options:

```powershell
bibcheck-verify verify references.bib `
  --metadata-file metadata.json `
  --depth 1 `
  --sources openalex,crossref `
  --confidence-threshold 0.85 `
  --max-requests 2000 `
  --output-dir risultati `
  --mailto nome@example.org
```

`--depth 0` checks only the provided references. With higher values, it can follow works cited by the verified publications and build a larger graph.

## Usage with a skill

The skill is located in [.github/skills/bibcheck-verify](.github/skills/bibcheck-verify). To install it:

1. install the `bibcheck-verify` command, from the repository with `uv tool install .` or from PyPI with `uv tool install bibcheck-verify` once it is available;
2. copy `SKILL.md` from `.github/skills/bibcheck-verify/` to the skills directory supported by your Hermes Agent or Claude Code installation;
3. ask the agent to verify a PDF, Markdown, text, or BibTeX file.

To download the skill without changing any provider directory, run:

```powershell
bibcheck-verify skill download
```

The command saves `bibcheck-verify-SKILL.md` in the default Downloads directory. Copy it as `SKILL.md` into the provider's skill directory. A custom destination is also supported:

```powershell
bibcheck-verify skill download --output C:\Temp\SKILL.md
```

For users who already use the Agent Skills ecosystem, the repository can also be added with:

```powershell
npx skills add TBergh98/bibcheck --skill bibcheck-verify
```

This is an optional installer managed by the external `skills` tool; it is not required by `bibcheck-verify`.

The session model reads the bibliography and creates a temporary file with the title, authors, year, DOI, journal, and search query. The `bibcheck-verify` command reads the original file, applies that metadata, and queries Crossref and OpenAlex. The model proposes metadata; it does not decide whether a publication exists.

This mode does not require `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`. It does require network access to the bibliographic sources, and the `bibcheck-verify` command must be available in the agent’s PATH.

## LLM metadata extraction

Standalone usage uses an LLM to extract metadata for every citation. This extraction does not replace verification against Crossref/OpenAlex.

```powershell
$env:OPENAI_API_KEY = "..."
bibcheck-verify verify references.md --llm-provider openai
```

The `openai`, `anthropic`, and `gemini` providers are supported. Keys must remain in environment variables or a local `.env` file, never in the repository, reports, or metadata JSON file. Alternatively, use `--metadata-file` with JSON produced by the compatible skill, which uses the session model and does not require a provider API key.

## Results

The output directory `bibcheck-verify-results` contains:

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
bibcheck-verify/
├── src/bibcheck/                 # Internal Python module for the bibcheck-verify command
│   ├── cli.py                    # `bibcheck-verify` commands and options
│   ├── ingest/                   # BibTeX, PDF, and text parsers
│   ├── resolve/                  # LLM metadata extraction, Crossref, OpenAlex, and fuzzy matching
│   ├── graph/                    # citation graph cache and traversal
│   └── report/                   # Markdown and JSON output
├── tests/                        # automated package tests
├── .github/skills/bibcheck-verify/ # skill for compatible agents
│   └── SKILL.md                  # agent operating instructions
├── pyproject.toml                # metadata, dependencies, and console command
├── uv.lock                       # locked dependency versions
├── .env.example                  # local LLM configuration example
└── README.md                     # this guide
```

The `bibcheck-verify-results*` directories are results from local runs and are not part of the distributed package.

## Development and testing

To prepare the repository environment:

```powershell
uv sync --extra test
uv run python -m pytest
```

### Install a local checkout

These commands are intended for development and testing when working on a cloned copy of the repository. They are not needed for normal use from PyPI.

To install the local checkout as a command-line tool:

```powershell
uv tool install .
```

After changing the local code, reinstall it with:

```powershell
uv tool install --force .
```

Alternatively, run the local code without installing it globally:

```powershell
uv run bibcheck-verify verify references.bib
```

The distributable package is built with:

```powershell
uv build
```

Artifacts are created in `dist/`. Before publishing to PyPI, it is advisable to check the wheel contents and test it in a clean environment or on TestPyPI.