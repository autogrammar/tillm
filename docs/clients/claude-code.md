# Claude Code

Claude Code is Anthropic's shell LLM coding client. In the semcod ecosystem it
is registered and launched by SLLM so Koru can delegate shell-agent control
through a single plugin boundary.

## When to use

| Scenario | SLLM command |
|---|---|
| Dry-run a task prompt | `tillm drive --client claude-code --prompt "Fix PLF-21"` |
| Execute a task prompt | `tillm drive --client claude-code --prompt "Fix PLF-21" --execute` |
| Natural-language intent | `tillm nlp "claude: napraw importy"` |

For explicit `tillm drive`, Claude Code is treated conservatively as a stdin
client. Koru launch compatibility keeps TTY behavior for interactive sessions.

## Environment

Claude Code needs Anthropic authentication:

```bash
claude-code login
# or
export ANTHROPIC_API_KEY=sk-ant-...
```

Project-specific rules files, permissions, and CI wrappers should stay in the
project repository. SLLM owns only the shell-client registry and invocation
control plane.
