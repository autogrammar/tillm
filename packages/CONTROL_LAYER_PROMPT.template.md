# Prompt: warstwa kontroli `*2{pkg}`

> Szablon do wklejenia w Cursor/LLM. Zamień `{pkg}` na nazwę paczki (np. `doql`, `testql`, `oql`).
> Przykład: `{pkg}` → `doql` daje `mcp2doql`, `dsl2doql`, …

## Tabela substytucji

| Placeholder | doql | nlp2dsl | testql |
|-------------|------|---------|--------|
| `{pkg}` | doql | nlp2dsl | testql |
| manifest | `app.doql.less` | `app.doql.less` (wspólny) | `app.testql.less` |
| EventStore | `app.doql.events.pb` | `app.nlp2dsl.events.pb` | `app.testql.events.pb` |
| REST port | `8210` | `8212` | `8214` |
| profil verbów | manifest DSL | runtime / NL | manifest DSL |
| referencja golden | `packages/dsl2doql/` | `packages/dsl2nlp2dsl/` | — |

## Najpierw przeczytaj (przed implementacją)

1. `packages/README.md` monorepo — indeks paczek i diagram przepływu
2. Istniejące `packages/*2{pkg}/` — rozszerz, nie buduj od zera
3. Lifecycle domeny w `{pkg}/` — verby wynikają z niego, nie z szablonu
4. Referencje golden: `doql` (manifest), `nlp2dsl` (runtime + shims `control.py`)

---

## Prompt (kopiuj od linii poniżej)

```
Zrefaktoryzuj / utwórz warstwę kontroli dla paczki `{pkg}` w monorepo.

## Cel

Paczka `{pkg}` ma być sterowana wyłącznie przez standaryzowany DSL i bus CQRS/ES.
Adaptery wejścia (MCP, REST, CLI, URI, NL) nie zawierają logiki domenowej — tylko delegują do `dsl2{pkg}`.

## Wymagane paczki w `packages/`

| Paczka | Rola | Dozwolone zależności |
|--------|------|----------------------|
| `dsl2{pkg}` | Grammar DSL + **JSON Schema** + **Protobuf** + CQRS bus + EventStore | `{pkg}` (core), `protobuf`, `jsonschema`, stdlib; **manifest DSL**: jawne `uri2{pkg}`, `nlp2{pkg}` w handlerach (lazy import preferowany) |
| `uri2{pkg}` | `uri://` → linia DSL → `dsl2{pkg}.dispatch()` | `dsl2{pkg}` |
| `nlp2{pkg}` | NL → linia DSL (bez side-effect) → opcjonalnie `dispatch()` | `dsl2{pkg}` |
| `cli2{pkg}` | Shell REPL / exec / run script | `dsl2{pkg}` |
| `mcp2{pkg}` | Serwer MCP (stdio), narzędzia = cienkie wrappery DSL | `dsl2{pkg}` |
| `rest2{pkg}` | REST API (FastAPI), endpointy = cienkie wrappery DSL | `dsl2{pkg}` |

**Nazewnictwo złożonego `{pkg}`** (np. `nlp2dsl`):
- Paczki: `dsl2nlp2dsl`, `uri2nlp2dsl`, `nlp2nlp2dsl` (nie `nlp2dsl2nlp2dsl`)
- MCP tools: pełna nazwa produktu — `nlp2dsl_run_command`, nie `dsl_run_command`

Reguły twarde:
- JEDYNY punkt wykonania mutacji: `dsl2{pkg}.dispatch()` → `CommandHandler`
- Query (read-only): `QueryHandler` — bez zapisu eventów
- Command (write): handler wykonuje się **przed** append do EventStore
- Adaptery NIE importują się nawzajem (wyjątek: wszystkie → `dsl2{pkg}`)
- Logika domenowa (parse, validate, export, adopt, konwertery) zostaje w `{pkg}/`, nie w adapterach
- Ta sama linia DSL daje identyczny wynik z CLI, URI, MCP, REST

