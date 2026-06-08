"""Append-only event store for dsl2tillm commands (jsonl)."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoredEvent:
    id: str
    ts_unix: int
    command: dict[str, Any]
    result: dict[str, Any]
    correlation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def for_workdir(cls, workdir: Path) -> EventStore:
        root = workdir.expanduser().resolve()
        events_dir = root / ".koru" / "tillm" / "events"
        events_dir.mkdir(parents=True, exist_ok=True)
        return cls(events_dir / "app.tillm.events.jsonl")

    def append_command(self, command: dict[str, Any], result: dict[str, Any], *, correlation_id: str = "") -> str:
        event_id = uuid.uuid4().hex
        event = StoredEvent(
            id=event_id,
            ts_unix=int(time.time()),
            command=command,
            result=result,
            correlation_id=correlation_id,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        return event_id

    def read_all(self) -> list[StoredEvent]:
        if not self.path.is_file():
            return []
        events: list[StoredEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            events.append(
                StoredEvent(
                    id=str(data["id"]),
                    ts_unix=int(data["ts_unix"]),
                    command=dict(data["command"]),
                    result=dict(data["result"]),
                    correlation_id=str(data.get("correlation_id", "")),
                )
            )
        return events
