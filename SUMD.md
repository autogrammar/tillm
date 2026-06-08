# tillm

Shell LLM client control plane for semcod/coru automation.

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `tillm`
- **version**: `0.1.31`
- **python_requires**: `>=3.11`
- **license**: Apache-2.0
- **ai_model**: `openrouter/deep/deep-v4-pro`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(1), app.doql.less, goal.yaml, .env.example, project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: tillm;
  version: 0.1.31;
}

dependencies {
  dev: "build>=1.0,<2.0, pytest>=8.0,<10.0, ruff>=0.11,<0.16, twine>=6.0,<7.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, testql>=1.2.0";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="tillm"] {
  entry: tillm.cli:main;
}
interface[type="cli"] page[name="sllm"] {
  entry: tillm.cli:main;
}

integration[name="nlp"] {
  type: api;
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_MAX_RETRIES, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_CREATE_BACKUPS, SILLM_DEFAULT_CLIENT, SILLM_NLP2DSL;
}

deploy {
  target: pip;
}

environment[name="local"] {
  runtime: python;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.11;
  vars: LLM_MODEL, OPENROUTER_API_KEY, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
  runtime_llm: OPENROUTER_API_KEY;
  runtime_pfix: PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
}
```

## Interfaces

### CLI Entry Points

- `tillm`
- `sllm`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m sllm
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m sllm --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m sllm --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m sllm --help" 10000
ASSERT_EXIT_CODE 0
```

## Configuration

```yaml
project:
  name: tillm
  version: 0.1.31
  env: local
```

## Dependencies

### Runtime

*(see pyproject.toml)*

### Development

```text markpact:deps python scope=dev
build>=1.0,<2.0
pytest>=8.0,<10.0
ruff>=0.11,<0.16
twine>=6.0,<7.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
testql>=1.2.0
```

## Deployment

