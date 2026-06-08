"""NLP-to-TILLM intent mapping.

The preferred external bridge is ``nlp2dsl``. It is intentionally opt-in at
runtime so a normal Koru/TILLM install does not require Docker services or HTTP
credentials just to list shell clients.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from tillm.registry import get_client_spec, iter_client_specs, normalize_client_id


@dataclass(frozen=True)
class ShellIntent:
    client_id: str
    prompt: str
    execute: bool = False
    source: str = "rules"
    raw_dsl: dict[str, Any] | None = None

    def to_dsl(self) -> dict[str, Any]:
        return {
            "name": "tillm_shell_drive",
            "steps": [
                {
                    "action": "tillm.drive",
                    "config": {
                        "client": self.client_id,
                        "prompt": self.prompt,
                        "execute": self.execute,
                    },
                }
            ],
        }


def _client_from_text(text: str, default_client: str | None) -> str:
    lower = text.lower()
    for spec in iter_client_specs():
        names = (spec.id, *spec.aliases, *spec.commands)
        if any(name and name.lower() in lower for name in names):
            return spec.id
    return normalize_client_id(default_client or os.getenv("TILLM_DEFAULT_CLIENT", "aider"))


def _strip_drive_prefix(text: str) -> str:
    stripped = text.strip()
    separators = (":", "->", "=>")
    for sep in separators:
        if sep in stripped:
            head, tail = stripped.split(sep, 1)
            client_tokens = ("aider", "claude", "codex", "gemini", "devin")
            if any(token in head.lower() for token in client_tokens):
                return tail.strip()
    return stripped


def _intent_from_nlp2dsl(text: str, default_client: str | None) -> ShellIntent | None:
    enabled = os.getenv("TILLM_NLP2DSL", "").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None
    try:
        from nlpshim.client import get_nlp2dsl_client
        ClientClass = get_nlp2dsl_client()
        with ClientClass.from_env() as client:
            payload = client.workflow_from_text(text, execute=False, mode="auto")
    except Exception:
        return None

    dsl = payload.get("dsl") if isinstance(payload, dict) else None
    steps = dsl.get("steps") if isinstance(dsl, dict) else None
    if not isinstance(steps, list):
        return None
    for step in steps:
        if not isinstance(step, dict):
            continue
        action = str(step.get("action") or "")
        if action not in {"tillm.drive", "shell_llm_drive", "drive_shell_llm"}:
            continue
        config = step.get("config") if isinstance(step.get("config"), dict) else {}
        client_id = normalize_client_id(str(config.get("client") or default_client or "aider"))
        prompt = str(config.get("prompt") or config.get("text") or text).strip()
        return ShellIntent(client_id=client_id, prompt=prompt, source="nlp2dsl", raw_dsl=dsl)
    return None


def intent_from_text(text: str, *, default_client: str | None = None) -> ShellIntent:
    if external := _intent_from_nlp2dsl(text, default_client):
        return external
    client_id = _client_from_text(text, default_client)
    if get_client_spec(client_id) is None:
        client_id = "aider"
    return ShellIntent(
        client_id=client_id,
        prompt=_strip_drive_prefix(text),
        source="rules",
    )


__all__ = ["ShellIntent", "intent_from_text"]
