"""Decode tillm:// URIs into dsl2tillm command lines."""

from __future__ import annotations

from uri2tillm.uri import parse_tillm_uri


def uri_to_dsl(uri: str, *, default_file: str | None = None) -> str:
    parsed = parse_tillm_uri(uri)
    source = str(parsed["source"])
    parts = list(parsed["parts"])  # type: ignore[arg-type]
    params = dict(parsed["params"])  # type: ignore[arg-type]
    project = str(params.get("project") or default_file or "")

    if source == "cmd":
        verb = parts[0].upper() if parts else str(params.get("verb", "")).upper()
        if verb == "HEALTH":
            return "HEALTH"
        if verb == "CLIENTS":
            return "CLIENTS"
        if verb == "ORIENT":
            return "ORIENT"
        if verb == "ACTIONS":
            return "ACTIONS"
        if verb == "DOCKER_STATUS":
            return "DOCKER_STATUS"
        if verb == "VALIDATE":
            client = params.get("client")
            return f"VALIDATE CLIENT {client}" if client else "VALIDATE"
        if verb == "RESOLVE":
            return f'RESOLVE "{params.get("prompt", "")}"'
        if verb == "DRIVE":
            line = f'DRIVE CLIENT {params.get("client", "")} PROMPT "{params.get("prompt", "")}"'
            if params.get("execute", "").lower() in {"1", "true", "yes"}:
                line += " EXECUTE true"
            if params.get("profile"):
                line += f' PROFILE {params["profile"]}'
            if params.get("backend"):
                line += f' BACKEND {params["backend"]}'
            if project:
                line += f" PROJECT {project}"
            return line
        if verb == "DRIVE_MATRIX":
            line = "DRIVE_MATRIX"
            if params.get("all", "").lower() in {"1", "true", "yes"}:
                line += " ALL"
            elif params.get("clients"):
                line += f' CLIENTS {params["clients"]}'
            line += f' PROMPT "{params.get("prompt", "")}"'
            if params.get("parallel"):
                line += f' PARALLEL {params["parallel"]}'
            return line
        raise ValueError(f"unsupported cmd uri verb: {verb}")

    if source == "client":
        client = parts[0] if parts else params.get("client", "")
        prompt = params.get("prompt", "")
        return f'DRIVE CLIENT {client} PROMPT "{prompt}"'

    raise ValueError(f"unsupported tillm uri source: {source}")
