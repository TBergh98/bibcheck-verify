# bibcheck

`bibcheck` è uno strumento per una prima verifica riproducibile di bibliografie scientifiche. Confronta ogni riferimento con i metadati indicizzati da Crossref e OpenAlex e produce un report che aiuta a individuare corrispondenze solide, possibili corrispondenze e riferimenti da controllare manualmente.

Non stabilisce da solo che una citazione sia inventata. Un riferimento può essere corretto ma non indicizzato, oppure può essere scritto in modo troppo incompleto per essere riconosciuto. I risultati sono quindi uno strumento di triage, non una prova definitiva.

## Perché esiste

Le bibliografie reali spesso arrivano da PDF, testo copiato o documenti con DOI e metadati mancanti. Controllarle una voce alla volta è lento; affidare il giudizio a un modello linguistico, invece, può introdurre dettagli inventati.

`bibcheck` separa i due problemi: l’estrazione di metadati incompleti può essere aiutata da un modello, mentre l’esistenza e la corrispondenza di un’opera vengono valutate interrogando fonti bibliografiche esterne e confrontando i risultati. Questo rende possibile sia una verifica interattiva con un agente sia l’elaborazione ripetuta di molte bibliografie tramite script, cache e limiti di richieste.

## Due modi di usare il progetto

La repository contiene due componenti collegate ma distinte:

1. **Il pacchetto Python standalone**: il programma `bibcheck` può essere usato da terminale, da script o da pipeline per controllare molte bibliografie. Può usare anche un provider LLM tramite API key come fallback per estrarre metadati mancanti.
2. **La skill `bibcheck`**: istruzioni per Hermes Agent, Claude Code o agenti compatibili. L’agente usa il modello della sessione per estrarre i metadati, senza una API key LLM separata, poi delega la verifica al comando Python `bibcheck`.

La skill non contiene una copia del programma. Per usarla bisogna installare prima il pacchetto Python e poi copiare la directory `.github/skills/bibcheck/` nella directory locale delle skill dell’agente.

## Installazione del pacchetto

Requisiti:

