from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.accounting_setup_service import tally_group_names
from services.company_profile_service import CompanyProfileService
from services.master_repository import MasterRepository
from services.mysql_source import MySqlSource
from services.pdf_print import write_report_pdf
from services.print_preview import show_print_preview
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.company_branding import ClientCompanyIdentityCard
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPGrid
from widgets.form_layout_helpers import build_field_section
from widgets.smart_combo import configure_smart_combo
from services.ui_profile_adapter import control_attribute_map_from_profile


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    kind: str = "text"
    options: tuple[str, ...] = ()
    required: bool = False
    width: int = 120
    checked: bool = True
    placeholder: str = ""
    tooltip: str = ""


@dataclass(frozen=True)
class MasterSpec:
    mode: str
    title: str
    subtitle: str
    query: str
    fields: tuple[FieldSpec, ...]
    columns: tuple[str, ...]


MASTER_SPECS: dict[str, MasterSpec] = {
    "category": MasterSpec(
        mode="category",
        title="Category Master",
        subtitle="Item group, default GST, margin and active status",
        query="""
            SELECT id, code, name, default_gst, margin_percent, is_active
            FROM item_categories
            ORDER BY sort_order, name
            LIMIT 500
        """,
        fields=(
            FieldSpec("code", "Code", width=110),
            FieldSpec("name", "Category Name", required=True, width=220),
            FieldSpec("default_gst", "Default GST %", "number", width=100),
            FieldSpec("margin_percent", "Margin %", "number", width=100),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "default_gst", "margin_percent", "is_active"),
    ),
    "brand": MasterSpec(
        mode="brand",
        title="Brand Master",
        subtitle="Brand and manufacturer records used by product master",
        query="""
            SELECT id, master_type, code, name, phone, gstin, is_active
            FROM business_masters
            WHERE master_type IN ('brand','manufacturer')
            ORDER BY id DESC
            LIMIT 500
        """,
        fields=(
            FieldSpec("master_type", "Type", "combo", ("brand", "manufacturer"), required=True, width=120),
            FieldSpec("code", "Code", width=130),
            FieldSpec("name", "Name", required=True, width=240),
            FieldSpec("phone", "Phone", width=130),
            FieldSpec("gstin", "GSTIN", width=160),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "master_type", "code", "name", "phone", "gstin", "is_active"),
    ),
    "unit": MasterSpec(
        mode="unit",
        title="Unit Master",
        subtitle="Sales, purchase and pack unit names",
        query="SELECT id, name, COALESCE(is_active,1) is_active FROM units ORDER BY name LIMIT 500",
        fields=(
            FieldSpec("name", "Unit Name", required=True, width=180),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "name", "is_active"),
    ),
    "gst_rate": MasterSpec(
        mode="gst_rate",
        title="GST Rate Master",
        subtitle="Tax slab rate and display name",
        query="SELECT id, rate, name, is_active FROM tax_slabs ORDER BY rate LIMIT 500",
        fields=(
            FieldSpec("rate", "Rate %", "number", required=True, width=100),
            FieldSpec("name", "Display Name", required=True, width=180),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "rate", "name", "is_active"),
    ),
    "bank": MasterSpec(
        mode="bank",
        title="Bank Master",
        subtitle="Bank accounts used for payments, receipts and reconciliation",
        query="SELECT id, code, name, account_number, ifsc, branch, account_type, opening_balance, is_active FROM banks ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Bank Code", required=True, width=120, placeholder="BNK001", tooltip="Unique bank account identifier."),
            FieldSpec("name", "Bank Name", required=True, width=220, placeholder="ABC Bank"),
            FieldSpec("account_number", "Account Number", required=True, width=200, placeholder="1234567890"),
            FieldSpec("ifsc", "IFSC", width=140, placeholder="ABCD0123456"),
            FieldSpec("branch", "Branch", width=220, placeholder="Main Branch"),
            FieldSpec("account_type", "Account Type", "combo", ("Savings", "Current", "Overdraft", "Cash Credit"), required=True, width=180),
            FieldSpec("opening_balance", "Opening Balance", "number", width=140),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "account_number", "ifsc", "branch", "account_type", "opening_balance", "is_active"),
    ),
    "tax_master": MasterSpec(
        mode="tax_master",
        title="Tax Code Master",
        subtitle="Tax code, HSN/SAC, GST split and effective date",
        query="SELECT id, tax_code, tax_name, hsn_sac, gst_rate, cgst, sgst, igst, cess, effective_from, is_active FROM tax_codes ORDER BY tax_code LIMIT 500",
        fields=(
            FieldSpec("tax_code", "Tax Code", required=True, width=140, placeholder="TAX001"),
            FieldSpec("tax_name", "Tax Name", required=True, width=220, placeholder="GST 18%"),
            FieldSpec("hsn_sac", "HSN/SAC", width=140, placeholder="9983"),
            FieldSpec("gst_rate", "GST Rate %", "number", required=True, width=120),
            FieldSpec("cgst", "CGST %", "number", width=120),
            FieldSpec("sgst", "SGST %", "number", width=120),
            FieldSpec("igst", "IGST %", "number", width=120),
            FieldSpec("cess", "Cess %", "number", width=100),
            FieldSpec("effective_from", "Effective From", width=140, placeholder="YYYY-MM-DD"),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "tax_code", "tax_name", "hsn_sac", "gst_rate", "cgst", "sgst", "igst", "cess", "effective_from", "is_active"),
    ),
    "payment_term": MasterSpec(
        mode="payment_term",
        title="Payment Terms Master",
        subtitle="Credit terms, due date rule and discount guidance",
        query="SELECT id, code, name, credit_days, due_date_rule, discount_percent, is_active FROM payment_terms ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Term Code", required=True, width=120, placeholder="PT001"),
            FieldSpec("name", "Term Name", required=True, width=220, placeholder="Net 30"),
            FieldSpec("credit_days", "Credit Days", "number", width=120, placeholder="30"),
            FieldSpec("due_date_rule", "Due Date Rule", "combo", ("Due on Receipt", "End of Month", "30 Days from Invoice", "45 Days from Invoice", "60 Days from Invoice"), required=True, width=220),
            FieldSpec("discount_percent", "Discount %", "number", width=120, placeholder="0"),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "credit_days", "due_date_rule", "discount_percent", "is_active"),
    ),
    "warehouse": MasterSpec(
        mode="warehouse",
        title="Warehouse Master",
        subtitle="Store locations used for billing, purchase and stock movement",
        query="SELECT w.id, w.code, w.name, b.name branch_name, w.address, w.contact_person, w.phone, w.is_active FROM warehouses w LEFT JOIN branches b ON b.id=w.branch_id ORDER BY w.id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Warehouse Code", required=True, width=120, placeholder="WH001", tooltip="Unique warehouse code for lookup."),
            FieldSpec("name", "Warehouse Name", required=True, width=220, placeholder="Main Store"),
            FieldSpec("branch_id", "Branch", "combo", (), required=True, width=200, tooltip="Select the branch that owns this warehouse."),
            FieldSpec("address", "Address / Location", width=260, placeholder="123 Warehouse Lane"),
            FieldSpec("contact_person", "Contact Person", width=180, placeholder="Mr. Rao"),
            FieldSpec("phone", "Phone", width=140, placeholder="9000000000"),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "branch_name", "address", "contact_person", "phone", "is_active"),
    ),
    "employee": MasterSpec(
        mode="employee",
        title="Employee / User Master",
        subtitle="Staff user records, roles and lock status",
        query="SELECT id, name, email, role, locked, last_login FROM users ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("name", "Name", required=True, width=220),
            FieldSpec("email", "Email / Login", required=True, width=220),
            FieldSpec("password", "Password", "password", width=160),
            FieldSpec("role", "Role", "combo", ("admin", "cashier", "accountant", "salesman", "viewer"), required=True, width=140),
            FieldSpec("locked", "Locked", "check", checked=False),
        ),
        columns=("id", "name", "email", "role", "locked", "last_login"),
    ),
    "branch": MasterSpec(
        mode="branch",
        title="Branch Master",
        subtitle="Branch GST, state and default branch setup",
        query="SELECT id, code, name, address, city, state, pin_code, phone, email, gstin, is_default, is_active FROM branches ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Branch Code", required=True, width=120, placeholder="BR001", tooltip="Unique branch identifier."),
            FieldSpec("name", "Branch Name", required=True, width=220, placeholder="Main Branch"),
            FieldSpec("address", "Address", width=260, placeholder="123 Business St"),
            FieldSpec("city", "City", width=140, placeholder="Hyderabad"),
            FieldSpec("state", "State", width=140, placeholder="Telangana"),
            FieldSpec("pin_code", "PIN", width=120, placeholder="500001"),
            FieldSpec("phone", "Phone", width=140, placeholder="9000000000"),
            FieldSpec("email", "Email", width=180, placeholder="branch@example.com"),
            FieldSpec("gstin", "GSTIN", width=170, placeholder="36AABCDE1234F1Z5"),
            FieldSpec("is_default", "Default", "check", checked=False),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "address", "city", "state", "pin_code", "phone", "email", "gstin", "is_default", "is_active"),
    ),
    "cost_center": MasterSpec(
        mode="cost_center",
        title="Cost Center Master",
        subtitle="Department or profit-center tagging for accounts",
        query="SELECT id, code, name, type, notes, is_active FROM cost_centers ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Cost Center Code", required=True, width=120, placeholder="CC001", tooltip="Unique cost center identifier."),
            FieldSpec("name", "Cost Center Name", required=True, width=240, placeholder="Sales Department"),
            FieldSpec("type", "Type", "combo", ("Department", "Project", "Expense", "Revenue"), required=True, width=160),
            FieldSpec("notes", "Notes", width=260, placeholder="Optional notes or remarks"),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "type", "notes", "is_active"),
    ),
    "route": MasterSpec(
        mode="route",
        title="Route Master",
        subtitle="Routes used for van sales, dispatch and collection planning",
        query="SELECT r.id, r.code, r.name, r.area, COALESCE(s.name,'') salesman_name, COALESCE(v.vehicle_no,'') vehicle_no, r.is_active FROM routes r LEFT JOIN salesmen s ON s.id=r.salesman_id LEFT JOIN vehicles v ON v.id=r.vehicle_id ORDER BY r.id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Route Code", required=True, width=120, placeholder="RT001", tooltip="Unique route identifier."),
            FieldSpec("name", "Route Name", required=True, width=220, placeholder="North Beat"),
            FieldSpec("area", "Area / Beat", width=220, placeholder="North Territory"),
            FieldSpec("salesman_id", "Salesman", "combo", (), width=220, tooltip="Optional salesman assigned to this route."),
            FieldSpec("vehicle_id", "Vehicle", "combo", (), width=220, tooltip="Optional vehicle assigned to this route."),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "area", "salesman_name", "vehicle_no", "is_active"),
    ),
    "salesman": MasterSpec(
        mode="salesman",
        title="Salesman Master",
        subtitle="Route sales and collection personnel records",
        query="SELECT id, code, name, mobile, email, address, is_active FROM salesmen ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Salesman Code", required=True, width=120, placeholder="SM001", tooltip="Unique salesman identifier."),
            FieldSpec("name", "Salesman Name", required=True, width=220, placeholder="Ravi Kumar"),
            FieldSpec("mobile", "Mobile", width=160, placeholder="9000000000"),
            FieldSpec("email", "Email", width=220, placeholder="salesman@example.com"),
            FieldSpec("address", "Address", width=260, placeholder="Local area or beat"),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "mobile", "email", "address", "is_active"),
    ),
    "vehicle": MasterSpec(
        mode="vehicle",
        title="Vehicle Master",
        subtitle="Fleet vehicles used for route delivery and loading",
        query="SELECT id, code, vehicle_no, vehicle_type, driver_name, driver_mobile, capacity, is_active FROM vehicles ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Vehicle Code", required=True, width=120, placeholder="VH001", tooltip="Unique vehicle identifier."),
            FieldSpec("vehicle_no", "Vehicle Number", required=True, width=180, placeholder="TS09AB1234"),
            FieldSpec("vehicle_type", "Vehicle Type", "combo", ("Van", "Truck", "Tempo", "Three-Wheeler"), required=True, width=180),
            FieldSpec("driver_name", "Driver Name", width=200, placeholder="Ramesh"),
            FieldSpec("driver_mobile", "Driver Mobile", width=160, placeholder="9000000000"),
            FieldSpec("capacity", "Capacity", "number", width=120, placeholder="1500"),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "vehicle_no", "vehicle_type", "driver_name", "driver_mobile", "capacity", "is_active"),
    ),
    "transporter": MasterSpec(
        mode="transporter",
        title="Transporter Master",
        subtitle="Transporters used for outward dispatch and logistics",
        query="SELECT id, code, name, gstin, mobile, address, is_active FROM transporters ORDER BY id DESC LIMIT 500",
        fields=(
            FieldSpec("code", "Transporter Code", required=True, width=120, placeholder="TP001", tooltip="Unique transporter identifier."),
            FieldSpec("name", "Transporter Name", required=True, width=240, placeholder="ABC Transport"),
            FieldSpec("gstin", "GSTIN", width=180, placeholder="36AABCDE1234F1Z5"),
            FieldSpec("mobile", "Mobile", width=160, placeholder="9000000000"),
            FieldSpec("address", "Address", width=280, placeholder="Transport depot address"),
            FieldSpec("is_active", "Active", "check"),
        ),
        columns=("id", "code", "name", "gstin", "mobile", "address", "is_active"),
    ),
    "ledger": MasterSpec(
        mode="ledger",
        title="Ledger Head Master",
        subtitle="Tally-style ledger heads used by vouchers, receipts and payments",
        query="SELECT id, name, group_name, opening_dr, opening_cr, is_system FROM account_ledgers ORDER BY group_name, name LIMIT 800",
        fields=(
            FieldSpec("name", "Ledger Name", required=True, width=240),
            FieldSpec("group_name", "Tally Group", "combo", tally_group_names(), required=True, width=190),
            FieldSpec("opening_dr", "Opening Dr", "number", width=120),
            FieldSpec("opening_cr", "Opening Cr", "number", width=120),
            FieldSpec("is_system", "System", "check", checked=False),
        ),
        columns=("id", "name", "group_name", "opening_dr", "opening_cr", "is_system"),
    ),
    "company": MasterSpec(
        mode="company",
        title="Company Settings",
        subtitle="Primary company, GST, contact and invoice identity",
        query="SELECT id, name, business_name, logo_path, business_type_code, gstin, pan, fssai_no, drug_license_no, phone, email, city, state, invoice_prefix, upi_id FROM company ORDER BY id LIMIT 20",
        fields=(
            FieldSpec("name", "Company Name", required=True, width=240),
            FieldSpec("business_name", "Business Name", width=220),
            FieldSpec("gstin", "GSTIN", width=170),
            FieldSpec("pan", "PAN", width=150),
            FieldSpec("fssai_no", "FSSAI No", width=160),
            FieldSpec("drug_license_no", "Drug License", width=170),
            FieldSpec("business_type_code", "Business Type", width=190),
            FieldSpec("phone", "Phone", width=130),
            FieldSpec("email", "Email", width=180),
            FieldSpec("invoice_prefix", "Invoice Prefix", width=120),
        ),
        columns=("id", "name", "business_name", "business_type_code", "gstin", "pan", "fssai_no", "drug_license_no", "phone", "email", "city", "state", "invoice_prefix", "upi_id"),
    ),
}