## Schemat przepływu (docelowy)

```mermaid
flowchart TB
  subgraph adapters [Adaptery wejścia — packages]
    NL[nlp2{pkg}]
    URI[uri2{pkg}]
    CLI[cli2{pkg}]
    MCP[mcp2{pkg}]
    REST[rest2{pkg}]
  end

  subgraph control [Warstwa kontroli]
    TXT[linia tekstowa DSL]
    DICT[dict JSON]
    PBIN[bytes protobuf]
    SCH[JSON Schema validate]
    DSL[dsl2{pkg}.dispatch]
    Q[QueryHandler]
    C[CommandHandler]
    ES[(EventStore *.events.pb / *.jsonl)]
  end

  subgraph domain [Domena — {pkg}/]
    P[parse / validate]
    A[adopt / import]
    X[export / materialize]
  end

  NL -->|"NL → linia DSL"| TXT
  URI -->|"uri → linia DSL"| TXT
  CLI -->|"linia DSL"| TXT
  MCP -->|"linia DSL / dict / pb"| TXT
  MCP --> DICT
  MCP --> PBIN
  REST -->|"linia DSL / dict / pb"| TXT
  REST --> DICT
  REST --> PBIN

  TXT --> SCH
  DICT --> SCH
  PBIN -->|"pb_codec"| DICT
  DICT --> SCH
  SCH --> DSL

  DSL -->|QUERY RESOLVE VALIDATE …| Q
  DSL -->|PATCH APPEND GENERATE ADOPT …| C
  C --> P
  C --> ES
  Q --> P
  Q --> X
  C --> X
  C --> A
```

## Schemat URI (dwa poziomy)

1. **Adres zasobu** (target komendy):
   `{pkg}://block/entity/Contact?file=app.{pkg}.less`

2. **Adres komendy DSL** (opcjonalnie, uri2{pkg}):
   `{pkg}://cmd/QUERY?target={pkg}://block/app&file=app.{pkg}.less&format=less`

`uri2{pkg}` dekoduje URI → **jedna linia DSL** → `dsl2{pkg}.dispatch()`.

## DSL: tekst + Schema + Protobuf

Warstwa `dsl2{pkg}` utrzymuje **trzy reprezentacje** tej samej komendy:

| Reprezentacja | Pliki | Rola |
|---------------|-------|------|
| **Tekst** (canonical UX) | `*.dsl`, REPL, CLI | czytelna linia: `QUERY …` |
| **JSON Schema** | `schema/commands/*.schema.json` | walidacja pól, dokumentacja, codegen |
| **Protobuf** | `proto/dsl2{pkg}/v1/*.proto` | serializacja REST/MCP/ES, wersjonowanie |

### Przepływ kodowania (dwa wejścia, jeden bus)

```text
# Wejście tekstowe (CLI, URI, MCP text/plain)
linia DSL → grammar.py → dict → jsonschema → handler → DslResult

# Wejście strukturalne (REST/MCP json lub protobuf)
dict / DslEnvelope bytes → pb_codec (jeśli pb) → jsonschema → handler → DslResult

# Wyjście opcjonalne
DslResult → to_text() / to_json() / SerializeToString (REST/MCP pb)
```

Reguły:
- **Schema jest źródłem prawdy** dla pól komend (nazwy, typy, required).
- **Protobuf odzwierciedla Schema** — każdy `verb` ma message `XxxCommand` / `XxxQuery`.
- Tekst DSL to **składnia cukrowa** nad Schema (nie odwrotnie).
- EventStore preferuje **protobuf** (`*.events.pb` lub base64 w jsonl); jsonl dozwolony w dev.
- REST/MCP akceptują: `text/plain` (linia DSL), `application/json` (dict), `application/x-protobuf`.
- Protobuf na wejściu busa jest **opcjonalny** — walidacja zawsze przez Schema (dict).

