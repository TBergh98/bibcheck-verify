---
name: bibcheck-verify
description: Use when verifying a bibliography from PDF, Markdown, text, or BibTeX, especially when references lack DOI or reliable metadata. Extract metadata with the current session model, then run the installed bibcheck-verify command with Crossref and OpenAlex.
---

# Verify bibliography with bibcheck-verify

Use the current session model to extract citation metadata, then use the installed `bibcheck-verify` command to verify that metadata against Crossref and OpenAlex. The verifier does not perform a second local metadata extraction.

The model extraction is a hypothesis. Crossref, OpenAlex and the local fuzzy match provide the verification evidence.

## Prerequisite

The user must have the `bibcheck-verify` command installed and available to the agent:

```powershell
uv tool install bibcheck-verify
```

Before the package is published, the user can install it from a local clone of the repository with `uv tool install <repository-directory>`.

The skill itself does not contain the Python verifier. Do not use `uv run --project` with a path relative to this skill and do not assume that the repository is available after the skill has been copied to the agent's skills directory.

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
6. Run the verifier against the original bibliography. Pass the metadata JSON only via `--metadata-file`:

```powershell
bibcheck-verify verify "C:\Temp\references.txt" --metadata-file "C:\Temp\bibcheck-verify_metadata.json"
```

Never use the metadata JSON as the positional input file. The verifier parses the original file only to determine the number and order of citations; the metadata fields come exclusively from the model output.
7. Read `summary.md` and, when needed, `graph.json` from the output directory. Do not copy the full contents of either file into the chat. Respond with a concise confirmation containing the output directory, the number of references checked, and the number of references requiring manual review. For `low_confidence`, `not_indexed`, or `suspected_hallucination` entries, include only their IDs and statuses unless the user explicitly asks for details. If no entries require review, state that all checked references received a verified status.

Use the user's requested options when provided. Do not pass `--llm-provider` in this workflow: the current session model already performed extraction.

## Important boundary

Never request, print, store, or add an API key to the metadata file or this skill.
