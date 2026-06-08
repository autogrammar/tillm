"""Validate dict commands."""

from __future__ import annotations

from typing import Any

import jsonschema

from dsl2tillm.grammar import parse_line
from dsl2tillm.pb_codec import decode_protobuf
from dsl2tillm.schema_registry import schema_for_verb


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    verb = str(payload.get("verb", "")).upper()
    if not verb:
        raise ValueError("missing verb")
    schema = schema_for_verb(verb)
    jsonschema.validate(payload, schema)
    return payload


def parse_text(line: str, *, default_file: str | None = None) -> dict[str, Any]:
    payload = parse_line(line, default_file=default_file)
    if not payload:
        return {}
    return validate_payload(payload)


def envelope_from_bytes(data: bytes) -> dict[str, Any]:
    return validate_payload(decode_protobuf(data))
