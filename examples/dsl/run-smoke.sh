#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

dsl2tillm run examples/dsl/smoke.dsl --json