class SimpleMasterView(QWidget):
    def __init__(self, config: AppConfig, mode: str) -> None:
        super().__init__()
        if mode not in MASTER_SPECS:
            raise ValueError(f"Unknown master mode: {mode}")
        self.config = config
        self.spec = MASTER_SPECS[mode]
        self.source = MySqlSource()
        self.repository = MasterRepository(self.source.sqlite_path)
        self.rows: list[dict[str, Any]] = []
        self.controls: dict[str, QWidget] = {}
        self.current_id = 0
        self._build()
        self._register_hotkeys()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._action_toolbar())
        root.addWidget(self._form_card())
        root.addWidget(self._list_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader(self.spec.title, self.spec.subtitle)
        self.source_status = header.status_label
        return header

    def _action_toolbar(self) -> CompactActionToolbar:
        self.action_toolbar = CompactActionToolbar(
            [
                ActionSpec("New", self.clear_form, "Clear the form and start a new record. Ctrl+N", role="positive"),
                ActionSpec(
                    f"Save {self.spec.title.replace(' Master', '')}",
                    self.save_draft,
                    "Validate and save this master record. Ctrl+S / F8",
                    role="primary",
                ),
                ActionSpec("Refresh", self.refresh, "Reload the current master list."),
                ActionSpec("Print", self.print_list, "Print the visible master rows. Ctrl+P"),
            ]
        )
        return self.action_toolbar

    def _form_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        if self.spec.mode == "company":
            self.company_brand = ClientCompanyIdentityCard(self.config)
            layout.addWidget(self.company_brand)

        fields: list[tuple[str, QWidget, int]] = []
        for field in self.spec.fields:
            control = self._make_control(field)
            self.controls[field.key] = control
            # If this is the company admin view, hide or readonly restricted fields
            if self.spec.mode == "company" and field.key in {"gstin", "fssai_no", "drug_license_no", "business_type_code", "invoice_template_code", "subscription_plan_code", "license_key", "installation_key"}:
                # Show read-only and tooltip
                if isinstance(control, QLineEdit):
                    control.setReadOnly(True)
                    control.setToolTip("Managed by Developer Dashboard")
                if isinstance(control, QComboBox):
                    control.setEnabled(False)
                    control.setToolTip("Managed by Developer Dashboard")
            fields.append((field.label, control, field.width))

        layout.addWidget(build_field_section(fields, spacing=6, margin=0))
        # build a simple mapping of control keys to widgets for the profile adapter runner
        try:
            self._profile_widget_map = {key: widget for key, widget in self.controls.items()}
        except Exception:
            self._profile_widget_map = {}
        return frame

    def _make_control(self, field: FieldSpec) -> QWidget:
        if field.kind == "combo":
            control = QComboBox()
            if field.options:
                control.addItems(list(field.options))
            control.setMaxVisibleItems(12)
            configure_smart_combo(control)
        elif field.kind == "check":
            control = QCheckBox(field.label)
            control.setChecked(field.checked)
        else:
            control = QLineEdit()
            if field.kind == "password":
                control.setEchoMode(QLineEdit.EchoMode.Password)
            if field.placeholder:
                control.setPlaceholderText(field.placeholder)
        control.setMinimumWidth(field.width)
        if field.tooltip:
            control.setToolTip(field.tooltip)
        if not isinstance(control, QCheckBox):
            control.setFixedHeight(28)
            control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return control

    def _populate_combo_fields(self) -> None:
        for field in self.spec.fields:
            if field.kind != "combo":
                continue
            control = self.controls[field.key]
            control.clear()
            if field.key == "branch_id":
                branches = self.source.branches()
                for branch in branches:
                    branch_id = int(branch.get("id") or 0)
                    branch_name = str(branch.get("name") or "")
                    control.addItem(branch_name, branch_id)
                if control.count() == 0:
                    control.addItem("No branches available", 0)
            elif field.key == "salesman_id":
                salesmen = self.source.salesmen()
                for salesman in salesmen:
                    salesman_id = int(salesman.get("id") or 0)
                    salesman_label = f"{salesman.get('code') or ''} | {salesman.get('name') or ''}".strip(" | ")
                    control.addItem(salesman_label, salesman_id)
                if control.count() == 0:
                    control.addItem("No salesmen available", 0)
            elif field.key == "vehicle_id":
                vehicles = self.source.vehicles()
                for vehicle in vehicles:
                    vehicle_id = int(vehicle.get("id") or 0)
                    vehicle_label = f"{vehicle.get('code') or ''} | {vehicle.get('vehicle_no') or ''}".strip(" | ")
                    control.addItem(vehicle_label, vehicle_id)
                if control.count() == 0:
                    control.addItem("No vehicles available", 0)

    def _field(self, label: str, widget: QWidget, minimum_width: int) -> QWidget:
        box = QFrame()
        box.setObjectName("fieldBox")
        box.setMinimumHeight(46)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        if isinstance(widget, QCheckBox):
            spacer = QLabel("")
            spacer.setObjectName("fieldLabel")
            layout.addWidget(spacer)
            layout.addWidget(widget)
        else:
            label_widget = QLabel(label)
            label_widget.setObjectName("fieldLabel")
            layout.addWidget(label_widget)
            layout.addWidget(widget)
        widget.setMinimumWidth(minimum_width)
        return box

    def _list_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        bar = QHBoxLayout()
        title = QLabel(f"{self.spec.title} List")
        title.setObjectName("cardTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search current master rows")
        self.search.textChanged.connect(self._redraw_table)
        bar.addWidget(title)
        bar.addStretch(1)
        bar.addWidget(self.search)
        layout.addLayout(bar)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self.load_selected_row)
        layout.addWidget(self.table, stretch=1)
        return frame

    def refresh(self) -> None:
        try:
            self.repository.ensure_schema()
            self.rows = self.source.rows(self.spec.query)
            self._populate_combo_fields()
            self.source_status.setText(f"Source: {len(self.rows)} rows")
        except Exception as exc:
            self.rows = []
            self.source_status.setText(f"Source unavailable: {exc}")
        self._redraw_table()
        if self.spec.mode == "company" and hasattr(self, "company_brand"):
            try:
                self.company_brand.set_company(CompanyProfileService(self.source.sqlite_path).current_profile())
            except Exception:
                self.company_brand.set_company({})
        # Apply profile-driven control attributes where applicable
        try:
            company = self.source.company() or {}
            profile_code = str(company.get("business_type_code") or company.get("business_type") or "distributor_wholesale")
            # Map master field keys to adapter keys where sensible
            master_to_adapter = {
                "default_gst": "gst",
                "gst_rate": "gst",
                "gstin": "gst",
                "hsn_sac": "hsn",
                "rate": "rate",
                "mrp": "mrp",
                "unit": "unit",
                "warehouse": "warehouse",
                "branch_id": "branch",
                "area": "area",
                "code": "product",
                "name": "product",
            }
            keys = []
            for k in self.controls.keys():
                mapped = master_to_adapter.get(k) or k
                keys.append(mapped)
            control_map = control_attribute_map_from_profile(profile_code, keys)
            for field_key, widget in self.controls.items():
                adapter_key = master_to_adapter.get(field_key) or field_key
                attrs = control_map.get(adapter_key)
                if not attrs:
                    continue
                try:
                    # Apply visibility/enable and a required placeholder where supported
                    if hasattr(widget, "setVisible"):
                        widget.setVisible(bool(attrs.get("visible", True)))
                    if hasattr(widget, "setEnabled"):
                        widget.setEnabled(bool(attrs.get("enabled", True)))
                    if attrs.get("required"):
                        try:
                            from services.ui_adapter_runner import apply_profile_to_widgets

                            # if we have a mapping available on this view, use runner
                            widget_map = getattr(self, "_profile_widget_map", None)
                            if widget_map:
                                apply_profile_to_widgets(company_profile_code, widget_map)
                            else:
                                from widgets.form_layout_helpers import mark_widget_required

                                mark_widget_required(widget)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    def _redraw_table(self) -> None:
        query = self.search.text().strip().lower()
        rows = []
        for row in self.rows:
            haystack = " ".join(str(value) for value in row.values()).lower()
            if not query or query in haystack:
                rows.append(row)
        if not rows:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setItem(0, 0, QTableWidgetItem("No matching records."))
            return
        self.table.setColumnCount(len(self.spec.columns))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([self._pretty(column) for column in self.spec.columns])
        for row_index, row in enumerate(rows):
            for column_index, column in enumerate(self.spec.columns):
                value = row.get(column, "")
                item = QTableWidgetItem(self._display(value))
                if isinstance(value, (int, float, Decimal)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column_index, item)
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def load_selected_row(self, row: int, _column: int) -> None:
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        try:
            selected_id = int(id_item.text())
        except ValueError:
            return
        selected = next((item for item in self.rows if int(item.get("id") or 0) == selected_id), None)
        if not selected:
            return
        self.current_id = selected_id
        for field in self.spec.fields:
            self._set_control_value(field, selected.get(field.key))
        if self.spec.mode == "company" and hasattr(self, "company_brand"):
            self.company_brand.set_company(selected)

    def clear_form(self) -> None:
        self.current_id = 0
        for field in self.spec.fields:
            control = self.controls[field.key]
            if isinstance(control, QLineEdit):
                control.clear()
            elif isinstance(control, QComboBox):
                control.setCurrentIndex(0)
            elif isinstance(control, QCheckBox):
                control.setChecked(field.checked)
        first = self.controls[self.spec.fields[0].key]
        first.setFocus()

    def save_draft(self) -> None:
        data: dict[str, Any] = {}
        for field in self.spec.fields:
            value = self._control_value(field)
            if field.required and str(value).strip() == "":
                QMessageBox.warning(self, self.spec.title, f"{field.label} is required.")
                self.controls[field.key].setFocus()
                return
            if field.kind == "number":
                try:
                    value = float(str(value or 0).replace(",", ""))
                except ValueError:
                    QMessageBox.warning(self, self.spec.title, f"{field.label} must be numeric.")
                    self.controls[field.key].setFocus()
                    return
            data[field.key] = value
        try:
            saved_id = self.repository.save_simple(self.spec.mode, self.current_id, data)
        except Exception as exc:
            QMessageBox.warning(self, self.spec.title, f"Record could not be saved:\n{exc}")
            return
        self.current_id = saved_id
        self.refresh()
        QMessageBox.information(self, self.spec.title, f"Saved to local database.\nID: {saved_id}")

    def _control_value(self, field: FieldSpec) -> Any:
        control = self.controls[field.key]
        if isinstance(control, QLineEdit):
            return control.text().strip()
        if isinstance(control, QComboBox):
            data = control.currentData()
            if data is not None:
                return data
            return control.currentText()
        if isinstance(control, QCheckBox):
            return control.isChecked()
        return ""

    def print_list(self) -> None:
        query = self.search.text().strip().lower()
        rows = [
            row
            for row in self.rows
            if not query or query in " ".join(str(value) for value in row.values()).lower()
        ]
        if not rows:
            QMessageBox.information(self, self.spec.title, "No visible rows to print.")
            return
        columns = [column for column in self.spec.columns if column.lower() != "id"]
        payload = [{column: row.get(column, "") for column in columns} for row in rows]
        path = self.config.project_root / "reports" / f"{self.spec.mode}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        try:
            write_report_pdf(
                path,
                f"{self.spec.title} List",
                self.source.company(),
                payload,
                {"Search": self.search.text().strip(), "Rows": len(payload)},
                db_path=self.source.sqlite_path,
                document_type="report",
            )
        except Exception as exc:
            QMessageBox.warning(self, self.spec.title, f"List print failed:\n{exc}")
            return
        show_print_preview(self, path, f"{self.spec.title} List Print Preview")

    def _set_control_value(self, field: FieldSpec, value: Any) -> None:
        control = self.controls[field.key]
        if isinstance(control, QLineEdit):
            control.setText(self._display(value))
        elif isinstance(control, QComboBox):
            index = -1
            if isinstance(value, (int, float)):
                index = control.findData(int(value))
            if index < 0:
                text = self._display(value)
                index = control.findText(text)
            if index < 0 and str(value).strip():
                control.addItem(self._display(value), value if isinstance(value, int) else None)
                index = control.findText(self._display(value))
            control.setCurrentIndex(index if index >= 0 else 0)
        elif isinstance(control, QCheckBox):
            control.setChecked(self._truthy(value))

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        return "" if value is None else str(value)

    def _pretty(self, value: str) -> str:
        return value.replace("_", " ").strip().title()

    def _truthy(self, value: Any) -> bool:
        if isinstance(value, str):
            return value.strip().lower() not in {"", "0", "false", "no", "inactive"}
        return bool(value)

    def _register_hotkeys(self) -> None:
        shortcuts = (
            ("Ctrl+N", self.clear_form),
            ("Ctrl+S", self.save_draft),
            ("F8", self.save_draft),
            ("Ctrl+P", self.print_list),
            ("F10", self.print_list),
            ("Ctrl+F", lambda: self.search.setFocus()),
            ("F3", lambda: self.search.setFocus()),
            ("Esc", self.clear_form),
        )
        self._shortcuts = []
        for sequence, handler in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)
