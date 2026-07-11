from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from config.app_config import AppConfig
from services.business_rules import profile_for


def company_name(company: dict[str, Any]) -> str:
    return str(
        company.get("company_name")
        or company.get("business_name")
        or company.get("name")
        or "Client Company"
    ).strip()


def resolve_company_logo(config: AppConfig, company: dict[str, Any]) -> Path | None:
    raw = str(company.get("logo_path") or "").strip()
    if not raw:
        return None
    value = Path(raw)
    candidates = [value] if value.is_absolute() else [
        config.project_root / value,
        config.resource_root / value,
        config.assets_dir / value.name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _initials(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    return "".join(word[0].upper() for word in words[:3]) or "CO"


def company_identity_lines(company: dict[str, Any]) -> list[str]:
    business_code = str(company.get("business_type_code") or company.get("business_type") or "").strip()
    business = profile_for(business_code).name if business_code else ""
    registrations = " | ".join(
        part
        for part in (
            f"GSTIN {company.get('gstin')}" if company.get("gstin") else "",
            f"FSSAI {company.get('fssai_no')}" if company.get("fssai_no") else "",
            f"Drug Lic. {company.get('drug_license_no')}" if company.get("drug_license_no") else "",
        )
        if part
    )
    contact = " | ".join(
        str(value).strip()
        for value in (company.get("phone") or company.get("mobile"), company.get("email"))
        if str(value or "").strip()
    )
    return [line for line in (business, registrations, contact) if line]


class CompanyBrandingWidget(QFrame):
    """Reusable client identity with the logo above the company name."""

    def __init__(
        self,
        config: AppConfig,
        company: dict[str, Any] | None = None,
        *,
        compact: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.compact = compact
        self.setObjectName("companyBranding")
        self.setProperty("companyBranding", True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(1)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.logo = QLabel()
        self.logo.setObjectName("clientLogo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(64 if compact else 104, 30 if compact else 64)
        self.name_label = QLabel()
        self.name_label.setObjectName("clientName")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumWidth(190 if compact else 420)
        self.detail_labels = [QLabel() for _ in range(3)]
        layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        for label in self.detail_labels:
            label.setObjectName("clientMeta")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setVisible(not compact)
            layout.addWidget(label)
        self.set_company(company or {})

    def set_company(self, company: dict[str, Any]) -> None:
        name = company_name(company)
        self.name_label.setText(name)
        path = resolve_company_logo(self.config, company)
        pixmap = QPixmap(str(path)) if path else QPixmap()
        if not pixmap.isNull():
            self.logo.setText("")
            self.logo.setPixmap(
                pixmap.scaled(
                    self.logo.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo.setPixmap(QPixmap())
            self.logo.setText(_initials(name))
            self.logo.setToolTip("Client logo is not configured; showing company initials.")
        lines = company_identity_lines(company)
        for index, label in enumerate(self.detail_labels):
            label.setText(lines[index] if index < len(lines) else "")
            label.setVisible(not self.compact and index < len(lines))
        self.setAccessibleName(f"Company branding: {name}")