```bash markpact:run
pip install tillm

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`tillm`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# tillm | 12f 1347L | python:9,shell:2,less:1 | 2026-06-08
# stats: 47 func | 9 cls | 12 mod | CC̄=4.3 | critical:3 | cycles:0
# alerts[5]: CC test_compat_exports_koru_agent_rows=19; CC _intent_from_nlp2dsl=15; CC drive_shell_llm=10; CC _validate_raw_dsl=9; CC launch_koru_agent=8
# hotspots[5]: _intent_from_nlp2dsl fan=11; test_compat_exports_koru_agent_rows fan=11; main fan=10; launch_koru_agent fan=10; build_drive_plan fan=10
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[12]:
  app.doql.less,47
  project.sh,63
  src/tillm/__init__.py,37
  src/tillm/__main__.py,8
  src/tillm/cli.py,168
  src/tillm/compat.py,206
  src/tillm/controller.py,249
  src/tillm/nlp.py,105
  src/tillm/registry.py,169
  src/tillm/validation.py,128
  tests/test_sillm.py,165
  tree.sh,2
D:
  src/tillm/__init__.py:
  src/tillm/__main__.py:
  src/tillm/cli.py:
    e: _print,_build_parser,_normalize_extra_arg_tokens,_read_prompt,_drive,_nlp,main
    _print(payload;output_format)
    _build_parser()
    _normalize_extra_arg_tokens(argv)
    _read_prompt(args)
    _drive(args)
    _nlp(args)
    main(argv)
  src/tillm/compat.py:
    e: agent_backend_profiles,agent_backend_aliases,is_shell_llm_client,is_client_available,shell_client_ids,shell_process_patterns,tool_registry_entries,autopilot_backend_for_client,detect_koru_agent_rows,drive_koru_chat,launch_koru_agent
    agent_backend_profiles()
    agent_backend_aliases()
    is_shell_llm_client(agent_id)
    is_client_available(client_id)
    shell_client_ids()
    shell_process_patterns()
    tool_registry_entries()
    autopilot_backend_for_client(agent_id)
    detect_koru_agent_rows()
    drive_koru_chat()
    launch_koru_agent()
  src/tillm/controller.py:
    e: _prompt_root,save_prompt,_resolve_spec,_resolve_command,build_drive_plan,_timeout_value,drive_shell_llm,result_from_error,TillmError,UnknownClientError,ClientUnavailableError,ShellDriveRequest,ShellDrivePlan,ShellDriveResult
    TillmError:  # Base error for SLLM control failures.
    UnknownClientError:  # Requested client is not registered.
    ClientUnavailableError:  # Registered client command is not available in PATH.
    ShellDriveRequest:
    ShellDrivePlan: shell_preview(0),to_dict(0)
    ShellDriveResult: to_dict(0)
    _prompt_root(project;prompt_dir)
    save_prompt(prompt)
    _resolve_spec(client_id)
    _resolve_command(spec)
    build_drive_plan(request)
    _timeout_value(timeout_seconds)
    drive_shell_llm(request)
    result_from_error(client_id;exc)
  src/tillm/nlp.py:
    e: _client_from_text,_strip_drive_prefix,_intent_from_nlp2dsl,intent_from_text,ShellIntent
    ShellIntent: to_dsl(0)
    _client_from_text(text;default_client)
    _strip_drive_prefix(text)
    _intent_from_nlp2dsl(text;default_client)
    intent_from_text(text)
  src/tillm/registry.py:
    e: normalize_client_id,iter_client_specs,get_client_spec,detect_clients,ShellClientSpec
    ShellClientSpec: command_path(1),to_dict(0)
    normalize_client_id(raw)
    iter_client_specs()
    get_client_spec(client_id)
    detect_clients()
  src/tillm/validation.py:
    e: validate_intent,_validate_raw_dsl,intent_contracts,validate_intent_contracts,ecosystem_status,ValidationResult
    ValidationResult: to_dict(0)
    validate_intent(intent)
    _validate_raw_dsl(raw_dsl;client_id)
    intent_contracts()
    validate_intent_contracts()
    ecosystem_status()
  tests/test_sillm.py:
    e: test_registry_normalizes_common_aliases,test_detect_clients_marks_available_from_injected_which,test_compat_exports_koru_agent_rows,test_build_drive_plan_uses_message_file_for_aider,test_drive_cli_accepts_space_form_extra_arg_flags,test_nlp_rules_select_client_and_prompt,test_validate_intent_rejects_raw_dsl_without_tillm_drive,test_intent_contracts_are_exposed_for_ecosystem_validation
    test_registry_normalizes_common_aliases()
    test_detect_clients_marks_available_from_injected_which()
    test_compat_exports_koru_agent_rows()
    test_build_drive_plan_uses_message_file_for_aider(tmp_path)
    test_drive_cli_accepts_space_form_extra_arg_flags(monkeypatch;tmp_path;capsys)
    test_nlp_rules_select_client_and_prompt()
    test_validate_intent_rejects_raw_dsl_without_tillm_drive()
    test_intent_contracts_are_exposed_for_ecosystem_validation()
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('tillm', '0.1.31', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 47, 'less').
project_file('project.sh', 63, 'shell').
project_file('src/tillm/__init__.py', 37, 'python').
project_file('src/tillm/__main__.py', 8, 'python').
project_file('src/tillm/cli.py', 168, 'python').
project_file('src/tillm/compat.py', 206, 'python').
project_file('src/tillm/controller.py', 249, 'python').
project_file('src/tillm/nlp.py', 105, 'python').
project_file('src/tillm/registry.py', 169, 'python').
project_file('src/tillm/validation.py', 128, 'python').
project_file('tests/test_sillm.py', 165, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('src/tillm/cli.py', '_print', 2, 6, 5).
python_function('src/tillm/cli.py', '_build_parser', 0, 1, 5).
python_function('src/tillm/cli.py', '_normalize_extra_arg_tokens', 1, 5, 3).
python_function('src/tillm/cli.py', '_read_prompt', 1, 4, 4).
python_function('src/tillm/cli.py', '_drive', 1, 5, 9).
python_function('src/tillm/cli.py', '_nlp', 1, 5, 9).
python_function('src/tillm/cli.py', 'main', 1, 6, 10).
python_function('src/tillm/compat.py', 'agent_backend_profiles', 0, 1, 0).
python_function('src/tillm/compat.py', 'agent_backend_aliases', 0, 1, 0).
python_function('src/tillm/compat.py', 'is_shell_llm_client', 1, 1, 1).
python_function('src/tillm/compat.py', 'is_client_available', 1, 2, 3).
python_function('src/tillm/compat.py', 'shell_client_ids', 0, 2, 2).
python_function('src/tillm/compat.py', 'shell_process_patterns', 0, 2, 2).
python_function('src/tillm/compat.py', 'tool_registry_entries', 0, 4, 4).
python_function('src/tillm/compat.py', 'autopilot_backend_for_client', 1, 2, 1).
python_function('src/tillm/compat.py', 'detect_koru_agent_rows', 0, 5, 6).
python_function('src/tillm/compat.py', 'drive_koru_chat', 0, 1, 3).
python_function('src/tillm/compat.py', 'launch_koru_agent', 0, 8, 10).
python_function('src/tillm/controller.py', '_prompt_root', 2, 2, 2).
python_function('src/tillm/controller.py', 'save_prompt', 1, 2, 7).
python_function('src/tillm/controller.py', '_resolve_spec', 1, 2, 2).
python_function('src/tillm/controller.py', '_resolve_command', 1, 2, 3).
python_function('src/tillm/controller.py', 'build_drive_plan', 1, 3, 10).
python_function('src/tillm/controller.py', '_timeout_value', 1, 3, 1).
python_function('src/tillm/controller.py', 'drive_shell_llm', 1, 10, 7).
python_function('src/tillm/controller.py', 'result_from_error', 2, 1, 2).
python_function('src/tillm/nlp.py', '_client_from_text', 2, 6, 5).
python_function('src/tillm/nlp.py', '_strip_drive_prefix', 1, 5, 4).
python_function('src/tillm/nlp.py', '_intent_from_nlp2dsl', 2, 15, 11).
python_function('src/tillm/nlp.py', 'intent_from_text', 1, 3, 5).
python_function('src/tillm/registry.py', 'normalize_client_id', 1, 1, 4).
python_function('src/tillm/registry.py', 'iter_client_specs', 0, 1, 0).
python_function('src/tillm/registry.py', 'get_client_spec', 1, 3, 1).
python_function('src/tillm/registry.py', 'detect_clients', 0, 4, 3).
python_function('src/tillm/validation.py', 'validate_intent', 1, 4, 7).
python_function('src/tillm/validation.py', '_validate_raw_dsl', 2, 9, 4).
python_function('src/tillm/validation.py', 'intent_contracts', 0, 1, 0).
python_function('src/tillm/validation.py', 'validate_intent_contracts', 0, 4, 3).
python_function('src/tillm/validation.py', 'ecosystem_status', 0, 2, 4).
python_function('tests/test_sillm.py', 'test_registry_normalizes_common_aliases', 0, 4, 2).
python_function('tests/test_sillm.py', 'test_detect_clients_marks_available_from_injected_which', 0, 8, 2).
python_function('tests/test_sillm.py', 'test_compat_exports_koru_agent_rows', 0, 19, 11).
python_function('tests/test_sillm.py', 'test_build_drive_plan_uses_message_file_for_aider', 1, 7, 4).
python_function('tests/test_sillm.py', 'test_drive_cli_accepts_space_form_extra_arg_flags', 3, 7, 6).
python_function('tests/test_sillm.py', 'test_nlp_rules_select_client_and_prompt', 0, 4, 2).
python_function('tests/test_sillm.py', 'test_validate_intent_rejects_raw_dsl_without_tillm_drive', 0, 3, 2).
python_function('tests/test_sillm.py', 'test_intent_contracts_are_exposed_for_ecosystem_validation', 0, 5, 3).

% ── Python Classes ───────────────────────────────────────
python_class('src/tillm/controller.py', 'TillmError').
python_class('src/tillm/controller.py', 'UnknownClientError').
python_class('src/tillm/controller.py', 'ClientUnavailableError').
python_class('src/tillm/controller.py', 'ShellDriveRequest').
python_class('src/tillm/controller.py', 'ShellDrivePlan').
python_method('ShellDrivePlan', 'shell_preview', 0, 2, 2).
python_method('ShellDrivePlan', 'to_dict', 0, 1, 3).
python_class('src/tillm/controller.py', 'ShellDriveResult').
python_method('ShellDriveResult', 'to_dict', 0, 1, 2).
python_class('src/tillm/nlp.py', 'ShellIntent').
python_method('ShellIntent', 'to_dsl', 0, 1, 0).
python_class('src/tillm/registry.py', 'ShellClientSpec').
python_method('ShellClientSpec', 'command_path', 1, 4, 1).
python_method('ShellClientSpec', 'to_dict', 0, 1, 2).
python_class('src/tillm/validation.py', 'ValidationResult').
python_method('ValidationResult', 'to_dict', 0, 1, 1).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Required: OpenRouter API key (https://openrouter.ai/keys)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Model (default: openrouter/qwen/qwen3-coder-next)').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
sumd_interface('cli', '').
```

