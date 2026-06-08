#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

tillm drive \
  --client claude-code \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Summarize the tillm registry in three bullet points. Do not edit files." \
  --format json
