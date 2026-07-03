"""Global fixtures: keep tests hermetic from the user's real tillm config."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_tillm_config(tmp_path, monkeypatch):
    """Point the token/config store at a temp dir and clear provider env.

    Without this, a developer's real ~/.config/tillm/providers.json (stored
    default provider!) and TILLM_PROVIDER/TILLM_LANG leak into every test.
    """
    monkeypatch.setenv("TILLM_CONFIG_DIR", str(tmp_path / "tillm-config"))
    monkeypatch.delenv("TILLM_PROVIDER", raising=False)
    monkeypatch.delenv("TILLM_LANG", raising=False)
