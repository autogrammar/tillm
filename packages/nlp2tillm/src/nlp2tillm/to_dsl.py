"""NL → dsl2tillm command line (no side effects)."""

from __future__ import annotations

from tillm.nlp import intent_from_text


def to_dsl(prompt: str, *, file: str | None = None) -> str:
    intent = intent_from_text(prompt)
    client = intent.client_id
    text = intent.prompt.replace('"', '\\"')
    if intent.execute:
        return f'DRIVE CLIENT {client} PROMPT "{text}" EXECUTE true'
    return f'DRIVE CLIENT {client} PROMPT "{text}"'


def apply_nl(prompt: str, *, file: str | None = None) -> dict:
    from dsl2tillm import dispatch

    line = to_dsl(prompt, file=file)
    return dispatch(line, default_file=file).to_dict()
