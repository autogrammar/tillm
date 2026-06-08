#!/usr/bin/env bash
# Requires: npm i -g opencode-ai
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if ! command -v opencode >/dev/null; then
  echo "skip: opencode not in PATH. Install: npm i -g opencode-ai" >&2
  exit 0
fi

tillm drive \
  --client opencode \
  --project "$TILLM_REPO_ROOT" \
  --prompt "What does tillm drive do? One sentence. Do not edit files." \
  --format json
