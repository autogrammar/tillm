# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `tillm.project_env` — auto-load `<project>/.env`, OpenRouter bridges, optional env2llm map refresh
- `OPENROUTER_API_KEY` accepted for aider readiness in registry
- Optional extra `pip install tillm[env]` → `env2llm>=0.1.12`
- `examples/*/*` — per-client smoke scripts (OpenRouter + tillm dry-run/execute)
- Control layer packages: `dsl2tillm`, `uri2tillm`, `nlp2tillm`, `cli2tillm`, `mcp2tillm`, `rest2tillm` (port **8216**)
- DSL verbs: `HEALTH`, `CLIENTS`, `ORIENT`, `ACTIONS`, `VALIDATE`, `RESOLVE`, `DOCKER_STATUS`, `DRIVE`, `DRIVE_MATRIX`
- JSON Schema validation, CQRS bus (`dispatch()`), EventStore for commands
- `tillm://` URI builders and decoders (`uri_for_cmd`, `uri_for_client`)
- Multi-client orchestration: `--clients`, `--all`, `--parallel`, `--fail-fast`, `--quorum`
- Execute profiles: `default` and `automation` (permission bypass per vendor)
- Transport layer: `binary` (subprocess) and `docker` (compose exec)
- Docker compose scaffold: `deploy/docker-compose.yml`
- Documentation: `docs/configuration.md`, `docs/control-layer.md`, `docs/clients/README.md`, `TODO.md`
- `packages/install-dev.sh` for editable control-layer installs

### Changed
- `docs/clients/aider.md`: OpenRouter setup (`AIDER_MODEL` vs `LLM_MODEL`, `.env` loading)
- `docs/clients/claude-code.md`: execute profiles, tillm naming
- `README.md`: architecture, control layer, multi-client, version/update guide

### Fixed
- Circular import between `tillm.controller` and `tillm.transports.binary` (lazy import in transports)
- `uri2tillm` parser: `source` from URI `netloc` (aligned with `gillm` pattern)

## [0.1.40] - 2026-07-19

### Docs
- Update README.md

### Test
- Update tests/conftest.py
- Update tests/test_cli_output.py
- Update tests/test_cli_parser.py

### Other
- Update uv.lock

## [0.1.39] - 2026-07-03

### Docs
- Update README.md

## [0.1.38] - 2026-07-03

### Docs
- Update README.md

## [0.1.37] - 2026-07-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.36] - 2026-07-03

### Docs
- Update README.md

### Test
- Update tests/test_tillm.py

### Other
- Update VERSION

## [0.1.36] - 2026-06-29

### Docs
- Update README.md

## [0.1.35] - 2026-06-08

### Docs
- Update README.md

### Test
- Update testql-scenarios/generated-cli-tests.testql.toon.yaml
- Update tests/test_tillm.py

### Other
- Update app.doql.less
- Update packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py

## [0.1.34] - 2026-06-08

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update docs/configuration.md
- Update examples/README.md

### Test
- Update tests/test_sillm.py

### Other
- Update .gitignore
- Update app.doql.less
- Update examples/aider/dry-run.sh
- Update examples/aider/execute.sh
- Update examples/aider/model-switch.sh
- Update examples/aider/refactor.sh
- Update examples/claude-code/dry-run.sh
- Update examples/claude-code/execute.sh
- Update examples/cline/dry-run.sh
- Update examples/codex/dry-run.sh
- ... and 24 more files

## [0.1.33] - 2026-06-08

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/README.md
- Update docs/clients/README.md
- Update docs/clients/aider-docker-autoloop.md
- Update docs/clients/aider.md
- Update docs/clients/claude-code.md
- ... and 9 more files

### Test
- Update tests/fixtures/refactor_sample.py
- Update tests/test_sillm.py

### Other
- Update .goal_test_report.xml
- Update app.doql.less
- Update coverage.json
- Update deploy/docker-compose.yml
- Update packages/cli2tillm/pyproject.toml
- Update packages/cli2tillm/src/cli2tillm/__init__.py
- Update packages/cli2tillm/src/cli2tillm/cli.py
- Update packages/cli2tillm/src/cli2tillm/shell.py
- Update packages/cli2tillm/tests/test_cli2tillm.py
- Update packages/dsl2tillm/pyproject.toml
- ... and 63 more files

## [0.1.32] - 2026-06-08

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/clients/aider.md
- Update docs/clients/claude-code.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_sillm.py

### Other
- Update .gitignore
- Update .goal_test_report.xml
- Update app.doql.less
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- ... and 13 more files

## [0.1.31] - 2026-06-08

### Docs
- Update README.md

### Other
- Update app.doql.less

## [0.1.30] - 2026-06-08

### Docs
- Update README.md

## [0.1.29] - 2026-06-08

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.28] - 2026-06-08

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.27] - 2026-06-08

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update project/README.md
- Update project/context.md

### Other
- Update app.doql.less
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- ... and 12 more files

## [0.1.26] - 2026-06-08

### Docs
- Update README.md

### Test
- Update tests/test_sillm.py

### Other
- Update .gitignore
- Update uv.lock

## [0.1.25] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.24] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.23] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.22] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.21] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.20] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.19] - 2026-06-03

### Docs
- Update README.md

## [0.1.18] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.17] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.16] - 2026-06-03

### Docs
- Update README.md

## [0.1.15] - 2026-06-03

### Docs
- Update README.md

### Other
- Update uv.lock

## [0.1.14] - 2026-06-03

### Docs
- Update CHANGELOG.md
- Update README.md

### Other
- Update VERSION
- Update uv.lock

## [0.1.13] - 2026-06-03

### Fixed
- Declare build/publish tooling for dev installs and align publish artifact pattern.

## [0.1.12] - 2026-06-03

### Docs
- Update README.md

## [0.1.11] - 2026-06-03

### Docs
- Update README.md

## [0.1.10] - 2026-06-03

### Docs
- Update README.md

### Test
- Update tests/test_sillm.py

## [0.1.9] - 2026-06-03

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql-scenarios/generated-cli-tests.testql.toon.yaml

### Other
- Update app.doql.less
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 11 more files

## [0.1.8] - 2026-06-03

### Docs
- Update README.md

### Other
- Update project.sh
- Update tree.sh

## [0.1.7] - 2026-06-03

### Docs
- Update README.md

## [0.1.6] - 2026-06-03

### Docs
- Update README.md

## [0.1.5] - 2026-06-03

### Docs
- Update README.md
- Update docs/clients/aider-docker-autoloop.md

### Test
- Update tests/test_tillm.py

### Other
- Update uv.lock

## [0.1.4] - 2026-06-03

### Docs
- Update README.md

## [0.1.3] - 2026-06-03

### Docs
- Update README.md

### Test
- Update tests/test_tillm.py

### Other
- Update uv.lock

## [0.1.2] - 2026-06-03

### Docs
- Update README.md
- Update docs/clients/aider.md
- Update docs/clients/claude-code.md

### Test
- Update tests/test_tillm.py

### Other
- Update uv.lock

## [0.1.1] - 2026-06-03

### Docs
- Update README.md

### Test
- Update tests/test_tillm.py

### Other
- Update .gitignore
- Update .idea/.gitignore
- Update uv.lock
