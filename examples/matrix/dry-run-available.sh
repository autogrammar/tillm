#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

tillm drive \
  --clients aider,codex,claude-code,devin \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Smoke test: reply plan only, no file edits." \
  --available-only \
  --parallel 2 \
  --format json
