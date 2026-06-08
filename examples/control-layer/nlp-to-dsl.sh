#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

nlp2tillm to-dsl "aider: add unit test for registry"
