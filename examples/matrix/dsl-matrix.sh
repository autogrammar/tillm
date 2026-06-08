#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

dsl2tillm exec 'DRIVE_MATRIX CLIENTS aider,codex PROMPT "matrix dsl smoke" PARALLEL 2' --json
