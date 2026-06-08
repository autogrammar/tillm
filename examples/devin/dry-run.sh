#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

tillm drive \
  --client devin \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Outline a short plan to add HTTP transport to tillm. Do not edit files." \
  --format json
