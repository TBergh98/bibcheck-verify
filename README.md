Quando configurato, puo usare un modello linguistico soltanto come fallback per estrarre metadati da citazioni incomplete. Il modello non decide se una citazione esiste: la verifica resta affidata a Crossref, OpenAlex e al confronto fuzzy locale.
# bibcheck

`bibcheck` controlla i riferimenti bibliografici di un articolo confrontandoli con i metadati disponibili in Crossref e OpenAlex.

## Skill per Hermes e Claude Code

La skill distribuibile si trova in [.github/skills/bibcheck-verify](.github/skills/bibcheck-verify).
Le istruzioni per installarla in Hermes Agent o Claude Code, i requisiti e i limiti per
utenti non tecnici sono nel [README della skill](.github/skills/bibcheck-verify/README.md).

La skill richiede Python 3.11+ e `uv` sulla macchina che esegue l'agente. Dopo la prima
installazione, l'utente può fornire una bibliografia all'agente e chiedere la verifica;
il risultato deve comunque essere sottoposto a revisione umana.

L'obiettivo e fornire un controllo riproducibile e ispezionabile: per ogni riferimento vengono conservati la fonte interrogata, la query usata, l'eventuale opera trovata e un livello di confidenza. Il programma non usa modelli linguistici per decidere se una citazione esiste.

## Quando usarlo

`bibcheck` e utile per una prima verifica di una bibliografia prima di una revisione manuale, soprattutto per individuare:

- DOI o metadati che corrispondono esattamente a un'opera indicizzata;
- riferimenti che sembrano corrispondere a un'opera, ma richiedono un confronto fuzzy;
- riferimenti senza metadati sufficienti o non trovati nelle fonti consultate.

Il risultato non sostituisce il controllo umano. Un riferimento puo essere corretto ma non essere indicizzato, oppure puo avere metadati troppo incompleti per essere confrontato in modo affidabile.

## Requisiti e installazione

