"""Execute shell LLM drives and multi-client orchestration."""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from tillm.controller_errors import TillmError
from tillm.controller_plan import build_drive_plan
from tillm.controller_types import (
    MultiShellDriveRequest,
    MultiShellDriveResult,
    ShellDriveRequest,
    ShellDriveResult,
    resolve_backend,
)
from tillm.transports.binary import run_binary_drive
from tillm.transports.docker import run_docker_drive


def timeout_value(timeout_seconds: float | None) -> float | None:
    if timeout_seconds is None:
        return None
    value = float(timeout_seconds)
    return None if value <= 0 else value


# Transports import this private alias from tillm.controller.
_timeout_value = timeout_value


def _drive_result_from_exception(client_id: str, exc: Exception) -> ShellDriveResult:
    return ShellDriveResult(
        ok=False,
        client_id=client_id,
        command=(),
        prompt_path=Path.cwd(),
        executed=False,
        dry_run=True,
        message=str(exc),
    )


def _drive_one_client(request: MultiShellDriveRequest, client_id: str) -> ShellDriveResult:
    single = ShellDriveRequest(
        client_id=client_id,
        prompt=request.prompt,
        project=request.project,
        execute=request.execute,
        dry_run=request.dry_run,
        extra_args=request.extra_args,
        execute_profile=request.execute_profile,
        backend=resolve_backend(request.backend),
        timeout_seconds=request.timeout_seconds,
        prompt_dir=request.prompt_dir,
        model=request.model,
        provider=getattr(request, "provider", None),
    )
    try:
        from tillm.controller import drive_shell_llm

        return drive_shell_llm(single)
    except TillmError as exc:
        return _drive_result_from_exception(client_id, exc)


def drive_shell_llm_many(request: MultiShellDriveRequest) -> MultiShellDriveResult:
    if not request.client_ids:
        return MultiShellDriveResult(
            ok=False,
            client_ids=(),
            results=(),
            succeeded=0,
            failed=0,
            executed=request.execute and not request.dry_run,
            dry_run=request.dry_run or not request.execute,
            message="no clients selected",
        )

    workers = max(1, min(int(request.parallel), len(request.client_ids)))
    results: list[ShellDriveResult] = []
    pending: dict[Future[ShellDriveResult], str] = {}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for client_id in request.client_ids:
            pending[pool.submit(_drive_one_client, request, client_id)] = client_id

        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                client_id = pending.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    result = _drive_result_from_exception(client_id, exc)
                results.append(result)

                successes = sum(1 for item in results if item.ok)
                if request.fail_fast and not result.ok:
                    for pending_future in pending:
                        pending_future.cancel()
                    pending.clear()
                    break
                if request.quorum is not None and successes >= request.quorum:
                    for pending_future in pending:
                        pending_future.cancel()
                    pending.clear()
                    break

    results.sort(key=lambda item: request.client_ids.index(item.client_id))
    succeeded = sum(1 for item in results if item.ok)
    failed = len(results) - succeeded
    executed = request.execute and not request.dry_run
    dry_run = request.dry_run or not request.execute
    quorum_met = request.quorum is None or succeeded >= request.quorum
    ok = failed == 0 if request.quorum is None else quorum_met

    if not results:
        message = "no results"
    elif request.quorum is not None and quorum_met:
        message = f"quorum met ({succeeded}/{request.quorum})"
    elif failed:
        message = f"{failed} of {len(results)} clients failed"
    else:
        message = f"all {len(results)} clients completed"

    return MultiShellDriveResult(
        ok=ok,
        client_ids=request.client_ids,
        results=tuple(results),
        succeeded=succeeded,
        failed=failed,
        executed=executed,
        dry_run=dry_run,
        message=message,
    )


def _drive_shell_llm_once(request: ShellDriveRequest) -> ShellDriveResult:
    plan = build_drive_plan(request)
    backend = resolve_backend(request.backend, spec=plan.spec)
    if backend == "docker":
        return run_docker_drive(request, plan)
    if backend == "http":
        return ShellDriveResult(
            ok=False,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=False,
            dry_run=request.dry_run or not request.execute,
            execute_profile=plan.execute_profile,
            message="http backend not implemented yet; use binary or docker",
        )
    return run_binary_drive(request, plan)


def result_from_error(client_id: str, exc: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "client_id": client_id,
        "backend": "tillm_shell",
        "error": type(exc).__name__,
        "message": str(exc),
    }
