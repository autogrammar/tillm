# API providers

A **client** is the tool tillm drives (claude-code, aider, codex). A
**provider** is the API or subscription serving the model behind it. tillm
owns the provider registry, secure token storage, connectivity probes, and
the environment overlay applied to the client subprocess.

## Walkthrough: claude-code on z.ai (GLM)

```bash
# 1. Store the token (prompted via getpass, saved chmod 600, auto-probed)
tillm provider set z.ai
# or non-interactively:
tillm provider set z.ai --token "$ZAI_API_KEY" --model glm-4.7

# 2. Verify connectivity any time
tillm provider test z.ai
# ✓ z.ai: messages endpoint OK (model glm-4.7)

# 3. Drive claude-code through z.ai
tillm drive --client claude-code --provider z.ai \
  --prompt "Reply with exactly: ok" --execute

# 4. Make it the default for everything (incl. koru autonomy)
export TILLM_PROVIDER=z.ai
export KORU_TILLM_CLIENT=claude-code
koru -a --ide claude
```

Interactive picker with the same registry: `koru tillm`.

## How the overlay works

| Client protocol | Env applied |
| --- | --- |
| anthropic (claude-code) | `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL` |
| openai (aider, codex) | `OPENAI_API_BASE`, `OPENAI_BASE_URL`, `OPENAI_API_KEY` |

The overlay is computed in `build_drive_plan` (`ShellDrivePlan.env_overlay`)
and merged into the subprocess env by the binary/docker transports — the
parent process environment is never mutated.

## Token resolution

1. Provider's env var (`ZAI_API_KEY`, `OPENROUTER_API_KEY`, …) — always wins.
2. Store: `~/.config/tillm/providers.json` (chmod 600; `TILLM_CONFIG_DIR`
   overrides the directory — used by tests).

API providers without any token fail fast with an actionable message; probes
report auth rejections (401/403) separately from model/endpoint errors.

## Adding a provider

Add a `ProviderSpec` to `_PROVIDERS` in `src/tillm/providers.py`: id, token
env var, base URL per protocol (anthropic/openai), probe models, aliases.
Clients gain provider support via `_CLIENT_PROTOCOLS`.
