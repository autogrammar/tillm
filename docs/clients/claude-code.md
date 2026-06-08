# Claude Code

Claude Code is Anthropic's shell LLM coding client, registered and launched by tillm.

## When to use

| Scenario | Command |
| --- | --- |
| Dry-run a task prompt | `tillm drive --client claude-code --prompt "Fix PLF-21"` |
| Execute a task prompt | `tillm drive --client claude-code --prompt "Fix PLF-21" --execute` |
| CI / permission bypass | `tillm drive --client claude-code --prompt "..." --execute --profile automation` |
| Natural-language intent | `tillm nlp "claude: napraw importy"` |

For `tillm drive`, Claude Code is a stdin client (`claude -p` with prompt on stdin).

## Environment

```bash
claude login
# or
export ANTHROPIC_API_KEY=sk-ant-...
```

## Execute profiles

| Profile | Args |
| --- | --- |
| `default` | `-p` |
| `automation` | `-p --dangerously-skip-permissions` |

```bash
export TILLM_EXECUTE_PROFILE=automation
tillm drive --client claude-code --prompt "Fix PLF-21" --execute
```

Project-specific rules, permissions, and CI wrappers stay in the project repository.
tillm owns only the shell-client registry and invocation control plane.
