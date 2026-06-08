#!/usr/bin/env bash
# Source from repo root: source examples/openrouter/load-env.sh
set -euo pipefail

_examples_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_repo_root="$(cd "$_examples_dir/../.." && pwd)"

# tillm auto-loads .env via project_env; this script is for standalone bash examples.
if [[ -f "$_repo_root/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$_repo_root/.env"
  set +a
elif [[ -f "$_examples_dir/env.example" ]]; then
  echo "warn: no .env in repo root; using examples/openrouter/env.example" >&2
  set -a
  # shellcheck disable=SC1091
  source "$_examples_dir/env.example"
  set +a
else
  echo "error: no .env found. Copy examples/openrouter/env.example → .env" >&2
  return 1 2>/dev/null || exit 1
fi

# aider + tillm OpenRouter bridge
export AIDER_MODEL="${AIDER_MODEL:-${LLM_MODEL:-openrouter/deepseek/deepseek-v4-pro}}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-${OPENROUTER_API_KEY:-}}"

export TILLM_REPO_ROOT="$_repo_root"
cd "$_repo_root"
