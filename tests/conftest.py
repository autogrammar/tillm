"""Global fixtures: keep tests hermetic from the user's real tillm config."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_tillm_config(tmp_path, monkeypatch):
    """Point the token/config store at a temp dir and clear provider env.

    Without this, a developer's real ~/.config/tillm/providers.json (stored
    default provider!) and TILLM_PROVIDER/TILLM_LANG leak into every test.

    LLM_MODEL/AIDER_MODEL are cleared too: ``bootstrap_project_env`` (called
    from ``main()`` for actions with no ``--project``, e.g. ``clients``) reads
    the repo's real ``.env`` and applies it via direct ``os.environ`` writes
    that monkeypatch never reverts, so one test's real-env read otherwise
    leaks into every later test's process env. Worse, ``apply_into_environ``
    skips keys already set (``overwrite=False``), so a leaked ``LLM_MODEL``
    silently shadows a *different* test's own tmp-path ``.env`` value too.
    """
    monkeypatch.setenv("TILLM_CONFIG_DIR", str(tmp_path / "tillm-config"))
    monkeypatch.delenv("TILLM_PROVIDER", raising=False)
    monkeypatch.delenv("TILLM_LANG", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("AIDER_MODEL", raising=False)
