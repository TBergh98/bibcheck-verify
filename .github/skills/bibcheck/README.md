# Skill `bibcheck`

This directory contains the integration for Hermes Agent, Claude Code, or compatible agents. The skill instructs the agent to extract metadata using the session model and invoke the Python `bibcheck` command.

## Installation

The skill and the Python package are separate components.

1. Install `bibcheck`:

   ```powershell
   uv tool install bibcheck-verify
   ```

   Before publishing to PyPI, use `uv tool install <repository-path>`.

2. Copy the entire `bibcheck` directory to the skills directory expected by your Hermes or Claude Code installation. The copied directory must contain `SKILL.md`.

3. Ask the agent to verify a PDF, Markdown, text, or BibTeX file.

Do not copy this directory expecting it to also contain the executable: the `bibcheck` command must already be installed and available in the agent's PATH.

## API key

The skill mode does not require an API key for an LLM provider. The session model extracts the metadata; `bibcheck` queries Crossref and OpenAlex.

API keys are required only when directly using the standalone command's LLM fallback with `--llm-provider`.
