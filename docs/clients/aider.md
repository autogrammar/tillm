# aider

`aider` is a shell LLM coding client. In the semcod ecosystem it is controlled
through SLLM instead of Koru keeping a separate launcher.

## When to use

| Scenario | SLLM command |
|---|---|
| Dry-run a task prompt | `tillm drive --client aider --prompt "Fix tests"` |
| Execute a task prompt | `tillm drive --client aider --prompt "Fix tests" --execute` |
| Natural-language intent | `tillm nlp "aider: napraw testy"` |

SLLM saves every prompt under `.koru/tillm/prompts/` before invoking the client.
For `aider`, SLLM uses the stable `--message-file` prompt contract.

## Environment

`aider` usually requires a model provider key. For OpenRouter-backed setups:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
export AIDER_MODEL=openrouter/deepseek/deepseek-v4-pro
```

Project-specific Docker, Taskfile, and workflow integration should stay in the
project repository. SLLM owns only the shell-client registry and invocation
control plane.
