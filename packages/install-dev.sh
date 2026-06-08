#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIP="${PIP:-python3 -m pip}"

cd "$ROOT"
$PIP install -e .
$PIP install -e packages/dsl2tillm
$PIP install -e packages/uri2tillm
$PIP install -e packages/nlp2tillm
$PIP install -e packages/cli2tillm
$PIP install -e packages/mcp2tillm
$PIP install -e packages/rest2tillm
echo "✓ tillm control layers installed"
