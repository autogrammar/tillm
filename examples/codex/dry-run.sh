#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

tillm drive \
  --client codex \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Suggest a one-line improvement for tillm CLI help text. Do not edit files." \
  --format json
