#!/usr/bin/env bash
# Run all dry-run examples (no API spend except skipped clients).
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"
source "$root/openrouter/load-env.sh"

run() {
  local script="$1"
  echo "=== $script ===" >&2
  bash "$script" >/dev/null && echo "ok: $script" || echo "fail: $script"
}

for script in \
  "$root/aider/dry-run.sh" \
  "$root/claude-code/dry-run.sh" \
  "$root/codex/dry-run.sh" \
  "$root/devin/dry-run.sh" \
  "$root/gemini-cli/dry-run.sh" \
  "$root/qwen-code/dry-run.sh" \
  "$root/opencode/dry-run.sh" \
  "$root/cline/dry-run.sh" \
  "$root/matrix/dry-run-available.sh" \
  "$root/dsl/run-smoke.sh" \
  "$root/control-layer/nlp-to-dsl.sh" \
  "$root/control-layer/uri-decode.sh" \
  "$root/control-layer/cli-exec.sh"
do
  run "$script"
done

echo "done" >&2
