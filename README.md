# tillm


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.32-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.48-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-7.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fdeep%2Fdeep--v4--pro-lightgrey)

- 🤖 **LLM usage:** $1.4788 (32 commits)
- 👤 **Human dev:** ~$701 (7.0h @ $100/h, 30min dedup)

Generated on 2026-06-08 using [openrouter/deep/deep-v4-pro](https://openrouter.ai/deep/deep-v4-pro)

---

Shell LLM control plane for the semcod/coru ecosystem.

SILLM owns the shell-client side of LLM automation: clients such as `aider`,
`claude`, `codex`, `gemini`, `qwen-code`, `opencode`, and `devin`. GUI/IDE
chat control stays in `koruide` and the existing Koru autopilot socket path.

## Commands

```bash
tillm clients
tillm drive --client aider --prompt "Refactor ticket PLF-1"          # dry-run
tillm drive --client aider --prompt "Refactor ticket PLF-1" --execute
tillm nlp "aider: napraw testy dla kolejki"                          # NLP -> DSL
tillm validate                                                       # ecosystem hooks + intents
```

`tillm drive` always saves the prompt under `.koru/tillm/prompts/` before it
executes or prints a dry-run plan.

Client notes:

- [`aider`](docs/clients/aider.md)
- [`claude-code`](docs/clients/claude-code.md)
- [`aider Docker autoloop`](docs/clients/aider-docker-autoloop.md)

## Optional ecosystem integrations

PyPI wheels ship only the `dev` extra. Monorepo siblings use local editable installs
(PyPI rejects `file://` URLs in package metadata):

```bash
pip install -e ".[dev]"
pip install -e ../nlp2dsl ../intract ../redsl ../proxym ../llx   # adjust paths for your checkout
```

The `nlp2dsl` bridge is opt-in at runtime:

```bash
export SILLM_NLP2DSL=1
export NLP2DSL_BACKEND_URL=http://localhost:8010
tillm nlp "uruchom claude dla ticketu PLF-123"
```

Without the service, SILLM falls back to a deterministic local parser.

`tillm validate` reports optional package availability and exposes the
`@intract.v1` intent contract used to validate `tillm.drive` DSL before shell
execution.


## License

Licensed under Apache-2.0.
