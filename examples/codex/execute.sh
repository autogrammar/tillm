#!/usr/bin/env bash
# Codex CLI uses OpenAI API — not OpenRouter directly.
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "error: set OPENAI_API_KEY (OpenAI, not OpenRouter) for codex execute" >&2
  exit 1
fi

tillm drive \
  --client codex \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Reply with exactly: pong" \
  --execute \
  --timeout 120 \
  --format json
