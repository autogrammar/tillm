"""Minimal CLI localization for tillm (en default, pl, de).

Language resolution precedence:
1. explicit ``set_language()`` / ``--lang`` flag,
2. ``TILLM_LANG`` environment variable,
3. language stored in the tillm config store (picked once via ``--lang``),
4. system locale (``LC_ALL``/``LC_MESSAGES``/``LANG``),
5. English.

Only languages with a full catalog are accepted; anything else falls back to
English. Catalogs are plain dicts — a missing key is a test failure, not a
runtime crash (falls back to the English string).
"""

from __future__ import annotations

import os

SUPPORTED = ("en", "pl", "de")
_DEFAULT = "en"

_override: str | None = None

_CATALOG: dict[str, dict[str, str]] = {
    "picker.title": {
        "en": "Available tools / providers (tillm):",
        "pl": "Dostępne narzędzia / providerzy (tillm):",
        "de": "Verfügbare Tools / Provider (tillm):",
    },
    "picker.col.provider": {"en": "provider", "pl": "provider", "de": "Provider"},
    "picker.col.kind": {"en": "type", "pl": "typ", "de": "Typ"},
    "picker.col.token": {"en": "token", "pl": "token", "de": "Token"},
    "picker.col.clients": {
        "en": "clients (✓ = binary on PATH)",
        "pl": "klienci (✓ = binarka w PATH)",
        "de": "Clients (✓ = Binärdatei im PATH)",
    },
    "picker.token.set": {"en": "✓ set", "pl": "✓ jest", "de": "✓ da"},
    "picker.token.missing": {"en": "✗ missing", "pl": "✗ brak", "de": "✗ fehlt"},
    "picker.default_mark": {"en": " ★default", "pl": " ★domyślny", "de": " ★Standard"},
    "picker.token_page": {"en": "token page", "pl": "strona tokenu", "de": "Token-Seite"},
    "picker.choose": {
        "en": "Choose provider [1-{count}, Enter=quit]: ",
        "pl": "Wybierz providera [1-{count}, Enter=wyjście]: ",
        "de": "Provider wählen [1-{count}, Enter=Beenden]: ",
    },
    "picker.invalid": {
        "en": "Invalid choice.",
        "pl": "Nieprawidłowy wybór.",
        "de": "Ungültige Auswahl.",
    },
    "picker.out_of_range": {
        "en": "Out of range.",
        "pl": "Poza zakresem.",
        "de": "Außerhalb des Bereichs.",
    },
    "token.local": {
        "en": "Local provider — no token needed.",
        "pl": "Provider lokalny — token niepotrzebny.",
        "de": "Lokaler Provider — kein Token nötig.",
    },
    "token.get_here": {
        "en": "Get your token here: {url}",
        "pl": "Token do pobrania tutaj: {url}",
        "de": "Token hier erstellen: {url}",
    },
    "token.prompt": {
        "en": "Token {label} ({env}){keep}: ",
        "pl": "Token {label} ({env}){keep}: ",
        "de": "Token {label} ({env}){keep}: ",
    },
    "token.keep_suffix": {
        "en": " [Enter = keep current]",
        "pl": " [Enter = zostaw obecny]",
        "de": " [Enter = aktuellen behalten]",
    },
    "token.unchanged": {
        "en": "Token unchanged.",
        "pl": "Token bez zmian.",
        "de": "Token unverändert.",
    },
    "token.empty": {
        "en": "Empty token — nothing stored.",
        "pl": "Pusty token — nic nie zapisano.",
        "de": "Leeres Token — nichts gespeichert.",
    },
    "token.saved": {
        "en": "✓ token saved (chmod 600)",
        "pl": "✓ token zapisany (chmod 600)",
        "de": "✓ Token gespeichert (chmod 600)",
    },
    "token.stored_in": {
        "en": "✓ stored token for {id} in {path}",
        "pl": "✓ zapisano token dla {id} w {path}",
        "de": "✓ Token für {id} gespeichert in {path}",
    },
    "model.label": {
        "en": "Model for {id}:",
        "pl": "Model dla {id}:",
        "de": "Modell für {id}:",
    },
    "model.current": {"en": " (current)", "pl": " (aktualny)", "de": " (aktuell)"},
    "model.choose": {
        "en": "Choice [1-{count}, name, Enter = {current}]: ",
        "pl": "Wybór [1-{count}, nazwa, Enter = {current}]: ",
        "de": "Auswahl [1-{count}, Name, Enter = {current}]: ",
    },
    "model.freeform": {
        "en": "Model for {id} [Enter = {current}]: ",
        "pl": "Model dla {id} [Enter = {current}]: ",
        "de": "Modell für {id} [Enter = {current}]: ",
    },
    "model.provider_default": {
        "en": "provider default",
        "pl": "domyślny providera",
        "de": "Provider-Standard",
    },
    "model.set": {
        "en": "✓ model set: {model}",
        "pl": "✓ model ustawiony: {model}",
        "de": "✓ Modell gesetzt: {model}",
    },
    "default.question": {
        "en": "Set {id} as the default provider for drive? [y/N, Enter = {current}]: ",
        "pl": "Ustawić {id} jako domyślny provider dla drive? [t/N, Enter = {current}]: ",
        "de": "{id} als Standard-Provider für drive setzen? [j/N, Enter = {current}]: ",
    },
    "default.none": {"en": "no default", "pl": "bez domyślnego", "de": "kein Standard"},
    "default.set": {
        "en": "✓ default provider: {id}",
        "pl": "✓ domyślny provider: {id}",
        "de": "✓ Standard-Provider: {id}",
    },
    "probe.label": {
        "en": "connection test: {detail}",
        "pl": "test połączenia: {detail}",
        "de": "Verbindungstest: {detail}",
    },
    "probe.result": {
        "en": "probe: {detail}",
        "pl": "test: {detail}",
        "de": "Probe: {detail}",
    },
    "usage.title": {"en": "How to use:", "pl": "Jak używać:", "de": "Verwendung:"},
    "usage.autonomy": {
        "en": "# for koru autonomy",
        "pl": "# dla autonomii koru",
        "de": "# für koru-Autonomie",
    },
    "noninteractive.hint": {
        "en": (
            "Non-interactive session — use: koru tillm provider set <id> --token ... "
            "and koru tillm provider test <id>"
        ),
        "pl": (
            "Sesja nieinteraktywna — użyj: koru tillm provider set <id> --token ... "
            "oraz koru tillm provider test <id>"
        ),
        "de": (
            "Nicht-interaktive Sitzung — nutze: koru tillm provider set <id> --token ... "
            "und koru tillm provider test <id>"
        ),
    },
    "keep.unchanged": {"en": "unchanged", "pl": "bez zmian", "de": "unverändert"},
    "token.already_set": {
        "en": "Token for {id} is already set ({env} or store).",
        "pl": "Token dla {id} już jest ustawiony ({env} lub magazyn).",
        "de": "Token für {id} ist bereits gesetzt ({env} oder Speicher).",
    },
    "overwrite.question": {
        "en": "Overwrite? [y/N]: ",
        "pl": "Nadpisać? [t/N]: ",
        "de": "Überschreiben? [j/N]: ",
    },
    "models.live": {
        "en": "live from API",
        "pl": "żywe z API",
        "de": "live von der API",
    },
    "models.curated": {
        "en": "built-in list; live fetch unavailable",
        "pl": "lista wbudowana; brak dostępu do żywej",
        "de": "eingebaute Liste; Live-Abruf nicht verfügbar",
    },
    "diag.title": {
        "en": "Diagnostics:",
        "pl": "Diagnostyka:",
        "de": "Diagnose:",
    },
    "lang.set": {
        "en": "✓ language: {lang}",
        "pl": "✓ język: {lang}",
        "de": "✓ Sprache: {lang}",
    },
}

