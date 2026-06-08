# tillm examples — shell LLM smoke tests

Runnable scripts to test vendor CLIs through `tillm` with **OpenRouter**.

## Quick start

```bash
# 1. Copy and fill API key
cp examples/openrouter/env.example .env
# edit .env → set OPENROUTER_API_KEY

# 2. Load env (from repo root)
source examples/openrouter/load-env.sh

# 3. Pick a client
bash examples/aider/execute.sh
bash examples/codex/dry-run.sh
bash examples/matrix/dry-run-available.sh
```

## Layout

| Path | Client | OpenRouter | Execute |
| --- | --- | --- | --- |
| [openrouter/](openrouter/) | shared env + models | setup | — |
| [aider/](aider/) | aider | **native** (`AIDER_MODEL`) | yes |
| [claude-code/](claude-code/) | Claude Code | dry-run only¹ | needs `ANTHROPIC_API_KEY` |
| [codex/](codex/) | Codex CLI | dry-run only¹ | needs `OPENAI_API_KEY` |
| [devin/](devin/) | Devin CLI | dry-run only | needs `DEVIN_API_KEY` |
| [gemini-cli/](gemini-cli/) | Gemini CLI | — | needs `gemini` + Google key |
| [qwen-code/](qwen-code/) | Qwen Code | — | needs `qwen-code` + DashScope |
| [opencode/](opencode/) | OpenCode | — | needs `opencode` binary |
| [cline/](cline/) | Cline | dry-run only | no headless execute |
| [matrix/](matrix/) | multi-client | — | dry-run fanout |
| [dsl/](dsl/) | dsl2tillm scripts | — | query + drive |
| [control-layer/](control-layer/) | REST / NLP / URI | — | adapters |

¹ OpenRouter works end-to-end **today** mainly via **aider**. Other clients: use `dry-run.sh` to verify tillm wiring; for `--execute` use the vendor's native API key (see per-client README).

## Suggested OpenRouter models (aider)

| Model slug | Use case |
| --- | --- |
| `openrouter/deepseek/deepseek-v4-pro` | coding / refactor |
| `openrouter/qwen/qwen3-coder-next` | coding |
| `openrouter/anthropic/claude-sonnet-4` | reasoning |
| `openrouter/google/gemini-2.5-pro` | general |

Set in `.env` or per-run:

```bash
export AIDER_MODEL=openrouter/deepseek/deepseek-v4-pro
bash examples/aider/execute.sh
```

## See also

- [docs/configuration.md](../docs/configuration.md)
- [docs/clients/README.md](../docs/clients/README.md)
