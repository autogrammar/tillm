#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../openrouter/load-env.sh"

uri2tillm decode --uri "tillm://client/aider?prompt=smoke%20test"
uri2tillm decode --uri "tillm://cmd/HEALTH"