- Python 3.11 o successivo;
- [`uv`](https://docs.astral.sh/uv/).

### Dal repository

Questa è la modalità utile durante lo sviluppo o prima della pubblicazione su PyPI:

```powershell
uv tool install .
```

Per aggiornare l’installazione dopo una modifica locale:

```powershell
uv tool install --force .
```

In alternativa, per usare il progetto senza installarlo globalmente:

```powershell
uv run bibcheck verify references.bib
```

### Da PyPI

Quando il pacchetto sarà pubblicato, l’installazione non richiederà il download del repository:

```powershell
uv tool install bibcheck
```

Per una singola esecuzione temporanea:

```powershell
uvx bibcheck verify references.bib
```

PyPI distribuisce il codice e le dipendenze. Non riceve automaticamente bibliografie, report o API key dell’utente.

## Uso standalone

Il comando accetta BibTeX, PDF, Markdown e testo semplice:

```powershell
bibcheck verify references.bib
bibcheck verify article.pdf
bibcheck verify references.md --output-dir risultati
```

Il formato viene riconosciuto dall’estensione:

- `.bib`: vengono estratti titolo, autori, anno, DOI, rivista o atti;
- `.pdf`: il testo viene estratto con PyMuPDF;
- altre estensioni: il file viene trattato come testo o Markdown.

Per testo e Markdown il parser cerca una sezione `References`, `Bibliography` o `Bibliografia`. Se non la trova, prova a interpretare l’intero file come bibliografia. Il parsing PDF è best effort; quando possibile, un file BibTeX produce risultati più prevedibili.

Per vedere tutte le opzioni:

```powershell
bibcheck --help
bibcheck verify --help
```

Esempio con le opzioni principali:

```powershell
bibcheck verify references.bib `
  --depth 1 `
  --sources openalex,crossref `
  --confidence-threshold 0.85 `
  --max-requests 2000 `
  --output-dir risultati `
  --mailto nome@example.org
```

`--depth 0` controlla solo i riferimenti forniti. Con valori maggiori può seguire le opere citate dalle pubblicazioni verificate e costruire un grafo più ampio.

## Uso con una skill

La skill si trova in [.github/skills/bibcheck](.github/skills/bibcheck). Per installarla:

1. installa il comando `bibcheck`, dal repository con `uv tool install .` oppure da PyPI con `uv tool install bibcheck` quando sarà disponibile;
2. copia l’intera directory `.github/skills/bibcheck/` nella directory delle skill supportata dalla tua installazione di Hermes Agent o Claude Code;
3. chiedi all’agente di verificare un file PDF, Markdown, testo o BibTeX.

Il modello della sessione legge la bibliografia e crea un file temporaneo con titolo, autori, anno, DOI, rivista e query di ricerca. Il comando `bibcheck` legge il file originale, applica quei metadati e interroga Crossref e OpenAlex. Il modello propone metadati: non decide se una pubblicazione esiste.

Questa modalità non richiede `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` o `GEMINI_API_KEY`. Serve invece accesso alla rete per le fonti bibliografiche e il comando `bibcheck` deve essere disponibile nel PATH dell’agente.

## API key e fallback LLM

L’uso standalone può chiedere al programma di estrarre metadati incompleti tramite un provider LLM. È un fallback opzionale e non sostituisce la verifica su Crossref/OpenAlex.

```powershell
$env:OPENAI_API_KEY = "..."
bibcheck verify references.md --llm-provider openai
```

Sono supportati i provider `openai`, `anthropic` e `gemini`. Le chiavi devono restare in variabili d’ambiente o in un file `.env` locale, mai nel repository, nei report o nel file JSON dei metadati.

## Risultati

La directory di output contiene:

- `summary.md`: report leggibile per la revisione manuale;
- `graph.json`: dettagli completi, query, fonti, nodi, archi e confidence;
- `cache.sqlite3`: cache locale delle risoluzioni.

Gli stati principali sono:

- `verified`: corrispondenza verificata, anche tramite DOI esatto;
- `verified_fuzzy`: corrispondenza accettata dal confronto fuzzy;
- `low_confidence`: possibile corrispondenza non abbastanza solida;
- `suspected_hallucination`: nessuna corrispondenza trovata nelle fonti consultate.

`suspected_hallucination` è un’etichetta di triage, non la prova che il riferimento sia inventato. Tutti i casi dubbi richiedono controllo umano.

## Struttura del progetto

```text
bibcheck/
├── src/bibcheck/                 # pacchetto Python e comando CLI
│   ├── cli.py                    # comandi `bibcheck` e opzioni
│   ├── ingest/                   # parser BibTeX, PDF e testo
│   ├── resolve/                  # Crossref, OpenAlex, fuzzy match e LLM opzionale
│   ├── graph/                    # cache e attraversamento del grafo citazionale
│   └── report/                   # output Markdown e JSON
├── tests/                        # test automatici del pacchetto
├── .github/skills/bibcheck/      # skill per agenti compatibili
│   ├── SKILL.md                  # istruzioni operative dell’agente
│   └── README.md                 # installazione manuale della skill
├── pyproject.toml                # metadati, dipendenze e comando console
├── uv.lock                       # versioni bloccate delle dipendenze
├── .env.example                  # esempio di configurazione LLM locale
└── README.md                     # questa guida
```

Le directory `bibcheck-results*` sono risultati di esecuzioni locali e non fanno parte del pacchetto distribuito.

## Sviluppo e test

Per preparare l’ambiente del repository:

```powershell
uv sync --extra test
uv run python -m pytest
```

Il pacchetto distribuibile si costruisce con:

```powershell
uv build
```

Gli artefatti vengono creati in `dist/`. Prima di pubblicare su PyPI è opportuno controllare il contenuto del wheel e provarlo in un ambiente pulito o su TestPyPI.

## Pubblicazione su PyPI

La pubblicazione è facoltativa e non è necessaria per usare il progetto localmente. In sintesi:

1. creare un account su PyPI e, preferibilmente, un token limitato al progetto;
2. eseguire `uv build`;
3. controllare gli artefatti in `dist/`;
4. caricare prima su TestPyPI;
5. caricare su PyPI usando il token, senza salvarlo nei file versionati.

Il nome di distribuzione `bibcheck` deve essere disponibile su PyPI. L’upload reale richiede le credenziali del proprietario e non viene eseguito da questo repository.

## Limiti

- la verifica richiede accesso alla rete;
- Crossref e OpenAlex possono avere dati incompleti o diversi tra loro;
- il limite di richieste può produrre un risultato parziale;
- la cache può riutilizzare risoluzioni precedenti;
- nessun risultato sostituisce la revisione della bibliografia originale.
