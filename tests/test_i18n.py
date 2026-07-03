"""Tests for CLI localization (en default, pl, de, system locale detection)."""

from __future__ import annotations

import pytest

from tillm import i18n


@pytest.fixture(autouse=True)
def _clean_lang(monkeypatch, tmp_path):
    monkeypatch.setenv("TILLM_CONFIG_DIR", str(tmp_path / "cfg"))
    for var in ("TILLM_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(var, raising=False)
    i18n.set_language(None)
    yield
    i18n.set_language(None)


class TestResolution:
    def test_default_is_english(self):
        assert i18n.current_language() == "en"
        assert i18n._("picker.title").startswith("Available tools")

    def test_system_locale_detected(self, monkeypatch):
        monkeypatch.setenv("LANG", "pl_PL.UTF-8")
        assert i18n.current_language() == "pl"
        assert "Dostępne" in i18n._("picker.title")

    def test_lc_all_wins_over_lang(self, monkeypatch):
        monkeypatch.setenv("LANG", "pl_PL.UTF-8")
        monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
        assert i18n.current_language() == "de"

    def test_tillm_lang_env_wins_over_locale(self, monkeypatch):
        monkeypatch.setenv("LANG", "de_DE.UTF-8")
        monkeypatch.setenv("TILLM_LANG", "pl")
        assert i18n.current_language() == "pl"

    def test_explicit_override_wins(self, monkeypatch):
        monkeypatch.setenv("TILLM_LANG", "pl")
        i18n.set_language("de")
        assert i18n.current_language() == "de"

    def test_unsupported_locale_falls_back_to_english(self, monkeypatch):
        monkeypatch.setenv("LANG", "fr_FR.UTF-8")
        assert i18n.current_language() == "en"

    def test_saved_language_persists(self, monkeypatch):
        assert i18n.save_language("de") == "de"
        assert i18n.current_language() == "de"
        monkeypatch.setenv("TILLM_LANG", "en")
        assert i18n.current_language() == "en"  # env beats store


class TestCatalog:
    def test_all_keys_have_all_languages(self):
        missing = [
            (key, lang)
            for key, entry in i18n._CATALOG.items()
            for lang in i18n.SUPPORTED
            if lang not in entry
        ]
        assert not missing

    def test_format_placeholders_consistent_across_languages(self):
        import string

        def placeholders(text):
            return {
                name for _, name, _, _ in string.Formatter().parse(text) if name
            }

        broken = []
        for key, entry in i18n._CATALOG.items():
            expected = placeholders(entry["en"])
            for lang in i18n.SUPPORTED:
                if placeholders(entry[lang]) != expected:
                    broken.append((key, lang))
        assert not broken

    def test_yes_answers_per_language(self):
        i18n.set_language("pl")
        assert "tak" in i18n.yes_answers()
        i18n.set_language("de")
        assert "ja" in i18n.yes_answers()
        i18n.set_language("en")
        assert i18n.yes_answers() == ("y", "yes")
