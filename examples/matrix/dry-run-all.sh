#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

tillm drive \
  --all \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Matrix smoke: describe your role in one line. No edits." \
  --parallel 2 \
  --format json
