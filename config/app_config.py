from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    source_root: Path

    @property
    def resource_root(self) -> Path:
        bundled = self.project_root / "_internal"
        return bundled if bundled.exists() else self.project_root

    @property
    def audit_dir(self) -> Path:
        source_audit = self.project_root / "audit"
        return source_audit if source_audit.exists() else self.resource_root / "audit"

    @property
    def theme_dir(self) -> Path:
        source_theme = self.project_root / "themes"
        return source_theme if source_theme.exists() else self.resource_root / "themes"

    @property
    def assets_dir(self) -> Path:
        source_assets = self.project_root / "assets"
        return source_assets if source_assets.exists() else self.resource_root / "assets"

    @property
    def log_dir(self) -> Path:
        return self.project_root / "logs"
