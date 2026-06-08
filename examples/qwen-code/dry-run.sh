#!/usr/bin/env bash
# Requires: npm i -g @qwen-code/qwen-code
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if ! command -v qwen-code >/dev/null && ! command -v qwen >/dev/null; then
  echo "skip: qwen-code not in PATH. Install: npm i -g @qwen-code/qwen-code" >&2
  exit 0
fi

tillm drive \
  --client qwen-code \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Explain tillm registry in one sentence. Do not edit files." \
  --format json
