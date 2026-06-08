#!/usr/bin/env bash
# Print suggested OpenRouter model slugs for aider smoke tests.
set -euo pipefail

cat <<'EOF'
openrouter/deepseek/deepseek-v4-pro
openrouter/qwen/qwen3-coder-next
openrouter/anthropic/claude-sonnet-4
openrouter/google/gemini-2.5-pro
openrouter/meta-llama/llama-3.3-70b-instruct
EOF
