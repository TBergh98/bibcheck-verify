# bibcheck-verify: scientific bibliography verification

`bibcheck-verify` is a reproducible scientific bibliography verification tool for papers, manuscripts, and peer review. It compares each reference with metadata indexed by Crossref and OpenAlex and produces an evidence-based report that helps identify strong matches, possible matches, and references that require manual review.

It does not determine on its own that a citation is fabricated. A reference may be correct but not indexed, or it may be written too incompletely to be recognized. The results are therefore a triage tool, not definitive proof.

## Why it exists

Real bibliographies often come from PDFs, copied text, or documents with missing DOIs and metadata. Checking them one entry at a time is slow; relying on a language model for the judgment, on the other hand, can introduce fabricated details. **This is especially useful for scientific peer reviewers who need an initial check before spending time on a deeper review of a manuscript.**

`bibcheck-verify` separates these two problems: a model extracts bibliographic metadata from each citation, while the existence and matching of a work are evaluated by querying external bibliographic sources and comparing the results. This makes both interactive verification with an agent and repeated processing of many bibliographies through scripts, caching, and request limits possible.

### For scientific peer reviewers

When reviewing a paper, use `bibcheck-verify` to check whether the cited works can be found in major bibliographic indexes and whether the citation metadata is consistent with those records. The resulting triage report can help reviewers decide whether the bibliography appears sufficiently reliable to proceed to a more detailed scientific review, or whether specific references need closer manual examination first. It supports editorial and peer-review workflows; it does not replace the reviewer's judgment about the paper or its sources.

### Why this matters

The scale of the problem is illustrated by a 2026 audit published in [The Lancet](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(26)00603-3/fulltext). The audit examined more than 2.4 million biomedical papers published between January 2023 and February 2026, covering more than 125 million structured references.

The authors identified 4,046 fabricated references across 2,810 papers. The reported rate increased substantially over the period studied: from approximately one affected paper in 2,828 in 2023 to one in 458 in 2025, and one in 277 during the first seven weeks of 2026.

The study compared claimed reference metadata with records from PubMed and Crossref, then applied automated filters, an LLM review step, and additional checks against OpenAlex and Google Scholar. It also distinguishes fabricated references from ordinary citation errors, such as abbreviated titles that still correspond to a real publication.

This is the problem `bibcheck-verify` is intended to make easier to investigate at a smaller and inspectable scale: verify references against external records, preserve the queries and evidence, and send uncertain cases to human review. Its results should not be interpreted as a replication of the Lancet audit or as definitive proof that an unmatched reference is fabricated.

## Two ways to use the project

The repository contains two related but distinct components:

1. **The `bibcheck-verify` skill for Claude and other agents** (recommended for most users): the agent uses its own session model to extract metadata, without a separate LLM API key, and then delegates verification to the Python `bibcheck-verify` command. In Claude it is installed as a plugin in a few clicks, and it fetches the Python command from PyPI by itself when needed.
2. **The standalone Python package**: the `bibcheck-verify` program can be used from a terminal, script, or pipeline to check many bibliographies. Metadata extraction is performed by an LLM provider or by metadata prepared by the compatible skill.

## Quick start: use it in Claude

This repository is also a Claude plugin marketplace. Installing the plugin adds the `bibcheck-verify` skill; there is nothing to copy by hand and no separate Python installation to do first.

### Claude desktop app and claude.ai (Cowork and chat)

Plugins require a paid Claude plan (Pro, Max, Team or Enterprise).

1. Open **Customize** in the sidebar and select **Plugins**.
2. Select **Add marketplace** and enter `TBergh98/bibcheck-verify` (or `https://github.com/TBergh98/bibcheck-verify`).
3. Find **bibcheck-verify** in the list and select **Install**.
4. **Allow the bibliographic sources.** When Claude runs code in a cloud sandbox, it can reach only allowed domains. Add `api.crossref.org` and `api.openalex.org` to the domains allowed for code execution in Claude's network settings (on Team and Enterprise plans an Owner manages this in the admin settings). Without this step the verifier stops with the message "Cannot reach the bibliographic sources"; it never reports references as fabricated because of a blocked network.
5. Attach a paper or a bibliography and ask, for example: *"Verify the bibliography of this PDF"*.

To receive new versions, select **Check for updates** on the marketplace, or turn on **Sync automatically**.

### Claude Code

In a Claude Code session:

```text
/plugin marketplace add TBergh98/bibcheck-verify
/plugin install bibcheck-verify@bibcheck-verify
```

Or from a terminal:

```powershell
claude plugin marketplace add TBergh98/bibcheck-verify
claude plugin install bibcheck-verify@bibcheck-verify
```

Then ask Claude to verify a PDF, Markdown, text, or BibTeX file, or invoke the skill directly with `/bibcheck-verify:bibcheck-verify`. Third-party marketplaces do not update automatically by default: run `/plugin marketplace update bibcheck-verify`, or enable auto-update for it in the **Marketplaces** tab of `/plugin`.

### What happens behind the scenes

The skill first looks for the verifier and, if it is missing, gets it from PyPI on its own: it uses an installed `bibcheck-verify` command if there is one, otherwise `uvx bibcheck-verify`, otherwise `pip install bibcheck-verify`. The only requirement is Python 3.11+ (or [`uv`](https://docs.astral.sh/uv/)) where Claude runs commands; Claude's cloud sandbox already has it. If you use Claude Code on your own computer and prefer a permanent installation, run `uv tool install bibcheck-verify` once.

## Package installation

Requirements:

- Python 3.11 or newer;
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
  --sources openalex,crossref `
  --confidence-threshold 0.85 `
  --max-requests 2000 `
  --output-dir risultati `
  --mailto nome@example.org
```

## Usage with other agents

For Claude, use the plugin described in [Quick start](#quick-start-use-it-in-claude). For Hermes Agent and other agents that read `SKILL.md` files, install the skill manually. It is located in [.github/skills/bibcheck-verify](.github/skills/bibcheck-verify).

With the external [`skills`](https://www.npmjs.com/package/skills) installer, if you already use it:

```powershell
npx skills add TBergh98/bibcheck-verify --skill bibcheck-verify
```

Or copy the file by hand:

1. copy `.github/skills/bibcheck-verify/SKILL.md` into the skills directory supported by your agent (as `bibcheck-verify/SKILL.md`);
2. ask the agent to verify a PDF, Markdown, text, or BibTeX file.

If you already installed the Python package, it can also save a copy of the skill without changing any agent directory:

```powershell
bibcheck-verify skill download
```

The command saves `bibcheck-verify-SKILL.md` in the default Downloads directory. Copy it as `SKILL.md` into the agent's skill directory. A custom destination is also supported:

```powershell
bibcheck-verify skill download --output C:\Temp\SKILL.md
```

### How the skill works

The session model reads the bibliography and creates a temporary file with the title, authors, year, DOI, journal, and search query. The `bibcheck-verify` command reads the original file, applies that metadata, and queries Crossref and OpenAlex. The model proposes metadata; it does not decide whether a publication exists.

This mode does not require `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`. It does require HTTPS access to `api.crossref.org` and `api.openalex.org`; the command checks both before starting and stops with an explicit error if they cannot be reached.

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
- `not_indexed`: no result available in the relevant indexes;
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
├── .github/skills/bibcheck-verify/ # skill for Claude and compatible agents
│   └── SKILL.md                  # agent operating instructions
├── .claude-plugin/               # Claude plugin and marketplace manifests
│   ├── plugin.json
│   └── marketplace.json
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
