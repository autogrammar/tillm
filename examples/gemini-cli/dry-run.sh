#!/usr/bin/env bash
# Requires: npm i -g @google/gemini-cli
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if ! command -v gemini >/dev/null; then
  echo "skip: gemini not in PATH. Install: npm i -g @google/gemini-cli" >&2
  exit 0
fi

tillm drive \
  --client gemini-cli \
  --project "$TILLM_REPO_ROOT" \
  --prompt "What is tillm in one sentence? Do not edit files." \
  --format json
