# tillm

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `tillm`
- **version**: `0.1.32`
- **python_requires**: `>=3.11`
- **license**: Apache-2.0
- **ai_model**: `openrouter/deep/deep-v4-pro`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(1), app.doql.less, goal.yaml, .env.example, project/(5 analysis files)

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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

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

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 62f 4173L | python:39,json:10,toml:7,shell:2,yaml:2,txt:1,yml:1 | 2026-06-08
# generated in 0.01s
# CC̅=4.4 | critical:10/136 | dups:0 | cycles:0

HEALTH[10]:
  🟡 CC    _main_subcommand CC=17 (limit:15)
  🟡 CC    uri_to_dsl CC=24 (limit:15)
  🟡 CC    main CC=16 (limit:15)
  🟡 CC    parse_line CC=35 (limit:15)
  🟡 CC    to_text CC=15 (limit:15)
  🟡 CC    _print CC=17 (limit:15)
  🟡 CC    dispatch CC=15 (limit:15)
  🟡 CC    _intent_from_nlp2dsl CC=15 (limit:15)
  🟡 CC    resolve_client_ids CC=15 (limit:15)
  🟡 CC    drive_shell_llm_many CC=26 (limit:15)

REFACTOR[1]:
  1. split 10 high-CC methods  (CC>15)

PIPELINES[38]:
  [1] Src [main]: main → _main_legacy → dispatch → envelope_from_bytes → ...(3 more)
      PURITY: 100% pure
  [2] Src [main]: main → run_server → create_server
      PURITY: 100% pure
  [3] Src [encode_protobuf]: encode_protobuf
      PURITY: 100% pure
  [4] Src [all_verbs]: all_verbs → _load_schemas
      PURITY: 100% pure
  [5] Src [main]: main → create_app → schema_for_verb → _load_schemas
      PURITY: 100% pure
  [6] Src [main]: main → run_shell → dispatch → envelope_from_bytes → ...(3 more)
      PURITY: 100% pure
  [7] Src [to_text]: to_text
      PURITY: 100% pure
  [8] Src [uri_for_cmd]: uri_for_cmd → _encode
      PURITY: 100% pure
  [9] Src [uri_for_client]: uri_for_client → _encode
      PURITY: 100% pure
  [10] Src [is_tillm_uri]: is_tillm_uri
      PURITY: 100% pure
  [11] Src [main]: main → _normalize_extra_arg_tokens
      PURITY: 100% pure
  [12] Src [main]: main → run_uri → uri_to_dsl → parse_tillm_uri → ...(1 more)
      PURITY: 100% pure
  [13] Src [main]: main → apply_nl → to_dsl → intent_from_text → ...(2 more)
      PURITY: 100% pure
  [14] Src [is_client_available]: is_client_available → get_client_spec → normalize_client_id
      PURITY: 100% pure
  [15] Src [shell_client_ids]: shell_client_ids → iter_client_specs
      PURITY: 100% pure
  [16] Src [shell_process_patterns]: shell_process_patterns → iter_client_specs
      PURITY: 100% pure
  [17] Src [tool_registry_entries]: tool_registry_entries → iter_client_specs
      PURITY: 100% pure
  [18] Src [autopilot_backend_for_client]: autopilot_backend_for_client → is_shell_llm_client → get_client_spec → normalize_client_id
      PURITY: 100% pure
  [19] Src [detect_koru_agent_rows]: detect_koru_agent_rows → detect_clients → normalize_client_id
      PURITY: 100% pure
  [20] Src [drive_koru_chat]: drive_koru_chat → drive_shell_llm → build_drive_plan → _resolve_spec → ...(2 more)
      PURITY: 100% pure
  [21] Src [launch_koru_agent]: launch_koru_agent → normalize_client_id
      PURITY: 100% pure
  [22] Src [to_dict]: to_dict
      PURITY: 100% pure
  [23] Src [for_workdir]: for_workdir
      PURITY: 100% pure
  [24] Src [append_command]: append_command
      PURITY: 100% pure
  [25] Src [read_all]: read_all
      PURITY: 100% pure
  [26] Src [__post_init__]: __post_init__ → _require_fastmcp
      PURITY: 100% pure
  [27] Src [_register_tools]: _register_tools → dispatch → envelope_from_bytes → validate_payload → ...(2 more)
      PURITY: 100% pure
  [28] Src [run]: run
      PURITY: 100% pure
  [29] Src [to_dict]: to_dict
      PURITY: 100% pure
  [30] Src [command_path]: command_path
      PURITY: 100% pure
  [31] Src [profile_execute_args]: profile_execute_args
      PURITY: 100% pure
  [32] Src [missing_env_vars]: missing_env_vars
      PURITY: 100% pure
  [33] Src [to_dict]: to_dict
      PURITY: 100% pure
  [34] Src [shell_preview]: shell_preview
      PURITY: 100% pure
  [35] Src [to_dict]: to_dict
      PURITY: 100% pure
  [36] Src [to_dict]: to_dict
      PURITY: 100% pure
  [37] Src [to_dict]: to_dict
      PURITY: 100% pure
  [38] Src [_drive_one_client]: _drive_one_client → drive_shell_llm → build_drive_plan → _resolve_spec → ...(2 more)
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=4.5    ←in:0  →out:0
  │ !! controller                 412L  10C   18m  CC=26     ←5
  │ !! cli                        314L  0C   12m  CC=17     ←0
  │ !! registry                   309L  1C   13m  CC=15     ←7
  │ compat                     205L  0C   11m  CC=8      ←0
  │ validation                 182L  1C    8m  CC=12     ←3
  │ docker                     143L  0C    5m  CC=10     ←2
  │ !! nlp                        104L  1C    5m  CC=15     ←2
  │ binary                      77L  0C    1m  CC=10     ←1
  │ __init__                    46L  0C    0m  CC=0.0    ←0
  │ __init__                    10L  0C    0m  CC=0.0    ←0
  │ __main__                     7L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=4.4    ←in:0  →out:0
  │ __init__                   176L  1C   12m  CC=8      ←1
  │ !! grammar                    151L  0C    5m  CC=35     ←1
  │ !! cli                        112L  0C    3m  CC=17     ←0
  │ !! bus                         88L  0C    3m  CC=15     ←7
  │ app                         78L  0C    1m  CC=1      ←1
  │ !! cli                         70L  0C    1m  CC=16     ←0
  │ server                      69L  1C    6m  CC=2      ←1
  │ events                      67L  2C    5m  CC=4      ←0
  │ !! decode                      60L  0C    1m  CC=24     ←2
  │ uri                         51L  0C    6m  CC=5      ←1
  │ schema_registry             49L  0C    4m  CC=5      ←3
  │ cli                         40L  0C    1m  CC=7      ←0
  │ cli                         40L  0C    1m  CC=7      ←0
  │ pyproject.toml              33L  0C    0m  CC=0.0    ←0
  │ shell                       32L  0C    1m  CC=8      ←1
  │ codec                       31L  0C    3m  CC=2      ←1
  │ pyproject.toml              31L  0C    0m  CC=0.0    ←0
  │ pb_codec                    28L  0C    3m  CC=3      ←3
  │ result                      28L  1C    1m  CC=1      ←0
  │ pyproject.toml              28L  0C    0m  CC=0.0    ←0
  │ cli                         27L  0C    1m  CC=3      ←0
  │ pyproject.toml              24L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              24L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              24L  0C    0m  CC=0.0    ←0
  │ cli                         23L  0C    1m  CC=3      ←0
  │ to_dsl                      21L  0C    2m  CC=2      ←3
  │ drive_matrix.schema.json    20L  0C    0m  CC=0.0    ←0
  │ drive.schema.json           16L  0C    0m  CC=0.0    ←0
  │ install-dev.sh              14L  0C    0m  CC=0.0    ←0
  │ run                         11L  0C    1m  CC=1      ←1
  │ resolve.schema.json         10L  0C    0m  CC=0.0    ←0
  │ validate.schema.json        10L  0C    0m  CC=0.0    ←0
  │ docker_status.schema.json     9L  0C    0m  CC=0.0    ←0
  │ health.schema.json           9L  0C    0m  CC=0.0    ←0
  │ clients.schema.json          9L  0C    0m  CC=0.0    ←0
  │ actions.schema.json          9L  0C    0m  CC=0.0    ←0
  │ orient.schema.json           9L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ engine                       5L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              77L  0C    0m  CC=0.0    ←0
  │ project.sh                  62L  0C    1m  CC=0.0    ←0
  │ tree.txt                    58L  0C    0m  CC=0.0    ←0
  │ coverage.json                1L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  deploy/                         CC̄=0.0    ←in:0  →out:0
  │ docker-compose.yml          77L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                        packages.dsl2tillm            src.tillm   packages.mcp2tillm  packages.rest2tillm   packages.nlp2tillm   packages.cli2tillm   packages.uri2tillm
   packages.dsl2tillm                   ──                   10                   ←6                   ←6                    1                   ←3                   ←1  hub
            src.tillm                  ←10                   ──                                                             ←1                                            hub
   packages.mcp2tillm                    6                                        ──                                         1                                          
  packages.rest2tillm                    6                                                             ──                                                               
   packages.nlp2tillm                    1                    1                   ←1                                        ──                                          
   packages.cli2tillm                    3                                                                                                       ──                     
   packages.uri2tillm                    1                                                                                                                            ──
  CYCLES: none
  HUB: src.tillm/ (fan-in=11)
  HUB: packages.dsl2tillm/ (fan-in=17)
  SMELL: packages.dsl2tillm/ fan-out=11 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 39f 3088L | 2026-06-08

