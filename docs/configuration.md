# Configuration

## `.env` in the project root

Copy `.env.example` and fill in keys. tillm **does not load `.env` automatically** — export variables before running commands:

```bash
set -a && source .env && set +a
```

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

tillm readiness check for aider expects `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. For OpenRouter-only setups, use a workaround before `--execute`:

```bash
export OPENAI_API_KEY="$OPENROUTER_API_KEY"
```

Run:

```bash
set -a && source .env && set +a
export OPENAI_API_KEY="$OPENROUTER_API_KEY"

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
