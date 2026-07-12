from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from config.app_config import AppConfig
from services.business_rules import profile_for


def client_company_name(company: dict[str, Any]) -> str:
    return str(
        company.get("company_name")
        or company.get("business_name")
        or company.get("name")
        or "Client Company"
    ).strip()


def resolve_client_company_logo(config: AppConfig, company: dict[str, Any]) -> Path | None:
    """Resolve only an explicitly configured client logo path."""

    raw = str(company.get("logo_path") or "").strip()
    if not raw:
        return None
    value = Path(raw)
    candidates = [value] if value.is_absolute() else [config.project_root / value, config.resource_root / value]
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
    raw_address = str(company.get("address") or "").strip()
    raw_address_lower = raw_address.lower()
    locality = ", ".join(
        str(value).strip()
        for value in (company.get("city"), company.get("state"), company.get("pin_code"))
        if str(value or "").strip() and str(value).strip().lower() not in raw_address_lower
    )
    address = ", ".join(part for part in (raw_address, locality) if part)
    branch_year = " | ".join(
        part
        for part in (
            f"Branch {company.get('branch_name')}" if company.get("branch_name") else "",
            f"FY {company.get('financial_year')}" if company.get("financial_year") else "",
        )
        if part
    )
    return [line for line in (business, registrations, contact, address, branch_year) if line]


class ClientCompanyIdentityCard(QFrame):
    """Reusable client identity for business-context surfaces only."""

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
        self.setProperty("clientCompanyIdentity", True)
        self.setProperty("erpPreserveGeometry", True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        if not compact:
            self.setMinimumWidth(240)
            self.setMinimumHeight(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(1 if compact else 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.logo = QLabel()
        self.logo.setObjectName("clientLogo")
        self.logo.setProperty("clientLogo", True)
        self.logo.setProperty("erpPreserveGeometry", True)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setScaledContents(False)
        self.logo.setFixedSize(84 if compact else 144, 56 if compact else 96)
        self.logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.name_label = QLabel()
        self.name_label.setObjectName("clientName")
        self.name_label.setProperty("erpPreserveGeometry", True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMinimumWidth(150 if compact else 220)
        self.name_label.setMaximumWidth(210 if compact else 440)
        self.name_label.setMinimumHeight(34 if compact else 40)
        self.detail_labels = [QLabel() for _ in range(5)]
        layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        for label in self.detail_labels:
            label.setObjectName("clientMeta")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setMinimumHeight(18)
            label.setVisible(not compact)
            layout.addWidget(label)
        self.set_company(company or {})

    def set_company(self, company: dict[str, Any]) -> None:
        name = client_company_name(company)
        self.name_label.setText(name)
        path = resolve_client_company_logo(self.config, company)
        pixmap = QPixmap(str(path)) if path else QPixmap()
        if not pixmap.isNull():
            self.logo.setText("")
            self.logo.setProperty("clientLogoPlaceholder", False)
            self.logo.setProperty("clientLogoPath", str(path))
            target = self.logo.size()
            target.setWidth(max(1, target.width() - 10))
            target.setHeight(max(1, target.height() - 10))
            self.logo.setPixmap(
                pixmap.scaled(
                    target,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.logo.setToolTip(f"Client company logo | {path.name}")
        else:
            self.logo.setPixmap(QPixmap())
            self.logo.setText(_initials(name))
            self.logo.setProperty("clientLogoPlaceholder", True)
            self.logo.setProperty("clientLogoPath", "")
            self.logo.setToolTip("Client logo is not configured; showing company initials.")
        lines = company_identity_lines(company)
        for index, label in enumerate(self.detail_labels):
            label.setText(lines[index] if index < len(lines) else "")
            label.setVisible(not self.compact and index < len(lines))
            if label.isVisible():
                # Reserve enough vertical space for wrapped registration,
                # contact and address lines. QVBoxLayout may otherwise
                # compress word-wrapped labels upward over the fixed logo.
                label.setMinimumHeight(max(18, label.heightForWidth(220)))
        if not self.compact:
            self.name_label.setMinimumHeight(max(40, self.name_label.heightForWidth(220)))
            visible_labels = [label for label in self.detail_labels if label.isVisible()]
            required_height = (
                6
                + self.logo.height()
                + self.name_label.minimumHeight()
                + sum(label.minimumHeight() for label in visible_labels)
                + self.layout().spacing() * (1 + len(visible_labels))
            )
            self.setMinimumHeight(max(260, required_height))
        self.setAccessibleName(f"Company branding: {name}")


# Backward-compatible names remain available for stable callers, while all new
# code uses explicit product/client ownership names.
company_name = client_company_name
resolve_company_logo = resolve_client_company_logo
CompanyBrandingWidget = ClientCompanyIdentityCard
