"""Text-interface LLM control plane for semcod/coru.

``tillm`` is the shell/terminal side of LLM automation: vendor CLI detection,
controlled invocations, NLP → drive DSL, and Koru compatibility hooks.
For graphical control, use ``gillm`` (GUI domain + *2gillm adapters).
"""

from tillm.controller import (
    MultiShellDriveRequest,
    MultiShellDriveResult,
    ShellDrivePlan,
    ShellDriveRequest,
    ShellDriveResult,
    build_drive_plan,
    drive_shell_llm,
    drive_shell_llm_many,
    save_prompt,
)
from tillm.headless import headless_client_ids, run_headless, supports_headless
from tillm.registry import (
    ShellClientSpec,
    available_client_ids,
    detect_clients,
    get_client_spec,
    iter_client_specs,
    normalize_client_id,
    resolve_client_ids,
)

__all__ = [
    "MultiShellDriveRequest",
    "MultiShellDriveResult",
    "ShellClientSpec",
    "ShellDrivePlan",
    "ShellDriveRequest",
    "ShellDriveResult",
    "available_client_ids",
    "build_drive_plan",
    "detect_clients",
    "drive_shell_llm",
    "drive_shell_llm_many",
    "get_client_spec",
    "iter_client_specs",
    "normalize_client_id",
    "resolve_client_ids",
    "save_prompt",
    "run_headless",
    "supports_headless",
    "headless_client_ids",
]
