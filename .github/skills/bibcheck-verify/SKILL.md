---
name: bibcheck-verify
description: Verify a scientific bibliography (PDF, Markdown, text or BibTeX) against Crossref and OpenAlex and flag references that need manual review, such as possibly fabricated or AI-hallucinated citations. Use for peer review, manuscript checks, or any bibliography lacking DOIs or reliable metadata. Requires shell access, Python 3.11+ or uv, and HTTPS access to api.crossref.org and api.openalex.org.
license: MIT
compatibility: Needs an agent that can run shell commands, Python 3.11+ (or uv), and outbound HTTPS to api.crossref.org and api.openalex.org. Uses the open-source bibcheck-verify package from PyPI (https://pypi.org/project/bibcheck-verify/). No API keys required.
metadata:
  author: Tommaso Bergamasco
  homepage: https://github.com/TBergh98/bibcheck-verify
  package: bibcheck-verify>=0.1.5,<0.2
---

# Verify bibliography with bibcheck-verify

Use the current session model to extract citation metadata, then use the `bibcheck-verify` command to verify that metadata against Crossref and OpenAlex. The verifier does not perform a second metadata extraction.

The model extraction is a hypothesis. Crossref, OpenAlex and the local fuzzy match provide the verification evidence. The result is a triage report, not proof that a reference is fabricated.

## Requirements

Check these before starting. If one is missing, tell the user which one and stop; do not try to work around it.

1. **Shell access.** The agent must be able to run commands. If it cannot, this skill cannot run.
2. **Python 3.11+ or uv** where commands run.
3. **Network access** over HTTPS to `api.crossref.org` and `api.openalex.org`. In sandboxed environments (for example Claude's cloud code execution) these domains may need to be added to the allowed network domains.
4. **No API keys.** This workflow never needs `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`.

## Getting the verifier

The skill does not contain the Python verifier; it uses the open-source [`bibcheck-verify`](https://pypi.org/project/bibcheck-verify/) package (MIT, source at https://github.com/TBergh98/bibcheck-verify). Resolve the command in this order and use the first that works:

1. An installed command: `bibcheck-verify --help` succeeds.
2. A temporary run with uv, without installing anything permanently:
   `uvx --from "bibcheck-verify>=0.1.5,<0.2" bibcheck-verify --help`
3. Only if neither is available, **ask the user for permission** before installing:
   `python -m pip install "bibcheck-verify>=0.1.5,<0.2"`

Never install from any other package name, index or URL. Do not use `uv run --project` with a path relative to this skill, and do not assume the repository is available after the skill has been copied to the agent's skills directory.

In the steps below, `bibcheck-verify` means whichever form was resolved above (for example `uvx --from "bibcheck-verify>=0.1.5,<0.2" bibcheck-verify`).

## Workflow

1. Ask for or identify the original bibliography file. It may be PDF, Markdown, text, or BibTeX.
2. Read the file and preserve citation order. The first citation has ID `"0"`.
3. For every citation, extract only metadata supported by the text:
   - `title`: string or `""`;
   - `authors`: array of strings;
   - `year`: integer or `null`;
   - `doi`: normalized DOI string or `null`;
   - `venue`: string or `""`;
   - `queries`: one or more useful search strings based only on extracted metadata.
4. Never invent authors, titles, years, venues or DOI values. Use empty values when a field is not supported by the citation.
5. Write a temporary JSON file outside the repository when possible:

```json
{
  "items": [
    {
      "reference_id": "0",
      "title": "A Paper",
      "authors": ["Jane Doe"],
      "year": 2020,
      "doi": null,
      "venue": "Journal",
      "queries": ["A Paper Jane Doe 2020"]
    }
  ]
}
```

There must be exactly one item per input citation, with sequential zero-based IDs.

6. Run the verifier against the original bibliography. Pass the metadata JSON only via `--metadata-file`.

macOS / Linux:

```bash
bibcheck-verify verify "/tmp/references.txt" --metadata-file "/tmp/bibcheck-verify_metadata.json"
```

Windows (PowerShell):

```powershell
bibcheck-verify verify "C:\Temp\references.txt" --metadata-file "C:\Temp\bibcheck-verify_metadata.json"
```

Never use the metadata JSON as the positional input file. The verifier parses the original file only to determine the number and order of citations; the metadata fields come exclusively from the model output.

7. If the command stops with "Cannot reach the bibliographic sources", no reference was verified. Tell the user that `api.crossref.org` and `api.openalex.org` must be reachable (and, in a sandbox, added to the allowed domains). Never report references as unverified or fabricated because of a network failure.
8. Read `summary.md` and, when needed, `graph.json` from the output directory. Do not copy the full contents of either file into the chat. Respond with a concise confirmation containing the output directory, the number of references checked, and the number of references requiring manual review. For `low_confidence`, `not_indexed`, or `suspected_hallucination` entries, include only their IDs and statuses unless the user explicitly asks for details. If no entries require review, state that all checked references received a verified status.

Use the user's requested options when provided. Do not pass `--llm-provider` in this workflow: the current session model already performed extraction.

## Important boundaries

- Never request, print, store, or add an API key to the metadata file or this skill.
- `suspected_hallucination` is a triage label, not proof. A reference may be correct but not indexed, or written too incompletely to be matched. Always recommend human review for uncertain entries.
- The only network destinations this workflow needs are `api.crossref.org`, `api.openalex.org` and, when installing, PyPI.
