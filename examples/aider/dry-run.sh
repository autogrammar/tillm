#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

tillm drive \
  --client aider \
  --project "$TILLM_REPO_ROOT" \
  --prompt "List three ways to improve test coverage. Do not edit files." \
  --format json
