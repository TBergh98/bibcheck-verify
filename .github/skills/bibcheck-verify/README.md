# bibcheck

Local verifier used by the `bibcheck-verify` Hermes skill.

## Requirements

Install Python 3.11 or newer and [uv](https://docs.astral.sh/uv/). The skill uses `uv`
to create its local environment on first use.

## Install in Hermes

Copy the complete `bibcheck-verify` directory into the Hermes skills directory. Keep
`SKILL.md`, `pyproject.toml`, `uv.lock`, and `src/bibcheck/`. Do not distribute `.venv`,
cache directories, generated results, `.env` files, or API keys.

The skill runs the local project with:

```text
uv run --project "<skill-dir>" bibcheck verify <input-file> --metadata-file <metadata-file>
```

`<skill-dir>` is the directory containing `SKILL.md`. `uv` creates the environment and
installs the dependencies locked in `uv.lock`. The command is portable across Windows,
macOS, and Linux.

The `--metadata-file` mode does not require an LLM API key: the session model extracts
metadata, while `bibcheck` verifies it through Crossref and OpenAlex.

## Using the skill

This package is an agent skill, not a standalone graphical application. It is intended
for an AI agent that can load `SKILL.md` and run local commands.

### Hermes Agent

1. Download the repository as a ZIP from GitHub.
2. Extract `bibcheck-verify` into the Hermes skills directory.
3. Make sure Python 3.11+ and `uv` are installed.
4. Ask Hermes to verify a bibliography and provide the PDF, Markdown, text, or BibTeX
	file.

On first use, Hermes creates the skill's local environment automatically. The agent
should report the location of `summary.md` and flag low-confidence or suspected
hallucination results for manual review.

### Claude Code

Copy the complete `bibcheck-verify` directory into Claude Code's skills directory using
the layout supported by the installed Claude Code version, for example:

```text
.claude/skills/bibcheck-verify/
```

The directory must contain `SKILL.md`, `pyproject.toml`, `uv.lock`, and `src/bibcheck/`.
Then ask Claude Code to verify the bibliography. The agent must have permission to run
`uv` and access Crossref/OpenAlex over the network.

## For non-technical users

The current package is not yet a one-click tool for a veterinarian: installing an agent,
Python, `uv`, and a skill still requires technical assistance. After installation, the
workflow itself can be simple: provide the bibliography and ask the agent to verify it.

For a genuinely non-technical workflow, the next product step is a small web or desktop
interface that accepts a file, runs this verifier, and displays `summary.md` with the
manual-review warnings. The skill can remain the agent integration layer behind that
interface.

## Publishing on GitHub

Before publishing, confirm that the repository contains no `.venv`, `.env`, API keys,
cache databases, generated reports, or absolute paths. Then create a public GitHub
repository and push the project with this directory included. Users can download the
repository ZIP, or clone it, and follow the platform-specific instructions above.