Sono necessari Python 3.11 o una versione successiva e [uv](https://docs.astral.sh/uv/).

Per installare il progetto e le dipendenze di test:

```bash
uv sync --extra test
```

L'installazione registra il comando `bibcheck` nell'ambiente del progetto. In alternativa, tutti gli esempi possono essere eseguiti con `uv run bibcheck`.

## Uso rapido

Per verificare una bibliografia BibTeX:

```bash
uv run bibcheck verify paper.bib
```

Al termine, il programma crea `./bibcheck-results/` con un riepilogo Markdown e il grafo completo in JSON.

Un esempio con le opzioni piu comuni:

```bash
uv run bibcheck verify paper.bib \
	--depth 2 \
	--sources openalex,crossref \
	--confidence-threshold 0.85 \
	--max-requests 2000 \
	--output-dir ./risultati-bibcheck \
	--mailto nome@example.org
```

Per vedere tutti i comandi e i valori predefiniti:

```bash
uv run bibcheck --help
uv run bibcheck verify --help
```

## Formati di input

Il comando `verify` accetta un percorso file. Il formato viene scelto dall'estensione:

- `.bib`: BibTeX. Vengono letti titolo, autori, anno, DOI, rivista o atti di conferenza;
- `.pdf`: il testo viene estratto con PyMuPDF e analizzato come testo libero;
- qualsiasi altra estensione: il file viene trattato come testo semplice o Markdown.

Per file di testo e Markdown, il parser cerca una sezione chiamata `References`, `Bibliography` o `Bibliografia`. Se non la trova, prova a interpretare il contenuto intero come bibliografia. Le voci numerate, le righe separate e i riferimenti con titolo tra virgolette sono i casi meglio supportati.

Il parsing PDF e volutamente best effort: impaginazione a colonne, note, intestazioni e testo estratto in ordine inatteso possono produrre riferimenti incompleti. Per risultati piu prevedibili, quando possibile e preferibile fornire il file `.bib` originale.

## Come funziona la verifica

Per ogni riferimento, `bibcheck` segue questa sequenza:

1. estrae i metadati disponibili dal file;
2. se e presente un DOI e Crossref e selezionato, prova prima una ricerca esatta per DOI;
3. altrimenti interroga le fonti selezionate e confronta i metadati della corrispondenza trovata;
4. salva l'esito, la confidence e i dettagli delle ricerche;
5. se la corrispondenza e verificata e `--depth` e maggiore di zero, puo seguire anche le opere citate da quella pubblicazione.

La profondita predefinita e `0`, quindi controlla soltanto i riferimenti presenti nel file di input. Con `--depth 1` vengono analizzati anche i riferimenti citati dalle opere verificate; valori piu alti estendono ulteriormente il grafo.

## Opzioni principali

| Opzione | Predefinito | Descrizione |
| --- | --- | --- |
| `--depth` | `0` | Profondita del grafo delle citazioni da esplorare. Deve essere almeno `0`. |
| `--sources` | `openalex,crossref` | Fonti da interrogare, separate da virgola. Sono supportate `openalex` e `crossref`. |
| `--confidence-threshold` | `0.85` | Soglia tra `0` e `1` per accettare una corrispondenza fuzzy. |
| `--max-requests` | `2000` | Numero massimo di richieste HTTP. Il risultato puo essere parziale se il limite viene raggiunto. |
| `--output-dir` | `./bibcheck-results` | Directory in cui scrivere risultati e cache. |
| `--mailto` | nessuno | Indirizzo incluso nello User-Agent delle richieste HTTP. |
| `--llm-provider` | nessuno | Abilita il fallback LLM (`openai`, `anthropic` o `gemini`). Richiede la relativa API key. |
| `--llm-model` | predefinito del provider | Modello da usare per l'estrazione batch. |
| `--metadata-file` | nessuno | JSON con metadati prodotti da una skill o da un estrattore esterno. Alternativo a `--llm-provider`. |

### Fallback LLM

Il fallback viene eseguito solo per riferimenti privi di DOI e con titolo, autori o anno mancanti. Le citazioni vengono inviate in batch e il risultato deve contenere una voce per ogni citazione. I valori gia estratti in modo deterministico non vengono sovrascritti.

Le API key vanno fornite tramite variabili d'ambiente:

```powershell
$env:OPENAI_API_KEY = "..."
uv run bibcheck verify input_test/test_poultry.md --llm-provider openai
```

Sono supportati `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` e `GEMINI_API_KEY`. Il testo delle citazioni viene inviato al provider scelto; non inserire le chiavi in file di progetto, cache o report.

Per una configurazione locale persistente, copia `.env.example` in `.env` e compila soltanto la chiave del provider scelto. `.env` e escluso da Git e viene caricato automaticamente da `bibcheck`:

```powershell
Copy-Item .env.example .env
notepad .env
uv run bibcheck verify input_test/test_poultry.md
```

Non creare `.env` nel repository condiviso e non incollare mai la chiave nei comandi salvati nella shell o nei file di configurazione versionati.

### Uso da skill

Una skill puo usare direttamente il modello della sessione per creare un file JSON, senza API key del provider LLM, e poi delegare la verifica a `bibcheck`:

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

Il campo `reference_id` deve essere l'indice zero-based della reference nel file di input e deve esserci esattamente una voce per ogni reference. La skill esegue quindi:

```powershell
uv run bibcheck verify paper.md --metadata-file metadata.json
```

In questa modalita l'LLM della skill estrae i metadati, mentre `bibcheck` continua a usare Crossref/OpenAlex per la verifica.

Per limitare la verifica a una sola fonte, ad esempio:

```bash
uv run bibcheck verify paper.bib --sources crossref
```

## Risultati

La directory di output contiene:

- `summary.md`: riepilogo leggibile con numero di richieste, eventuale risultato parziale e conteggi per profondita e stato;
- `graph.json`: dati completi della verifica, inclusi nodi, archi, riferimenti, confidence, opere trovate e query inviate alle fonti;
- `cache.sqlite3`: cache locale delle risoluzioni, riutilizzabile nelle esecuzioni successive con la stessa directory.

Gli stati piu importanti sono:

- `verified`: corrispondenza verificata, incluso il caso di DOI esatto;
- `verified_fuzzy`: corrispondenza accettata sulla base della similarita dei metadati;
- `low_confidence`: esiste una possibile corrispondenza, ma non supera la soglia o i dati di input sono insufficienti;
- `suspected_hallucination`: nessuna corrispondenza e stata trovata nelle fonti consultate.

`suspected_hallucination` e un'etichetta di triage, non una prova che il riferimento sia inventato. Va sempre verificata manualmente, insieme alle query registrate in `graph.json`.

`summary.md` e il report principale per la revisione manuale. Include il numero delle reference originali, quante sono state controllate e quante hanno una possibile opera corrispondente, con percentuali esplicite. Mostra inoltre i conteggi per profondita e stato, una spiegazione della confidence e una tabella dettagliata per ogni riferimento con titolo, autori, anno, opera candidata, fonte, DOI o URL quando disponibili e azione consigliata.

Le percentuali riferite alla bibliografia originale usano come denominatore il numero di reference fornite in input. Le percentuali delle sezioni per profondita usano invece i nodi controllati nel grafo: questi possono essere deduplicati oppure includere opere scoperte a `depth` maggiore di zero. Se il limite di richieste viene raggiunto, il report segnala che il risultato e parziale e le reference non elencate non devono essere interpretate come verificate o inesistenti.

## Limiti e comportamento in caso di errore

- La verifica richiede accesso alla rete e dipende dalla disponibilita e dalla qualita dei metadati di Crossref e OpenAlex.
- Un riferimento senza titolo, autori o anno viene trattato con bassa confidenza.
- Il limite `--max-requests` include le richieste ripetute dopo una risposta HTTP `429`. Se viene superato, `summary.md` e `graph.json` vengono comunque scritti, ma il campo `partial` in `graph.json` sara `true`.
- Le chiamate vengono memorizzate nella cache della directory di output. Per una nuova verifica pulita, usa una directory diversa o rimuovi la cache dopo aver salvato i risultati che ti servono.

## Sviluppo e test

Per eseguire la suite di test:

```bash
uv run pytest
```

Il codice sorgente si trova in `src/bibcheck/`; i test corrispondenti sono in `tests/`.
