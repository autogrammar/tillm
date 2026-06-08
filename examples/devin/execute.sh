#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if [[ -z "${DEVIN_API_KEY:-}" ]]; then
  echo "error: set DEVIN_API_KEY in .env" >&2
  exit 1
fi

tillm drive \
  --client devin \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Reply with exactly: pong" \
  --execute \
  --timeout 120 \
  --format json
