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

