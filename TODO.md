# TODO

## High priority

- [x] Add `OPENROUTER_API_KEY` to aider registry `env_vars_any`
- [x] Auto-load project `.env` via `project_env` + env2llm (`TILLM_ENV_FILE`, `TILLM_ENV2LLM`)
- [ ] Publish `tillm` and `*2tillm` packages to PyPI

## Control layer

- [ ] HTTP transport (`TILLM_BACKEND=http`) — AgentAPI pattern
- [ ] Real protobuf codec (replace JSON stub in `pb_codec.py`)
- [ ] `DRIVE_MATRIX` JSON Schema: enforce `clients` OR `all_clients`
- [ ] Optional: delegate legacy `tillm` CLI to `dsl2tillm.dispatch()`

## Docker

- [ ] Production-ready images (compose is currently a scaffold)
- [ ] Document per-client Docker setup in `docs/clients/`

## Documentation

- [x] `examples/*/*` — per-client OpenRouter smoke scripts
- [x] `docs/configuration.md` — `.env`, OpenRouter, tillm env vars
- [x] `docs/control-layer.md` — `*2tillm` overview
- [x] `docs/clients/README.md` — client matrix
- [ ] Per-client docs: codex, gemini-cli, qwen-code, opencode, devin, cline
- [ ] Sync `SUMD.md` with control-layer packages and DSL verbs

## Testing

- [x] Core + control-layer pytest (73 tests)
- [ ] Integration test: aider execute with mocked subprocess + OpenRouter env
- [ ] `rest2tillm` live server smoke in CI
