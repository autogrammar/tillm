#!/usr/bin/env bash
# Cline: tillm plans prompts but does not auto-execute (interactive CLI).
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

if ! command -v cline >/dev/null; then
  echo "skip: cline not in PATH" >&2
  exit 0
fi

tillm drive \
  --client cline \
  --project "$TILLM_REPO_ROOT" \
  --prompt "Review tillm README structure. Do not edit files." \
  --format json
