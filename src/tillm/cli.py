"""CLI for TILLM shell-client control.

Command dispatch and per-subcommand handlers live here. Output rendering
(:mod:`tillm.cli_output`) and argument-parser construction
(:mod:`tillm.cli_parser`) were split into cohesive submodules so this file
focuses on wiring parsed arguments to the controller layer.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import sys
from pathlib import Path

from tillm.cli_output import _print
from tillm.cli_parser import _EXTRA_ARG_OPTION, _build_parser, _normalize_extra_arg_tokens
from tillm.controller import (
    MultiShellDriveRequest,
    ShellDriveRequest,
    drive_shell_llm,
    drive_shell_llm_many,
    result_from_error,
)
from tillm.drive_log import log_drive_event
from tillm.nlp import intent_from_text
from tillm.project_env import bootstrap_project_env
from tillm.registry import detect_clients, normalize_execute_profile, resolve_client_ids
from tillm.validation import ecosystem_status, validate_intent


def _resolve_execute_profile(raw: str | None) -> str:
    return normalize_execute_profile(raw or os.getenv("TILLM_EXECUTE_PROFILE"))


def _missing_prompt_error() -> ValueError:
    return ValueError(
        "missing prompt; provide --prompt, --prompt-file, or pipe text on stdin. "
        "Examples:\n"
        "  tillm drive --client aider --prompt 'Refactor X' --execute\n"
        "  tillm drive --client aider --prompt-file task.md --execute\n"
        "  echo 'Refactor X' | tillm drive --client aider --execute"
    )


def _stdin_has_data() -> bool:
    try:
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except Exception:
        return False


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file is not None:
        return args.prompt_file.read_text(encoding="utf-8")
    if args.prompt is not None:
        return args.prompt
    if sys.stdin.isatty() or not _stdin_has_data():
        raise _missing_prompt_error()
    data = sys.stdin.read()
    if data.strip():
        return data
    raise _missing_prompt_error()


def _resolve_drive_targets(args: argparse.Namespace) -> tuple[str, ...]:
    return resolve_client_ids(
        client=args.client,
        clients=args.clients,
        all_clients=bool(args.all),
        available_only=bool(args.available_only),
    )


def _base_drive_request(args: argparse.Namespace, prompt: str) -> MultiShellDriveRequest:
    return MultiShellDriveRequest(
        client_ids=_resolve_drive_targets(args),
        prompt=prompt,
        project=args.project,
        execute=bool(args.execute),
        dry_run=bool(args.dry_run or not args.execute),
        extra_args=tuple(args.extra_arg or ()),
        execute_profile=_resolve_execute_profile(args.profile),
        timeout_seconds=args.timeout,
        parallel=max(1, int(args.parallel)),
        fail_fast=bool(args.fail_fast),
        quorum=args.quorum,
        model=args.model,
        provider=args.provider,
    )


def _drive(args: argparse.Namespace) -> int:
    try:
        prompt = _read_prompt(args)
    except ValueError as exc:
        label = args.client or args.clients or "all"
        log_drive_event(
            args.project,
            phase="prompt_error",
            client_id=str(label),
            execute=bool(args.execute),
            dry_run=bool(args.dry_run or not args.execute),
            ok=False,
            error=type(exc).__name__,
            message=str(exc),
        )
        payload = result_from_error(str(label), exc)
        _print(payload, args.format)
        return 2

    client_label = args.client or args.clients or "all"
    log_drive_event(
        args.project,
        phase="start",
        client_id=str(client_label),
        execute=bool(args.execute),
        dry_run=bool(args.dry_run or not args.execute),
        prompt=prompt,
    )
    try:
        if args.client:
            result = drive_shell_llm(
                ShellDriveRequest(
                    client_id=args.client,
                    prompt=prompt,
                    project=args.project,
                    execute=bool(args.execute),
                    dry_run=bool(args.dry_run or not args.execute),
                    extra_args=tuple(args.extra_arg or ()),
                    execute_profile=_resolve_execute_profile(args.profile),
                    timeout_seconds=args.timeout,
                    model=args.model,
                    provider=args.provider,
                )
            )
            payload: dict[str, object] = result.to_dict()
        else:
            matrix = drive_shell_llm_many(_base_drive_request(args, prompt))
            payload = matrix.to_dict()
    except Exception as exc:
        log_drive_event(
            args.project,
            phase="error",
            client_id=str(client_label),
            execute=bool(args.execute),
            dry_run=bool(args.dry_run or not args.execute),
            prompt=prompt,
            ok=False,
            error=type(exc).__name__,
            message=str(exc),
        )
        payload = result_from_error(str(client_label), exc)
        _print(payload, args.format)
        return 2

    if args.client and isinstance(payload, dict):
        log_drive_event(
            args.project,
            phase="finish",
            client_id=str(payload.get("client_id", client_label)),
            execute=bool(args.execute),
            dry_run=bool(payload.get("dry_run", True)),
            prompt=prompt,
            prompt_path=str(payload.get("prompt_path", "")),
            command=list(payload.get("command", [])) if payload.get("command") else None,
            ok=bool(payload.get("ok")),
            exit_code=payload.get("exit_code"),  # type: ignore[arg-type]
            message=str(payload.get("message", "")),
        )
    _print(payload, args.format)
    return 0 if payload.get("ok") else 1


def _providers_list(args: argparse.Namespace) -> int:
    from tillm.providers import iter_provider_specs, resolve_provider_token

    rows = []
    for spec in iter_provider_specs():
        token = resolve_provider_token(spec.id)
        rows.append(
            {
                "id": spec.id,
                "label": spec.label,
                "kind": spec.kind,
                "token": "set" if token else "missing",
                "token_env": spec.token_env,
                "clients": list(spec.compatible_clients()),
                "notes": spec.notes,
            }
        )
    if args.format == "json":
        print(json.dumps(rows, indent=2))
        return 0
    for row in rows:
        token_mark = "✓" if row["token"] == "set" else "✗"
        print(
            f"{row['id']:<12} {row['kind']:<12} token={token_mark} "
            f"({row['token_env']})  clients: {', '.join(row['clients']) or '-'}"
        )
        if row["notes"]:
            print(f"{'':<12} {row['notes']}")
    return 0


_SYNC_SURFACE_SHORT = {
    "claude-settings": "claude",
    "codex-config": "codex",
    "opencode-config": "opencode",
    "jetbrains-openai-like": "jetbrains",
    "qoder": "qoder",
}

_SYNC_ACTION_MARKS = {
    "ok": "✓",
    "export": "→",
    "import-token": "←",
    "manual": "⚠",
    "skip": "·",
}


def _sync_matrix(args: argparse.Namespace) -> int:
    from tillm.surfaces import sync_all

    matrix = sync_all(level=args.level, apply=args.apply)
    if getattr(args, "format", "text") == "json":
        print(json.dumps(matrix, indent=2))
        return 0
    mode = "applied" if args.apply else "plan (dry-run; use --apply)"
    print(f"provider sync matrix — {mode}")
    failures = 0
    for report in matrix["providers"]:
        store_mark = "✓" if report["store_token"] else "✗"
        cells = []
        for step in report["steps"]:
            mark = _SYNC_ACTION_MARKS.get(step["action"], "?")
            if args.apply and step["action"] in {"export", "import-token"}:
                mark = "✓" if step.get("done") else "✗"
                failures += 0 if step.get("done") else 1
            cells.append(f"{mark}{_SYNC_SURFACE_SHORT.get(step['surface_id'], step['surface_id'])}")
        line = f"  {store_mark} {report['provider']:<12} {' '.join(cells)}"
        if not report["store_token"] and report.get("token_url"):
            line += f"   token: {report['token_url']}"
        print(line)
    print("  legend: ✓ in sync  → export pending  ← import pending  ⚠ manual (IDE keychain)  · no token")
    return 1 if failures else 0


def _provider_action(args: argparse.Namespace) -> int:
    from tillm.providers import (
        UnknownProviderError,
        get_provider_spec,
        probe_provider,
        save_provider_token,
    )

    if args.provider_action == "sync" and not args.provider_id:
        return _sync_matrix(args)

    try:
        spec = get_provider_spec(args.provider_id)
    except UnknownProviderError as exc:
        print(f"tillm: {exc}", file=sys.stderr)
        return 2

    if args.provider_action == "set":
        token = (args.token or "").strip()
        if not token:
            import getpass

            from tillm.i18n import _

            if spec.token_url:
                print(_("token.get_here", url=spec.token_url))
            token = getpass.getpass(f"{spec.label} token ({spec.token_env}): ").strip()
        if not token:
            from tillm.i18n import _

            print(f"tillm: {_('token.empty')}", file=sys.stderr)
            return 2
        from tillm.i18n import _

        path = save_provider_token(spec.id, token, model=args.model)
        print(_("token.stored_in", id=spec.id, path=path))
        result = probe_provider(spec.id)
        print(("✓" if result.ok else "✗") + " " + _("probe.result", detail=result.detail))
        return 0 if result.ok else 1

    if args.provider_action == "test":
        result = probe_provider(spec.id, model=args.model)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            mark = "✓" if result.ok else "✗"
            print(f"{mark} {spec.id}: {result.detail}")
            if result.endpoint:
                print(f"  endpoint: {result.endpoint}")
            if result.attempts:
                print(f"  attempts: {', '.join(result.attempts)}")
        return 0 if result.ok else 1

    if args.provider_action == "models":
        from tillm.providers import list_provider_models

        listing = list_provider_models(spec.id)
        if getattr(args, "format", "text") == "json":
            print(json.dumps({
                "provider": listing.provider_id,
                "source": listing.source,
                "models": list(listing.models[: max(1, args.limit)]),
            }, indent=2))
        else:
            print(f"{spec.id}: {listing.source} ({len(listing.models)} models)")
            for model in listing.models[: max(1, args.limit)]:
                print(f"  {model}")
        return 0 if listing.models else 1

    if args.provider_action == "doctor":
        from tillm.providers import diagnose_provider

        diagnosis = diagnose_provider(spec.id)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(diagnosis.to_dict(), indent=2))
        else:
            marks = {"ok": "✓", "warn": "⚠", "fail": "✗"}
            print(f"{spec.id}: {'OK' if diagnosis.ok else 'PROBLEMS FOUND'}")
            for item in diagnosis.items:
                print(f"  {marks[item.level]} {item.code}: {item.message}")
                if item.fix:
                    print(f"     fix: {item.fix}")
        return 0 if diagnosis.ok else 1

    if args.provider_action == "sync":
        from tillm.surfaces import apply_sync, plan_sync

        run = apply_sync if args.apply else plan_sync
        report = run(spec.id, level=args.level)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(report, indent=2))
        else:
            store_mark = "✓" if report["store_token"] else "✗"
            mode = "applied" if args.apply else "plan (dry-run; use --apply)"
            print(f"{spec.id}: store token {store_mark} — {mode}")
            states = {state["surface_id"]: state for state in report["states"]}
            marks = {
                "ok": "✓",
                "export": "→",
                "import-token": "←",
                "manual": "⚠",
                "skip": "·",
            }
            for step in report["steps"]:
                state = states.get(step["surface_id"], {})
                mark = marks.get(step["action"], "?")
                if args.apply and step["action"] in {"export", "import-token"}:
                    mark = "✓" if step.get("done") else "✗"
                flags = []
                if state.get("configured"):
                    flags.append("configured")
                if state.get("has_token"):
                    flags.append("token")
                where = state.get("path") or "(no config file)"
                print(
                    f"  {mark} [{state.get('level', '?'):<8}] "
                    f"{step['action']:<12} {state.get('label', step['surface_id'])}"
                )
                print(f"      {where}  {'+'.join(flags) or '-'}")
                if step.get("detail"):
                    print(f"      {step['detail']}")
        problems = any(
            step["action"] == "manual"
            or (args.apply and step["action"] in {"export", "import-token"} and not step.get("done"))
            for step in report["steps"]
        )
        return 1 if problems else 0

    raise AssertionError(args.provider_action)


def _nlp(args: argparse.Namespace) -> int:
    text = " ".join(args.text)
    intent = intent_from_text(text, default_client=args.client)
    validation = validate_intent(intent)
    if not validation.ok:
        payload = {"ok": False, "intent": intent.to_dsl(), "validation": validation.to_dict()}
        _print(payload, args.format)
        return 2
    if not args.execute:
        payload = {"ok": True, "source": intent.source, "dsl": intent.to_dsl()}
        _print(payload, args.format)
        return 0
    result = drive_shell_llm(
        ShellDriveRequest(
            client_id=intent.client_id,
            prompt=intent.prompt,
            project=args.project,
            execute=True,
            dry_run=False,
            extra_args=tuple(args.extra_arg or ()),
            execute_profile=_resolve_execute_profile(args.profile),
        )
    )
    _print({"ok": result.ok, "source": intent.source, "result": result.to_dict()}, args.format)
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parse_argv = sys.argv[1:] if argv is None else argv
    args = _build_parser().parse_args(_normalize_extra_arg_tokens(list(parse_argv)))
    bootstrap_project_env(getattr(args, "project", None))
    if args.action == "clients":
        _print(detect_clients(), args.format)
        return 0
    if args.action == "drive":
        return _drive(args)
    if args.action == "providers":
        return _providers_list(args)
    if args.action == "provider":
        return _provider_action(args)
    if args.action == "nlp":
        return _nlp(args)
    if args.action == "validate":
        _print(ecosystem_status(), args.format)
        return 0
    raise AssertionError(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
