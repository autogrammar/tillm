"""Lightweight validation hooks for SILLM ecosystem integration."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any

from tillm.nlp import ShellIntent
from tillm.registry import get_client_spec, normalize_client_id

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


def validate_intent(intent: ShellIntent) -> ValidationResult:
    errors: list[str] = []
    if get_client_spec(intent.client_id) is None:
        errors.append(f"unknown client: {intent.client_id}")
    if not intent.prompt.strip():
        errors.append("prompt is empty")
    if intent.raw_dsl is not None:
        errors.extend(_validate_raw_dsl(intent.raw_dsl, intent.client_id))
    return ValidationResult(ok=not errors, errors=tuple(errors))


def _validate_raw_dsl(raw_dsl: dict[str, Any], client_id: str) -> list[str]:
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
        if normalize_client_id(raw_client) != client_id:
            return [f"raw_dsl client mismatch: {raw_client} != {client_id}"]
        return []
    return ["raw_dsl has no tillm drive action"]


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


def ecosystem_status() -> dict[str, object]:
    packages = {
        "nlp2dsl": "nlp2dsl_sdk",
        "intract": "intract",
        "redsl": "redsl",
        "proxym": "proxym",
        "llx": "llx",
    }
    return {
        "ok": True,
        "packages": {
            name: {"import": module, "available": importlib.util.find_spec(module) is not None}
            for name, module in packages.items()
        },
        "expected_actions": sorted(SLLM_DRIVE_ACTIONS),
        "intent_contracts": validate_intent_contracts(),
    }


__all__ = [
    "SLLM_DRIVE_ACTIONS",
    "SLLM_INTENT_CONTRACTS",
    "ValidationResult",
    "ecosystem_status",
    "intent_contracts",
    "validate_intent",
    "validate_intent_contracts",
]
