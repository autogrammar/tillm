"""GUI IDE provider configuration surfaces (detect-only)."""

from __future__ import annotations

from pathlib import Path

from tillm.providers import ProviderSpec
from tillm.surfaces_io import same_url
from tillm.surfaces_types import SurfaceState


class JetBrainsOpenAILikeSurface:
    """JetBrains AI Assistant OpenAI-like provider XML."""

    id = "jetbrains-openai-like"
    level = "gui"
    label = "JetBrains IDE (AI Assistant, OpenAI-like)"
    writable = False

    def _paths(self) -> list[Path]:
        root = Path.home() / ".config" / "JetBrains"
        return sorted(root.glob("*/options/llm.provider.openai.like.xml"))

    def applicable(self, spec: ProviderSpec) -> bool:
        return bool(spec.openai_base_url)

    def read(self, spec: ProviderSpec) -> SurfaceState:
        import xml.etree.ElementTree as ET

        paths = self._paths()
        configured_path: Path | None = None
        for path in reversed(paths):
            try:
                tree = ET.parse(path)
            except (OSError, ET.ParseError):
                continue
            for option in tree.iter("option"):
                if option.get("name") == "baseUrl" and same_url(
                    option.get("value"), spec.openai_base_url,
                ):
                    configured_path = path
                    break
            if configured_path:
                break
        shown = configured_path or (paths[-1] if paths else None)
        return SurfaceState(
            surface_id=self.id,
            level=self.level,
            label=self.label,
            path=str(shown) if shown else None,
            present=bool(paths),
            configured=bool(configured_path),
            has_token=False,
            model=None,
            writable=self.writable,
            detail="API key lives in the IDE keychain — paste it once in "
            "Settings → AI Assistant → Models, or let gillm drive the dialog",
        )

    def read_token(self, spec: ProviderSpec) -> str | None:
        return None


class QoderSurface:
    """Qoder (JetBrains plugin) BYOK settings — detect-only."""

    id = "qoder"
    level = "gui"
    label = "Qoder (BYOK)"
    writable = False

    def _paths(self) -> list[Path]:
        root = Path.home() / ".config" / "JetBrains"
        return sorted(root.glob("*/options/qoder_setting.xml"))

    def applicable(self, spec: ProviderSpec) -> bool:
        return bool(self._markers(spec))

    def _markers(self, spec: ProviderSpec) -> tuple[str, ...]:
        markers = [spec.id.lower(), *[alias.lower() for alias in spec.aliases]]
        for url in (spec.openai_base_url, spec.anthropic_base_url):
            if url:
                markers.append(url.split("//", 1)[-1].split("/", 1)[0].lower())
        return tuple(marker for marker in markers if len(marker) > 2)

    def read(self, spec: ProviderSpec) -> SurfaceState:
        paths = self._paths()
        configured_path: Path | None = None
        markers = self._markers(spec)
        for path in reversed(paths):
            raw = self._configured_text(path)
            if raw and any(marker in raw for marker in markers):
                configured_path = path
                break
        shown = configured_path or (paths[-1] if paths else None)
        return SurfaceState(
            surface_id=self.id,
            level=self.level,
            label=self.label,
            path=str(shown) if shown else None,
            present=bool(paths),
            configured=bool(configured_path),
            has_token=False,
            model=None,
            writable=self.writable,
            detail="configure the key in Qoder → Settings → Models (BYOK)",
        )

    @staticmethod
    def _configured_text(path: Path) -> str:
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(path)
        except (OSError, ET.ParseError):
            return ""
        parts: list[str] = []
        for option in tree.iter("option"):
            if option.get("name") == "cachedByokConfigJson":
                continue
            parts.append(option.get("value") or "")
        return " ".join(parts).lower()

    def read_token(self, spec: ProviderSpec) -> str | None:
        return None
