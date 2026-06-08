# System Architecture Analysis
<!-- generated in 0.00s -->

## Overview

- **Project**: /home/tom/github/semcod/tillm
- **Primary Language**: python
- **Languages**: python: 8, yaml: 2, txt: 1, shell: 1, toml: 1
- **Analysis Mode**: static
- **Total Functions**: 47
- **Total Classes**: 9
- **Modules**: 13
- **Entry Points**: 20

## Architecture by Module

### src.tillm.controller
- **Functions**: 11
- **Classes**: 6
- **File**: `controller.py`

### src.tillm.compat
- **Functions**: 11
- **File**: `compat.py`

### src.tillm.cli
- **Functions**: 7
- **File**: `cli.py`

### src.sillm.registry
- **Functions**: 6
- **Classes**: 1
- **File**: `registry.py`

### src.tillm.validation
- **Functions**: 6
- **Classes**: 1
- **File**: `validation.py`

### src.tillm.nlp
- **Functions**: 5
- **Classes**: 1
- **File**: `nlp.py`

### project
- **Functions**: 1
- **File**: `project.sh`

## Key Entry Points

Main execution flows into the system:

### src.tillm.compat.launch_koru_agent
> Launch a Koru agent through SILLM while preserving TTY behavior.

Clients with a file/arg prompt contract receive the prompt directly.
Stdin-only clie
- **Calls**: src.sillm.registry.normalize_client_id, src.sillm.registry.get_client_spec, src.tillm.controller.save_prompt, print, print, print, ShellDriveRequest, src.tillm.controller.build_drive_plan

### src.tillm.cli.main
- **Calls**: None.parse_args, AssertionError, src.tillm.cli._normalize_extra_arg_tokens, src.tillm.cli._print, src.tillm.cli._drive, src.tillm.cli._nlp, src.tillm.cli._print, src.tillm.cli._build_parser

### src.tillm.compat.detect_koru_agent_rows
> Return SLLM clients in Koru ``AgentOption.to_dict`` shape.
- **Calls**: src.sillm.registry.detect_clients, row.get, str, bool, rows.append, row.get, bool, bool

### src.tillm.controller.ShellDrivePlan.to_dict
- **Calls**: list, self.shell_preview, str, str

### src.sillm.registry.ShellClientSpec.to_dict
- **Calls**: self.command_path, list, list, list

### src.tillm.compat.tool_registry_entries
- **Calls**: src.sillm.registry.iter_client_specs, tuple, entries.append, list

### src.tillm.compat.is_client_available
- **Calls**: src.sillm.registry.get_client_spec, bool, spec.command_path

### src.tillm.compat.drive_koru_chat
- **Calls**: src.tillm.controller.drive_shell_llm, result.to_dict, ShellDriveRequest

### src.tillm.controller.ShellDrivePlan.shell_preview
- **Calls**: None.join, shlex.quote

### src.tillm.controller.ShellDriveResult.to_dict
- **Calls**: list, str

### src.tillm.compat.shell_client_ids
- **Calls**: tuple, src.sillm.registry.iter_client_specs

### src.tillm.compat.shell_process_patterns
- **Calls**: tuple, src.sillm.registry.iter_client_specs

### src.sillm.registry.ShellClientSpec.command_path
- **Calls**: resolver

### src.tillm.validation.ValidationResult.to_dict
- **Calls**: list

### src.tillm.compat.autopilot_backend_for_client
- **Calls**: src.tillm.compat.is_shell_llm_client

### project.venv_is_usable

### src.tillm.validation.intent_contracts

### src.tillm.nlp.ShellIntent.to_dsl

### src.tillm.compat.agent_backend_profiles
> Return Koru-compatible backend profile metadata for shell LLM control.

### src.tillm.compat.agent_backend_aliases
> Return Koru backend aliases owned by SLLM.

## Process Flows

Key execution flows identified:

### Flow 1: launch_koru_agent
```
launch_koru_agent [src.tillm.compat]
  └─ →> normalize_client_id
  └─ →> get_client_spec
      └─> normalize_client_id
  └─ →> save_prompt
      └─> _prompt_root
```

### Flow 2: main
```
main [src.tillm.cli]
  └─> _normalize_extra_arg_tokens
  └─> _print
```

### Flow 3: detect_koru_agent_rows
```
detect_koru_agent_rows [src.tillm.compat]
  └─ →> detect_clients
      └─> normalize_client_id
```

### Flow 4: to_dict
```
to_dict [src.tillm.controller.ShellDrivePlan]
```

### Flow 5: tool_registry_entries
```
tool_registry_entries [src.tillm.compat]
  └─ →> iter_client_specs
```

### Flow 6: is_client_available
```
is_client_available [src.tillm.compat]
  └─ →> get_client_spec
      └─> normalize_client_id
```

### Flow 7: drive_koru_chat
```
drive_koru_chat [src.tillm.compat]
  └─ →> drive_shell_llm
      └─> build_drive_plan
          └─> _resolve_spec
          └─> _resolve_command
```

### Flow 8: shell_preview
```
shell_preview [src.tillm.controller.ShellDrivePlan]
```

### Flow 9: shell_client_ids
```
shell_client_ids [src.tillm.compat]
  └─ →> iter_client_specs
```

### Flow 10: shell_process_patterns
```
shell_process_patterns [src.tillm.compat]
  └─ →> iter_client_specs
```

## Key Classes

