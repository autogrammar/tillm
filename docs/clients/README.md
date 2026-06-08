# Shell clients

tillm registers eight vendor CLIs. Use `tillm clients` for live status.

| Client | Binary | Env vars | Execute | Profiles |
| --- | --- | --- | --- | --- |
| **claude-code** | `claude` | `ANTHROPIC_API_KEY` | yes | default, automation |
| **aider** | `aider` | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`¹ | yes | default |
| **codex** | `codex` | `OPENAI_API_KEY` | yes | default, automation |
| **gemini-cli** | `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | yes | default, automation |
| **cline** | `cline` | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` | dry-run only | default |
| **qwen-code** | `qwen-code` | `DASHSCOPE_API_KEY` or `OPENAI_API_KEY` | yes | default |
| **opencode** | `opencode` | — | yes | default |
| **devin** | `devin` | `DEVIN_API_KEY` | yes | default, automation |

¹ For OpenRouter, see [configuration.md](../configuration.md#aider--openrouter).

## Status legend (`tillm clients`)

| Mark | Meaning |
| --- | --- |
| `ok` | Binary in PATH and required env vars set |
| `~` | Binary in PATH, missing env vars |
| `--` | Binary not in PATH |

## Commands

```bash
tillm clients
tillm validate
tillm drive --client aider --prompt "Fix tests"              # dry-run
tillm drive --client aider --prompt "Fix tests" --execute
tillm drive --clients aider,codex --prompt "review"          # matrix dry-run
tillm drive --all --prompt "review" --parallel 2 --execute
tillm nlp "codex: plan refactor"
```

## Per-client docs

- [aider.md](aider.md)
- [claude-code.md](claude-code.md)
- [aider-docker-autoloop.md](aider-docker-autoloop.md)
