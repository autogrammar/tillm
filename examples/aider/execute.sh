#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "error: set OPENROUTER_API_KEY in .env" >&2
  exit 1
fi

echo "model: ${AIDER_MODEL}" >&2

tillm drive \
  --client aider \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Reply with exactly one word: pong. Do not edit any files." \
  --execute \
  --timeout 120 \
  --format json
