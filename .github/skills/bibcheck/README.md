# Skill `bibcheck`

Questa directory contiene l'integrazione per Hermes Agent, Claude Code o agenti compatibili. La skill istruisce l'agente a estrarre i metadati con il modello della sessione e a invocare il comando Python `bibcheck`.

## Installazione

La skill e il pacchetto Python sono componenti separati.

1. Installa `bibcheck`:

   ```powershell
   uv tool install bibcheck
   ```

   Prima della pubblicazione su PyPI, usa `uv tool install <percorso-del-repository>`.

2. Copia l'intera directory `bibcheck` nella directory delle skill prevista dalla tua installazione di Hermes o Claude Code. La directory copiata deve contenere `SKILL.md`.

3. Chiedi all'agente di verificare un PDF, Markdown, testo o BibTeX.

Non copiare questa directory aspettandoti che contenga anche l'eseguibile: il comando `bibcheck` deve essere già installato e disponibile nel PATH dell'agente.

## API key

La modalità della skill non richiede una API key per un provider LLM. Il modello della sessione estrae i metadati; `bibcheck` interroga Crossref e OpenAlex.

Le API key sono necessarie solo se si usa direttamente il fallback LLM del comando standalone con `--llm-provider`.
