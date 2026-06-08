# tillm

Text-interface LLM control plane for semcod/coru shell automation (pair with gillm for GUI).

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
- **version**: `0.1.32`
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
  version: 0.1.32;
}

dependencies {
  dev: "build>=1.0,<2.0, pytest>=8.0,<10.0, ruff>=0.11,<0.16, twine>=6.0,<7.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, testql>=1.2.0";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
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
  keys: OPENROUTER_API_KEY, LLM_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_MAX_RETRIES, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_CREATE_BACKUPS, TILLM_EXECUTE_PROFILE, TILLM_BACKEND, TILLM_DEFAULT_CLIENT, TILLM_NLP2DSL, TILLM_COMPOSE_FILE;
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
  version: 0.1.32
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
# tillm | 50f 3959L | python:46,shell:3,less:1 | 2026-06-08
# stats: 158 func | 18 cls | 50 mod | CC̄=4.8 | critical:17 | cycles:0
# alerts[5]: CC parse_line=35; CC drive_shell_llm_many=26; CC uri_to_dsl=24; CC test_compat_exports_koru_agent_rows=20; CC _main_subcommand=17
# hotspots[5]: create_app fan=19; drive_shell_llm_many fan=18; dispatch fan=17; _main_subcommand fan=17; main fan=15
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[50]:
  app.doql.less,52
  packages/cli2tillm/src/cli2tillm/__init__.py,4
  packages/cli2tillm/src/cli2tillm/cli.py,71
  packages/cli2tillm/src/cli2tillm/shell.py,33
  packages/cli2tillm/tests/test_cli2tillm.py,7
  packages/dsl2tillm/src/dsl2tillm/__init__.py,7
  packages/dsl2tillm/src/dsl2tillm/bus.py,89
  packages/dsl2tillm/src/dsl2tillm/cli.py,113
  packages/dsl2tillm/src/dsl2tillm/codec.py,32
  packages/dsl2tillm/src/dsl2tillm/engine.py,6
  packages/dsl2tillm/src/dsl2tillm/events.py,68
  packages/dsl2tillm/src/dsl2tillm/grammar.py,152
  packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py,177
  packages/dsl2tillm/src/dsl2tillm/pb_codec.py,29
  packages/dsl2tillm/src/dsl2tillm/result.py,29
  packages/dsl2tillm/src/dsl2tillm/schema_registry.py,50
  packages/dsl2tillm/tests/test_bus.py,37
  packages/install-dev.sh,15
  packages/mcp2tillm/src/mcp2tillm/__init__.py,4
  packages/mcp2tillm/src/mcp2tillm/cli.py,24
  packages/mcp2tillm/src/mcp2tillm/server.py,70
  packages/mcp2tillm/tests/test_mcp2tillm.py,6
  packages/nlp2tillm/src/nlp2tillm/__init__.py,4
  packages/nlp2tillm/src/nlp2tillm/cli.py,41
  packages/nlp2tillm/src/nlp2tillm/to_dsl.py,22
  packages/nlp2tillm/tests/test_to_dsl.py,13
  packages/rest2tillm/src/rest2tillm/__init__.py,4
  packages/rest2tillm/src/rest2tillm/app.py,79
  packages/rest2tillm/src/rest2tillm/cli.py,28
  packages/rest2tillm/tests/test_rest2tillm.py,29
  packages/uri2tillm/src/uri2tillm/__init__.py,5
  packages/uri2tillm/src/uri2tillm/cli.py,41
  packages/uri2tillm/src/uri2tillm/decode.py,61
  packages/uri2tillm/src/uri2tillm/run.py,12
  packages/uri2tillm/src/uri2tillm/uri.py,52
  packages/uri2tillm/tests/test_uri.py,13
  project.sh,63
  src/tillm/__init__.py,47
  src/tillm/__main__.py,8
  src/tillm/cli.py,315
  src/tillm/compat.py,206
  src/tillm/controller.py,413
  src/tillm/nlp.py,105
  src/tillm/registry.py,310
  src/tillm/transports/__init__.py,11
  src/tillm/transports/binary.py,78
  src/tillm/transports/docker.py,144
  src/tillm/validation.py,183
  tests/test_sillm.py,595
  tree.sh,2
D:
  packages/cli2tillm/src/cli2tillm/__init__.py:
  packages/cli2tillm/src/cli2tillm/cli.py:
    e: main
    main(argv)
  packages/cli2tillm/src/cli2tillm/shell.py:
    e: run_shell
    run_shell()
  packages/cli2tillm/tests/test_cli2tillm.py:
    e: test_exec_health_via_bus
    test_exec_health_via_bus()
  packages/dsl2tillm/src/dsl2tillm/__init__.py:
  packages/dsl2tillm/src/dsl2tillm/bus.py:
    e: dispatch,execute_dsl_line,execute_dsl
    dispatch(command)
    execute_dsl_line(line)
    execute_dsl(text)
  packages/dsl2tillm/src/dsl2tillm/cli.py:
    e: _main_legacy,_main_subcommand,main
    _main_legacy(argv)
    _main_subcommand(argv)
    main(argv)
  packages/dsl2tillm/src/dsl2tillm/codec.py:
    e: validate_payload,parse_text,envelope_from_bytes
    validate_payload(payload)
    parse_text(line)
    envelope_from_bytes(data)
  packages/dsl2tillm/src/dsl2tillm/engine.py:
  packages/dsl2tillm/src/dsl2tillm/events.py:
    e: StoredEvent,EventStore
    StoredEvent: to_dict(0)
    EventStore: __init__(1),for_workdir(2),append_command(2),read_all(0)
  packages/dsl2tillm/src/dsl2tillm/grammar.py:
    e: _flag,_bool_flag,_quoted_or_tail,parse_line,to_text
    _flag(rest;name)
    _bool_flag(rest;name)
    _quoted_or_tail(rest)
    parse_line(line)
    to_text(payload)
  packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py:
    e: run_query,run_command,_health,_clients,_orient,_actions,_validate,_resolve,_docker_status,_drive,_drive_matrix,HandlerResult
    HandlerResult: to_dict(0)
    run_query(payload)
    run_command(payload)
    _health()
    _clients()
    _orient()
    _actions()
    _validate(payload)
    _resolve(payload)
    _docker_status()
    _drive(payload)
    _drive_matrix(payload)
  packages/dsl2tillm/src/dsl2tillm/pb_codec.py:
    e: encode_protobuf,decode_protobuf,encode_result_protobuf
    encode_protobuf(payload)
    decode_protobuf(data)
    encode_result_protobuf(result)
  packages/dsl2tillm/src/dsl2tillm/result.py:
    e: DslResult
    DslResult: to_dict(0)
  packages/dsl2tillm/src/dsl2tillm/schema_registry.py:
    e: _load_schemas,schema_for_verb,all_verbs,validate_schemas
    _load_schemas()
    schema_for_verb(verb)
    all_verbs()
    validate_schemas()
  packages/dsl2tillm/tests/test_bus.py:
    e: test_health,test_orient,test_clients,test_actions,test_validate_ecosystem,test_resolve
    test_health()
    test_orient()
    test_clients()
    test_actions()
    test_validate_ecosystem()
    test_resolve()
  packages/mcp2tillm/src/mcp2tillm/__init__.py:
  packages/mcp2tillm/src/mcp2tillm/cli.py:
    e: main
    main(argv)
  packages/mcp2tillm/src/mcp2tillm/server.py:
    e: _require_fastmcp,create_server,run_server,TillmMCPServer
    TillmMCPServer: __post_init__(0),_register_tools(0),run(0)
    _require_fastmcp()
    create_server(name)
    run_server()
  packages/mcp2tillm/tests/test_mcp2tillm.py:
    e: test_create_server
    test_create_server()
  packages/nlp2tillm/src/nlp2tillm/__init__.py:
  packages/nlp2tillm/src/nlp2tillm/cli.py:
    e: main
    main(argv)
  packages/nlp2tillm/src/nlp2tillm/to_dsl.py:
    e: to_dsl,apply_nl
    to_dsl(prompt)
    apply_nl(prompt)
  packages/nlp2tillm/tests/test_to_dsl.py:
    e: test_to_dsl_aider,test_to_dsl_codex
    test_to_dsl_aider()
    test_to_dsl_codex()
  packages/rest2tillm/src/rest2tillm/__init__.py:
  packages/rest2tillm/src/rest2tillm/app.py:
    e: create_app
    create_app()
  packages/rest2tillm/src/rest2tillm/cli.py:
    e: main
    main(argv)
  packages/rest2tillm/tests/test_rest2tillm.py:
    e: test_root_endpoint,test_health_endpoint,test_post_dsl_health
    test_root_endpoint()
    test_health_endpoint()
    test_post_dsl_health()
  packages/uri2tillm/src/uri2tillm/__init__.py:
  packages/uri2tillm/src/uri2tillm/cli.py:
    e: main
    main(argv)
  packages/uri2tillm/src/uri2tillm/decode.py:
    e: uri_to_dsl
    uri_to_dsl(uri)
  packages/uri2tillm/src/uri2tillm/run.py:
    e: run_uri
    run_uri(uri)
  packages/uri2tillm/src/uri2tillm/uri.py:
    e: _encode,_decode,uri_for_cmd,uri_for_client,is_tillm_uri,parse_tillm_uri
    _encode(value)
    _decode(value)
    uri_for_cmd(verb)
    uri_for_client(client)
    is_tillm_uri(uri)
    parse_tillm_uri(uri)
  packages/uri2tillm/tests/test_uri.py:
    e: test_decode_health_cmd,test_decode_drive_client
    test_decode_health_cmd()
    test_decode_drive_client()
  src/tillm/__init__.py:
  src/tillm/__main__.py:
  src/tillm/cli.py:
    e: _format_client_row,_format_matrix_row,_print,_build_parser,_normalize_extra_arg_tokens,_resolve_execute_profile,_read_prompt,_resolve_drive_targets,_base_drive_request,_drive,_nlp,main
    _format_client_row(row)
    _format_matrix_row(result)
    _print(payload;output_format)
    _build_parser()
    _normalize_extra_arg_tokens(argv)
    _resolve_execute_profile(raw)
    _read_prompt(args)
    _resolve_drive_targets(args)
    _base_drive_request(args;prompt)
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
    e: resolve_backend,_prompt_root,save_prompt,_resolve_spec,_resolve_command,_validate_request,_resolve_execute_args,build_drive_plan,_timeout_value,_drive_result_from_exception,_drive_one_client,drive_shell_llm_many,drive_shell_llm,result_from_error,TillmError,UnknownClientError,ClientUnavailableError,ClientNotReadyError,UnknownProfileError,ShellDriveRequest,ShellDrivePlan,MultiShellDriveRequest,ShellDriveResult,MultiShellDriveResult
    TillmError:  # Base error for SLLM control failures.
    UnknownClientError:  # Requested client is not registered.
    ClientUnavailableError:  # Registered client command is not available in PATH.
    ClientNotReadyError:  # Registered client is missing binary, env vars, or requested 
    UnknownProfileError:  # Requested execute profile is not registered for the client.
    ShellDriveRequest:
    ShellDrivePlan: shell_preview(0),to_dict(0)
    MultiShellDriveRequest:
    ShellDriveResult: to_dict(0)
    MultiShellDriveResult: to_dict(0)
    resolve_backend(raw)
    _prompt_root(project;prompt_dir)
    save_prompt(prompt)
    _resolve_spec(client_id)
    _resolve_command(spec)
    _validate_request(request;spec)
    _resolve_execute_args(spec)
    build_drive_plan(request)
    _timeout_value(timeout_seconds)
    _drive_result_from_exception(client_id;exc)
    _drive_one_client(request;client_id)
    drive_shell_llm_many(request)
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
    e: normalize_client_id,iter_client_specs,get_client_spec,available_client_ids,registered_client_ids,resolve_client_ids,detect_clients,normalize_execute_profile,ShellClientSpec
    ShellClientSpec: command_path(1),profile_execute_args(1),supported_execute_profiles(0),missing_env_vars(1),to_dict(0)
    normalize_client_id(raw)
    iter_client_specs()
    get_client_spec(client_id)
    available_client_ids()
    registered_client_ids()
    resolve_client_ids()
    detect_clients()
    normalize_execute_profile(raw)
  src/tillm/transports/__init__.py:
  src/tillm/transports/binary.py:
    e: run_binary_drive
    run_binary_drive(request;plan)
  src/tillm/transports/docker.py:
    e: _compose_file,docker_service_name,docker_service_status,_docker_argv,run_docker_drive
    _compose_file()
    docker_service_name(client_id)
    docker_service_status()
    _docker_argv(plan)
    run_docker_drive(request;plan)
  src/tillm/validation.py:
    e: validate_client_readiness,validate_intent,validate_raw_dsl,client_status_rows,intent_contracts,validate_intent_contracts,ecosystem_status,ValidationResult
    ValidationResult: to_dict(0)
    validate_client_readiness(client_id)
    validate_intent(intent)
    validate_raw_dsl(raw_dsl;client_id)
    client_status_rows()
    intent_contracts()
    validate_intent_contracts()
    ecosystem_status()
  tests/test_sillm.py:
    e: test_registry_normalizes_common_aliases,test_registry_lists_all_shell_clients,test_detect_clients_marks_available_from_injected_which,test_detect_clients_reports_capabilities_and_env,test_build_drive_plan_for_each_registered_client,test_execute_args_match_vendor_headless_flags,test_build_drive_plan_includes_execute_args_when_executing,test_build_drive_plan_rejects_execute_for_cline,test_build_drive_plan_uses_message_file_for_aider,test_validate_client_readiness_reports_missing_binary_and_env,test_validate_client_readiness_rejects_execute_for_interactive_only,test_validate_raw_dsl_rejects_unknown_client,test_compat_exports_koru_agent_rows,test_drive_cli_accepts_space_form_extra_arg_flags,test_clients_cli_lists_registered_clients,test_nlp_rules_select_client_and_prompt,test_validate_intent_rejects_raw_dsl_without_tillm_drive,test_ecosystem_status_includes_client_rows,test_automation_profile_uses_permission_bypass_flags,test_automation_profile_is_rejected_when_unsupported,test_drive_cli_accepts_automation_profile,test_resolve_client_ids_for_all_available_only,test_resolve_client_ids_for_clients_list,test_drive_many_plans_all_selected_clients,test_drive_many_fail_fast_stops_after_first_failure,test_drive_cli_all_available_clients,test_registry_lists_transport_metadata,test_registered_and_available_client_helpers,test_intent_contracts_are_exposed_for_ecosystem_validation
    test_registry_normalizes_common_aliases(alias;canonical)
    test_registry_lists_all_shell_clients()
    test_detect_clients_marks_available_from_injected_which()
    test_detect_clients_reports_capabilities_and_env()
    test_build_drive_plan_for_each_registered_client(client_id;tmp_path;monkeypatch)
    test_execute_args_match_vendor_headless_flags(client_id)
    test_build_drive_plan_includes_execute_args_when_executing(client_id;tmp_path;monkeypatch)
    test_build_drive_plan_rejects_execute_for_cline(tmp_path)
    test_build_drive_plan_uses_message_file_for_aider(tmp_path)
    test_validate_client_readiness_reports_missing_binary_and_env(monkeypatch)
    test_validate_client_readiness_rejects_execute_for_interactive_only()
    test_validate_raw_dsl_rejects_unknown_client()
    test_compat_exports_koru_agent_rows()
    test_drive_cli_accepts_space_form_extra_arg_flags(monkeypatch;tmp_path;capsys)
    test_clients_cli_lists_registered_clients(capsys)
    test_nlp_rules_select_client_and_prompt()
    test_validate_intent_rejects_raw_dsl_without_tillm_drive()
    test_ecosystem_status_includes_client_rows()
    test_automation_profile_uses_permission_bypass_flags(client_id;tmp_path;monkeypatch)
    test_automation_profile_is_rejected_when_unsupported(tmp_path;monkeypatch)
    test_drive_cli_accepts_automation_profile(monkeypatch;tmp_path;capsys)
    test_resolve_client_ids_for_all_available_only(monkeypatch)
    test_resolve_client_ids_for_clients_list()
    test_drive_many_plans_all_selected_clients(tmp_path;monkeypatch)
    test_drive_many_fail_fast_stops_after_first_failure(tmp_path;monkeypatch)
    test_drive_cli_all_available_clients(monkeypatch;tmp_path;capsys)
    test_registry_lists_transport_metadata()
    test_registered_and_available_client_helpers(monkeypatch)
    test_intent_contracts_are_exposed_for_ecosystem_validation()
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('tillm', '0.1.32', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 52, 'less').
project_file('packages/cli2tillm/src/cli2tillm/__init__.py', 4, 'python').
project_file('packages/cli2tillm/src/cli2tillm/cli.py', 71, 'python').
project_file('packages/cli2tillm/src/cli2tillm/shell.py', 33, 'python').
project_file('packages/cli2tillm/tests/test_cli2tillm.py', 7, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/__init__.py', 7, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/bus.py', 89, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/cli.py', 113, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/codec.py', 32, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/engine.py', 6, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/events.py', 68, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/grammar.py', 152, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', 177, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/pb_codec.py', 29, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/result.py', 29, 'python').
project_file('packages/dsl2tillm/src/dsl2tillm/schema_registry.py', 50, 'python').
project_file('packages/dsl2tillm/tests/test_bus.py', 37, 'python').
project_file('packages/install-dev.sh', 15, 'shell').
project_file('packages/mcp2tillm/src/mcp2tillm/__init__.py', 4, 'python').
project_file('packages/mcp2tillm/src/mcp2tillm/cli.py', 24, 'python').
project_file('packages/mcp2tillm/src/mcp2tillm/server.py', 70, 'python').
project_file('packages/mcp2tillm/tests/test_mcp2tillm.py', 6, 'python').
project_file('packages/nlp2tillm/src/nlp2tillm/__init__.py', 4, 'python').
project_file('packages/nlp2tillm/src/nlp2tillm/cli.py', 41, 'python').
project_file('packages/nlp2tillm/src/nlp2tillm/to_dsl.py', 22, 'python').
project_file('packages/nlp2tillm/tests/test_to_dsl.py', 13, 'python').
project_file('packages/rest2tillm/src/rest2tillm/__init__.py', 4, 'python').
project_file('packages/rest2tillm/src/rest2tillm/app.py', 79, 'python').
project_file('packages/rest2tillm/src/rest2tillm/cli.py', 28, 'python').
project_file('packages/rest2tillm/tests/test_rest2tillm.py', 29, 'python').
project_file('packages/uri2tillm/src/uri2tillm/__init__.py', 5, 'python').
project_file('packages/uri2tillm/src/uri2tillm/cli.py', 41, 'python').
project_file('packages/uri2tillm/src/uri2tillm/decode.py', 61, 'python').
project_file('packages/uri2tillm/src/uri2tillm/run.py', 12, 'python').
project_file('packages/uri2tillm/src/uri2tillm/uri.py', 52, 'python').
project_file('packages/uri2tillm/tests/test_uri.py', 13, 'python').
project_file('project.sh', 63, 'shell').
project_file('src/tillm/__init__.py', 47, 'python').
project_file('src/tillm/__main__.py', 8, 'python').
project_file('src/tillm/cli.py', 315, 'python').
project_file('src/tillm/compat.py', 206, 'python').
project_file('src/tillm/controller.py', 413, 'python').
project_file('src/tillm/nlp.py', 105, 'python').
project_file('src/tillm/registry.py', 310, 'python').
project_file('src/tillm/transports/__init__.py', 11, 'python').
project_file('src/tillm/transports/binary.py', 78, 'python').
project_file('src/tillm/transports/docker.py', 144, 'python').
project_file('src/tillm/validation.py', 183, 'python').
project_file('tests/test_sillm.py', 595, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('packages/cli2tillm/src/cli2tillm/cli.py', 'main', 1, 16, 15).
python_function('packages/cli2tillm/src/cli2tillm/shell.py', 'run_shell', 0, 8, 7).
python_function('packages/cli2tillm/tests/test_cli2tillm.py', 'test_exec_health_via_bus', 0, 2, 1).
python_function('packages/dsl2tillm/src/dsl2tillm/bus.py', 'dispatch', 1, 15, 17).
python_function('packages/dsl2tillm/src/dsl2tillm/bus.py', 'execute_dsl_line', 1, 1, 1).
python_function('packages/dsl2tillm/src/dsl2tillm/bus.py', 'execute_dsl', 1, 4, 5).
python_function('packages/dsl2tillm/src/dsl2tillm/cli.py', '_main_legacy', 1, 12, 12).
python_function('packages/dsl2tillm/src/dsl2tillm/cli.py', '_main_subcommand', 1, 17, 17).
python_function('packages/dsl2tillm/src/dsl2tillm/cli.py', 'main', 1, 4, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/codec.py', 'validate_payload', 1, 2, 6).
python_function('packages/dsl2tillm/src/dsl2tillm/codec.py', 'parse_text', 1, 2, 2).
python_function('packages/dsl2tillm/src/dsl2tillm/codec.py', 'envelope_from_bytes', 1, 1, 2).
python_function('packages/dsl2tillm/src/dsl2tillm/grammar.py', '_flag', 2, 4, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/grammar.py', '_bool_flag', 2, 2, 2).
python_function('packages/dsl2tillm/src/dsl2tillm/grammar.py', '_quoted_or_tail', 1, 3, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/grammar.py', 'parse_line', 1, 35, 8).
python_function('packages/dsl2tillm/src/dsl2tillm/grammar.py', 'to_text', 1, 15, 5).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', 'run_query', 1, 8, 10).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', 'run_command', 1, 3, 5).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_health', 0, 1, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_clients', 0, 1, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_orient', 0, 1, 4).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_actions', 0, 1, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_validate', 1, 3, 8).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_resolve', 1, 2, 4).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_docker_status', 0, 2, 4).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_drive', 1, 3, 9).
python_function('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', '_drive_matrix', 1, 4, 11).
python_function('packages/dsl2tillm/src/dsl2tillm/pb_codec.py', 'encode_protobuf', 1, 1, 2).
python_function('packages/dsl2tillm/src/dsl2tillm/pb_codec.py', 'decode_protobuf', 1, 3, 5).
python_function('packages/dsl2tillm/src/dsl2tillm/pb_codec.py', 'encode_result_protobuf', 1, 1, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/schema_registry.py', '_load_schemas', 0, 4, 9).
python_function('packages/dsl2tillm/src/dsl2tillm/schema_registry.py', 'schema_for_verb', 1, 2, 4).
python_function('packages/dsl2tillm/src/dsl2tillm/schema_registry.py', 'all_verbs', 0, 1, 3).
python_function('packages/dsl2tillm/src/dsl2tillm/schema_registry.py', 'validate_schemas', 0, 5, 5).
python_function('packages/dsl2tillm/tests/test_bus.py', 'test_health', 0, 3, 1).
python_function('packages/dsl2tillm/tests/test_bus.py', 'test_orient', 0, 3, 1).
python_function('packages/dsl2tillm/tests/test_bus.py', 'test_clients', 0, 3, 1).
python_function('packages/dsl2tillm/tests/test_bus.py', 'test_actions', 0, 3, 1).
python_function('packages/dsl2tillm/tests/test_bus.py', 'test_validate_ecosystem', 0, 2, 1).
python_function('packages/dsl2tillm/tests/test_bus.py', 'test_resolve', 0, 3, 1).
python_function('packages/mcp2tillm/src/mcp2tillm/cli.py', 'main', 1, 3, 5).
python_function('packages/mcp2tillm/src/mcp2tillm/server.py', '_require_fastmcp', 0, 2, 1).
python_function('packages/mcp2tillm/src/mcp2tillm/server.py', 'create_server', 1, 1, 1).
python_function('packages/mcp2tillm/src/mcp2tillm/server.py', 'run_server', 0, 1, 2).
python_function('packages/mcp2tillm/tests/test_mcp2tillm.py', 'test_create_server', 0, 2, 1).
python_function('packages/nlp2tillm/src/nlp2tillm/cli.py', 'main', 1, 7, 11).
python_function('packages/nlp2tillm/src/nlp2tillm/to_dsl.py', 'to_dsl', 1, 2, 2).
python_function('packages/nlp2tillm/src/nlp2tillm/to_dsl.py', 'apply_nl', 1, 1, 3).
python_function('packages/nlp2tillm/tests/test_to_dsl.py', 'test_to_dsl_aider', 0, 3, 2).
python_function('packages/nlp2tillm/tests/test_to_dsl.py', 'test_to_dsl_codex', 0, 2, 1).
python_function('packages/rest2tillm/src/rest2tillm/app.py', 'create_app', 0, 1, 19).
python_function('packages/rest2tillm/src/rest2tillm/cli.py', 'main', 1, 3, 7).
python_function('packages/rest2tillm/tests/test_rest2tillm.py', 'test_root_endpoint', 0, 4, 4).
python_function('packages/rest2tillm/tests/test_rest2tillm.py', 'test_health_endpoint', 0, 3, 4).
python_function('packages/rest2tillm/tests/test_rest2tillm.py', 'test_post_dsl_health', 0, 4, 4).
python_function('packages/uri2tillm/src/uri2tillm/cli.py', 'main', 1, 7, 10).
python_function('packages/uri2tillm/src/uri2tillm/decode.py', 'uri_to_dsl', 1, 24, 8).
python_function('packages/uri2tillm/src/uri2tillm/run.py', 'run_uri', 1, 1, 2).
python_function('packages/uri2tillm/src/uri2tillm/uri.py', '_encode', 1, 1, 1).
python_function('packages/uri2tillm/src/uri2tillm/uri.py', '_decode', 1, 2, 1).
python_function('packages/uri2tillm/src/uri2tillm/uri.py', 'uri_for_cmd', 1, 4, 4).
python_function('packages/uri2tillm/src/uri2tillm/uri.py', 'uri_for_client', 1, 4, 3).
python_function('packages/uri2tillm/src/uri2tillm/uri.py', 'is_tillm_uri', 1, 1, 2).
python_function('packages/uri2tillm/src/uri2tillm/uri.py', 'parse_tillm_uri', 1, 5, 7).
python_function('packages/uri2tillm/tests/test_uri.py', 'test_decode_health_cmd', 0, 2, 2).
python_function('packages/uri2tillm/tests/test_uri.py', 'test_decode_drive_client', 0, 2, 2).
python_function('src/tillm/cli.py', '_format_client_row', 1, 13, 5).
python_function('src/tillm/cli.py', '_format_matrix_row', 1, 5, 3).
python_function('src/tillm/cli.py', '_print', 2, 17, 8).
python_function('src/tillm/cli.py', '_build_parser', 0, 1, 6).
python_function('src/tillm/cli.py', '_normalize_extra_arg_tokens', 1, 5, 3).
python_function('src/tillm/cli.py', '_resolve_execute_profile', 1, 2, 2).
python_function('src/tillm/cli.py', '_read_prompt', 1, 4, 4).
python_function('src/tillm/cli.py', '_resolve_drive_targets', 1, 1, 2).
python_function('src/tillm/cli.py', '_base_drive_request', 2, 3, 7).
python_function('src/tillm/cli.py', '_drive', 1, 8, 13).
python_function('src/tillm/cli.py', '_nlp', 1, 5, 10).
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
python_function('src/tillm/controller.py', 'resolve_backend', 1, 5, 3).
python_function('src/tillm/controller.py', '_prompt_root', 2, 2, 2).
python_function('src/tillm/controller.py', 'save_prompt', 1, 2, 7).
python_function('src/tillm/controller.py', '_resolve_spec', 1, 2, 2).
python_function('src/tillm/controller.py', '_resolve_command', 1, 2, 3).
python_function('src/tillm/controller.py', '_validate_request', 2, 5, 3).
python_function('src/tillm/controller.py', '_resolve_execute_args', 1, 3, 3).
python_function('src/tillm/controller.py', 'build_drive_plan', 1, 3, 14).
python_function('src/tillm/controller.py', '_timeout_value', 1, 3, 1).
python_function('src/tillm/controller.py', '_drive_result_from_exception', 2, 1, 3).
python_function('src/tillm/controller.py', '_drive_one_client', 2, 2, 4).
python_function('src/tillm/controller.py', 'drive_shell_llm_many', 1, 26, 18).
python_function('src/tillm/controller.py', 'drive_shell_llm', 1, 4, 5).
python_function('src/tillm/controller.py', 'result_from_error', 2, 1, 2).
python_function('src/tillm/nlp.py', '_client_from_text', 2, 6, 5).
python_function('src/tillm/nlp.py', '_strip_drive_prefix', 1, 5, 4).
python_function('src/tillm/nlp.py', '_intent_from_nlp2dsl', 2, 15, 11).
python_function('src/tillm/nlp.py', 'intent_from_text', 1, 3, 5).
python_function('src/tillm/registry.py', 'normalize_client_id', 1, 1, 4).
python_function('src/tillm/registry.py', 'iter_client_specs', 0, 1, 0).
python_function('src/tillm/registry.py', 'get_client_spec', 1, 3, 1).
python_function('src/tillm/registry.py', 'available_client_ids', 0, 4, 2).
python_function('src/tillm/registry.py', 'registered_client_ids', 0, 2, 1).
python_function('src/tillm/registry.py', 'resolve_client_ids', 0, 15, 13).
python_function('src/tillm/registry.py', 'detect_clients', 0, 4, 3).
python_function('src/tillm/registry.py', 'normalize_execute_profile', 1, 4, 2).
python_function('src/tillm/transports/binary.py', 'run_binary_drive', 2, 10, 6).
python_function('src/tillm/transports/docker.py', '_compose_file', 0, 2, 4).
python_function('src/tillm/transports/docker.py', 'docker_service_name', 1, 4, 1).
python_function('src/tillm/transports/docker.py', 'docker_service_status', 0, 9, 8).
python_function('src/tillm/transports/docker.py', '_docker_argv', 1, 1, 5).
python_function('src/tillm/transports/docker.py', 'run_docker_drive', 2, 10, 7).
python_function('src/tillm/validation.py', 'validate_client_readiness', 1, 7, 7).
python_function('src/tillm/validation.py', 'validate_intent', 1, 5, 8).
python_function('src/tillm/validation.py', 'validate_raw_dsl', 2, 12, 8).
python_function('src/tillm/validation.py', 'client_status_rows', 0, 1, 1).
python_function('src/tillm/validation.py', 'intent_contracts', 0, 1, 0).
python_function('src/tillm/validation.py', 'validate_intent_contracts', 0, 4, 3).
python_function('src/tillm/validation.py', 'ecosystem_status', 0, 5, 10).
python_function('tests/test_sillm.py', 'test_registry_normalizes_common_aliases', 2, 3, 3).
python_function('tests/test_sillm.py', 'test_registry_lists_all_shell_clients', 0, 7, 2).
python_function('tests/test_sillm.py', 'test_detect_clients_marks_available_from_injected_which', 0, 9, 2).
python_function('tests/test_sillm.py', 'test_detect_clients_reports_capabilities_and_env', 0, 8, 2).
python_function('tests/test_sillm.py', 'test_build_drive_plan_for_each_registered_client', 3, 11, 7).
python_function('tests/test_sillm.py', 'test_execute_args_match_vendor_headless_flags', 1, 3, 2).
python_function('tests/test_sillm.py', 'test_build_drive_plan_includes_execute_args_when_executing', 3, 9, 6).
python_function('tests/test_sillm.py', 'test_build_drive_plan_rejects_execute_for_cline', 1, 1, 3).
python_function('tests/test_sillm.py', 'test_build_drive_plan_uses_message_file_for_aider', 1, 7, 4).
python_function('tests/test_sillm.py', 'test_validate_client_readiness_reports_missing_binary_and_env', 1, 4, 3).
python_function('tests/test_sillm.py', 'test_validate_client_readiness_rejects_execute_for_interactive_only', 0, 3, 2).
python_function('tests/test_sillm.py', 'test_validate_raw_dsl_rejects_unknown_client', 0, 2, 1).
python_function('tests/test_sillm.py', 'test_compat_exports_koru_agent_rows', 0, 20, 11).
python_function('tests/test_sillm.py', 'test_drive_cli_accepts_space_form_extra_arg_flags', 3, 7, 6).
python_function('tests/test_sillm.py', 'test_clients_cli_lists_registered_clients', 1, 4, 2).
python_function('tests/test_sillm.py', 'test_nlp_rules_select_client_and_prompt', 0, 4, 2).
python_function('tests/test_sillm.py', 'test_validate_intent_rejects_raw_dsl_without_tillm_drive', 0, 3, 2).
python_function('tests/test_sillm.py', 'test_ecosystem_status_includes_client_rows', 0, 4, 3).
python_function('tests/test_sillm.py', 'test_automation_profile_uses_permission_bypass_flags', 3, 8, 7).
python_function('tests/test_sillm.py', 'test_automation_profile_is_rejected_when_unsupported', 2, 2, 5).
python_function('tests/test_sillm.py', 'test_drive_cli_accepts_automation_profile', 3, 5, 7).
python_function('tests/test_sillm.py', 'test_resolve_client_ids_for_all_available_only', 1, 2, 2).
python_function('tests/test_sillm.py', 'test_resolve_client_ids_for_clients_list', 0, 2, 1).
python_function('tests/test_sillm.py', 'test_drive_many_plans_all_selected_clients', 2, 7, 4).
python_function('tests/test_sillm.py', 'test_drive_many_fail_fast_stops_after_first_failure', 2, 5, 4).
python_function('tests/test_sillm.py', 'test_drive_cli_all_available_clients', 3, 6, 6).
python_function('tests/test_sillm.py', 'test_registry_lists_transport_metadata', 0, 5, 2).
python_function('tests/test_sillm.py', 'test_registered_and_available_client_helpers', 1, 5, 4).
python_function('tests/test_sillm.py', 'test_intent_contracts_are_exposed_for_ecosystem_validation', 0, 6, 3).

% ── Python Classes ───────────────────────────────────────
python_class('packages/dsl2tillm/src/dsl2tillm/events.py', 'StoredEvent').
python_method('StoredEvent', 'to_dict', 0, 1, 1).
python_class('packages/dsl2tillm/src/dsl2tillm/events.py', 'EventStore').
python_method('EventStore', '__init__', 1, 1, 0).
python_method('EventStore', 'for_workdir', 2, 1, 4).
python_method('EventStore', 'append_command', 2, 1, 9).
python_method('EventStore', 'read_all', 0, 4, 11).
python_class('packages/dsl2tillm/src/dsl2tillm/handlers/__init__.py', 'HandlerResult').
python_method('HandlerResult', 'to_dict', 0, 1, 0).
python_class('packages/dsl2tillm/src/dsl2tillm/result.py', 'DslResult').
python_method('DslResult', 'to_dict', 0, 1, 0).
python_class('packages/mcp2tillm/src/mcp2tillm/server.py', 'TillmMCPServer').
python_method('TillmMCPServer', '__post_init__', 0, 1, 3).
python_method('TillmMCPServer', '_register_tools', 0, 1, 6).
python_method('TillmMCPServer', 'run', 0, 1, 1).
python_class('src/tillm/controller.py', 'TillmError').
python_class('src/tillm/controller.py', 'UnknownClientError').
python_class('src/tillm/controller.py', 'ClientUnavailableError').
python_class('src/tillm/controller.py', 'ClientNotReadyError').
python_class('src/tillm/controller.py', 'UnknownProfileError').
python_class('src/tillm/controller.py', 'ShellDriveRequest').
python_class('src/tillm/controller.py', 'ShellDrivePlan').
python_method('ShellDrivePlan', 'shell_preview', 0, 2, 2).
python_method('ShellDrivePlan', 'to_dict', 0, 2, 3).
python_class('src/tillm/controller.py', 'MultiShellDriveRequest').
python_class('src/tillm/controller.py', 'ShellDriveResult').
python_method('ShellDriveResult', 'to_dict', 0, 2, 2).
python_class('src/tillm/controller.py', 'MultiShellDriveResult').
python_method('MultiShellDriveResult', 'to_dict', 0, 2, 2).
python_class('src/tillm/nlp.py', 'ShellIntent').
python_method('ShellIntent', 'to_dsl', 0, 1, 0).
python_class('src/tillm/registry.py', 'ShellClientSpec').
python_method('ShellClientSpec', 'command_path', 1, 4, 1).
python_method('ShellClientSpec', 'profile_execute_args', 1, 6, 3).
python_method('ShellClientSpec', 'supported_execute_profiles', 0, 2, 0).
python_method('ShellClientSpec', 'missing_env_vars', 1, 7, 6).
python_method('ShellClientSpec', 'to_dict', 0, 4, 4).
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
sumd_interface('api', '').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
sumd_interface('cli', '').
```

## Call Graph

*105 nodes · 135 edges · 24 modules · CC̄=4.4*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `dispatch` *(in packages.dsl2tillm.src.dsl2tillm.bus)* | 15 ⚠ | 14 | 29 | **43** |
| `_main_subcommand` *(in packages.dsl2tillm.src.dsl2tillm.cli)* | 17 ⚠ | 1 | 40 | **41** |
| `_print` *(in src.tillm.cli)* | 17 ⚠ | 7 | 29 | **36** |
| `_build_parser` *(in src.tillm.cli)* | 1 | 1 | 34 | **35** |
| `create_app` *(in packages.rest2tillm.src.rest2tillm.app)* | 1 | 1 | 34 | **35** |
| `_drive_matrix` *(in packages.dsl2tillm.src.dsl2tillm.handlers)* | 4 | 1 | 32 | **33** |
| `parse_line` *(in packages.dsl2tillm.src.dsl2tillm.grammar)* | 35 ⚠ | 1 | 29 | **30** |
| `uri_to_dsl` *(in packages.uri2tillm.src.uri2tillm.decode)* | 24 ⚠ | 2 | 27 | **29** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/tillm
# generated in 0.05s
# nodes: 105 | edges: 135 | modules: 24
# CC̄=4.4

HUBS[20]:
  packages.dsl2tillm.src.dsl2tillm.bus.dispatch
    CC=15  in:14  out:29  total:43
  packages.dsl2tillm.src.dsl2tillm.cli._main_subcommand
    CC=17  in:1  out:40  total:41
  src.tillm.cli._print
    CC=17  in:7  out:29  total:36
  src.tillm.cli._build_parser
    CC=1  in:1  out:34  total:35
  packages.rest2tillm.src.rest2tillm.app.create_app
    CC=1  in:1  out:34  total:35
  packages.dsl2tillm.src.dsl2tillm.handlers._drive_matrix
    CC=4  in:1  out:32  total:33
  packages.dsl2tillm.src.dsl2tillm.grammar.parse_line
    CC=35  in:1  out:29  total:30
  packages.uri2tillm.src.uri2tillm.decode.uri_to_dsl
    CC=24  in:2  out:27  total:29
  src.tillm.controller.drive_shell_llm_many
    CC=26  in:2  out:25  total:27
  src.tillm.nlp._intent_from_nlp2dsl
    CC=15  in:1  out:25  total:26
  packages.dsl2tillm.src.dsl2tillm.cli._main_legacy
    CC=12  in:1  out:20  total:21
  packages.dsl2tillm.src.dsl2tillm.handlers._drive
    CC=3  in:1  out:19  total:20
  src.tillm.registry.resolve_client_ids
    CC=15  in:3  out:17  total:20
  packages.dsl2tillm.src.dsl2tillm.grammar._flag
    CC=4  in:14  out:4  total:18
  src.tillm.compat.launch_koru_agent
    CC=8  in:0  out:17  total:17
  src.tillm.cli._drive
    CC=8  in:1  out:16  total:17
  src.tillm.validation.validate_raw_dsl
    CC=12  in:1  out:16  total:17
  packages.mcp2tillm.src.mcp2tillm.server.TillmMCPServer._register_tools
    CC=1  in:0  out:17  total:17
  src.tillm.controller.build_drive_plan
    CC=3  in:2  out:15  total:17
  src.tillm.validation.validate_client_readiness
    CC=7  in:5  out:11  total:16

MODULES:
  packages.cli2tillm.src.cli2tillm.shell  [1 funcs]
    run_shell  CC=8  out:11
  packages.dsl2tillm.src.dsl2tillm.bus  [3 funcs]
    dispatch  CC=15  out:29
    execute_dsl  CC=4  out:6
    execute_dsl_line  CC=1  out:1
  packages.dsl2tillm.src.dsl2tillm.cli  [3 funcs]
    _main_legacy  CC=12  out:20
    _main_subcommand  CC=17  out:40
    main  CC=4  out:3
  packages.dsl2tillm.src.dsl2tillm.codec  [3 funcs]
    envelope_from_bytes  CC=1  out:2
    parse_text  CC=2  out:2
    validate_payload  CC=2  out:6
  packages.dsl2tillm.src.dsl2tillm.grammar  [4 funcs]
    _bool_flag  CC=2  out:2
    _flag  CC=4  out:4
    _quoted_or_tail  CC=3  out:4
    parse_line  CC=35  out:29
  packages.dsl2tillm.src.dsl2tillm.handlers  [11 funcs]
    _actions  CC=1  out:3
    _clients  CC=1  out:3
    _docker_status  CC=2  out:4
    _drive  CC=3  out:19
    _drive_matrix  CC=4  out:32
    _health  CC=1  out:3
    _orient  CC=1  out:5
    _resolve  CC=2  out:6
    _validate  CC=3  out:11
    run_command  CC=3  out:5
  packages.dsl2tillm.src.dsl2tillm.pb_codec  [2 funcs]
    decode_protobuf  CC=3  out:5
    encode_result_protobuf  CC=1  out:3
  packages.dsl2tillm.src.dsl2tillm.schema_registry  [4 funcs]
    _load_schemas  CC=4  out:11
    all_verbs  CC=1  out:3
    schema_for_verb  CC=2  out:4
    validate_schemas  CC=5  out:9
  packages.mcp2tillm.src.mcp2tillm.cli  [1 funcs]
    main  CC=3  out:5
  packages.mcp2tillm.src.mcp2tillm.server  [5 funcs]
    __post_init__  CC=1  out:3
    _register_tools  CC=1  out:17
    _require_fastmcp  CC=2  out:1
    create_server  CC=1  out:1
    run_server  CC=1  out:2
  packages.nlp2tillm.src.nlp2tillm.to_dsl  [2 funcs]
    apply_nl  CC=1  out:3
    to_dsl  CC=2  out:2
  packages.rest2tillm.src.rest2tillm.app  [1 funcs]
    create_app  CC=1  out:34
  packages.rest2tillm.src.rest2tillm.cli  [1 funcs]
    main  CC=3  out:8
  packages.uri2tillm.src.uri2tillm.decode  [1 funcs]
    uri_to_dsl  CC=24  out:27
  packages.uri2tillm.src.uri2tillm.run  [1 funcs]
    run_uri  CC=1  out:2
  packages.uri2tillm.src.uri2tillm.uri  [5 funcs]
    _decode  CC=2  out:1
    _encode  CC=1  out:1
    parse_tillm_uri  CC=5  out:9
    uri_for_client  CC=4  out:6
    uri_for_cmd  CC=4  out:5
  src.tillm.cli  [10 funcs]
    _base_drive_request  CC=3  out:9
    _build_parser  CC=1  out:34
    _drive  CC=8  out:16
    _nlp  CC=5  out:14
    _normalize_extra_arg_tokens  CC=5  out:5
    _print  CC=17  out:29
    _read_prompt  CC=4  out:4
    _resolve_drive_targets  CC=1  out:3
    _resolve_execute_profile  CC=2  out:2
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
    tool_registry_entries  CC=4  out:6
  src.tillm.controller  [14 funcs]
    _drive_one_client  CC=2  out:4
    _drive_result_from_exception  CC=1  out:3
    _prompt_root  CC=2  out:3
    _resolve_command  CC=2  out:3
    _resolve_execute_args  CC=3  out:3
    _resolve_spec  CC=2  out:2
    _timeout_value  CC=3  out:1
    _validate_request  CC=5  out:4
    build_drive_plan  CC=3  out:15
    drive_shell_llm  CC=4  out:5
  src.tillm.nlp  [4 funcs]
    _client_from_text  CC=6  out:6
    _intent_from_nlp2dsl  CC=15  out:25
    _strip_drive_prefix  CC=5  out:5
    intent_from_text  CC=3  out:5
  src.tillm.registry  [8 funcs]
    available_client_ids  CC=4  out:2
    detect_clients  CC=4  out:3
    get_client_spec  CC=3  out:1
    iter_client_specs  CC=1  out:0
    normalize_client_id  CC=1  out:4
    normalize_execute_profile  CC=4  out:2
    registered_client_ids  CC=2  out:1
    resolve_client_ids  CC=15  out:17
  src.tillm.transports.binary  [1 funcs]
    run_binary_drive  CC=10  out:9
  src.tillm.transports.docker  [5 funcs]
    _compose_file  CC=2  out:6
    _docker_argv  CC=1  out:5
    docker_service_name  CC=4  out:1
    docker_service_status  CC=9  out:10
    run_docker_drive  CC=10  out:10
  src.tillm.validation  [6 funcs]
    client_status_rows  CC=1  out:1
    ecosystem_status  CC=5  out:10
    validate_client_readiness  CC=7  out:11
    validate_intent  CC=5  out:10
    validate_intent_contracts  CC=4  out:6
    validate_raw_dsl  CC=12  out:16

EDGES:
  packages.dsl2tillm.src.dsl2tillm.cli._main_legacy → packages.dsl2tillm.src.dsl2tillm.bus.dispatch
  packages.dsl2tillm.src.dsl2tillm.cli._main_legacy → packages.dsl2tillm.src.dsl2tillm.bus.execute_dsl
  packages.dsl2tillm.src.dsl2tillm.cli.main → packages.dsl2tillm.src.dsl2tillm.cli._main_legacy
  packages.dsl2tillm.src.dsl2tillm.cli.main → packages.dsl2tillm.src.dsl2tillm.cli._main_subcommand
  packages.nlp2tillm.src.nlp2tillm.to_dsl.to_dsl → src.tillm.nlp.intent_from_text
  packages.nlp2tillm.src.nlp2tillm.to_dsl.apply_nl → packages.nlp2tillm.src.nlp2tillm.to_dsl.to_dsl
  packages.nlp2tillm.src.nlp2tillm.to_dsl.apply_nl → packages.dsl2tillm.src.dsl2tillm.bus.dispatch
  packages.mcp2tillm.src.mcp2tillm.cli.main → packages.mcp2tillm.src.mcp2tillm.server.run_server
  packages.rest2tillm.src.rest2tillm.app.create_app → packages.dsl2tillm.src.dsl2tillm.schema_registry.schema_for_verb
  packages.rest2tillm.src.rest2tillm.app.create_app → packages.dsl2tillm.src.dsl2tillm.schema_registry.validate_schemas
  packages.dsl2tillm.src.dsl2tillm.codec.validate_payload → packages.dsl2tillm.src.dsl2tillm.schema_registry.schema_for_verb
  packages.dsl2tillm.src.dsl2tillm.codec.parse_text → packages.dsl2tillm.src.dsl2tillm.grammar.parse_line
  packages.dsl2tillm.src.dsl2tillm.codec.parse_text → packages.dsl2tillm.src.dsl2tillm.codec.validate_payload
  packages.dsl2tillm.src.dsl2tillm.codec.envelope_from_bytes → packages.dsl2tillm.src.dsl2tillm.codec.validate_payload
  packages.dsl2tillm.src.dsl2tillm.codec.envelope_from_bytes → packages.dsl2tillm.src.dsl2tillm.pb_codec.decode_protobuf
  packages.dsl2tillm.src.dsl2tillm.schema_registry.schema_for_verb → packages.dsl2tillm.src.dsl2tillm.schema_registry._load_schemas
  packages.dsl2tillm.src.dsl2tillm.schema_registry.all_verbs → packages.dsl2tillm.src.dsl2tillm.schema_registry._load_schemas
  packages.dsl2tillm.src.dsl2tillm.schema_registry.validate_schemas → packages.dsl2tillm.src.dsl2tillm.schema_registry._load_schemas
  packages.rest2tillm.src.rest2tillm.cli.main → packages.rest2tillm.src.rest2tillm.app.create_app
  packages.uri2tillm.src.uri2tillm.decode.uri_to_dsl → packages.uri2tillm.src.uri2tillm.uri.parse_tillm_uri
  packages.dsl2tillm.src.dsl2tillm.grammar._bool_flag → packages.dsl2tillm.src.dsl2tillm.grammar._flag
  packages.dsl2tillm.src.dsl2tillm.grammar.parse_line → packages.dsl2tillm.src.dsl2tillm.grammar._flag
  packages.dsl2tillm.src.dsl2tillm.grammar.parse_line → packages.dsl2tillm.src.dsl2tillm.grammar._quoted_or_tail
  packages.dsl2tillm.src.dsl2tillm.grammar.parse_line → packages.dsl2tillm.src.dsl2tillm.grammar._bool_flag
  packages.cli2tillm.src.cli2tillm.shell.run_shell → packages.dsl2tillm.src.dsl2tillm.bus.dispatch
  packages.uri2tillm.src.uri2tillm.uri.uri_for_cmd → packages.uri2tillm.src.uri2tillm.uri._encode
  packages.uri2tillm.src.uri2tillm.uri.uri_for_client → packages.uri2tillm.src.uri2tillm.uri._encode
  packages.uri2tillm.src.uri2tillm.uri.parse_tillm_uri → packages.uri2tillm.src.uri2tillm.uri._decode
  src.tillm.cli._resolve_execute_profile → src.tillm.registry.normalize_execute_profile
  src.tillm.cli._resolve_drive_targets → src.tillm.registry.resolve_client_ids
  src.tillm.cli._base_drive_request → src.tillm.cli._resolve_drive_targets
  src.tillm.cli._base_drive_request → src.tillm.cli._resolve_execute_profile
  src.tillm.cli._drive → src.tillm.cli._read_prompt
  src.tillm.cli._drive → src.tillm.cli._print
  src.tillm.cli._drive → src.tillm.controller.drive_shell_llm
  src.tillm.cli._drive → src.tillm.controller.drive_shell_llm_many
  src.tillm.cli._drive → src.tillm.controller.result_from_error
  src.tillm.cli._nlp → src.tillm.nlp.intent_from_text
  src.tillm.cli._nlp → src.tillm.validation.validate_intent
  src.tillm.cli._nlp → src.tillm.controller.drive_shell_llm
  src.tillm.cli._nlp → src.tillm.cli._print
  src.tillm.cli.main → src.tillm.cli._normalize_extra_arg_tokens
  src.tillm.cli.main → src.tillm.cli._print
  src.tillm.cli.main → src.tillm.cli._drive
  src.tillm.cli.main → src.tillm.cli._nlp
  src.tillm.cli.main → src.tillm.cli._build_parser
  src.tillm.cli.main → src.tillm.registry.detect_clients
  src.tillm.transports.binary.run_binary_drive → src.tillm.controller._timeout_value
  src.tillm.compat.is_shell_llm_client → src.tillm.registry.get_client_spec
  src.tillm.compat.is_client_available → src.tillm.registry.get_client_spec
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Intent

Text-interface LLM control plane for semcod/coru shell automation (pair with gillm for GUI).
