---
name: bibcheck-verify
description: Use when verifying a bibliography from PDF, Markdown, text, or BibTeX, especially when references lack DOI or reliable metadata. Extract metadata with the current session model, then run bibcheck with Crossref and OpenAlex.
---

# Verify bibliography with bibcheck

Use this skill to combine the current agent model with the local `bibcheck` verifier.
The model extracts metadata; `bibcheck` performs the external lookup, fuzzy comparison,
cache, citation graph traversal, and reports.

## Workflow

1. Ask for or identify the bibliography input file.
2. Read the file and use the existing parser behavior as a guide. Preserve the citation
   order exactly; the first citation has `reference_id` `"0"`.
3. For every citation, extract only metadata supported by the text:
   - `title`: string or `""`;
   - `authors`: array of strings;
   - `year`: integer or `null`;
   - `doi`: normalized DOI string or `null`;
   - `venue`: string or `""`;
   - `queries`: one or more useful search strings based only on extracted metadata.
4. Do not invent authors, titles, years, venues, or DOI values. Use empty values when
   the citation does not support a field.
5. Write a temporary JSON file outside the repository when possible. Its exact shape is:

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
6. Run the verifier through the skill's local Python project. The skill directory is the
directory that contains this `SKILL.md`; call it `<skill-dir>` below. Do not use a path
from the author's computer. On first use, `uv` creates a local environment in the skill
directory and installs the pinned dependencies from `uv.lock`.

The positional `<input-file>` must be the original bibliography file (PDF, Markdown,
text, or BibTeX), not the generated metadata JSON. The metadata JSON is a sidecar file
and must be passed only through `--metadata-file`.

For example, if the raw bibliography is in `C:\Temp\references.txt` and the extracted
metadata is in `C:\Temp\bibcheck_metadata.json`, run:

```powershell
uv run --project "<skill-dir>" bibcheck verify "C:\Temp\references.txt" --metadata-file "C:\Temp\bibcheck_metadata.json"
```

The same command works on macOS and Linux with the corresponding path syntax. If the
environment does not have `uv`, stop and report that Python 3.11+ and `uv` are required;
do not fall back to the author's environment or a globally installed `bibcheck`.

Never use the metadata JSON as `<input-file>`. `bibcheck` first parses the original
bibliography to determine the number and order of references, then applies the matching
metadata items from `--metadata-file`.

Use the user's requested options when provided, otherwise use the defaults. Do not pass
`--llm-provider` in this mode: the current session model already performed extraction.
7. Read `summary.md` and, when needed, `graph.json` from the output directory. Report
   low-confidence and suspected-hallucination entries for manual review.

## Important boundary

The model extraction is a hypothesis, not proof that a publication exists. Treat
Crossref/OpenAlex results and the local fuzzy match as the verification evidence.
Never request, print, store, or add an API key to the metadata file or skill.