"""Lightweight validation hooks for TILLM ecosystem integration."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from typing import Any

from pathlib import Path

from tillm.nlp import ShellIntent
from tillm.project_env import bootstrap_project_env
from tillm.registry import detect_clients, get_client_spec, iter_client_specs, normalize_client_id

SLLM_DRIVE_ACTIONS = frozenset({"tillm.drive", "shell_llm_drive", "drive_shell_llm"})
SLLM_INTENT_CONTRACTS = (
    (
        "# @intract.v1 id:tillm.shell_drive scope:block "
        "intent:drive:shell_llm domain:shell "
        "input:client,prompt output:shell_invocation effect:process "
        "validate:known_client,prompt_presence,allowed_action "
        'meaning:"validate shell LLM drive intent before execution"'
    ),
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "errors": list(self.errors)}


def validate_client_readiness(
    client_id: str,
    *,
    require_execute: bool = False,
    environ: dict[str, str] | None = None,
) -> ValidationResult:
    spec = get_client_spec(client_id)
    if spec is None:
        return ValidationResult(ok=False, errors=(f"unknown client: {client_id}",))

    env = environ if environ is not None else os.environ
    errors: list[str] = []
    if spec.command_path() is None:
        commands = ", ".join(spec.commands)
        errors.append(f"{spec.id}: binary not in PATH ({commands})")
    missing_env = spec.missing_env_vars(env)
    if missing_env:
        errors.append(f"{spec.id}: missing env vars: {', '.join(missing_env)}")
    if require_execute and not spec.supports_execute:
        errors.append(f"{spec.id}: client does not support non-interactive --execute")
    return ValidationResult(ok=not errors, errors=tuple(errors))


def validate_intent(intent: ShellIntent) -> ValidationResult:
    errors: list[str] = []
    spec = get_client_spec(intent.client_id)
    if spec is None:
        errors.append(f"unknown client: {intent.client_id}")
    elif not intent.prompt.strip():
        errors.append("prompt is empty")
    elif intent.execute:
        readiness = validate_client_readiness(intent.client_id, require_execute=True)
        errors.extend(readiness.errors)
    if intent.raw_dsl is not None:
        errors.extend(validate_raw_dsl(intent.raw_dsl, intent.client_id))
    return ValidationResult(ok=not errors, errors=tuple(errors))


def validate_raw_dsl(raw_dsl: dict[str, Any], client_id: str) -> list[str]:
    steps = raw_dsl.get("steps")
    if not isinstance(steps, list):
        return ["raw_dsl.steps is missing"]
    for step in steps:
        if not isinstance(step, dict):
            continue
        action = str(step.get("action") or "")
        if action not in SLLM_DRIVE_ACTIONS:
            continue
        config = step.get("config") if isinstance(step.get("config"), dict) else {}
        raw_client = str(config.get("client") or client_id)
        normalized = normalize_client_id(raw_client)
        if normalized != client_id:
            return [f"raw_dsl client mismatch: {raw_client} != {client_id}"]
        if get_client_spec(normalized) is None:
            return [f"raw_dsl unknown client: {raw_client}"]
        if bool(config.get("execute")):
            readiness = validate_client_readiness(normalized, require_execute=True)
            if not readiness.ok:
                return list(readiness.errors)
        return []
    return ["raw_dsl has no tillm drive action"]


def client_status_rows() -> list[dict[str, object]]:
    return detect_clients()


def intent_contracts() -> tuple[str, ...]:
    return SLLM_INTENT_CONTRACTS


def validate_intent_contracts() -> dict[str, object]:
    try:
        from intract.parsers.inline import parse_contract_line
    except Exception:
        return {
            "available": False,
            "ok": True,
            "contracts": list(SLLM_INTENT_CONTRACTS),
            "parsed": [],
        }
    parsed = []
    errors = []
    for line in SLLM_INTENT_CONTRACTS:
        contract = parse_contract_line(line)
        if contract is None:
            errors.append(line)
        else:
            parsed.append(
                {
                    "id": contract.contract_id,
                    "intent": contract.key,
                    "domain": contract.domain,
                    "validators": list(contract.validators),
                }
            )
    return {
        "available": True,
        "ok": not errors,
        "contracts": list(SLLM_INTENT_CONTRACTS),
        "parsed": parsed,
        "errors": errors,
    }


def ecosystem_status(*, project: Path | str | None = None) -> dict[str, object]:
    bootstrap_project_env(project or Path.cwd())
    packages = {
        "nlp2dsl": "nlp2dsl_sdk",
        "intract": "intract",
        "redsl": "redsl",
        "proxym": "proxym",
        "llx": "llx",
        "env2llm": "env2llm",
    }
    clients = client_status_rows()
    client_errors: list[str] = []
    for row in clients:
        client_id = str(row["id"])
        readiness = validate_client_readiness(client_id)
        if not readiness.ok:
            client_errors.extend(readiness.errors)
    return {
        "ok": True,
        "packages": {
            name: {"import": module, "available": importlib.util.find_spec(module) is not None}
            for name, module in packages.items()
        },
        "clients": {
            "count": len(clients),
            "registered": [spec.id for spec in iter_client_specs()],
            "rows": clients,
            "errors": client_errors,
        },
        "expected_actions": sorted(SLLM_DRIVE_ACTIONS),
        "intent_contracts": validate_intent_contracts(),
    }


__all__ = [
    "SLLM_DRIVE_ACTIONS",
    "SLLM_INTENT_CONTRACTS",
    "ValidationResult",
    "client_status_rows",
    "ecosystem_status",
    "intent_contracts",
    "validate_client_readiness",
    "validate_intent",
    "validate_intent_contracts",
    "validate_raw_dsl",
]
