"""Compatibility helpers used by Koru during the migration to TILLM."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tillm.controller import (
    ClientUnavailableError,
    ShellDriveRequest,
    build_drive_plan,
    drive_shell_llm,
    save_prompt,
)
from tillm.registry import detect_clients, get_client_spec, iter_client_specs, normalize_client_id

SHELL_AUTOPILOT_BACKEND = "tillm_shell"
SHELL_BACKEND_PROFILE_ID = "vendor_agent_cli"


def agent_backend_profiles() -> tuple[dict[str, object], ...]:
    """Return Koru-compatible backend profile metadata for shell LLM control."""
    return (
        {
            "id": SHELL_BACKEND_PROFILE_ID,
            "transport": "tillm shell subprocess",
            "can_push_chat": True,
            "can_pull_chat_text": False,
            "needs_gui_session": False,
            "mcp_tools_only": False,
            "primary_code": "/home/tom/github/semcod/tillm",
        },
    )


def agent_backend_aliases() -> dict[str, str]:
    """Return Koru backend aliases owned by TILLM."""
    return {
        "tillm_shell": SHELL_BACKEND_PROFILE_ID,
        "cursor_cli": SHELL_BACKEND_PROFILE_ID,
        "vendor_cli": SHELL_BACKEND_PROFILE_ID,
    }


def is_shell_llm_client(agent_id: str) -> bool:
    return get_client_spec(agent_id) is not None


def is_client_available(client_id: str) -> bool:
    spec = get_client_spec(client_id)
    return bool(spec and spec.command_path())


def shell_client_ids() -> tuple[str, ...]:
    return tuple(spec.id for spec in iter_client_specs())


def shell_process_patterns() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    return tuple((spec.id, spec.label, spec.commands) for spec in iter_client_specs())


def tool_registry_entries() -> tuple[dict[str, object], ...]:
    entries: list[dict[str, object]] = []
    stable = {"claude-code", "aider"}
    for spec in iter_client_specs():
        registry_id = "codex-cli" if spec.id == "codex" else spec.id
        entries.append(
            {
                "id": registry_id,
                "name": spec.label,
                "category": "cli_agent",
                "lane": "native",
                "stability": "stable" if spec.id in stable else "beta",
                "detect": {
                    "commands": list(spec.commands),
                    "markers": [],
                    "env": list(spec.env_vars) + list(spec.env_vars_any),
                },
                "invoke": (
                    f"koru tillm drive --client {spec.id} "
                    "--prompt '<prompt>' --execute"
                ),
                "notes": "Shell agent lane delegated to the external tillm plugin.",
            }
        )
    return tuple(entries)


def autopilot_backend_for_client(agent_id: str) -> str | None:
    return SHELL_AUTOPILOT_BACKEND if is_shell_llm_client(agent_id) else None


def detect_koru_agent_rows(
    *,
    project_hint_ids: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Return TILLM clients in Koru ``AgentOption.to_dict`` shape."""
    rows: list[dict[str, Any]] = []
    for row in detect_clients(project_hint_ids=project_hint_ids):
        command = row.get("command_path")
        label = str(row["label"])
        project_hint = bool(row.get("project_hint"))
        if command:
            reason = f"{label} CLI detected in PATH."
        elif project_hint:
            reason = f"{label} project config detected; open the prompt manually."
        else:
            reason = f"{label} CLI is not in PATH."
        rows.append(
            {
                "id": row["id"],
                "label": label,
                "available": bool(row["available"]),
                "launchable": bool(command),
                "command": command if isinstance(command, str) else None,
                "reason": reason,
                "project_hint": project_hint,
                "autopilot_backend": SHELL_AUTOPILOT_BACKEND,
            }
        )
    return rows


def drive_koru_chat(
    *,
    client_id: str,
    project: Path,
    prompt: str,
    execute: bool = True,
    model: str | None = None,
    execute_profile: str = "default",
) -> dict[str, object]:
    result = drive_shell_llm(
        ShellDriveRequest(
            client_id=client_id,
            prompt=prompt,
            project=project,
            execute=execute,
            dry_run=not execute,
            model=model,
            execute_profile=execute_profile,
        )
    )
    return result.to_dict()


def launch_koru_agent(
    *,
    agent_id: str,
    project: Path,
    prompt: str,
    command: str | None = None,
) -> int:
    """Launch a Koru agent through TILLM while preserving TTY behavior.

    Clients with a file/arg prompt contract receive the prompt directly.
    Stdin-only clients are launched interactively after TILLM saves the prompt,
    matching Koru's legacy behavior and avoiding accidental TTY breakage.
    """
    client_id = normalize_client_id(agent_id)
    spec = get_client_spec(client_id)
    if spec is None:
        return 2

    if spec.prompt_mode in {"message-file", "arg"}:
        request = ShellDriveRequest(client_id=client_id, prompt=prompt, project=project)
        plan = build_drive_plan(request)
        argv = list(plan.argv)
        if command:
            argv[0] = command
        print(f"tillm: launching {spec.label}")
        print(f"Prompt saved: {plan.prompt_path}")
        try:
            return subprocess.call(argv, cwd=project)
        except OSError as exc:
            print(f"tillm: failed to launch {spec.label}: {exc}")
            return 1

    prompt_path = save_prompt(prompt, project=project)
    command_path = command or spec.command_path()
    if not command_path:
        raise ClientUnavailableError(f"{client_id}: command not found")
    print(f"tillm: launching {spec.label}")
    print(f"Prompt saved: {prompt_path}")
    print("Open that prompt in the agent if its CLI starts an interactive session.")
    try:
        return subprocess.call([command_path], cwd=project)
    except OSError as exc:
        print(f"tillm: failed to launch {spec.label}: {exc}")
        return 1


__all__ = [
    "SHELL_AUTOPILOT_BACKEND",
    "SHELL_BACKEND_PROFILE_ID",
    "agent_backend_aliases",
    "agent_backend_profiles",
    "autopilot_backend_for_client",
    "detect_koru_agent_rows",
    "drive_koru_chat",
    "is_client_available",
    "is_shell_llm_client",
    "launch_koru_agent",
    "shell_client_ids",
    "shell_process_patterns",
    "tool_registry_entries",
]
