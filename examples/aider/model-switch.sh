#!/usr/bin/env bash
# Usage: bash examples/aider/model-switch.sh openrouter/qwen/qwen3-coder-next
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

model="${1:-openrouter/deepseek/deepseek-v4-pro}"
export AIDER_MODEL="$model"

echo "testing aider with model: $AIDER_MODEL" >&2

tillm drive \
  --client aider \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Reply with exactly: ok" \
  --execute \
  --timeout 120 \
  --format json
