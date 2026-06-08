# aider

`aider` is a shell LLM coding client controlled through tillm (unified registry + drive pipeline).

## When to use

| Scenario | Command |
| --- | --- |
| Dry-run a task prompt | `tillm drive --client aider --prompt "Fix tests"` |
| Execute a task prompt | `tillm drive --client aider --prompt "Fix tests" --execute` |
| Natural-language intent | `tillm nlp "aider: napraw testy"` |
| Via DSL | `dsl2tillm exec 'DRIVE CLIENT aider PROMPT "fix tests" EXECUTE true'` |

tillm saves every prompt under `.koru/tillm/prompts/` before invoking the client.
For aider, tillm uses the stable `--message-file` contract with `argv_prefix`:
`--no-show-model-warnings --yes-always`.

## Environment

### OpenRouter (recommended in semcod)

In project `.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=openrouter/deepseek/deepseek-v4-pro
AIDER_MODEL=openrouter/deepseek/deepseek-v4-pro
```

Load and run:

```bash
set -a && source .env && set +a
export OPENAI_API_KEY="$OPENROUTER_API_KEY"   # tillm readiness workaround

tillm drive --client aider --prompt "Fix tests" --execute
```

> **Note:** aider reads `AIDER_MODEL`, not `LLM_MODEL`. `LLM_MODEL` is for pfix and other semcod tools.

### Direct provider keys

```bash
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=sk-ant-...
export AIDER_MODEL=openrouter/deepseek/deepseek-v4-pro
```

### Model override without `.env`

```bash
tillm drive --client aider --prompt "Fix tests" --execute \
  --extra-arg --model --extra-arg openrouter/deepseek/deepseek-v4-pro
```

Or aider's own env file:

```bash
tillm drive --client aider --prompt "Fix tests" --execute \
  --extra-arg --env-file --extra-arg .env \
  --extra-arg --model --extra-arg openrouter/deepseek/deepseek-v4-pro
```

## Docker

See [aider-docker-autoloop.md](aider-docker-autoloop.md) for container workflows.
For tillm Docker transport: `TILLM_BACKEND=docker` + [deploy/docker-compose.yml](../../deploy/docker-compose.yml).
