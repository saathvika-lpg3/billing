from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from config.app_config import AppConfig
from config.product_version import DISPLAY_VERSION, PRODUCT_NAME


PRODUCT_TAGLINE = "Way to future, Today"
PRODUCT_LOGO_FILE = "PRM_SoftSolutions.jpg"
PRODUCT_ICON_FILE = "PRM_SoftSolutions.ico"


def _first_existing(paths: list[Path]) -> Path | None:
    seen: set[str] = set()
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.is_file():
            return path
    return None


def resolve_product_logo(config: AppConfig) -> Path | None:
    """Return only the fixed PRM Software product logo resource."""

    return _first_existing(
        [
            config.assets_dir / PRODUCT_LOGO_FILE,
            config.resource_root / "assets" / PRODUCT_LOGO_FILE,
            config.project_root / "assets" / PRODUCT_LOGO_FILE,
        ]
    )


def resolve_product_icon(config: AppConfig) -> Path | None:
    """Return the PRM executable/window icon without consulting client data."""

    return _first_existing(
        [
            config.assets_dir / PRODUCT_ICON_FILE,
            config.resource_root / "assets" / PRODUCT_ICON_FILE,
            config.project_root / "assets" / PRODUCT_ICON_FILE,
        ]
    ) or resolve_product_logo(config)


def product_icon(config: AppConfig) -> QIcon:
    path = resolve_product_icon(config)
    return QIcon(str(path)) if path else QIcon()


class ProductBrandHeader(QFrame):
    """Fixed PRM Software product identity; never reads a client profile."""

    def __init__(self, config: AppConfig, *, compact: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.compact = compact
        self.setObjectName("productBrandHeader")
        self.setProperty("productBrandHeader", True)
        self.setAccessibleName("PRM Software product branding")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9 if compact else 12)

        logo_width, logo_height = ((68, 52) if compact else (92, 72))
        self.logo = QLabel()
        self.logo.setObjectName("brandLogo")
        self.logo.setProperty("productLogo", True)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(logo_width, logo_height)
        self.logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.logo.setAccessibleName("PRM Software logo")

        self.title_label = QLabel(PRODUCT_NAME)
        self.title_label.setObjectName("brandTitle")
        self.title_label.setProperty("productName", True)
        self.title_label.setAccessibleName("Product name")
        self.version_label = QLabel(DISPLAY_VERSION)
        self.version_label.setObjectName("caption")
        self.version_label.setProperty("productVersion", True)
        self.version_label.setAccessibleName("Product version")
        self.version_label.setToolTip(f"{PRODUCT_NAME} {DISPLAY_VERSION}")
        self.tagline_label = QLabel(PRODUCT_TAGLINE)
        self.tagline_label.setObjectName("caption")
        self.tagline_label.setProperty("productTagline", True)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(0)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        title_row.addWidget(self.title_label)
        title_row.addWidget(self.version_label, alignment=Qt.AlignmentFlag.AlignBottom)
        title_row.addStretch(1)
        title_box.addLayout(title_row)
        title_box.addWidget(self.tagline_label)

        layout.addWidget(self.logo)
        layout.addLayout(title_box)
        self._load_product_logo()

    def _load_product_logo(self) -> None:
        path = resolve_product_logo(self.config)
        pixmap = QPixmap(str(path)) if path else QPixmap()
        self.logo.setText("")
        self.logo.setProperty("resourceError", pixmap.isNull())
        if pixmap.isNull():
            self.logo.setPixmap(QPixmap())
            self.logo.setToolTip("PRM Software product logo resource is missing.")
            return
        target = self.logo.size()
        self.logo.setPixmap(
            pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.logo.setToolTip(f"PRM Software | {path.name}")
        self.logo.setProperty("productLogoPath", str(path))
