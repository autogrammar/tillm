#!/usr/bin/env bash
# Claude Code uses Anthropic API — not OpenRouter directly.
# Set ANTHROPIC_API_KEY in .env or: claude login
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if [[ -z "${ANTHROPIC_API_KEY:-}" ]] && ! command -v claude >/dev/null; then
  echo "error: install claude CLI and set ANTHROPIC_API_KEY (or claude login)" >&2
  exit 1
fi

tillm drive \
  --client claude-code \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Reply with exactly: pong" \
  --execute \
  --timeout 120 \
  --format json
