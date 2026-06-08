"""Registry of shell LLM clients.

The registry is intentionally declarative. Vendor CLIs change, so SLLM keeps
only conservative invocation defaults here and lets callers override arguments
with ``--extra-arg`` or project config later.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

PromptMode = Literal["stdin", "message-file", "arg"]
ExecuteProfileId = Literal["default", "automation"]
ClientTransport = Literal["binary", "docker", "http"]
WhichFn = Callable[[str], str | None]

DEFAULT_EXECUTE_PROFILE = "default"
KNOWN_EXECUTE_PROFILES = ("default", "automation")


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
    supports_execute: bool = True
    supports_dry_run: bool = True
    env_vars: tuple[str, ...] = ()
    env_vars_any: tuple[str, ...] = ()
    execute_args: tuple[str, ...] = ()
    execute_profiles: tuple[tuple[str, tuple[str, ...]], ...] = ()
    transport: ClientTransport = "binary"
    docker_service: str = ""
    http_base_url: str = ""

    def command_path(self, which: WhichFn | None = None) -> str | None:
        resolver = which or shutil.which
        for command in self.commands:
            path = resolver(command)
            if path:
                return path
        return None

    def profile_execute_args(self, profile: str | None = None) -> tuple[str, ...]:
        key = (profile or DEFAULT_EXECUTE_PROFILE).strip().lower()
        if key in {"", DEFAULT_EXECUTE_PROFILE}:
            return self.execute_args
        for profile_id, args in self.execute_profiles:
            if profile_id == key:
                return args
        supported = (DEFAULT_EXECUTE_PROFILE, *(pid for pid, _ in self.execute_profiles))
        raise ValueError(f"{self.id}: unsupported execute profile {profile!r}; supported: {supported}")

    def supported_execute_profiles(self) -> tuple[str, ...]:
        return (DEFAULT_EXECUTE_PROFILE, *(profile_id for profile_id, _ in self.execute_profiles))

    def missing_env_vars(self, environ: dict[str, str] | None = None) -> tuple[str, ...]:
        env = environ if environ is not None else os.environ
        missing = [name for name in self.env_vars if not env.get(name, "").strip()]
        if self.env_vars_any and not any(env.get(name, "").strip() for name in self.env_vars_any):
            missing.append(" or ".join(self.env_vars_any))
        return tuple(missing)

    def to_dict(self, *, which: WhichFn | None = None, environ: dict[str, str] | None = None) -> dict[str, object]:
        command_path = self.command_path(which)
        missing_env = self.missing_env_vars(environ)
        return {
            "id": self.id,
            "label": self.label,
            "commands": list(self.commands),
            "command_path": command_path,
            "available": command_path is not None,
            "prompt_mode": self.prompt_mode,
            "argv_prefix": list(self.argv_prefix),
            "execute_args": list(self.execute_args),
            "execute_profiles": {
                profile_id: list(args) for profile_id, args in self.execute_profiles
            },
            "supported_execute_profiles": list(self.supported_execute_profiles()),
            "prompt_file_flag": self.prompt_file_flag,
            "aliases": list(self.aliases),
            "notes": self.notes,
            "supports_execute": self.supports_execute,
            "supports_dry_run": self.supports_dry_run,
            "env_vars": list(self.env_vars),
            "env_vars_any": list(self.env_vars_any),
            "missing_env_vars": list(missing_env),
            "ready": command_path is not None and not missing_env,
            "transport": self.transport,
            "docker_service": self.docker_service or f"tillm-{self.id}",
            "http_base_url": self.http_base_url,
        }


_SPECS: tuple[ShellClientSpec, ...] = (
    ShellClientSpec(
        id="claude-code",
        label="Claude Code",
        commands=("claude", "claude-code"),
        prompt_mode="stdin",
        aliases=("claude", "anthropic"),
        env_vars=("ANTHROPIC_API_KEY",),
        execute_args=("-p",),
        execute_profiles=(
            ("automation", ("-p", "--dangerously-skip-permissions")),
        ),
        notes="Headless via claude -p/--print with prompt on stdin.",
    ),
    ShellClientSpec(
        id="aider",
        label="aider",
        commands=("aider",),
        prompt_mode="message-file",
        prompt_file_flag="--message-file",
        argv_prefix=("--no-show-model-warnings", "--yes-always"),
        env_vars_any=("OPENAI_API_KEY", "ANTHROPIC_API_KEY"),
        notes="Aider message-file workflow; argv_prefix skips headless confirmation prompts.",
    ),
    ShellClientSpec(
        id="codex",
        label="Codex CLI",
        commands=("codex",),
        prompt_mode="stdin",
        aliases=("codex-cli", "openai-codex"),
        env_vars=("OPENAI_API_KEY",),
        execute_args=("exec",),
        execute_profiles=(
            (
                "automation",
                ("exec", "--dangerously-bypass-approvals-and-sandbox"),
            ),
        ),
        notes="Non-interactive via codex exec; prompt is read from stdin.",
    ),
    ShellClientSpec(
        id="gemini-cli",
        label="Gemini CLI",
        commands=("gemini",),
        prompt_mode="stdin",
        aliases=("gemini",),
        env_vars_any=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        execute_args=("-p", "--approval-mode", "auto_edit"),
        execute_profiles=(
            ("automation", ("-p", "--yolo")),
        ),
        notes="Headless via gemini -p/--prompt with prompt on stdin.",
    ),
    ShellClientSpec(
        id="cline",
        label="Cline",
        commands=("cline",),
        prompt_mode="stdin",
        supports_execute=False,
        env_vars_any=("OPENAI_API_KEY", "ANTHROPIC_API_KEY"),
        notes="Interactive CLI; tillm drive plans prompts but does not auto-execute.",
    ),
    ShellClientSpec(
        id="qwen-code",
        label="Qwen Code",
        commands=("qwen-code", "qwen"),
        prompt_mode="stdin",
        aliases=("qwen",),
        env_vars_any=("DASHSCOPE_API_KEY", "OPENAI_API_KEY"),
        execute_args=("-p", "--approval-mode", "yolo"),
        notes="Headless via qwen -p/--prompt with prompt on stdin.",
    ),
    ShellClientSpec(
        id="opencode",
        label="OpenCode",
        commands=("opencode",),
        prompt_mode="stdin",
        aliases=("open-code",),
        execute_args=("run", "--dangerously-skip-permissions"),
        notes="Non-interactive via opencode run; prompt is read from stdin when omitted.",
    ),
    ShellClientSpec(
        id="devin",
        label="Devin CLI",
        commands=("devin",),
        prompt_mode="stdin",
        aliases=("devin-cli",),
        env_vars=("DEVIN_API_KEY",),
        execute_args=("-p",),
        execute_profiles=(
            ("automation", ("-p", "--permission-mode", "dangerous")),
        ),
        notes="Headless via devin -p/--print with prompt on stdin.",
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


def available_client_ids(*, which: WhichFn | None = None) -> tuple[str, ...]:
    resolver = which or shutil.which
    return tuple(spec.id for spec in _SPECS if spec.command_path(resolver) is not None)


def registered_client_ids() -> tuple[str, ...]:
    return tuple(spec.id for spec in _SPECS)


def resolve_client_ids(
    *,
    client: str | None = None,
    clients: str | None = None,
    all_clients: bool = False,
    available_only: bool = True,
    which: WhichFn | None = None,
) -> tuple[str, ...]:
    if sum(bool(value) for value in (client, clients, all_clients)) != 1:
        raise ValueError("specify exactly one of client, clients, or all_clients")

    if all_clients:
        source = available_client_ids(which=which) if available_only else registered_client_ids()
        return source

    raw_ids = [client] if client else [part.strip() for part in (clients or "").split(",") if part.strip()]
    resolved: list[str] = []
    seen: set[str] = set()
    for raw in raw_ids:
        normalized = normalize_client_id(raw)
        if get_client_spec(normalized) is None:
            raise ValueError(f"unknown client: {raw}")
        if normalized in seen:
            continue
        seen.add(normalized)
        resolved.append(normalized)

    if available_only:
        available = set(available_client_ids(which=which))
        resolved = [client_id for client_id in resolved if client_id in available]
    return tuple(resolved)


def detect_clients(
    *,
    project_hint_ids: Iterable[str] = (),
    which: WhichFn | None = None,
    environ: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    hinted = {normalize_client_id(value) for value in project_hint_ids}
    rows: list[dict[str, object]] = []
    for spec in _SPECS:
        row = spec.to_dict(which=which, environ=environ)
        if spec.id in hinted:
            row["project_hint"] = True
            row["available"] = True
            row["ready"] = not row["missing_env_vars"]
        else:
            row["project_hint"] = False
        rows.append(row)
    return rows


def normalize_execute_profile(raw: str | None) -> str:
    key = (raw or DEFAULT_EXECUTE_PROFILE).strip().lower()
    if key in {"", DEFAULT_EXECUTE_PROFILE}:
        return DEFAULT_EXECUTE_PROFILE
    if key == "automation":
        return "automation"
    return key


__all__ = [
    "DEFAULT_EXECUTE_PROFILE",
    "KNOWN_EXECUTE_PROFILES",
    "ClientTransport",
    "PromptMode",
    "ShellClientSpec",
    "available_client_ids",
    "detect_clients",
    "get_client_spec",
    "iter_client_specs",
    "normalize_client_id",
    "normalize_execute_profile",
    "registered_client_ids",
    "resolve_client_ids",
]
