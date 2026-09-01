"""JSON/TOML helpers for provider surface configs."""

from __future__ import annotations

import json
import re
import stat
from pathlib import Path

from tillm.providers import ProviderSpec


def provider_slug(spec: ProviderSpec) -> str:
    return re.sub(r"[^a-z0-9]+", "", spec.id.lower())


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def write_private_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def same_url(a: str | None, b: str | None) -> bool:
    return bool(a) and bool(b) and a.rstrip("/") == b.rstrip("/")
