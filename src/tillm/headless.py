"""One-call headless execution for every batch-capable shell client.

TILLM already has the full headless lane — the registry carries each client's non-interactive
invocation (``claude -p``, ``codex exec``, ``gemini -p``, ``qwen -p``, ``opencode run``,
``devin -p``, aider ``--yes-always``) and :func:`tillm.controller.drive_shell_llm` runs it via
the local binary transport with ``execute=True``. This module is the thin convenience over
that lane so a caller (e.g. Koru's autonomous cycle) can run a prompt to completion WITHOUT
driving a GUI: no vdisplay, no window, no autopilot socket.

Use this instead of the ``plugin_socket`` (GUI drive) backend whenever the target client
:func:`supports_headless`. GUI-only clients (cline; IDE plugins like qoder/cursor that are not
in the registry) still need the plugin lane.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tillm.controller import ShellDriveRequest, drive_shell_llm
from tillm.registry import get_client_spec, normalize_client_id


def supports_headless(client_id: str) -> bool:
    """True when the client can run a prompt to completion non-interactively.

    A client is headless-capable when it is in the registry, supports execute, and either
    declares ``execute_args`` (e.g. ``-p``/``exec``) or auto-applies via its ``argv_prefix``
    (aider's ``--yes-always``). This is the test Koru should use to pick the headless lane
    over GUI drive."""
    spec = get_client_spec(normalize_client_id(client_id))
    if spec is None or not spec.supports_execute:
        return False
    return bool(spec.execute_args) or "--yes-always" in spec.argv_prefix \
        or "--dangerously-skip-permissions" in spec.argv_prefix


def headless_client_ids() -> list[str]:
    """Every registered client that can be driven headless — the coverage of this lane."""
    from tillm.registry import iter_client_specs
    return [s.id for s in iter_client_specs() if supports_headless(s.id)]


def run_headless(client_id: str, prompt: str, *, project: str | Path | None = None,
                 profile: str = "automation", timeout: float | None = 900.0,
                 model: str | None = None) -> dict[str, Any]:
    """Run ``prompt`` through ``client_id`` headless and return the result.

    ``profile='automation'`` uses the client's unattended profile (e.g. ``claude -p
    --dangerously-skip-permissions``) so the agent applies changes without a confirmation
    prompt; pass ``profile='default'`` for the safer variant. Returns
    ``{ok, client, exit_code, stdout, stderr, argv}`` — a plain dict, no GUI anywhere."""
    norm = normalize_client_id(client_id)
    spec = get_client_spec(norm)
    if spec is None:
        return {"ok": False, "client": client_id, "error": f"unknown client {client_id!r}"}
    if not supports_headless(norm):
        return {"ok": False, "client": norm,
                "error": f"{norm} has no headless mode — use the GUI/plugin lane"}
    use_profile = profile if profile in spec.supported_execute_profiles() else "default"
    req = ShellDriveRequest(
        client_id=norm, prompt=prompt,
        project=Path(project).expanduser() if project else Path.cwd(),
        execute=True, execute_profile=use_profile, timeout_seconds=timeout, model=model,
    )
    result = drive_shell_llm(req)
    d = result.to_dict()
    return {"ok": bool(d.get("ok")) and d.get("executed") is not False,
            "client": norm, "exit_code": d.get("exit_code"), "executed": d.get("executed"),
            "stdout": d.get("stdout", ""), "stderr": d.get("stderr", ""),
            "message": d.get("message", ""), "profile": use_profile,
            "argv": list(d.get("command", []))}
