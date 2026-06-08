"""JSON envelope codec (protobuf optional later)."""

from __future__ import annotations

import json
from typing import Any

from dsl2tillm.result import DslResult


def encode_protobuf(payload: dict[str, Any], *, default_file: str = "", correlation_id: str = "") -> bytes:
    envelope = {
        "payload": payload,
        "default_file": default_file,
        "correlation_id": correlation_id,
    }
    return json.dumps(envelope, sort_keys=True, ensure_ascii=False).encode("utf-8")


def decode_protobuf(data: bytes) -> dict[str, Any]:
    envelope = json.loads(data.decode("utf-8"))
    if not isinstance(envelope, dict) or "payload" not in envelope:
        raise ValueError("invalid protobuf envelope")
    return dict(envelope["payload"])


def encode_result_protobuf(result: DslResult) -> bytes:
    return json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=False).encode("utf-8")
