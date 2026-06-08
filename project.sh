#!/usr/bin/env bash
set -e
clear 2>/dev/null || true

if [ -d ".venv" ]; then
    VENV=".venv"
elif [ -d "venv" ]; then
    VENV="venv"
else
    VENV=".venv"
fi

PIP="$VENV/bin/pip"
PYTHON="$VENV/bin/python3"

venv_is_usable() {
    [ -x "$PIP" ] && "$PIP" --version >/dev/null 2>&1
}

if ! venv_is_usable; then
    echo "Creating virtual environment in $VENV..."
    rm -rf "$VENV"
    python3 -m venv "$VENV"
fi

$PIP install -e .
$PIP install regix --upgrade --quiet
#$PIP install pyqual --upgrade --quiet
$PIP install prefact --upgrade --quiet
$PIP install vallm --upgrade --quiet
$PIP install redup --upgrade --quiet
$PIP install glon --upgrade --quiet
$PIP install code2logic --upgrade --quiet
$PIP install code2llm --upgrade --quiet
#$VENV/bin/code2llm ./ -f toon,evolution,code2logic,project-yaml -o ./project --no-chunk
$VENV/bin/code2llm ./ -f all -o ./project --no-chunk --exclude '*.md'
#$VENV/bin/code2llm report --format all       # → all views

#$PIP install code2docs --upgrade --quiet
#$VENV/bin/code2docs ./ --readme-only
$VENV/bin/redup scan . --format toon --output ./project
#$VENV/bin/redup scan . --functions-only -f toon --output ./project
#$VENV/bin/vallm batch ./src --recursive --semantic --model qwen2.5-coder:7b
#$VENV/bin/vallm batch --parallel .
#$VENV/bin/vallm batch . --recursive --format toon --output ./project
#$VENV/bin/prefact -a -e "examples/**"


$PIP install doql --upgrade --quiet
$VENV/bin/doql adopt . --format less --output app.doql.less --force

$PIP install sumd --upgrade --quiet
$VENV/bin/sumd .
$VENV/bin/sumr .


$PIP install goal testql --upgrade --quiet

bash ./tree.sh
$PYTHON -m testql.cli inspect https://tom.sapletta.com/ --scan-network --out-dir .testql

#$VENV/bin/goal -a