### src.tillm.controller.ShellDrivePlan
- **Methods**: 2
- **Key Methods**: src.tillm.controller.ShellDrivePlan.shell_preview, src.tillm.controller.ShellDrivePlan.to_dict

### src.sillm.registry.ShellClientSpec
- **Methods**: 2
- **Key Methods**: src.sillm.registry.ShellClientSpec.command_path, src.sillm.registry.ShellClientSpec.to_dict

### src.tillm.controller.ShellDriveResult
- **Methods**: 1
- **Key Methods**: src.tillm.controller.ShellDriveResult.to_dict

### src.tillm.validation.ValidationResult
- **Methods**: 1
- **Key Methods**: src.tillm.validation.ValidationResult.to_dict

### src.tillm.nlp.ShellIntent
- **Methods**: 1
- **Key Methods**: src.tillm.nlp.ShellIntent.to_dsl

### src.tillm.controller.TillmError
> Base error for SLLM control failures.
- **Methods**: 0
- **Inherits**: RuntimeError

### src.tillm.controller.UnknownClientError
> Requested client is not registered.
- **Methods**: 0
- **Inherits**: TillmError

### src.tillm.controller.ClientUnavailableError
> Registered client command is not available in PATH.
- **Methods**: 0
- **Inherits**: TillmError

### src.tillm.controller.ShellDriveRequest
- **Methods**: 0

## Data Transformation Functions

Key functions that process and transform data:

### src.tillm.cli._build_parser
- **Output to**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, clients.add_argument, sub.add_parser

### src.tillm.validation.validate_intent
- **Output to**: ValidationResult, src.sillm.registry.get_client_spec, errors.append, intent.prompt.strip, errors.append

### src.tillm.validation._validate_raw_dsl
- **Output to**: raw_dsl.get, isinstance, str, str, isinstance

### src.tillm.validation.validate_intent_contracts
- **Output to**: parse_contract_line, list, errors.append, parsed.append, list

### src.tillm.compat.shell_process_patterns
- **Output to**: tuple, src.sillm.registry.iter_client_specs

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `src.tillm.compat.launch_koru_agent` - 17 calls
- `src.tillm.cli.main` - 11 calls
- `src.tillm.controller.build_drive_plan` - 11 calls
- `src.tillm.controller.drive_shell_llm` - 10 calls
- `src.tillm.compat.detect_koru_agent_rows` - 9 calls
- `src.tillm.validation.validate_intent` - 8 calls
- `src.tillm.controller.save_prompt` - 7 calls
- `src.tillm.validation.validate_intent_contracts` - 6 calls
- `src.tillm.nlp.intent_from_text` - 5 calls
- `src.tillm.controller.ShellDrivePlan.to_dict` - 4 calls
- `src.sillm.registry.ShellClientSpec.to_dict` - 4 calls
- `src.sillm.registry.normalize_client_id` - 4 calls
- `src.tillm.validation.ecosystem_status` - 4 calls
- `src.tillm.compat.tool_registry_entries` - 4 calls
- `src.sillm.registry.detect_clients` - 3 calls
- `src.tillm.compat.is_client_available` - 3 calls
- `src.tillm.compat.drive_koru_chat` - 3 calls
- `src.tillm.controller.ShellDrivePlan.shell_preview` - 2 calls
- `src.tillm.controller.ShellDriveResult.to_dict` - 2 calls
- `src.tillm.controller.result_from_error` - 2 calls
- `src.tillm.compat.shell_client_ids` - 2 calls
- `src.tillm.compat.shell_process_patterns` - 2 calls
- `src.sillm.registry.ShellClientSpec.command_path` - 1 calls
- `src.sillm.registry.get_client_spec` - 1 calls
- `src.tillm.validation.ValidationResult.to_dict` - 1 calls
- `src.tillm.compat.is_shell_llm_client` - 1 calls
- `src.tillm.compat.autopilot_backend_for_client` - 1 calls
- `project.venv_is_usable` - 0 calls
- `src.sillm.registry.iter_client_specs` - 0 calls
- `src.tillm.validation.intent_contracts` - 0 calls
- `src.tillm.nlp.ShellIntent.to_dsl` - 0 calls
- `src.tillm.compat.agent_backend_profiles` - 0 calls
- `src.tillm.compat.agent_backend_aliases` - 0 calls

## System Interactions

How components interact:

```mermaid
graph TD
    launch_koru_agent --> normalize_client_id
    launch_koru_agent --> get_client_spec
    launch_koru_agent --> save_prompt
    launch_koru_agent --> print
    main --> parse_args
    main --> AssertionError
    main --> _normalize_extra_arg
    main --> _print
    main --> _drive
    detect_koru_agent_ro --> detect_clients
    detect_koru_agent_ro --> get
    detect_koru_agent_ro --> str
    detect_koru_agent_ro --> bool
    detect_koru_agent_ro --> append
    to_dict --> list
    to_dict --> shell_preview
    to_dict --> str
    to_dict --> command_path
    tool_registry_entrie --> iter_client_specs
    tool_registry_entrie --> tuple
    tool_registry_entrie --> append
    tool_registry_entrie --> list
    is_client_available --> get_client_spec
    is_client_available --> bool
    is_client_available --> command_path
    drive_koru_chat --> drive_shell_llm
    drive_koru_chat --> to_dict
    drive_koru_chat --> ShellDriveRequest
    shell_preview --> join
    shell_preview --> quote
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.