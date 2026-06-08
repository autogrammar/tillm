# Tillm control layers (`*2tillm`)

Warstwa kontroli według [`CONTROL_LAYER_PROMPT.template.md`](CONTROL_LAYER_PROMPT.template.md) (referencja: `gillm`, `doql`).

**See also:** [README.md](../README.md) · [docs/control-layer.md](../docs/control-layer.md) · [docs/configuration.md](../docs/configuration.md) · [SUMD.md](../SUMD.md) · [TODO.md](../TODO.md)

## Paczki

| Pakiet | Rola | Port |
|--------|------|------|
| **dsl2tillm** | DSL + JSON Schema + CQRS bus + EventStore | — |
| **uri2tillm** | `tillm://` → linia DSL → `dispatch()` | — |
| **nlp2tillm** | NL → DSL (`to-dsl`); `apply` = dispatch | — |
| **cli2tillm** | Shell REPL / exec / run | — |
| **mcp2tillm** | MCP stdio (`tillm_run_command`, …) | — |
| **rest2tillm** | FastAPI `/v1/dsl`, port **8216** | 8216 |

Domena shell LLM (registry, drive, matrix, docker) pozostaje w `src/tillm/` — adaptery są cienkimi mostami.

## Instalacja (dev)

```bash
bash packages/install-dev.sh
```

## Szybki smoke test

```bash
dsl2tillm validate-schema
dsl2tillm exec HEALTH
dsl2tillm exec CLIENTS
nlp2tillm to-dsl "drive aider: fix tests"
curl http://127.0.0.1:8216/health
```

## DSL tillm (shell control)

```text
HEALTH
CLIENTS
ORIENT
ACTIONS
VALIDATE
RESOLVE "aider: fix tests"
DRIVE CLIENT aider PROMPT "fix tests"
DRIVE CLIENT codex PROMPT "plan" EXECUTE true PROFILE automation
DRIVE_MATRIX CLIENTS aider,codex PROMPT "review" PARALLEL 2
DRIVE_MATRIX ALL PROMPT "review"
DOCKER_STATUS
```

## Verby

| Typ | Verby |
|-----|-------|
| Query | `HEALTH`, `CLIENTS`, `ORIENT`, `ACTIONS`, `VALIDATE`, `RESOLVE`, `DOCKER_STATUS` |
| Command | `DRIVE`, `DRIVE_MATRIX` |

## Backendy transportu

| Tryb | Env | Opis |
|------|-----|------|
| `binary` | `TILLM_BACKEND=binary` (domyślnie) | lokalny subprocess / PATH |
| `docker` | `TILLM_BACKEND=docker` | `docker compose exec` do serwisu `tillm-<client>` |

Compose scaffold: [deploy/docker-compose.yml](../deploy/docker-compose.yml)
