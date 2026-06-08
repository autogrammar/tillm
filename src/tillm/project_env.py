"""Bootstrap project environment from `.env` and env2llm."""

from __future__ import annotations

import os
import re
from pathlib import Path

_ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


def _strip_quotes(value: str) -> str:
    text = value.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return text


def load_env_file(path: Path) -> dict[str, str]:
    """Parse a KEY=value .env file."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _ENV_LINE.match(line)
        if not match:
            continue
        key, value = match.group(1), _strip_quotes(match.group(2))
        values[key] = value
    return values


def apply_into_environ(values: dict[str, str], *, overwrite: bool = False) -> list[str]:
    """Apply parsed values to os.environ. Returns keys applied."""
    applied: list[str] = []
    for key, value in values.items():
        if not overwrite and key in os.environ and os.environ[key].strip():
            continue
        os.environ[key] = value
        applied.append(key)
    return applied


def apply_llm_bridges() -> None:
    """Map semcod/OpenRouter vars to vendor CLI expectations."""
    openrouter = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if openrouter:
        os.environ.setdefault("OPENAI_API_KEY", openrouter)
    llm_model = os.environ.get("LLM_MODEL", "").strip()
    if llm_model:
        os.environ.setdefault("AIDER_MODEL", llm_model)


def _env2llm_enabled() -> bool:
    return os.environ.get("TILLM_ENV2LLM", "1").strip().lower() not in {"0", "false", "no", "off"}


def _ensure_env2llm_map(project: Path) -> None:
    if not _env2llm_enabled():
        return
    try:
        from env2llm.bootstrap import ensure_environment_map
    except ImportError:
        return
    try:
        ensure_environment_map(project, merge_existing=True)
    except Exception:
        return


def resolve_env_file(project: Path, env_file: str | Path | None = None) -> Path | None:
    if env_file:
        candidate = Path(env_file).expanduser()
        return candidate if candidate.is_file() else None
    custom = os.environ.get("TILLM_ENV_FILE", "").strip()
    if custom:
        candidate = Path(custom).expanduser()
        if candidate.is_file():
            return candidate
    project_env = project / ".env"
    return project_env if project_env.is_file() else None


def bootstrap_project_env(
    project: Path | str | None = None,
    *,
    env_file: str | Path | None = None,
) -> dict[str, str]:
    """
    Load project ``.env``, apply LLM bridges, optionally refresh env2llm map.

    Existing non-empty process env vars win over ``.env`` (``setdefault`` semantics
    for bridges; file keys skip already-set non-empty values).
    """
    root = Path(project or os.getcwd()).expanduser().resolve()
    os.environ.setdefault("ENV2LLM_PROJECT_DIR", str(root))

    path = resolve_env_file(root, env_file)
    if path is not None:
        apply_into_environ(load_env_file(path))

    apply_llm_bridges()
    _ensure_env2llm_map(root)
    return dict(os.environ)


__all__ = [
    "apply_into_environ",
    "apply_llm_bridges",
    "bootstrap_project_env",
    "load_env_file",
    "resolve_env_file",
]