## Call Graph

*36 nodes · 46 edges · 6 modules · CC̄=3.3*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_intent_from_nlp2dsl` *(in src.tillm.nlp)* | 15 ⚠ | 1 | 25 | **26** |
| `_build_parser` *(in src.tillm.cli)* | 1 | 1 | 25 | **26** |
| `launch_koru_agent` *(in src.tillm.compat)* | 8 | 0 | 17 | **17** |
| `_print` *(in src.tillm.cli)* | 6 | 7 | 10 | **17** |
| `_nlp` *(in src.tillm.cli)* | 5 | 1 | 13 | **14** |
| `build_drive_plan` *(in src.tillm.controller)* | 3 | 2 | 11 | **13** |
| `drive_shell_llm` *(in src.tillm.controller)* | 10 ⚠ | 3 | 10 | **13** |
| `_drive` *(in src.tillm.cli)* | 5 | 1 | 11 | **12** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/tillm
# generated in 0.02s
# nodes: 36 | edges: 46 | modules: 6
# CC̄=3.3

HUBS[20]:
  src.tillm.nlp._intent_from_nlp2dsl
    CC=15  in:1  out:25  total:26
  src.tillm.cli._build_parser
    CC=1  in:1  out:25  total:26
  src.tillm.compat.launch_koru_agent
    CC=8  in:0  out:17  total:17
  src.tillm.cli._print
    CC=6  in:7  out:10  total:17
  src.tillm.cli._nlp
    CC=5  in:1  out:13  total:14
  src.tillm.controller.build_drive_plan
    CC=3  in:2  out:11  total:13
  src.tillm.controller.drive_shell_llm
    CC=10  in:3  out:10  total:13
  src.tillm.cli._drive
    CC=5  in:1  out:11  total:12
  src.tillm.validation._validate_raw_dsl
    CC=9  in:1  out:11  total:12
  src.tillm.cli.main
    CC=6  in:0  out:11  total:11
  src.sillm.registry.normalize_client_id
    CC=1  in:6  out:4  total:10
  src.tillm.validation.validate_intent
    CC=4  in:1  out:8  total:9
  src.tillm.compat.detect_koru_agent_rows
    CC=5  in:0  out:9  total:9
  src.tillm.controller.save_prompt
    CC=2  in:2  out:7  total:9
  src.tillm.nlp._client_from_text
    CC=6  in:1  out:6  total:7
  src.tillm.validation.validate_intent_contracts
    CC=4  in:1  out:6  total:7
  src.sillm.registry.get_client_spec
    CC=3  in:6  out:1  total:7
  src.tillm.nlp.intent_from_text
    CC=3  in:1  out:5  total:6
  src.tillm.nlp._strip_drive_prefix
    CC=5  in:1  out:5  total:6
  src.tillm.cli._normalize_extra_arg_tokens
    CC=5  in:1  out:5  total:6

MODULES:
  src.sillm.registry  [4 funcs]
    detect_clients  CC=4  out:3
    get_client_spec  CC=3  out:1
    iter_client_specs  CC=1  out:0
    normalize_client_id  CC=1  out:4
  src.tillm.cli  [7 funcs]
    _build_parser  CC=1  out:25
    _drive  CC=5  out:11
    _nlp  CC=5  out:13
    _normalize_extra_arg_tokens  CC=5  out:5
    _print  CC=6  out:10
    _read_prompt  CC=4  out:4
    main  CC=6  out:11
  src.tillm.compat  [9 funcs]
    autopilot_backend_for_client  CC=2  out:1
    detect_koru_agent_rows  CC=5  out:9
    drive_koru_chat  CC=1  out:3
    is_client_available  CC=2  out:3
    is_shell_llm_client  CC=1  out:1
    launch_koru_agent  CC=8  out:17
    shell_client_ids  CC=2  out:2
    shell_process_patterns  CC=2  out:2
    tool_registry_entries  CC=4  out:4
  src.tillm.controller  [8 funcs]
    _prompt_root  CC=2  out:3
    _resolve_command  CC=2  out:3
    _resolve_spec  CC=2  out:2
    _timeout_value  CC=3  out:1
    build_drive_plan  CC=3  out:11
    drive_shell_llm  CC=10  out:10
    result_from_error  CC=1  out:2
    save_prompt  CC=2  out:7
  src.tillm.nlp  [4 funcs]
    _client_from_text  CC=6  out:6
    _intent_from_nlp2dsl  CC=15  out:25
    _strip_drive_prefix  CC=5  out:5
    intent_from_text  CC=3  out:5
  src.tillm.validation  [4 funcs]
    _validate_raw_dsl  CC=9  out:11
    ecosystem_status  CC=2  out:4
    validate_intent  CC=4  out:8
    validate_intent_contracts  CC=4  out:6

EDGES:
  src.tillm.cli._drive → src.tillm.cli._print
  src.tillm.cli._drive → src.tillm.controller.drive_shell_llm
  src.tillm.cli._drive → src.tillm.controller.result_from_error
  src.tillm.cli._drive → src.tillm.cli._read_prompt
  src.tillm.cli._nlp → src.tillm.nlp.intent_from_text
  src.tillm.cli._nlp → src.tillm.validation.validate_intent
  src.tillm.cli._nlp → src.tillm.controller.drive_shell_llm
  src.tillm.cli._nlp → src.tillm.cli._print
  src.tillm.cli.main → src.tillm.cli._normalize_extra_arg_tokens
  src.tillm.cli.main → src.tillm.cli._print
  src.tillm.cli.main → src.tillm.cli._drive
  src.tillm.cli.main → src.tillm.cli._nlp
  src.tillm.cli.main → src.tillm.cli._build_parser
  src.tillm.cli.main → src.sillm.registry.detect_clients
  src.tillm.controller.save_prompt → src.tillm.controller._prompt_root
  src.tillm.controller._resolve_spec → src.sillm.registry.get_client_spec
  src.tillm.controller.build_drive_plan → src.tillm.controller._resolve_spec
  src.tillm.controller.build_drive_plan → src.tillm.controller._resolve_command
  src.tillm.controller.build_drive_plan → src.tillm.controller.save_prompt
  src.tillm.controller.drive_shell_llm → src.tillm.controller.build_drive_plan
  src.tillm.controller.drive_shell_llm → src.tillm.controller._timeout_value
  src.sillm.registry.get_client_spec → src.sillm.registry.normalize_client_id
  src.sillm.registry.detect_clients → src.sillm.registry.normalize_client_id
  src.tillm.validation.validate_intent → src.sillm.registry.get_client_spec
  src.tillm.validation.validate_intent → src.tillm.validation._validate_raw_dsl
  src.tillm.validation._validate_raw_dsl → src.sillm.registry.normalize_client_id
  src.tillm.validation.ecosystem_status → src.tillm.validation.validate_intent_contracts
  src.tillm.nlp._client_from_text → src.sillm.registry.iter_client_specs
  src.tillm.nlp._client_from_text → src.sillm.registry.normalize_client_id
  src.tillm.nlp._intent_from_nlp2dsl → src.sillm.registry.normalize_client_id
  src.tillm.nlp.intent_from_text → src.tillm.nlp._client_from_text
  src.tillm.nlp.intent_from_text → src.tillm.nlp._intent_from_nlp2dsl
  src.tillm.nlp.intent_from_text → src.sillm.registry.get_client_spec
  src.tillm.nlp.intent_from_text → src.tillm.nlp._strip_drive_prefix
  src.tillm.compat.is_shell_llm_client → src.sillm.registry.get_client_spec
  src.tillm.compat.is_client_available → src.sillm.registry.get_client_spec
  src.tillm.compat.shell_client_ids → src.sillm.registry.iter_client_specs
  src.tillm.compat.shell_process_patterns → src.sillm.registry.iter_client_specs
  src.tillm.compat.tool_registry_entries → src.sillm.registry.iter_client_specs
  src.tillm.compat.autopilot_backend_for_client → src.tillm.compat.is_shell_llm_client
  src.tillm.compat.detect_koru_agent_rows → src.sillm.registry.detect_clients
  src.tillm.compat.drive_koru_chat → src.tillm.controller.drive_shell_llm
  src.tillm.compat.launch_koru_agent → src.sillm.registry.normalize_client_id
  src.tillm.compat.launch_koru_agent → src.sillm.registry.get_client_spec
  src.tillm.compat.launch_koru_agent → src.tillm.controller.save_prompt
  src.tillm.compat.launch_koru_agent → src.tillm.controller.build_drive_plan
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Intent

Shell LLM client control plane for semcod/coru automation.