SUMMARY:
  files_scanned: 39
  total_lines:   3088
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       2189
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 136 func | 30f | 2026-06-08
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !! SPLIT-FUNC      drive_shell_llm_many  CC=26  fan=18
      WHY: CC=26 exceeds 15
      EFFORT: ~1h  IMPACT: 468

  [2] !  SPLIT-FUNC      _main_subcommand  CC=17  fan=20
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 340

  [3] !! SPLIT-FUNC      parse_line  CC=35  fan=8
      WHY: CC=35 exceeds 15
      EFFORT: ~1h  IMPACT: 280

  [4] !  SPLIT-FUNC      main  CC=16  fan=17
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 272

  [5] !  SPLIT-FUNC      dispatch  CC=15  fan=18
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 270

  [6] !  SPLIT-FUNC      _intent_from_nlp2dsl  CC=15  fan=14
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 210

  [7] !  SPLIT-FUNC      resolve_client_ids  CC=15  fan=13
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 195

  [8] !  SPLIT-FUNC      uri_to_dsl  CC=24  fan=8
      WHY: CC=24 exceeds 15
      EFFORT: ~1h  IMPACT: 192

  [9] !  SPLIT-FUNC      _print  CC=17  fan=9
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 153

  [10] !  SPLIT-FUNC      to_text  CC=15  fan=5
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 75


RISKS[1]:
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          4.4 → ≤3.1
  max-CC:      35 → ≤17
  god-modules: 1 → 0
  high-CC(≥15): 10 → ≤5
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=3.3 → now CC̄=4.4
```

## Intent

Text-interface LLM control plane for semcod/coru shell automation (pair with gillm for GUI).
