"""Registry of shell LLM clients.

The registry is intentionally declarative. Vendor CLIs change, so SLLM keeps
only conservative invocation defaults here and lets callers override arguments
with ``--extra-arg`` or project config later.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

PromptMode = Literal["stdin", "message-file", "arg"]
WhichFn = Callable[[str], str | None]


@dataclass(frozen=True)
class ShellClientSpec:
    id: str
    label: str
    commands: tuple[str, ...]
    prompt_mode: PromptMode = "stdin"
    argv_prefix: tuple[str, ...] = ()
    prompt_file_flag: str = "--prompt-file"
    aliases: tuple[str, ...] = ()
    notes: str = ""

    def command_path(self, which: WhichFn | None = None) -> str | None:
        resolver = which or shutil.which
        for command in self.commands:
            path = resolver(command)
            if path:
                return path
        return None

    def to_dict(self, *, which: WhichFn | None = None) -> dict[str, object]:
        command_path = self.command_path(which)
        return {
            "id": self.id,
            "label": self.label,
            "commands": list(self.commands),
            "command_path": command_path,
            "available": command_path is not None,
            "prompt_mode": self.prompt_mode,
            "argv_prefix": list(self.argv_prefix),
            "prompt_file_flag": self.prompt_file_flag,
            "aliases": list(self.aliases),
            "notes": self.notes,
        }


_SPECS: tuple[ShellClientSpec, ...] = (
    ShellClientSpec(
        id="claude-code",
        label="Claude Code",
        commands=("claude", "claude-code"),
        prompt_mode="stdin",
        aliases=("claude", "anthropic"),
        notes="Conservative default uses stdin for explicit SLLM drive; Koru launch keeps TTY.",
    ),
    ShellClientSpec(
        id="aider",
        label="aider",
        commands=("aider",),
        prompt_mode="message-file",
        prompt_file_flag="--message-file",
        argv_prefix=("--no-show-model-warnings", "--yes-always"),
        notes="Aider message-file workflow; argv_prefix skips headless confirmation prompts.",
    ),
    ShellClientSpec(
        id="codex",
        label="Codex CLI",
        commands=("codex",),
        prompt_mode="stdin",
        aliases=("codex-cli", "openai-codex"),
    ),
    ShellClientSpec(
        id="gemini-cli",
        label="Gemini CLI",
        commands=("gemini",),
        prompt_mode="stdin",
        aliases=("gemini",),
    ),
    ShellClientSpec(
        id="cline",
        label="Cline",
        commands=("cline",),
        prompt_mode="stdin",
    ),
    ShellClientSpec(
        id="qwen-code",
        label="Qwen Code",
        commands=("qwen-code", "qwen"),
        prompt_mode="stdin",
        aliases=("qwen",),
    ),
    ShellClientSpec(
        id="opencode",
        label="OpenCode",
        commands=("opencode",),
        prompt_mode="stdin",
        aliases=("open-code",),
    ),
    ShellClientSpec(
        id="devin",
        label="Devin CLI",
        commands=("devin",),
        prompt_mode="stdin",
        aliases=("devin-cli",),
        notes=(
            "Registered as an optional shell client; exact vendor flags "
            "can be supplied by config."
        ),
    ),
)

_ALIASES: dict[str, str] = {}
for _spec in _SPECS:
    _ALIASES[_spec.id] = _spec.id
    for _alias in _spec.aliases:
        _ALIASES[_alias] = _spec.id


def normalize_client_id(raw: str) -> str:
    key = raw.strip().lower().replace("_", "-")
    return _ALIASES.get(key, key)


def iter_client_specs() -> tuple[ShellClientSpec, ...]:
    return _SPECS


def get_client_spec(client_id: str) -> ShellClientSpec | None:
    normalized = normalize_client_id(client_id)
    for spec in _SPECS:
        if spec.id == normalized:
            return spec
    return None


def detect_clients(
    *,
    project_hint_ids: Iterable[str] = (),
    which: WhichFn | None = None,
) -> list[dict[str, object]]:
    hinted = {normalize_client_id(value) for value in project_hint_ids}
    rows: list[dict[str, object]] = []
    for spec in _SPECS:
        row = spec.to_dict(which=which)
        if spec.id in hinted:
            row["project_hint"] = True
            row["available"] = True
        else:
            row["project_hint"] = False
        rows.append(row)
    return rows


__all__ = [
    "PromptMode",
    "ShellClientSpec",
    "detect_clients",
    "get_client_spec",
    "iter_client_specs",
    "normalize_client_id",
]
