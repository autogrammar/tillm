#!/usr/bin/env bash
# Safe refactor demo on examples/fixtures/demo_module.py
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

fixture="$TILLM_REPO_ROOT/examples/fixtures/demo_module.py"

tillm drive \
  --client aider \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Refactor ${fixture#"$TILLM_REPO_ROOT"/} only: extract duplicate string 'hello' into a constant HELLO_PREFIX. Do not touch other files." \
  --execute \
  --timeout 180 \
  --format json
