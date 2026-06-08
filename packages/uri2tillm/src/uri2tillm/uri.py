"""tillm:// URI builders and parsers."""

from __future__ import annotations

from urllib.parse import parse_qs, quote, unquote, urlparse

TILLM_SCHEME = "tillm"
_CMD_SOURCE = "cmd"
_CLIENT_SOURCE = "client"


def _encode(value: str) -> str:
    return quote(value, safe="")


def _decode(value: str) -> str:
    return unquote(value or "")


def uri_for_cmd(verb: str, **params: str) -> str:
    query = "&".join(f"{k}={_encode(v)}" for k, v in params.items() if v)
    uri = f"{TILLM_SCHEME}://{_CMD_SOURCE}/{_encode(verb.upper())}"
    if query:
        uri += f"?{query}"
    return uri


def uri_for_client(client: str, *, prompt: str = "", project: str = "") -> str:
    uri = f"{TILLM_SCHEME}://{_CLIENT_SOURCE}/{_encode(client)}"
    query_parts = []
    if prompt:
        query_parts.append(f"prompt={_encode(prompt)}")
    if project:
        query_parts.append(f"project={_encode(project)}")
    if query_parts:
        uri += "?" + "&".join(query_parts)
    return uri


def is_tillm_uri(uri: str) -> bool:
    return urlparse(uri).scheme.lower() == TILLM_SCHEME


def parse_tillm_uri(uri: str) -> dict[str, object]:
    parsed = urlparse(uri)
    if parsed.scheme != TILLM_SCHEME:
        raise ValueError(f"unsupported scheme: {parsed.scheme}")
    source = _decode(parsed.netloc)
    parts = [_decode(part) for part in parsed.path.strip("/").split("/") if part]
    params = {key: _decode(values[-1]) for key, values in parse_qs(parsed.query).items()}
    return {"source": source, "parts": parts, "params": params}
