from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from config.app_config import AppConfig
from services.company_profile_service import CompanyProfileService
from services.license_service import LicenseContext, LicenseService
from widgets.company_branding import ClientCompanyIdentityCard
from widgets.product_branding import ProductBrandHeader


class LoginDialog(QDialog):
    def __init__(self, config: AppConfig, license_context: LicenseContext, license_service: LicenseService) -> None:
        super().__init__()
        self.config = config
        self.license_context = license_context
        self.license_service = license_service
        self.session: dict[str, str] = {}
        self.setWindowTitle("PRM BILLING INVENTORY Login")
        self.setMinimumWidth(540)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.product_brand = ProductBrandHeader(self.config, compact=False)
        root.addWidget(self.product_brand, alignment=Qt.AlignmentFlag.AlignHCenter)

        license_card = QFrame()
        license_card.setObjectName("card")
        card_layout = QVBoxLayout(license_card)
        client_heading = QLabel("Licensed Company")
        client_heading.setObjectName("cardTitle")
        client_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(client_heading)
        try:
            company_profile = CompanyProfileService(self.license_service.db_path).current_profile()
        except Exception:
            company_profile = {}
        company_profile["company_name"] = company_profile.get("company_name") or self.license_context.company_name
        company_profile["business_type_code"] = (
            company_profile.get("business_type_code") or self.license_context.business_type_code
        )
        company = ClientCompanyIdentityCard(self.config, company_profile)
        self.client_company_identity = company
        details = QLabel(
            f"{self.license_context.area} | Plan: {self.license_context.plan} | Valid till: {self.license_context.expiry_date}"
        )
        details.setObjectName("pageSubtitle")
        card_layout.addWidget(company)
        card_layout.addWidget(details)
        root.addWidget(license_card)

        self.username = QLineEdit()
        self.username.setPlaceholderText("User name / email")
        self.username.setText(self.license_context.super_admin_username)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.username.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self.try_login)
        root.addWidget(QLabel("Login"))
        root.addWidget(self.username)
        root.addWidget(self.password)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        login = QPushButton("Login")
        login.setObjectName("primaryButton")
        login.clicked.connect(self.try_login)
        actions.addWidget(login)
        actions.addWidget(cancel)
        root.addLayout(actions)

    def try_login(self) -> None:
        session = self.license_service.authenticate_user(
            self.username.text(),
            self.password.text(),
            self.license_context,
        )
        if not session:
            QMessageBox.warning(self, "Login", "Invalid login or locked user.")
            self.password.selectAll()
            self.password.setFocus()
            return
        self.session = session
        self.accept()
