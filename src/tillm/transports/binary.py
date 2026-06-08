"""Local subprocess transport (default)."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tillm.controller import ShellDrivePlan, ShellDriveRequest, ShellDriveResult


def run_binary_drive(request: ShellDriveRequest, plan: ShellDrivePlan) -> ShellDriveResult:
    from tillm.controller import ShellDriveResult, _timeout_value
    if request.dry_run or not request.execute:
        return ShellDriveResult(
            ok=True,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=False,
            dry_run=True,
            execute_profile=plan.execute_profile,
            message="dry-run: command planned but not executed",
        )

    try:
        proc = subprocess.run(
            list(plan.argv),
            cwd=plan.cwd,
            input=plan.stdin_text,
            capture_output=True,
            text=True,
            check=False,
            timeout=_timeout_value(request.timeout_seconds),
            env=dict(os.environ),
        )
    except subprocess.TimeoutExpired as exc:
        return ShellDriveResult(
            ok=False,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=True,
            dry_run=False,
            execute_profile=plan.execute_profile,
            exit_code=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            message=f"timeout after {request.timeout_seconds}s",
        )
    except OSError as exc:
        return ShellDriveResult(
            ok=False,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=True,
            dry_run=False,
            execute_profile=plan.execute_profile,
            exit_code=None,
            message=str(exc),
        )

    return ShellDriveResult(
        ok=proc.returncode == 0,
        client_id=plan.spec.id,
        command=plan.argv,
        prompt_path=plan.prompt_path,
        executed=True,
        dry_run=False,
        execute_profile=plan.execute_profile,
        exit_code=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        message="completed" if proc.returncode == 0 else "client command failed",
    )
