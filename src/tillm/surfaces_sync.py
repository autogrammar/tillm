"""Provider token import/export across configuration surfaces."""

from __future__ import annotations

from tillm.providers import (
    ProviderSpec,
    get_provider_spec,
    provider_default_model,
    resolve_provider_token,
    save_provider_token,
)
from tillm.surfaces_registry import iter_surfaces
from tillm.surfaces_terminal import CodexConfigSurface
from tillm.surfaces_types import SurfaceState, SyncStep


def _surface_in_sync(surface, spec: ProviderSpec, store_token: str) -> bool:
    own_token = surface.read_token(spec)
    if surface.id == CodexConfigSurface.id:
        return True
    return own_token == store_token


def plan_sync(
    provider_id: str,
    *,
    level: str | None = None,
    only: frozenset[str] | None = None,
) -> dict:
    spec = get_provider_spec(provider_id)
    store_token = resolve_provider_token(spec.id)
    states: list[SurfaceState] = []
    steps: list[SyncStep] = []
    import_pending = store_token is None
    for surface in iter_surfaces(level=level, only=only):
        if not surface.applicable(spec):
            continue
        state = surface.read(spec)
        states.append(state)
        if import_pending and surface.read_token(spec):
            steps.append(
                SyncStep(
                    surface.id,
                    "import-token",
                    f"copy token into tillm store from {state.path}",
                ),
            )
            import_pending = False
        elif not state.writable:
            steps.append(
                SyncStep(
                    surface.id,
                    "ok" if state.configured else "manual",
                    state.detail,
                ),
            )
        elif store_token is None:
            steps.append(SyncStep(surface.id, "skip", "no token in store yet"))
        elif state.configured and _surface_in_sync(surface, spec, store_token):
            steps.append(SyncStep(surface.id, "ok"))
        else:
            warning = getattr(surface, "export_warning", "")
            detail = f"write base URL + token for {spec.id}"
            steps.append(
                SyncStep(surface.id, "export", f"{detail}; {warning}" if warning else detail),
            )
    return {
        "provider": spec.id,
        "store_token": store_token is not None,
        "states": [state.to_dict() for state in states],
        "steps": [step.to_dict() for step in steps],
    }


def sync_all(
    *,
    level: str | None = None,
    only: frozenset[str] | None = None,
    apply: bool = False,
) -> dict:
    from tillm.providers import iter_provider_specs

    runner = apply_sync if apply else plan_sync
    reports: list[dict] = []
    for spec in iter_provider_specs():
        report = runner(spec.id, level=level, only=only)
        relevant = report["store_token"] or any(
            state["present"] for state in report["states"]
        )
        if not report["states"] or not relevant:
            continue
        report["label"] = spec.label
        report["kind"] = spec.kind
        report["token_url"] = spec.token_url
        reports.append(report)
    selected = [surface.id for surface in iter_surfaces(level=level, only=only)]
    return {
        "applied": apply,
        "level": level,
        "surfaces": selected,
        "providers": reports,
    }


def apply_sync(
    provider_id: str,
    *,
    level: str | None = None,
    only: frozenset[str] | None = None,
) -> dict:
    spec = get_provider_spec(provider_id)
    surfaces = {
        surface.id: surface for surface in iter_surfaces(level=level, only=only)
    }
    plan = plan_sync(provider_id, level=level, only=only)
    import_result: dict | None = None
    for step in plan["steps"]:
        if step["action"] != "import-token":
            continue
        token = surfaces[step["surface_id"]].read_token(spec)
        if token:
            save_provider_token(spec.id, token)
            import_result = {**step, "done": True}
            plan = plan_sync(provider_id, level=level, only=only)
        else:
            import_result = {**step, "done": False, "detail": "token vanished"}
        break
    results: list[dict] = [import_result] if import_result else []
    for step in plan["steps"]:
        if step["action"] == "import-token":
            continue
        if step["action"] != "export":
            results.append({**step, "done": step["action"] == "ok"})
            continue
        surface = surfaces[step["surface_id"]]
        token = resolve_provider_token(spec.id)
        write = getattr(surface, "write", None)
        if not token or write is None:
            results.append({**step, "done": False, "detail": "no token in store"})
            continue
        path = write(spec, token, provider_default_model(spec.id))
        results.append({**step, "done": True, "detail": f"wrote {path}"})
    plan["steps"] = results
    plan["states"] = [
        surfaces[state["surface_id"]].read(spec).to_dict() for state in plan["states"]
    ]
    plan["store_token"] = resolve_provider_token(spec.id) is not None
    return plan