### Przykład Schema (`schema/commands/query.schema.json`)

```json
{
  "$id": "dsl2{pkg}/commands/query",
  "type": "object",
  "required": ["verb", "target"],
  "properties": {
    "verb": { "const": "QUERY" },
    "target": { "type": "string", "format": "uri", "pattern": "^{pkg}://" },
    "file": { "type": "string" },
    "format": { "enum": ["json", "yaml", "less"], "default": "json" }
  },
  "additionalProperties": false
}
```

### Przykład Protobuf — `command.proto` (bez Result/Event)

```protobuf
syntax = "proto3";
package dsl2{pkg}.v1;

message QueryCommand {
  string target = 1;   // {pkg}://block/...
  string file = 2;
  string format = 3;   // json|yaml|less
}

message PatchCommand {
  string target = 1;
  string file = 2;
  string with_path = 3;
  bytes with_content = 4;
}

message DslEnvelope {
  string verb = 1;     // QUERY | PATCH | VALIDATE | ...
  oneof body {
    QueryCommand query = 10;
    PatchCommand patch = 11;
    // … pozostałe komendy
  }
  string default_file = 20;
  string correlation_id = 21;
}
```

### Przykład Protobuf — `result.proto` (osobny plik)

```protobuf
syntax = "proto3";
package dsl2{pkg}.v1;

import "dsl2{pkg}/v1/command.proto";

message DslResult {
  bool ok = 1;
  string verb = 2;
  string output = 3;
  bytes data_json = 4;
  string error = 5;
  string event_id = 6;   // Commands only
}

message DslEvent {
  string id = 1;
  int64 ts_unix = 2;
  DslEnvelope command = 3;
  DslResult result = 4;
  string correlation_id = 5;
}
```

**Wersjonowanie proto:** nowe pola = nowe numery; `v2/` tylko przy breaking change.

### Generacja kodu (oczekiwana)

```bash
# w packages/dsl2{pkg}/
bash scripts/generate-proto.sh   # preferowane: grpc_tools.protoc
# lub: buf generate
python -m dsl2{pkg}.codegen      # schema → pydantic (Faza 5)
```

Skrypt `scripts/generate-proto.sh` (wzorzec):

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m grpc_tools.protoc -I "$ROOT/proto" --python_out="$ROOT/src" \
  "$ROOT/proto/dsl2{pkg}/v1/command.proto" \
  "$ROOT/proto/dsl2{pkg}/v1/result.proto"
```

Opcjonalnie `buf.yaml`:

```yaml
version: v2
modules:
  - path: proto
    name: buf.build/oqlos/dsl2{pkg}
