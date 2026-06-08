# Configuration

## `.env` in the project root

Copy `.env.example` and fill in keys. tillm **auto-loads** `<project>/.env` on every CLI run and before `drive` / `validate` (via `tillm.project_env` + optional [env2llm](https://github.com/semcod/env2llm)).

Manual export is still supported (shell env wins over `.env` for non-empty values):

```bash
set -a && source .env && set +a
```

| Variable | Purpose |
| --- | --- |
| `TILLM_ENV_FILE` | Override path to env file (default: `<project>/.env`) |
| `TILLM_ENV2LLM` | `0` disables env2llm map refresh (default: `1`) |

### Semcod / pfix variables

| Variable | Purpose |
| --- | --- |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `LLM_MODEL` | Default model for pfix and other semcod tools |

### tillm variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `TILLM_DEFAULT_CLIENT` | `aider` | Default client for `tillm nlp` |
| `TILLM_EXECUTE_PROFILE` | `default` | `automation` = permission bypass (CI) |
| `TILLM_BACKEND` | `binary` | `docker` = compose exec transport |
| `TILLM_COMPOSE_FILE` | `deploy/docker-compose.yml` | Docker compose path |
| `TILLM_WORKSPACE` | `..` | Workspace mount for Docker services |
| `TILLM_NLP2DSL` | off | Enable external `nlp2dsl` bridge |
| `NLP2DSL_BACKEND_URL` | — | URL of NLP2DSL service |

## aider + OpenRouter

aider reads **`AIDER_MODEL`**, not `LLM_MODEL`. Add both to `.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=openrouter/deepseek/deepseek-v4-pro
AIDER_MODEL=openrouter/deepseek/deepseek-v4-pro
```

With `OPENROUTER_API_KEY` in `.env`, tillm auto-maps `OPENAI_API_KEY` and `AIDER_MODEL` from `LLM_MODEL` — no manual workaround needed.

```bash
tillm drive --client aider --prompt "fix tests" --execute
```

Or pass the model explicitly:

```bash
tillm drive --client aider --prompt "fix tests" --execute \
  --extra-arg --model --extra-arg openrouter/deepseek/deepseek-v4-pro
```

## Execute profiles

| Profile | Use case |
| --- | --- |
| `default` | Conservative headless flags per vendor |
| `automation` | Permission bypass for CI / sandboxed runs |

```bash
tillm drive --client claude-code --prompt "..." --execute --profile automation
export TILLM_EXECUTE_PROFILE=automation
```

## Docker transport

```bash
export TILLM_BACKEND=docker
docker compose -f deploy/docker-compose.yml up -d
dsl2tillm exec DOCKER_STATUS
```

Compose scaffold: [deploy/docker-compose.yml](../deploy/docker-compose.yml)
