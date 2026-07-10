from __future__ import annotations

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.backup_service import BackupService
from services.business_rules import PERMISSION_CATALOG, permission_keys, profile_rows
from services.company_profile_service import CompanyProfileService
from services.communication_log_service import CommunicationLogService, mask_recipient
from services.communication_template_service import CommunicationTemplateService
from services.data_maintenance_service import DataMaintenanceService
from services.email_service import EmailDeliveryService, SmtpEmailConfig, protect_secret
from services.mysql_source import MySqlSource
from services.pdf_print import write_template_preview_pdf
from services.share_service import whatsapp_readiness
from widgets.form_layout_helpers import build_field_section
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPToolbar, ERPGrid


class DeveloperConsoleView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.backup_service = BackupService(config)
        self.db_path = self.source.sqlite_path
        self.maintenance_service = DataMaintenanceService(config, self.db_path)
        self.company_profile_service = CompanyProfileService(self.db_path)
        self.communication_service = CommunicationLogService(self.db_path)
        self.communication_template_service = CommunicationTemplateService(self.db_path)
        self.selected_template_id: int | None = None
        self.permission_checks: dict[str, QCheckBox] = {}
        self.company_controls: dict[str, QWidget] = {}
        self._ensure_developer_schema()
        self.communication_service.ensure_schema()
        self.communication_template_service.seed_defaults()
        self._build()
        self.refresh_all()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        self.tabs = QTabWidget()
        self.tabs.addTab(self._summary_tab(), "Dashboard")
        self.tabs.addTab(self._companies_tab(), "Companies")
        self.tabs.addTab(self._business_tab(), "Business Rules")
        self.tabs.addTab(self._templates_tab(), "Print Templates")
        self.tabs.addTab(self._permissions_tab(), "Permissions")
        self.tabs.addTab(self._backup_tab(), "Backup")
        self.tabs.addTab(self._communication_tab(), "Communication")
        self.tabs.addTab(self._settings_tab(), "Settings")
        root.addWidget(self.tabs, stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Developer Console", "Desktop super-admin controls for licenses, templates, permissions, settings and backup")
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_all)
        header.layout().addWidget(refresh)
        header.status_label.setText("Ready")
        self.status_label = header.status_label
        return header

    def _summary_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        grid_host = QWidget()
        grid_host.setMaximumHeight(238)
        grid_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(6)
        grid.setHorizontalSpacing(6)
        self.summary_cards: dict[str, QLabel] = {}
        for index, (key, title) in enumerate(
            [
                ("companies", "Developer Companies"),
                ("licenses", "Active Licenses"),
                ("templates", "Print Templates"),
                ("permissions", "Permission Rows"),
                ("backups", "Backup Logs"),
                ("users", "Users"),
            ]
        ):
            card = QFrame()
            card.setObjectName("metricCard")
            card.setMinimumHeight(88)
            card.setMaximumHeight(112)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 6, 8, 6)
            card_layout.setSpacing(3)
            label = QLabel(title)
            label.setObjectName("metricTitle")
            value = QLabel("0")
            value.setObjectName("metricValue")
            note = QLabel("Live desktop database")
            note.setObjectName("metricNote")
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            card_layout.addWidget(note)
            self.summary_cards[key] = value
            grid.addWidget(card, index // 3, index % 3)
        layout.addWidget(grid_host, 0, Qt.AlignmentFlag.AlignTop)
        self.summary_table = self._table()
        layout.addWidget(self.summary_table, stretch=1)
        return page

    def _companies_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        caption = QLabel("Manage the product-purchased customer, license validity, feature plan and default print profile.")
        caption.setObjectName("pageSubtitle")
        layout.addWidget(caption)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(8, 6, 8, 6)
        form_layout.setSpacing(6)

        business_types = self.company_profile_service.business_types()
        business_labels = [f"{row.get('name') or ''} ({row.get('code') or ''})" for row in business_types]
        self.business_label_to_code = {label: str(row.get('code') or '') for label, row in zip(business_labels, business_types)}

        fields: list[tuple[str, str, QWidget, int]] = [
            ("company_name", "Company Name", QLineEdit(), 220),
            ("owner_name", "Owner Name", QLineEdit(), 170),
            ("phone", "Phone", QLineEdit(), 130),
            ("email", "Email", QLineEdit(), 190),
            ("business_type_code", "Business Type", QComboBox(), 190),
            ("subscription_plan_code", "Plan", QComboBox(), 120),
            ("license_key", "License Key", QLineEdit(), 180),
            ("installation_key", "Installation Key", QLineEdit(), 170),
            ("activation_date", "Activation Date", QLineEdit(), 120),
            ("expiry_date", "Expiry Date", QLineEdit(), 120),
            ("status", "Status", QComboBox(), 110),
            ("max_users", "Max Users", QLineEdit(), 90),
            ("gstin", "GSTIN Optional", QLineEdit(), 150),
            ("pan", "PAN Optional", QLineEdit(), 140),
            ("fssai_no", "FSSAI Optional", QLineEdit(), 150),
            ("invoice_prefix", "Invoice Prefix", QLineEdit(), 110),
            ("state", "State", QLineEdit(), 140),
        ]

        display_fields: list[tuple[str, QWidget, int]] = []
        for key, label, widget, width in fields:
            self.company_controls[key] = widget
            if key == "business_type_code" and isinstance(widget, QComboBox):
                widget.addItems(business_labels or ["Distributor / Wholesale (distributor_wholesale)"])
                widget.currentTextChanged.connect(self._business_type_changed)
            elif key == "subscription_plan_code" and isinstance(widget, QComboBox):
                widget.addItems(["basic", "standard", "premium", "enterprise"])
            elif key == "status" and isinstance(widget, QComboBox):
                widget.addItems(["active", "trial", "expired", "suspended", "cancelled"])
            display_fields.append((label, widget, width))

        form_layout.addWidget(build_field_section(display_fields, spacing=6, margin=0))

        self.company_address = QTextEdit()
        self.company_address.setMinimumHeight(38)
        self.company_address.setMaximumHeight(70)
        self.company_notes = QTextEdit()
        self.company_notes.setMinimumHeight(38)
        self.company_notes.setMaximumHeight(70)
        self.company_controls["address"] = self.company_address
        self.company_controls["notes"] = self.company_notes
        address_box = self._company_field("Address", self.company_address, 280)
        notes_box = self._company_field("Developer Notes", self.company_notes, 280)
        extra_row = QHBoxLayout()
        extra_row.setSpacing(6)
        extra_row.addWidget(address_box, stretch=2)
        extra_row.addWidget(notes_box, stretch=2)
        form_layout.addLayout(extra_row)

        self.company_logo_preview = QLabel("No Logo")
        self.company_logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.company_logo_preview.setFixedSize(96, 46)
        self.company_logo_preview.setObjectName("fieldBox")
        self.company_logo_path = QLineEdit()
        self.company_logo_path.setReadOnly(True)
        self.company_logo_path.setPlaceholderText("Client logo path")
        self.company_controls["logo_path"] = self.company_logo_path
        upload_logo = QPushButton("Upload Client Logo")
        upload_logo.clicked.connect(self.choose_company_logo)
        clear_logo = QPushButton("Clear Logo")
        clear_logo.clicked.connect(self.clear_company_logo)
        logo_box = QFrame()
        logo_box.setObjectName("fieldBox")
        logo_layout = QHBoxLayout(logo_box)
        logo_layout.setContentsMargins(6, 4, 6, 4)
        logo_layout.setSpacing(5)
        logo_layout.addWidget(self.company_logo_preview)
        logo_layout.addWidget(self.company_logo_path, stretch=1)
        logo_layout.addWidget(upload_logo)
        logo_layout.addWidget(clear_logo)
        form_layout.addWidget(logo_box)

        self.company_template_label = QLabel("Template: wholesale_tax_invoice")
        self.company_template_label.setObjectName("caption")
        save = QPushButton("Save Client Profile")
        save.clicked.connect(self.save_company_profile)
        reload_button = QPushButton("Reload Profile")
        reload_button.clicked.connect(self.refresh_all)
        actions = QHBoxLayout()
        actions.setSpacing(5)
        actions.addWidget(self.company_template_label)
        actions.addStretch(1)
        actions.addWidget(save)
        actions.addWidget(reload_button)
        form_layout.addLayout(actions)

        layout.addWidget(form_card)

        layout.addWidget(QLabel("Developer companies and license status"))
        self.company_table = self._table()
        layout.addWidget(self.company_table, stretch=1)
        self.license_table = self._table()
        layout.addWidget(self.license_table, stretch=1)
        return page

    def _company_field(self, label: str, widget: QWidget, minimum_width: int) -> QWidget:
        box = QFrame()
        box.setObjectName("fieldBox")
        box.setMinimumHeight(46 if not isinstance(widget, QTextEdit) else 56)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("fieldLabel")
        layout.addWidget(label_widget)
        layout.addWidget(widget)
        widget.setMinimumWidth(minimum_width)
        if isinstance(widget, QLineEdit):
            widget.setFixedHeight(28)
        if isinstance(widget, QComboBox):
            widget.setFixedHeight(28)
            widget.setMaxVisibleItems(14)
        return box

    def _business_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        caption = QLabel("Business profile rules are used by entry screens for required fields, item columns and print defaults.")
        caption.setObjectName("pageSubtitle")
        layout.addWidget(caption)
        self.business_table = self._table()
        layout.addWidget(self.business_table, stretch=1)
        return page

    def _templates_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        split = QHBoxLayout()
        self.template_table = self._table()
        self.template_table.itemSelectionChanged.connect(self._load_selected_template)
        split.addWidget(self.template_table, stretch=3)
        form_card = QFrame()
        form_card.setObjectName("card")
        form = QFormLayout(form_card)
        self.template_code = QLineEdit()
        self.template_name = QLineEdit()
        self.template_document = QComboBox()
        self.template_document.addItems(["sales_invoice", "purchase_invoice", "quotation", "delivery_challan", "sales_return", "purchase_return", "receipt"])
        self.template_paper = QComboBox()
        self.template_paper.addItems(["a2", "a3", "a4", "a5", "half_page", "thermal_58", "thermal_80"])
        self.template_orientation = QComboBox()
        self.template_orientation.addItems(["portrait", "landscape"])
        self.template_mode = QComboBox()
        self.template_mode.addItems(["laser", "thermal", "pdf"])
        self.template_html = QTextEdit()
        self.template_html.setMinimumHeight(60)
        self.template_html.setMaximumHeight(118)
        self.template_css = QTextEdit()
        self.template_css.setMinimumHeight(49)
        self.template_css.setMaximumHeight(98)
        form.addRow("Code", self.template_code)
        form.addRow("Name", self.template_name)
        form.addRow("Document", self.template_document)
        form.addRow("Paper", self.template_paper)
        form.addRow("Orientation", self.template_orientation)
        form.addRow("Print Mode", self.template_mode)
        form.addRow("HTML", self.template_html)
        form.addRow("CSS", self.template_css)
        buttons = QHBoxLayout()
        save = QPushButton("Save Template")
        save.clicked.connect(self.save_template)
        preview = QPushButton("Preview PDF")
        preview.clicked.connect(self.preview_template)
        export = QPushButton("Export HTML/CSS")
        export.clicked.connect(self.export_template_files)
        clear = QPushButton("New")
        clear.clicked.connect(self.clear_template_form)
        buttons.addWidget(save)
        buttons.addWidget(preview)
        buttons.addWidget(export)
        buttons.addWidget(clear)
        form.addRow(buttons)
        split.addWidget(form_card, stretch=2)
        layout.addLayout(split, stretch=1)
        return page

    def _permissions_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        bar = QHBoxLayout()
        self.role_selector = QComboBox()
        self.role_selector.currentTextChanged.connect(self.load_permissions)
        save = QPushButton("Save Permissions")
        save.clicked.connect(self.save_permissions)
        bar.addWidget(QLabel("Role"))
        bar.addWidget(self.role_selector)
        bar.addStretch(1)
        bar.addWidget(save)
        layout.addLayout(bar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = QWidget()
        grid = QGridLayout(holder)
        row = 0
        for group, permissions in PERMISSION_CATALOG.items():
            title = QLabel(group)
            title.setObjectName("cardTitle")
            grid.addWidget(title, row, 0, 1, 3)
            row += 1
            for index, (key, label) in enumerate(permissions):
                check = QCheckBox(label)
                self.permission_checks[key] = check
                grid.addWidget(check, row, index % 3)
                if index % 3 == 2:
                    row += 1
            row += 1
        scroll.setWidget(holder)
        layout.addWidget(scroll, stretch=1)
        return page

    def _backup_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card = QFrame()
        card.setObjectName("card")
        form = QFormLayout(card)
        self.backup_password = QLineEdit()
        self.backup_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.restore_file = QLineEdit()
        self.restore_password = QLineEdit()
        self.restore_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.restore_confirm = QLineEdit()
        form.addRow("Backup Password", self.backup_password)
        buttons = QHBoxLayout()
        normal = QPushButton("Create JSON Backup")
        normal.clicked.connect(lambda: self.create_backup(False))
        encrypted = QPushButton("Create Encrypted .pgst")
        encrypted.clicked.connect(lambda: self.create_backup(True))
        buttons.addWidget(normal)
        buttons.addWidget(encrypted)
        form.addRow(buttons)
        browse = QPushButton("Choose Restore File")
        browse.clicked.connect(self.choose_restore_file)
        form.addRow("Restore File", self.restore_file)
        form.addRow("", browse)
        form.addRow("Restore Password", self.restore_password)
        form.addRow("Type RESTORE", self.restore_confirm)
        restore = QPushButton("Restore Backup")
        restore.clicked.connect(self.restore_backup)
        form.addRow("", restore)
        layout.addWidget(card)

        free_card = QFrame()
        free_card.setObjectName("card")
        free_form = QFormLayout(free_card)
        note = QLabel(
            "Deletes old transaction/history rows only after a full SQLite backup and Excel export are created."
        )
        note.setObjectName("pageSubtitle")
        note.setWordWrap(True)
        free_form.addRow("Free Space", note)
        current_year = datetime.now().year
        self.free_from_year = QSpinBox()
        self.free_from_year.setRange(2000, current_year)
        self.free_from_year.setValue(max(2000, current_year - 8))
        self.free_to_year = QSpinBox()
        self.free_to_year.setRange(2000, current_year)
        self.free_to_year.setValue(max(2000, current_year - 2))
        years = QHBoxLayout()
        years.addWidget(QLabel("From"))
        years.addWidget(self.free_from_year)
        years.addWidget(QLabel("To"))
        years.addWidget(self.free_to_year)
        years.addStretch(1)
        free_form.addRow("Years", years)
        free_button = QPushButton("Free Space")
        free_button.setObjectName("dangerButton")
        free_button.clicked.connect(self.free_space)
        free_form.addRow("", free_button)
        layout.addWidget(free_card)

        self.backup_table = self._table()
        layout.addWidget(QLabel("Backup history"))
        layout.addWidget(self.backup_table, stretch=1)
        self.maintenance_table = self._table()
        layout.addWidget(QLabel("Data maintenance history"))
        layout.addWidget(self.maintenance_table, stretch=1)
        return page

    def _communication_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        self.communication_tabs = QTabWidget()
        self.communication_tabs.addTab(self._communication_delivery_tab(), "Delivery")
        self.communication_tabs.addTab(self._communication_templates_tab(), "Message Templates")
        layout.addWidget(self.communication_tabs, stretch=1)
        return page

    def _communication_delivery_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        settings_card = QFrame()
        settings_card.setObjectName("card")
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(10, 8, 10, 8)
        settings_layout.setSpacing(6)
        title = QLabel("Email Delivery Settings")
        title.setObjectName("sectionTitle")
        settings_layout.addWidget(title)

        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(5)
        self.email_delivery_mode = QComboBox()
        self.email_delivery_mode.addItems(["handoff", "smtp"])
        self.email_smtp_host = QLineEdit()
        self.email_smtp_host.setPlaceholderText("smtp.example.com")
        self.email_smtp_port = QSpinBox()
        self.email_smtp_port.setRange(1, 65535)
        self.email_smtp_port.setValue(587)
        self.email_smtp_username = QLineEdit()
        self.email_smtp_password = QLineEdit()
        self.email_smtp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.email_smtp_password.setPlaceholderText("Leave blank to keep current password")
        self.email_smtp_from = QLineEdit()
        self.email_smtp_timeout = QSpinBox()
        self.email_smtp_timeout.setRange(5, 120)
        self.email_smtp_timeout.setValue(20)
        self.email_smtp_tls = QCheckBox("STARTTLS")
        self.email_smtp_ssl = QCheckBox("SSL")

        fields = [
            ("Mode", self.email_delivery_mode),
            ("SMTP Host", self.email_smtp_host),
            ("Port", self.email_smtp_port),
            ("Username", self.email_smtp_username),
            ("Password", self.email_smtp_password),
            ("From Email", self.email_smtp_from),
            ("Timeout", self.email_smtp_timeout),
            ("Security", self._email_security_box()),
        ]
        for index, (label, widget) in enumerate(fields):
            row = index // 2
            col = (index % 2) * 2
            form.addWidget(QLabel(label), row, col)
            form.addWidget(widget, row, col + 1)
        settings_layout.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch(1)
        save = QPushButton("Save SMTP Settings")
        save.clicked.connect(self.save_email_settings)
        retry = QPushButton("Retry Failed Email")
        retry.clicked.connect(self.retry_failed_emails)
        refresh = QPushButton("Refresh Logs")
        refresh.clicked.connect(self.refresh_all)
        actions.addWidget(save)
        actions.addWidget(retry)
        actions.addWidget(refresh)
        settings_layout.addLayout(actions)
        layout.addWidget(settings_card)

        diagnostics_card = QFrame()
        diagnostics_card.setObjectName("card")
        diagnostics_card.setMaximumHeight(126)
        diagnostics_layout = QVBoxLayout(diagnostics_card)
        diagnostics_layout.setContentsMargins(10, 8, 10, 8)
        diagnostics_layout.setSpacing(5)
        diagnostics_title = QLabel("Delivery Diagnostics")
        diagnostics_title.setObjectName("sectionTitle")
        diagnostics_layout.addWidget(diagnostics_title)
        diagnostic_form = QGridLayout()
        diagnostic_form.setContentsMargins(0, 0, 0, 0)
        diagnostic_form.setHorizontalSpacing(8)
        diagnostic_form.setVerticalSpacing(4)
        self.comm_test_email = QLineEdit()
        self.comm_test_email.setPlaceholderText("test-recipient@example.com")
        self.comm_test_whatsapp = QLineEdit()
        self.comm_test_whatsapp.setPlaceholderText("9000000000")
        diagnostic_form.addWidget(QLabel("Test Email"), 0, 0)
        diagnostic_form.addWidget(self.comm_test_email, 0, 1)
        diagnostic_form.addWidget(QLabel("WhatsApp No."), 0, 2)
        diagnostic_form.addWidget(self.comm_test_whatsapp, 0, 3)
        test_smtp = QPushButton("Test SMTP")
        test_smtp.clicked.connect(self.test_email_delivery_settings)
        check_whatsapp = QPushButton("Check WhatsApp Link")
        check_whatsapp.clicked.connect(self.check_whatsapp_delivery_link)
        diagnostic_form.addWidget(test_smtp, 0, 4)
        diagnostic_form.addWidget(check_whatsapp, 0, 5)
        diagnostics_layout.addLayout(diagnostic_form)
        self.comm_delivery_diagnostics = QLabel("Diagnostics not run.")
        self.comm_delivery_diagnostics.setObjectName("hintLabel")
        self.comm_delivery_diagnostics.setWordWrap(True)
        diagnostics_layout.addWidget(self.comm_delivery_diagnostics)
        layout.addWidget(diagnostics_card)

        layout.addWidget(QLabel("Pending email retries"))
        self.communication_retry_table = self._table()
        self.communication_retry_table.setMaximumHeight(140)
        layout.addWidget(self.communication_retry_table)

        layout.addWidget(QLabel("Recent communication history"))
        self.communication_log_table = self._table()
        self.communication_log_table.setMaximumHeight(260)
        layout.addWidget(self.communication_log_table, stretch=1)
        return page

    def _communication_templates_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        card = QFrame()
        card.setObjectName("card")
        card.setMaximumHeight(286)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(6)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title = QLabel("Message Template Settings")
        title.setObjectName("sectionTitle")
        title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        card_layout.addWidget(title)

        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(5)
        self.comm_template_code = QLineEdit()
        self.comm_template_code.setPlaceholderText("sales_invoice_email")
        self.comm_template_channel = QComboBox()
        self.comm_template_channel.addItems(["email", "whatsapp", "sms"])
        self.comm_template_document_type = QComboBox()
        self.comm_template_document_type.setEditable(True)
        self.comm_template_document_type.addItems(
            [
                "sales_invoice",
                "purchase_invoice",
                "quotation",
                "sales_order",
                "purchase_order",
                "receipt",
                "payment",
                "payment_reminder",
                "stock_out",
                "dispatch_return",
                "route_settlement",
                "general",
            ]
        )
        if self.comm_template_document_type.lineEdit():
            self.comm_template_document_type.lineEdit().setPlaceholderText("sales_invoice")
        self.comm_template_name = QLineEdit()
        self.comm_template_name.setPlaceholderText("Template name")
        self.comm_template_subject = QLineEdit()
        self.comm_template_subject.setPlaceholderText("Subject with {document_no}")
        self.comm_contact_field = QComboBox()
        self.comm_template_active = QCheckBox("Active")
        self.comm_template_active.setChecked(True)
        fields = [
            ("Code", self.comm_template_code),
            ("Channel", self.comm_template_channel),
            ("Document Type", self.comm_template_document_type),
            ("Name", self.comm_template_name),
            ("Preferred Contact", self.comm_contact_field),
            ("Subject", self.comm_template_subject),
            ("Status", self.comm_template_active),
        ]
        for index, (label, widget) in enumerate(fields):
            row = index // 2
            col = (index % 2) * 2
            form.addWidget(QLabel(label), row, col)
            form.addWidget(widget, row, col + 1)
        card_layout.addLayout(form)

        self.comm_template_body = QTextEdit()
        self.comm_template_body.setPlaceholderText("Body text. Supported placeholders include {party_name}, {document_no}, {amount}, {company_name}.")
        self.comm_template_body.setMinimumHeight(64)
        self.comm_template_body.setMaximumHeight(96)
        self.comm_template_body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card_layout.addWidget(self.comm_template_body)

        actions = QHBoxLayout()
        actions.addStretch(1)
        save = QPushButton("Save Template")
        save.clicked.connect(self.save_communication_template)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_communication_template_form)
        actions.addWidget(save)
        actions.addWidget(clear)
        card_layout.addLayout(actions)
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignTop)

        preview_card = QFrame()
        preview_card.setObjectName("card")
        preview_card.setMaximumHeight(188)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(10, 8, 10, 8)
        preview_layout.setSpacing(5)
        preview_title = QLabel("Template Preview And Contact Check")
        preview_title.setObjectName("sectionTitle")
        preview_layout.addWidget(preview_title)

        preview_form = QGridLayout()
        preview_form.setContentsMargins(0, 0, 0, 0)
        preview_form.setHorizontalSpacing(8)
        preview_form.setVerticalSpacing(5)
        self.comm_preview_party = QLineEdit("Demo Customer")
        self.comm_preview_document_no = QLineEdit("DEMO-001")
        self.comm_preview_amount = QLineEdit("Rs 1,250.00")
        self.comm_preview_email = QLineEdit("customer@example.test")
        self.comm_preview_mobile = QLineEdit("9000000000")
        preview_fields = [
            ("Party", self.comm_preview_party),
            ("Doc No", self.comm_preview_document_no),
            ("Amount", self.comm_preview_amount),
            ("Email", self.comm_preview_email),
            ("Mobile", self.comm_preview_mobile),
        ]
        for index, (label, widget) in enumerate(preview_fields):
            row = index // 3
            col = (index % 3) * 2
            preview_form.addWidget(QLabel(label), row, col)
            preview_form.addWidget(widget, row, col + 1)
        preview_layout.addLayout(preview_form)

        preview_actions = QHBoxLayout()
        self.comm_contact_result = QLabel("Contact: Auto")
        self.comm_contact_result.setObjectName("hintLabel")
        preview_actions.addWidget(self.comm_contact_result, stretch=1)
        preview = QPushButton("Preview Message")
        preview.clicked.connect(self.preview_communication_template)
        preview_actions.addWidget(preview)
        preview_layout.addLayout(preview_actions)

        self.comm_template_preview = QTextEdit()
        self.comm_template_preview.setReadOnly(True)
        self.comm_template_preview.setPlaceholderText("Rendered subject, body and resolved contact appear here.")
        self.comm_template_preview.setMinimumHeight(48)
        self.comm_template_preview.setMaximumHeight(72)
        preview_layout.addWidget(self.comm_template_preview)
        layout.addWidget(preview_card, 0, Qt.AlignmentFlag.AlignTop)

        templates_label = QLabel("Available templates")
        templates_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(templates_label, 0, Qt.AlignmentFlag.AlignTop)
        self.communication_template_table = self._table()
        self.communication_template_table.setMinimumHeight(300)
        self.communication_template_table.setMaximumHeight(16777215)
        self.communication_template_table.itemSelectionChanged.connect(self._load_selected_communication_template)
        layout.addWidget(self.communication_template_table, stretch=1)
        self.comm_template_channel.currentTextChanged.connect(self._load_contact_preference_for_form)
        self.comm_template_document_type.currentTextChanged.connect(self._load_contact_preference_for_form)
        self._load_contact_preference_for_form()
        return page

    def _email_security_box(self) -> QWidget:
        box = QWidget()
        layout = QHBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.email_smtp_tls)
        layout.addWidget(self.email_smtp_ssl)
        layout.addStretch(1)
        return box

    def _settings_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        form_card = QFrame()
        form_card.setObjectName("card")
        form = QHBoxLayout(form_card)
        self.setting_key = QLineEdit()
        self.setting_key.setPlaceholderText("setting_key")
        self.setting_value = QLineEdit()
        self.setting_value.setPlaceholderText("setting value")
        save = QPushButton("Save Setting")
        save.clicked.connect(self.save_setting)
        form.addWidget(self.setting_key)
        form.addWidget(self.setting_value, stretch=2)
        form.addWidget(save)
        layout.addWidget(form_card)
        self.settings_table = self._table()
        layout.addWidget(self.settings_table, stretch=1)
        return page

    def _table(self) -> QTableWidget:
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setMinimumHeight(72)
        table.setMaximumHeight(180)
        table.verticalHeader().setDefaultSectionSize(26)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def refresh_all(self) -> None:
        self._refresh_summary()
        self._load_company_profile()
        self._fill_table(self.company_table, self.company_profile_service.developer_rows())
        self._fill_table(self.license_table, self._rows("SELECT id,license_key,company_name,business_type,license_plan,expiry_date,status,max_users,updated_at FROM license ORDER BY id DESC LIMIT 200"))
        self._fill_table(self.business_table, profile_rows())
        self._fill_table(self.template_table, self.source.operation_rows("print_templates", 1000))
        self._fill_table(self.backup_table, self.source.operation_rows("backup", 500))
        self._fill_table(
            self.maintenance_table,
            self._rows(
                """
                SELECT id,operation,status,records_exported,records_deleted,backup_path,report_path,created_by,created_at
                FROM data_maintenance_logs
                ORDER BY id DESC
                LIMIT 200
                """
            ),
        )
        self._fill_table(self.settings_table, self._rows("SELECT setting_key,setting_value,updated_at FROM app_settings ORDER BY setting_key"))
        self._load_email_settings()
        self._refresh_communication_tables()
        self._refresh_communication_templates()
        self._reload_roles()
        self.status_label.setText(f"Refreshed {datetime.now():%H:%M:%S}")

    def _refresh_summary(self) -> None:
        counts = {
            "companies": self._scalar("SELECT COUNT(*) FROM company"),
            "licenses": self._scalar("SELECT COUNT(*) FROM license WHERE COALESCE(status,'Active')='Active'"),
            "templates": self._scalar("SELECT COUNT(*) FROM print_templates"),
            "permissions": self._scalar("SELECT COUNT(*) FROM role_permissions"),
            "backups": self._scalar("SELECT COUNT(*) FROM backup_logs"),
            "users": self._scalar("SELECT COUNT(*) FROM users"),
        }
        for key, value in counts.items():
            self.summary_cards[key].setText(str(value))
        self._fill_table(
            self.summary_table,
            [
                {"Area": "Backup", "Status": "Ready", "Detail": str(self.config.project_root / "backups")},
                {"Area": "Free Space", "Status": "Backup + Excel + Delete + Vacuum", "Detail": str(self.config.project_root / "archives" / "free_space")},
                {"Area": "Database", "Status": "Local SQLite", "Detail": str(self.db_path)},
                {"Area": "Mode", "Status": "Desktop", "Detail": "No XAMPP required on client machines"},
            ],
        )

    def _load_company_profile(self) -> None:
        if not self.company_controls:
            return
        profile = self.company_profile_service.current_profile()
        for key, widget in self.company_controls.items():
            value = "" if profile.get(key) is None else str(profile.get(key))
            if isinstance(widget, QLineEdit):
                widget.setText(value)
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(value)
            elif isinstance(widget, QComboBox):
                if key == "business_type_code":
                    self._set_business_combo(value)
                else:
                    if widget.findText(value) < 0:
                        widget.addItem(value)
                    widget.setCurrentText(value)
        self._business_type_changed(self.company_controls["business_type_code"].currentText())
        self._set_company_logo_preview(str(profile.get("logo_path") or ""))

    def _set_business_combo(self, code: str) -> None:
        combo = self.company_controls.get("business_type_code")
        if not isinstance(combo, QComboBox):
            return
        target = next((label for label, row_code in self.business_label_to_code.items() if row_code == code), "")
        if not target and code:
            target = code
            combo.addItem(target)
            self.business_label_to_code[target] = code
        if target:
            combo.setCurrentText(target)

    def _business_type_changed(self, label: str) -> None:
        code = self.business_label_to_code.get(label, label)
        template_code = self.company_profile_service.template_for_business_type(code)
        template_name = self.company_profile_service.template_name_for_code(template_code)
        if template_name and template_name != template_code:
            self.company_template_label.setText(f"Template: {template_name} ({template_code})")
        else:
            self.company_template_label.setText(f"Template: {template_code}")

    def save_company_profile(self) -> None:
        data: dict[str, Any] = {}
        for key, widget in self.company_controls.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                data[key] = widget.toPlainText().strip()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText().strip()
        data["business_type_code"] = self.business_label_to_code.get(str(data.get("business_type_code") or ""), str(data.get("business_type_code") or ""))
        if not data.get("company_name"):
            QMessageBox.warning(self, "Client Profile", "Company name is required.")
            self.company_controls["company_name"].setFocus()
            return
        try:
            # Developer console updates are allowed to update all fields
            company_id = self.company_profile_service.save_profile(data, developer=True)
        except Exception as exc:
            QMessageBox.warning(self, "Client Profile", f"Client profile could not be saved:\n{exc}")
            return
        QMessageBox.information(self, "Client Profile", f"Client profile saved.\nCompany ID: {company_id}")
        self.refresh_all()

    def choose_company_logo(self) -> None:
        path_text, _ = QFileDialog.getOpenFileName(
            self,
            "Upload Client Logo",
            str(self.config.project_root),
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if not path_text:
            return
        source = Path(path_text)
        target_dir = self.config.project_root / "uploads"
        target_dir.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix.lower() if source.suffix else ".png"
        target = target_dir / f"client_logo_{datetime.now():%Y%m%d_%H%M%S}{suffix}"
        try:
            shutil.copy2(source, target)
        except OSError as exc:
            QMessageBox.warning(self, "Client Logo", f"Logo could not be copied:\n{exc}")
            return
        relative = target.relative_to(self.config.project_root).as_posix()
        self.company_logo_path.setText(relative)
        self._set_company_logo_preview(relative)

    def clear_company_logo(self) -> None:
        self.company_logo_path.clear()
        self._set_company_logo_preview("")

    def _set_company_logo_preview(self, raw_path: str) -> None:
        path = self._resolve_company_logo(raw_path)
        if not path:
            self.company_logo_preview.setPixmap(QPixmap())
            self.company_logo_preview.setText("No Logo")
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.company_logo_preview.setPixmap(QPixmap())
            self.company_logo_preview.setText("Logo\nUnavailable")
            return
        self.company_logo_preview.setText("")
        self.company_logo_preview.setPixmap(
            pixmap.scaled(
                self.company_logo_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _resolve_company_logo(self, raw_path: str) -> Path | None:
        value = str(raw_path or "").strip()
        if not value:
            return None
        path = Path(value)
        candidates = [path] if path.is_absolute() else [self.config.project_root / value, self.config.resource_root / value]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _safe_rows(self, table: str) -> list[dict[str, Any]]:
        return self._rows(f'SELECT * FROM "{table}" ORDER BY id DESC LIMIT 500')

    def _rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, params)
            conn.commit()

    def _scalar(self, sql: str) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                return int(conn.execute(sql).fetchone()[0] or 0)
        except sqlite3.Error:
            return 0

    def _ensure_developer_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT,
                    updated_at TEXT
                )
                """
            )

    def _load_email_settings(self) -> None:
        config = SmtpEmailConfig.from_sources(db_path=self.db_path)
        mode = config.delivery_mode if config.delivery_mode in {"handoff", "smtp"} else "handoff"
        self.email_delivery_mode.setCurrentText(mode)
        self.email_smtp_host.setText(config.host)
        self.email_smtp_port.setValue(int(config.port or 587))
        self.email_smtp_username.setText(config.username)
        self.email_smtp_password.clear()
        self.email_smtp_from.setText(config.from_email)
        self.email_smtp_timeout.setValue(max(5, min(120, int(config.timeout or 20))))
        self.email_smtp_tls.setChecked(bool(config.use_tls))
        self.email_smtp_ssl.setChecked(bool(config.use_ssl))

    def _refresh_communication_tables(self) -> None:
        pending = [
            {
                    "id": row.get("id"),
                    "recipient": mask_recipient(row.get("recipient")),
                    "subject": row.get("subject"),
                    "code": row.get("result_code"),
                "attempts": row.get("attempts"),
                "next_retry_at": row.get("next_retry_at"),
            }
            for row in self.communication_service.pending_retries(100)
        ]
        self._fill_table(self.communication_retry_table, pending)
        self._fill_table(self.communication_log_table, self.communication_service.recent_logs(200))

    def _refresh_communication_templates(self) -> None:
        self._fill_table(
            self.communication_template_table,
            [
                {
                    "id": row.get("id"),
                    "template_code": row.get("template_code"),
                    "channel": row.get("channel"),
                    "document_type": row.get("document_type"),
                    "template_name": row.get("template_name"),
                    "is_active": row.get("is_active"),
                    "updated_at": row.get("updated_at"),
                }
                for row in self.communication_template_service.templates(200)
            ],
        )

    def _save_app_settings(self, values: dict[str, object]) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO app_settings(setting_key,setting_value,updated_at)
                VALUES(?,?,?)
                ON CONFLICT(setting_key) DO UPDATE
                SET setting_value=excluded.setting_value,
                    updated_at=excluded.updated_at
                """,
                [(key, "" if value is None else str(value), now) for key, value in values.items()],
            )

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, Any]]) -> None:
        if not rows:
            table.setColumnCount(1)
            table.setRowCount(1)
            table.setHorizontalHeaderLabels(["Status"])
            table.setItem(0, 0, QTableWidgetItem("No rows found."))
            return
        headers = list(rows[0].keys())
        table.setColumnCount(len(headers))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels([header.replace("_", " ").title() for header in headers])
        for row_index, row in enumerate(rows):
            for col_index, header in enumerate(headers):
                item = QTableWidgetItem("" if row.get(header) is None else str(row.get(header)))
                if isinstance(row.get(header), (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row_index, col_index, item)
        table.resizeRowsToContents()

    def _load_selected_template(self) -> None:
        items = self.template_table.selectedItems()
        if not items:
            return
        row = items[0].row()
        template_id_item = self.template_table.item(row, 0)
        if not template_id_item:
            return
        try:
            template_id = int(template_id_item.text())
        except ValueError:
            return
        rows = self._rows("SELECT * FROM print_templates WHERE id=?", (template_id,))
        if not rows:
            return
        template = rows[0]
        self.selected_template_id = template_id
        self.template_code.setText(str(template.get("template_code") or ""))
        self.template_name.setText(str(template.get("template_name") or ""))
        self.template_document.setCurrentText(str(template.get("document_type") or "sales_invoice"))
        self.template_paper.setCurrentText(str(template.get("paper_size") or "a4"))
        self.template_orientation.setCurrentText(str(template.get("orientation") or "portrait"))
        self.template_mode.setCurrentText(str(template.get("print_mode") or "laser"))
        self.template_html.setPlainText(str(template.get("html_template") or ""))
        self.template_css.setPlainText(str(template.get("css_template") or ""))

    def clear_template_form(self) -> None:
        self.selected_template_id = None
        self.template_code.clear()
        self.template_name.clear()
        self.template_orientation.setCurrentText("portrait")
        self.template_html.clear()
        self.template_css.clear()

    def save_template(self) -> None:
        code = self.template_code.text().strip()
        name = self.template_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Print Template", "Template code and name are required.")
            return
        family_id = self._scalar("SELECT COALESCE(MIN(id),0) FROM print_template_families")
        if not family_id:
            self._execute(
                """
                INSERT INTO print_template_families(
                    business_type,family_code,family_name,description,default_paper_size,
                    default_print_mode,supports_thermal,supports_a4,is_default,is_active,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                ("distributor_wholesale", "desktop_default", "Desktop Default", "Created by desktop console", "a4", "laser", 1, 1, 1, 1, datetime.now().isoformat(timespec="seconds"), datetime.now().isoformat(timespec="seconds")),
            )
            family_id = self._scalar("SELECT COALESCE(MIN(id),0) FROM print_template_families")
        params = (
            family_id,
            code,
            name,
            self.template_document.currentText(),
            self.template_paper.currentText(),
            self.template_orientation.currentText(),
            self.template_mode.currentText(),
            self.template_html.toPlainText(),
            self.template_css.toPlainText(),
            0,
            1,
            datetime.now().isoformat(timespec="seconds"),
        )
        if self.selected_template_id:
            self._execute(
                """
                UPDATE print_templates
                SET family_id=?,template_code=?,template_name=?,document_type=?,paper_size=?,orientation=?,
                    print_mode=?,html_template=?,css_template=?,is_default=?,is_active=?,updated_at=?
                WHERE id=?
                """,
                params + (self.selected_template_id,),
            )
        else:
            self._execute(
                """
                INSERT INTO print_templates(
                    family_id,template_code,template_name,document_type,paper_size,orientation,print_mode,
                    html_template,css_template,is_default,is_active,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                params,
            )
        QMessageBox.information(self, "Print Template", "Template saved.")
        self.refresh_all()

    def preview_template(self) -> None:
        template = self._current_template_payload()
        if not template["template_code"] or not template["template_name"]:
            QMessageBox.warning(self, "Print Template", "Template code and name are required for preview.")
            return
        output = self.config.project_root / "prints" / f"template_preview_{template['template_code']}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        try:
            write_template_preview_pdf(output, self.source.company(), template)
        except Exception as exc:
            QMessageBox.warning(self, "Print Template", f"Preview could not be created:\n{exc}")
            return
        QMessageBox.information(self, "Print Template", f"Preview PDF created:\n{output}")

    def export_template_files(self) -> None:
        template = self._current_template_payload()
        code = template["template_code"]
        if not code:
            QMessageBox.warning(self, "Print Template", "Template code is required for export.")
            return
        export_dir = self.config.project_root / "print_templates" / "exported" / code
        export_dir.mkdir(parents=True, exist_ok=True)
        html_path = export_dir / f"{code}.html"
        css_path = export_dir / f"{code}.css"
        meta_path = export_dir / f"{code}.txt"
        html_path.write_text(template["html_template"], encoding="utf-8")
        css_path.write_text(template["css_template"], encoding="utf-8")
        meta_path.write_text(
            "\n".join(
                [
                    f"Template: {template['template_name']}",
                    f"Document: {template['document_type']}",
                    f"Paper: {template['paper_size']}",
                    f"Orientation: {template['orientation']}",
                    f"Mode: {template['print_mode']}",
                    f"Exported: {datetime.now().isoformat(timespec='seconds')}",
                ]
            ),
            encoding="utf-8",
        )
        QMessageBox.information(self, "Print Template", f"Template exported:\n{export_dir}")

    def _current_template_payload(self) -> dict[str, Any]:
        return {
            "template_code": self.template_code.text().strip(),
            "template_name": self.template_name.text().strip(),
            "document_type": self.template_document.currentText(),
            "paper_size": self.template_paper.currentText(),
            "orientation": self.template_orientation.currentText(),
            "print_mode": self.template_mode.currentText(),
            "html_template": self.template_html.toPlainText(),
            "css_template": self.template_css.toPlainText(),
        }

    def _reload_roles(self) -> None:
        current = self.role_selector.currentText()
        roles = {row.get("role") for row in self._rows("SELECT DISTINCT role FROM users WHERE COALESCE(role,'')<>''")}
        roles.update(row.get("role_name") for row in self._rows("SELECT DISTINCT role_name FROM role_permissions WHERE COALESCE(role_name,'')<>''"))
        self.role_selector.blockSignals(True)
        self.role_selector.clear()
        self.role_selector.addItems(sorted(str(role) for role in roles if role) or ["Admin"])
        if current:
            self.role_selector.setCurrentText(current)
        self.role_selector.blockSignals(False)
        self.load_permissions(self.role_selector.currentText())

    def load_permissions(self, role: str) -> None:
        allowed = {
            row["permission_key"]: int(row["allowed"] or 0)
            for row in self._rows("SELECT permission_key,allowed FROM role_permissions WHERE role_name=?", (role,))
        }
        for key, check in self.permission_checks.items():
            check.setChecked(bool(allowed.get(key, 1 if role.lower() in {"admin", "administrator"} else 0)))

    def save_permissions(self) -> None:
        role = self.role_selector.currentText().strip() or "Admin"
        with sqlite3.connect(self.db_path) as conn:
            with conn:
                conn.execute("DELETE FROM role_permissions WHERE role_name=?", (role,))
                conn.executemany(
                    "INSERT INTO role_permissions(role_name,permission_key,allowed) VALUES(?,?,?)",
                    [(role, key, 1 if self.permission_checks[key].isChecked() else 0) for key in permission_keys()],
                )
        QMessageBox.information(self, "Permissions", f"Permissions saved for {role}.")
        self.refresh_all()

    def create_backup(self, encrypted: bool) -> None:
        password = self.backup_password.text().strip() if encrypted else ""
        if encrypted and len(password) < 6:
            QMessageBox.warning(self, "Backup", "Encrypted backup password must be at least 6 characters.")
            return
        try:
            path = self.backup_service.create_backup(password=password, tag="developer")
        except Exception as exc:
            QMessageBox.warning(self, "Backup", f"Backup could not be created:\n{exc}")
            return
        QMessageBox.information(self, "Backup", f"Backup created:\n{path}")
        self.refresh_all()

    def choose_restore_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose PRM Backup", str(self.config.project_root / "backups"), "PRM Backups (*.json *.pgst)")
        if path:
            self.restore_file.setText(path)

    def restore_backup(self) -> None:
        if self.restore_confirm.text().strip().upper() != "RESTORE":
            QMessageBox.warning(self, "Restore", "Type RESTORE to confirm.")
            return
        path = Path(self.restore_file.text().strip())
        if not path.exists():
            QMessageBox.warning(self, "Restore", "Choose a valid backup file.")
            return
        try:
            safety = self.backup_service.restore_backup(path, password=self.restore_password.text())
        except Exception as exc:
            QMessageBox.warning(self, "Restore", f"Restore failed:\n{exc}")
            return
        QMessageBox.information(self, "Restore", f"Restore completed. Safety backup:\n{safety}")
        self.refresh_all()

    def free_space(self) -> None:
        from_year = int(self.free_from_year.value())
        to_year = int(self.free_to_year.value())
        if from_year > to_year:
            QMessageBox.warning(self, "Free Space", "From year cannot be greater than To year.")
            return
        confirm = QMessageBox.question(
            self,
            "Confirm Free Space",
            (
                f"This will archive and delete transaction/history rows from {from_year} to {to_year}.\n\n"
                "A full SQLite backup and an Excel export will be created first.\n"
                "Masters, company, license, users, templates and current stock/customer/supplier master balances are retained.\n\n"
                "Continue?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            result = self.maintenance_service.free_space_by_year_range(from_year, to_year, user_name="Developer")
        except Exception as exc:
            QMessageBox.warning(self, "Free Space", f"Free Space failed:\n{exc}")
            return
        self.refresh_all()
        QMessageBox.information(
            self,
            "Free Space Complete",
            (
                f"Backup created:\n{result.backup_path}\n\n"
                f"Excel export created:\n{result.export_path}\n\n"
                f"Rows exported: {result.records_exported}\n"
                f"Rows deleted: {result.records_deleted}\n"
                "SQLite database compacted successfully."
            ),
        )

    def save_email_settings(self) -> None:
        mode = self.email_delivery_mode.currentText().strip() or "handoff"
        host = self.email_smtp_host.text().strip()
        from_email = self.email_smtp_from.text().strip()
        if mode == "smtp" and (not host or not from_email):
            QMessageBox.warning(self, "Communication", "SMTP mode requires SMTP Host and From Email.")
            return
        values: dict[str, object] = {
            "email.delivery_mode": mode,
            "smtp.host": host,
            "smtp.port": self.email_smtp_port.value(),
            "smtp.username": self.email_smtp_username.text().strip(),
            "smtp.from_email": from_email,
            "smtp.use_tls": 1 if self.email_smtp_tls.isChecked() else 0,
            "smtp.use_ssl": 1 if self.email_smtp_ssl.isChecked() else 0,
            "smtp.timeout": self.email_smtp_timeout.value(),
        }
        password = self.email_smtp_password.text()
        if password:
            values["smtp.password"] = protect_secret(password)
        self._save_app_settings(values)
        self.email_smtp_password.clear()
        self.refresh_all()
        QMessageBox.information(self, "Communication", "Email delivery settings saved.")

    def _current_email_config(self) -> SmtpEmailConfig:
        saved = SmtpEmailConfig.from_sources(db_path=self.db_path)
        return SmtpEmailConfig(
            delivery_mode=self.email_delivery_mode.currentText().strip() or "handoff",
            host=self.email_smtp_host.text().strip(),
            port=self.email_smtp_port.value(),
            username=self.email_smtp_username.text().strip(),
            password=self.email_smtp_password.text() or saved.password,
            from_email=self.email_smtp_from.text().strip(),
            use_tls=self.email_smtp_tls.isChecked(),
            use_ssl=self.email_smtp_ssl.isChecked(),
            timeout=float(self.email_smtp_timeout.value()),
        )

    def test_email_delivery_settings(self) -> None:
        result = EmailDeliveryService(self._current_email_config()).test_connection()
        status = "OK" if result.get("ok") else "Check"
        self.comm_delivery_diagnostics.setText(
            f"SMTP {status}: {result.get('code')} - {result.get('message')}"
        )

    def check_whatsapp_delivery_link(self) -> None:
        phone = self.comm_test_whatsapp.text().strip()
        result = whatsapp_readiness(phone, "PRM communication test")
        status = "OK" if result.get("ok") else "Check"
        detail = str(result.get("web_url") or result.get("message") or "")
        self.comm_delivery_diagnostics.setText(f"WhatsApp {status}: {result.get('code')} - {detail}")

    def retry_failed_emails(self) -> None:
        try:
            results = self.communication_service.retry_pending_emails(
                delivery_service=EmailDeliveryService.from_environment(self.db_path),
                limit=10,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Communication", f"Email retry failed:\n{exc}")
            return
        self.refresh_all()
        if not results:
            QMessageBox.information(self, "Communication", "No failed email rows are ready for retry.")
            return
        sent = sum(1 for row in results if row.get("ok"))
        QMessageBox.information(self, "Communication", f"Retried {len(results)} email row(s). Sent: {sent}.")

    def save_communication_template(self) -> None:
        channel = self.comm_template_channel.currentText()
        document_type = self.comm_template_document_type.currentText()
        preferred_contact = self._selected_contact_field()
        payload = {
            "template_code": self.comm_template_code.text(),
            "channel": channel,
            "document_type": document_type,
            "template_name": self.comm_template_name.text(),
            "subject_template": self.comm_template_subject.text(),
            "body_template": self.comm_template_body.toPlainText(),
            "is_active": 1 if self.comm_template_active.isChecked() else 0,
        }
        try:
            template_id = self.communication_template_service.save_template(payload)
            self.communication_template_service.save_contact_preference(channel, document_type, preferred_contact)
        except Exception as exc:
            QMessageBox.warning(self, "Message Templates", f"Template could not be saved:\n{exc}")
            return
        self._refresh_communication_templates()
        QMessageBox.information(self, "Message Templates", f"Template saved.\nID: {template_id}")

    def clear_communication_template_form(self) -> None:
        self.comm_template_code.clear()
        self.comm_template_channel.setCurrentText("email")
        self.comm_template_document_type.setCurrentText("")
        self.comm_template_name.clear()
        self.comm_template_subject.clear()
        self.comm_template_body.clear()
        self.comm_template_active.setChecked(True)
        self.comm_template_preview.clear()
        self._load_contact_preference_for_form()

    def _load_selected_communication_template(self) -> None:
        items = self.communication_template_table.selectedItems()
        if not items:
            return
        row_index = items[0].row()
        id_item = self.communication_template_table.item(row_index, 0)
        if not id_item:
            return
        try:
            template_id = int(id_item.text())
        except ValueError:
            return
        row = next((item for item in self.communication_template_service.templates(500) if int(item.get("id") or 0) == template_id), None)
        if not row:
            return
        self.comm_template_code.setText(str(row.get("template_code") or ""))
        self.comm_template_channel.setCurrentText(str(row.get("channel") or "email"))
        self.comm_template_document_type.setCurrentText(str(row.get("document_type") or ""))
        self.comm_template_name.setText(str(row.get("template_name") or ""))
        self.comm_template_subject.setText(str(row.get("subject_template") or ""))
        self.comm_template_body.setPlainText(str(row.get("body_template") or ""))
        self.comm_template_active.setChecked(bool(int(row.get("is_active") or 0)))
        self._load_contact_preference_for_form()

    def _load_contact_preference_for_form(self, *_args: object) -> None:
        if not hasattr(self, "comm_contact_field"):
            return
        channel = self.comm_template_channel.currentText()
        document_type = self.comm_template_document_type.currentText()
        preferred = self.communication_template_service.contact_preference(channel, document_type) if document_type else ""
        self._refresh_contact_field_options(preferred)

    def _refresh_contact_field_options(self, preferred: str = "") -> None:
        self.comm_contact_field.blockSignals(True)
        self.comm_contact_field.clear()
        self.comm_contact_field.addItem("Auto", "")
        for field in self.communication_template_service.contact_fields(self.comm_template_channel.currentText()):
            self.comm_contact_field.addItem(field.replace("_", " ").title(), field)
        index = self.comm_contact_field.findData(preferred)
        self.comm_contact_field.setCurrentIndex(index if index >= 0 else 0)
        self.comm_contact_field.blockSignals(False)

    def _selected_contact_field(self) -> str:
        data = self.comm_contact_field.currentData()
        return "" if data is None else str(data)

    def _communication_preview_context(self) -> dict[str, object]:
        email = self.comm_preview_email.text().strip()
        mobile = self.comm_preview_mobile.text().strip()
        return {
            "party_name": self.comm_preview_party.text().strip() or "Demo Customer",
            "document_no": self.comm_preview_document_no.text().strip() or "DEMO-001",
            "doc_no": self.comm_preview_document_no.text().strip() or "DEMO-001",
            "amount": self.comm_preview_amount.text().strip() or "Rs 0.00",
            "company_name": str(self.source.company().get("name") or "PRM Billing Inventory"),
            "pdf_path": str(self.config.project_root / "prints" / "sample.pdf"),
            "email": email,
            "customer_email": email,
            "supplier_email": email,
            "party_email": email,
            "billing_email": email,
            "contact_email": email,
            "whatsapp": mobile,
            "whatsapp_no": mobile,
            "mobile": mobile,
            "phone": mobile,
            "customer_phone": mobile,
            "supplier_phone": mobile,
            "party_phone": mobile,
        }

    def preview_communication_template(self) -> None:
        template = {
            "subject_template": self.comm_template_subject.text(),
            "body_template": self.comm_template_body.toPlainText(),
        }
        context = self._communication_preview_context()
        channel = self.comm_template_channel.currentText()
        document_type = self.comm_template_document_type.currentText()
        rendered = self.communication_template_service.render_template(template, context)
        contact = self.communication_template_service.resolve_contact(
            channel,
            context,
            document_type=document_type,
            preferred_field=self._selected_contact_field(),
        )
        contact_text = "Auto"
        if contact.get("value"):
            contact_text = f"{contact.get('field')}: {contact.get('value')}"
        self.comm_contact_result.setText(f"Contact: {contact_text}")
        self.comm_template_preview.setPlainText(
            "\n".join(
                [
                    f"Subject: {rendered.get('subject') or '(No subject)'}",
                    "",
                    rendered.get("body") or "(No body)",
                ]
            )
        )

    def save_setting(self) -> None:
        key = self.setting_key.text().strip()
        value = self.setting_value.text().strip()
        if not key:
            QMessageBox.warning(self, "Settings", "Setting key is required.")
            return
        self._execute(
            """
            INSERT INTO app_settings(setting_key,setting_value,updated_at)
            VALUES(?,?,?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value, updated_at=excluded.updated_at
            """,
            (key, value, datetime.now().isoformat(timespec="seconds")),
        )
        self.setting_key.clear()
        self.setting_value.clear()
        self.refresh_all()