```

**WAŻNE — ścieżka importów protobuf:**
- `package dsl2{pkg}.v1;` w `.proto` → wygenerowane pliki **muszą** trafić do `src/dsl2{pkg}/v1/*_pb2.py`
- **NIE** używaj `src/dsl2{pkg}/gen/` — `protoc` generuje importy `from dsl2{pkg}.v1 import …` i `gen/` łamie runtime
- Po generacji dodaj `src/dsl2{pkg}/v1/__init__.py`

Wygenerowane / ręczne moduły:
- `src/dsl2{pkg}/v1/` — `*_pb2.py` z `.proto`
- `src/dsl2{pkg}/schema/commands/` — `*.schema.json` (wewnątrz `src/`, nie obok!) + `schema_registry.py`
- `src/dsl2{pkg}/pb_codec.py` — dict ↔ `DslEnvelope` / `DslResult` (osobno od `codec.py`)
- `src/dsl2{pkg}/result.py` — `DslResult` dataclass (**osobny plik** — unika cykli importów)
- `src/dsl2{pkg}/engine.py` — **opcjonalny shim** wstecznej kompatybilności (re-export z `bus.py`)

### `pyproject.toml` (fragment)

```toml
[project]
dependencies = [
    "{pkg}>=1.0.0",
    "protobuf>=5.0",
    "jsonschema>=4.0",
    # manifest DSL (doql): jawne zależności handlerów:
    # "uri2{pkg}>=0.1.0", "nlp2{pkg}>=0.1.0",
]

[project.optional-dependencies]
codegen = ["grpcio-tools>=1.60"]
dev = ["pytest>=8.0"]

[tool.setuptools.package-data]
"dsl2{pkg}" = ["schema/commands/*.json"]
```

## Grammar DSL tekstowa (minimum)

Jedna linia = jedna komenda. Komentarz: `#`.

**Verby nie są uniwersalne** — wynikają z lifecycle domeny `{pkg}`:

| Profil domeny | Przykładowe Query | Przykładowe Command |
|---------------|-------------------|---------------------|
| Manifest DSL (`doql`, `oql`) | `QUERY`, `RESOLVE`, `VALIDATE` | `PATCH`, `APPEND`, `MATERIALIZE`, `GENERATE`, `ADOPT`, `CONVERT` |
| Runtime / NL (`nlp2dsl`, serwisy) | `ORIENT`, `PARSE`, `PLAN`, `VALIDATE`, `HEALTH`, `ACTIONS`, `RESOLVE` | `EXECUTE`, `SIMULATE`, `GENERATE`, `CHAT`, `DRAFT`, `OBSERVE`, `COMPOSE` |

Zasada: najpierw wypisz lifecycle domeny (np. `parse → plan → validate → execute`), potem mapuj na Query/Command.

Przykłady (manifest DSL — `doql`):
```text
QUERY {pkg}://block/app?file=app.{pkg}.less FORMAT json
VALIDATE app.{pkg}.less
PATCH {pkg}://block/entity/Contact?file=app.{pkg}.less WITH contact.patch.less
APPEND app.{pkg}.less WITH workflow.fragment.less
GENERATE "CRM z kontaktami" OUT app.{pkg}.less
ADOPT . OUT app.{pkg}.less
CONVERT scenarios/test.oql OUT workflow.less
RESOLVE "pokaż workflow install" FILE app.{pkg}.less
```

## CQRS / EventStore

- `QueryResult` / `CommandResult`: protobuf `DslResult` (+ opcjonalny JSON export)
- `Event`: protobuf `DslEvent` (command + result + metadata)
- Store: `app.{pkg}.events.pb` (preferowany) lub `app.{pkg}.events.jsonl` (dev fallback)
- Format `.pb`: ramki length-prefixed (`uint32_be + protobuf_bytes`); replay czyta sekwencyjnie
- Format `.jsonl`: jedna linia JSON na event; opcjonalne pole `"pb": "<base64 DslEvent>"` dla audytu
- Replay: `dsl2{pkg} replay --file app.{pkg}.less` (odczyt sekwencji `DslEvent`)
- Walidacja przed dispatch: **schema JSON** → handler (protobuf opcjonalny na wejściu REST/MCP)
- **Kolejność CQRS**: handler wykonuje się **przed** append do EventStore (nie odwrotnie)

## Kontrakty adapterów

### cli2{pkg} / dsl2{pkg} (dual-mode CLI)

**Legacy** (wsteczna kompatybilność — bez subcommand):
```bash
dsl2{pkg} -c 'QUERY {pkg}://block/app'
dsl2{pkg} script.dsl --file app.{pkg}.less
```

**Subcommands** (nowe — pierwszy arg z `_SUBCOMMANDS`):
```bash
cli2{pkg} shell [--file app.{pkg}.less]
cli2{pkg} exec 'QUERY {pkg}://block/app'
cli2{pkg} run script.dsl
dsl2{pkg} validate-schema
dsl2{pkg} encode 'QUERY {pkg}://block/app' --format protobuf
dsl2{pkg} decode --input command.pb --format protobuf
dsl2{pkg} replay --file app.{pkg}.less
```

Wzorzec argparse: jeśli `argv[0] in _SUBCOMMANDS` → `_main_subcommand()`, inaczej `_main_legacy()` (unika kolizji positional `script` z subcommands).

### uri2{pkg}

**Poziom dojrzałości:**
- **minimal** (doql): `uri.py`, `query.py`, `patch.py`, `resolve.py` — handlery w `dsl2{pkg}`
- **pełny** (nlp2dsl): + `decode.py` (`uri → linia DSL`), `run --uri`

```bash
uri2{pkg} decode --uri '{pkg}://cmd/QUERY?...'     # → linia DSL
uri2{pkg} run --uri '{pkg}://cmd/PATCH?...'       # decode + dispatch
uri2{pkg} resolve "pokaż app" --file app.{pkg}.less
```

### nlp2{pkg}

Jeśli `nlp2{pkg}` już istnieje (np. `nlp2doql` z `apply.py`, `pipeline.py`) — dodaj `to_dsl()` / `apply_nl()` delegujące do `dispatch()`, nie przenoś całej logiki NL do busa.

```bash
nlp2{pkg} to-dsl "validate app.{pkg}.less"          # tylko DSL, bez wykonania
nlp2{pkg} apply "validate app.{pkg}.less"           # to-dsl + dispatch
nlp2{pkg} generate "CRM" --out app.{pkg}.less
```

### mcp2{pkg}

```bash
mcp2{pkg} serve
```

Narzędzia MCP (minimum DSL):
- `{product}_run_dsl(script: str, default_file: str = "")` — `{product}` = pełna nazwa (`doql`, `nlp2dsl`)
- `{product}_run_command(command: str, default_file: str = "")`
- `{product}_run_command_pb(envelope_bytes: bytes) -> bytes`
- `{product}_to_dsl(prompt: str) -> str`

**Legacy granular tools** (dozwolone obok DSL): np. `doql_query`, `doql_patch`, `doql_validate` — zachowaj dla wstecznej kompatybilności MCP klientów; nowe integracje preferują `{product}_run_command`.

### rest2{pkg}

```bash
rest2{pkg} serve --port 8xxx
```

**Tabela portów** (rezerwa `82xx`):

| Produkt | Port |
|---------|------|
| doql | 8210 |
| nlp2dsl | 8212 |
| testql | 8214 |

Endpointy (minimum):
- `POST /v1/dsl` — `text/plain` | `application/json` | `application/x-protobuf` (`DslEnvelope`)
- `POST /v1/commands` — alias; body zgodny ze Schema
- `GET /v1/schema/{verb}` — JSON Schema komendy
- `GET /v1/proto` — descriptor / link do `.proto`
- `GET /v1/events?file=app.{pkg}.less` — stream `DslEvent` (pb lub json)
- `GET /health`

## Co przenieść do `{pkg}/` (core)

Jeśli logika jest w adapterze, przenieś do core:
- skanery adopt → `{pkg}/adopt/scanner/`
- konwertery formatów → `{pkg}/importers/`
- parse/validate/export → już w `{pkg}/`

Adapter zostaje cienkim mostem.

## Migracja istniejących paczek `packages/` (monorepo z LLM)

Gdy monorepo ma już paczki SDK korzystające z LLM / env2llm — **nie przenoś ich od razu do `dsl2{pkg}`**.
Zamiast tego dodaj cienki shim `control.py` delegujący do busa:

```python
# packages/foo/src/foo/control.py
def dispatch_validate(**kwargs) -> dict:
    from dsl2{pkg} import dispatch
    return dispatch('VALIDATE …').to_dict()
```

Wzorzec (sprawdzony na `nlp2dsl`):
| Istniejąca paczka | Verb DSL | Plik shim |
|-------------------|----------|-----------|
| kontrakty / drafty LLM | `DRAFT` | `dsl-contracts/control.py` |
| walidacja runtime | `VALIDATE` | `dsl-validate/control.py` |
| artefakty / registry | `OBSERVE` | `*-artifacts/control.py` |
| compose / deploy | `COMPOSE` | `*-stack/control.py` |
| legacy MCP | delegacja | `{pkg}-mcp/server.py` → `mcp2{pkg}` + zachowaj stare narzędzia HTTP |

Kolejność `install-dev.sh` (po paczkach SDK, przed integracjami):
`dsl2{pkg}` → `uri2{pkg}` → `nlp2{pkg}` → `cli2{pkg}` → `mcp2{pkg}` → `rest2{pkg}` → legacy `{pkg}-mcp`

## Reguły importów (unikaj cykli)

- `DslResult` w **`result.py`** — nigdy w `bus.py` jeśli importują go `handlers/`
- `handlers/` importują `result.py`, **nie** `bus.py`
- `bus.py` robi **lazy import** handlerów wewnątrz `_dispatch_cmd()`
- `uri2{pkg}` → `dsl2{pkg}`; `nlp2{pkg}` → `dsl2{pkg}`; adaptery **nie** importują się nawzajem
- `dsl2{pkg}` **nie importuje** `uri2{pkg}` na poziomie modułu — tylko lazy w handlerze `RESOLVE` (wyjątek: jawne deps w `pyproject.toml` jak w `doql` jest OK, jeśli handler ich wymaga)

## Struktura katalogów (oczekiwana)

```
packages/
  dsl2{pkg}/
    proto/dsl2{pkg}/v1/
      command.proto       # DslEnvelope, *Command, *Query
      result.proto        # DslResult, DslEvent
    src/dsl2{pkg}/
      schema/commands/    # *.schema.json — MUSI być w src/ (package-data)
      v1/                 # wygenerowane *_pb2.py (protoc → --python_out=src)
      grammar.py          # tekst DSL → dict
      codec.py            # validate(schema); encode/decode text
      pb_codec.py         # dict ↔ DslEnvelope / DslResult protobuf
      result.py           # DslResult dataclass (bez cykli)
      engine.py           # opcjonalny shim: re-export dispatch z bus.py
      schema_registry.py  # verb → JSON Schema
      bus.py              # dispatch(str | dict | bytes)
      events.py           # EventStore (*.pb length-prefixed + jsonl)
      handlers/           # query.py, command.py
      cli.py              # dual-mode: legacy + subcommands
    scripts/generate-proto.sh
    buf.yaml              # opcjonalnie
    pyproject.toml
    tests/
      test_{pkg}.py
      test_protobuf.py
      test_parity.py
  uri2{pkg}/src/uri2{pkg}/
    uri.py
    decode.py             # pełny profil; opcjonalny w minimal
    cli.py
  nlp2{pkg}/src/nlp2{pkg}/
    to_dsl.py             # lub apply.py jeśli pakiet już istnieje
    cli.py
  cli2{pkg}/src/cli2{pkg}/
    shell.py
    cli.py
  mcp2{pkg}/src/mcp2{pkg}/
    server.py
    cli.py
  rest2{pkg}/src/rest2{pkg}/
    app.py
    cli.py
```

## Kryteria akceptacji (must pass)

1. **Parity**: ta sama komenda (tekst / JSON / protobuf) → ten sam `DslResult` z:
   - `cli2{pkg} exec` / `dsl2{pkg} -c`
   - `uri2{pkg} run`
   - `mcp2{pkg}` tool `{product}_run_command`
   - `rest2{pkg}` POST `/v1/dsl`

2. **Schema** (fazowo):
   - **Faza 0 minimum**: `QUERY`, `VALIDATE`, główny Command (`PATCH` lub `EXECUTE`)
   - **Faza 4**: wszystkie publiczne verby mają `*.schema.json`
   - `dsl2{pkg} validate-schema` — Faza 0: sprawdza `verb const` w registry; Faza 5: pełny audit `handler verb ⇒ schema istnieje`

3. **Protobuf**: `dsl2{pkg} encode/decode` round-trip: tekst → pb → tekst (semantycznie równoważne).

4. **Separacja**: `nlp2{pkg} to-dsl` nie mutuje plików; mutacja tylko przez `dispatch()`.

5. **CQRS**: Query nie zapisują eventów; Command appenduje `DslEvent` (protobuf) **po** handlerze.

6. **Brak cykli**: adaptery nie importują `{pkg}/cli` ani siebie nawzajem.

7. **Testy**:
   ```bash
   pytest packages/dsl2{pkg}/tests packages/uri2{pkg}/tests \
          packages/nlp2{pkg}/tests packages/cli2{pkg}/tests \
          packages/mcp2{pkg}/tests packages/rest2{pkg}/tests -q
   ```
   + `test_parity.py` (offline: HEALTH/VALIDATE; runtime z backendem: EXECUTE/PATCH)

8. **Dokumentacja**: każdy pakiet ma README; zaktualizuj `packages/README.md` (indeks + diagram).

9. **Manifest** (jeśli dotyczy): wpisy w `app.{pkg}.less`:
   - `interface[type="cli"] page[name="dsl2{pkg}"]` + `entry: dsl2{pkg}.cli:main`
   - `interface[type="cli"] page[name="cli2{pkg}"]`
   - `interface[type="cli"] page[name="nlp2{pkg}"]`
   - `interface[type="cli"] page[name="uri2{pkg}"]`
   - `interface[type="mcp"] page[name="mcp2{pkg}"]`
   - `interface[type="api"] page[name="rest2{pkg}"]` + `port: 8xxx`
   - opcjonalnie legacy `{pkg}-mcp` jako drugi `page` pod `interface[type="mcp"]`

## Checklist przed „done”

- [ ] Diagram mermaid w `packages/README.md` zgodny z implementacją
- [ ] `dispatch()` jedyny punkt mutacji; adaptery cienkie
- [ ] `result.py` osobno; brak cykli importów
- [ ] Protobuf w `src/dsl2{pkg}/v1/`, nie `gen/`
- [ ] `validate-schema` przechodzi (Faza 0 minimum)
- [ ] `encode/decode` round-trip dla głównych verbów
- [ ] Dual-mode CLI bez kolizji argparse
- [ ] `engine.py` shim jeśli był stary import `engine`
- [ ] MCP: `{product}_run_command` + legacy tools zachowane jeśli były
- [ ] REST port z tabeli; `GET /health` działa
- [ ] `pytest packages/ -q` green
- [ ] Manifest `app.{pkg}.less` zaktualizowany

## Fazy implementacji

| Faza | Zakres |
|------|--------|
| 0 | `proto/` + `schema/` (minimum verbów) + `codec.py` + `grammar.py` |
| 1 | `dsl2{pkg}` bus + handlers + przepięcie `cli2{pkg}` + `engine.py` shim |
| 2 | `uri2{pkg}` decode→DSL; `nlp2{pkg}` to-dsl; usunąć direct calls |
| 3 | `mcp2{pkg}` + `rest2{pkg}` (text + json + protobuf) |
| 4 | EventStore protobuf + replay + pełne schema + `control.py` shims |
| 5 | `python -m dsl2{pkg}.codegen` → `models.py` (pydantic); test parity runtime |

### Szkielet `test_parity.py`

```python
"""Parity: ta sama linia DSL → ten sam wynik (offline verby)."""

from dsl2{pkg} import dispatch

def test_parity_text_vs_dict() -> None:
    line = "VALIDATE app.{pkg}.less"
    r1 = dispatch(line)
    r2 = dispatch({"verb": "VALIDATE", "path": "app.{pkg}.less"})
    assert r1.ok == r2.ok
    assert r1.verb == r2.verb

# Faza 5: test_parity_across_adapters (wymaga serwisu / plików fixture)
```

## Nie rób

- Nie duplikuj logiki domenowej w adapterach.
- Nie wołaj handlerów z `nlp2{pkg}` / `uri2{pkg}` omijając Schema + bus.
- Nie pomijaj `rest2{pkg}` — brak = fail kryteriów.
- Nie rozjedzaj Schema i Protobuf — zmiana verb wymaga obu + testu round-trip.
- Nie commituj bez uruchomienia testów.
- Nie umieszczaj `schema/` poza `src/dsl2{pkg}/` — `importlib.resources` nie znajdzie plików.
- Nie umieszczaj `DslResult` / `DslEvent` w `command.proto` — tylko w `result.proto`.
- Nie wymuszaj pełnego `decode.py` w `uri2{pkg}` jeśli minimal profil wystarczy (jak `doql`).

Na końcu podaj: listę plików, diagram przepływu po refaktorze, wynik testów, znane luki Fazy 5.
```

---

## Przykład wypełniony: `{pkg}` = `doql`

Zamień w prompcie:
- `{pkg}` → `doql`, `{product}` → `doql`
- manifest → `app.doql.less`
- EventStore → `app.doql.events.pb` (+ opcjonalny `.jsonl` w dev)
- Schema → `packages/dsl2doql/src/dsl2doql/schema/commands/*.schema.json`
- Proto → `packages/dsl2doql/proto/dsl2doql/v1/*.proto`
- REST port → `8210`
- Referencja golden → `packages/dsl2doql/`, `packages/rest2doql/`

Oczekiwane paczki:
`dsl2doql`, `uri2doql`, `nlp2doql`, `cli2doql`, `mcp2doql`, `rest2doql`

Wyjątki referencyjne:
- `dsl2doql/pyproject.toml` zależy od `uri2doql`, `nlp2doql`
- `engine.py` shim; dual-mode CLI (`-c` legacy + subcommands)
- `uri2doql` minimal (bez `decode.py`); `nlp2doql` używa `apply.py`
- MCP: `doql_run_command` + legacy `doql_query`, `doql_patch`, …
- Schema: 7 plików na 12 verbów (Faza 4 w toku)

---

## Przykład wypełniony: `{pkg}` = `nlp2dsl`

Zamień w prompcie:
- `{pkg}` → `nlp2dsl`, `{product}` → `nlp2dsl`
- manifest → `app.doql.less` (wspólny z env2llm)
- EventStore → `app.nlp2dsl.events.pb`
- Verby → lifecycle runtime: `PARSE`, `PLAN`, `VALIDATE`, `EXECUTE`, `SIMULATE`, `GENERATE`, …
- REST port → `8212`
- Istniejące paczki LLM → shim `control.py` (nie pełna migracja od razu)
- Referencja golden → `packages/dsl2nlp2dsl/`

Oczekiwane paczki:
`dsl2nlp2dsl`, `uri2nlp2dsl`, `nlp2nlp2dsl`, `cli2nlp2dsl`, `mcp2nlp2dsl`, `rest2nlp2dsl`

Uwaga nazewnictwa: `nlp2nlp2dsl` (nie `nlp2dsl2nlp2dsl`); MCP tools: `nlp2dsl_run_command`.

---

## Przykład wypełniony: `{pkg}` = `testql`

Zamień w prompcie:
- `{pkg}` → `testql`, `{product}` → `testql`
- manifest → `app.testql.less`
- REST port → `8214`
- Profil → manifest DSL (jak `doql`, skrócona lista verbów: `QUERY`, `VALIDATE`, `PATCH`, `GENERATE`)
- Brak legacy MCP — czysta implementacja od zera

Oczekiwane paczki:
`dsl2testql`, `uri2testql`, `nlp2testql`, `cli2testql`, `mcp2testql`, `rest2testql`