# Affirmative answers per language (always accept English forms too).
_YES = {
    "en": ("y", "yes"),
    "pl": ("t", "tak", "y", "yes"),
    "de": ("j", "ja", "y", "yes"),
}


def _normalize(code: str | None) -> str | None:
    token = (code or "").strip().lower().replace("-", "_")
    if not token:
        return None
    short = token.split("_")[0].split(".")[0]
    return short if short in SUPPORTED else None


def _stored_language() -> str | None:
    try:
        from tillm.providers import _load_store

        entry = _load_store().get("_settings")
        if isinstance(entry, dict):
            return _normalize(entry.get("lang"))
    except Exception:
        return None
    return None


def _system_language() -> str | None:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        found = _normalize(os.environ.get(var))
        if found:
            return found
    return None


def set_language(code: str | None) -> str:
    """Explicit override for this process; returns the effective language."""
    global _override
    _override = _normalize(code)
    return current_language()


def save_language(code: str) -> str | None:
    """Persist the language choice in the tillm config store."""
    normalized = _normalize(code)
    if not normalized:
        return None
    from tillm.providers import _load_store, _write_store

    store = _load_store()
    settings = dict(store.get("_settings") or {})
    settings["lang"] = normalized
    store["_settings"] = settings
    _write_store(store)
    return normalized


def current_language() -> str:
    return (
        _override
        or _normalize(os.environ.get("TILLM_LANG"))
        or _stored_language()
        or _system_language()
        or _DEFAULT
    )


def _(key: str, **fmt: object) -> str:
    entry = _CATALOG.get(key)
    if not entry:
        return key
    text = entry.get(current_language()) or entry[_DEFAULT]
    return text.format(**fmt) if fmt else text


def yes_answers() -> tuple[str, ...]:
    return _YES.get(current_language(), _YES[_DEFAULT])


__all__ = [
    "SUPPORTED",
    "_",
    "current_language",
    "save_language",
    "set_language",
    "yes_answers",
]
