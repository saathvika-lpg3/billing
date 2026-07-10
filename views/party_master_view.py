from __future__ import annotations

from decimal import Decimal
from typing import Any

from PyQt6.QtCore import Qt, QEvent, QObject
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.master_repository import MasterRepository
from services.mysql_source import MySqlSource
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPToolbar, ERPGrid
from widgets.form_layout_helpers import build_field_section


class PartyMasterView(QWidget):
    def __init__(self, config: AppConfig, party_type: str) -> None:
        super().__init__()
        if party_type not in {"customer", "supplier"}:
            raise ValueError("party_type must be customer or supplier")
        self.config = config
        self.party_type = party_type
        self.table_name = "customers" if party_type == "customer" else "suppliers"
        self.title = "Customer Master" if party_type == "customer" else "Supplier Master"
        self.source = MySqlSource()
        self.repository = MasterRepository(self.source.sqlite_path)
        self.parties: list[dict[str, Any]] = []
        self.form_controls: list[QWidget] = []
        self.current_id = 0
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        root.addWidget(self._title_bar())
        root.addWidget(self._form_card())
        root.addWidget(self._list_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader(
            self.title,
            "GST-ready ledger master | contact, compliance, opening balance, address",
            self,
        )
        self.source_status = header.status_label
        toolbar = ERPToolbar(
            [
                ("New", self.clear_form),
                ("Refresh", self.refresh),
                (f"Save {self.party_type.title()}", self.save_draft),
            ]
        )
        header.layout().addWidget(toolbar)
        return header

    def _prepare_control(self, widget: QWidget, minimum_width: int = 100, fixed_height: int = 32) -> QWidget:
        widget.setMinimumWidth(minimum_width)
        if isinstance(widget, QTextEdit):
            widget.setMinimumHeight(58)
            widget.setMaximumHeight(98)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            widget.setFixedHeight(min(fixed_height, 28))
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if isinstance(widget, QComboBox):
            widget.setMaxVisibleItems(12)
            widget.setMinimumContentsLength(10)
            widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        return widget

    def _field(self, label: str, widget: QWidget, minimum_width: int = 100) -> QWidget:
        self._prepare_control(widget, minimum_width=minimum_width)
        return ERPFieldBox(label, widget, self)

    def _form_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.code = QLineEdit()
        self.code.setPlaceholderText("Required")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Required")
        self.party_type_control = QComboBox()
        self.party_type_control.addItems(["Retail", "Wholesale", "Distributor", "Hospital", "Restaurant", "Government", "Services", "Other"])
        self.status = QComboBox()
        self.status.addItems(["Active", "Inactive", "Hold"])
        self.gstin = QLineEdit()
        self.pan = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.contact = QLineEdit()
        self.city = QLineEdit()
        self.state = QLineEdit("Telangana")
        self.pin_code = QLineEdit()
        self.country = QLineEdit("India")
        self.area = QLineEdit()
        self.place_supply = QLineEdit("Telangana")
        self.balance = QLineEdit("0.00")
        self.balance_type = QComboBox()
        self.balance_type.addItems(["Debit", "Credit"])
        self.credit_limit = QLineEdit("0.00")
        self.gst_treatment = QComboBox()
        self.gst_treatment.addItems(["Regular", "Unregistered", "Composition", "Consumer", "SEZ", "Overseas"])
        self.default_print_format = QComboBox()
        self.default_print_format.addItems(["Auto", "A4 Portrait", "A2 Landscape"])
        self.hsn_code = QLineEdit()
        self.fssai = QLineEdit()
        self.drug_license = QLineEdit()
        self.reverse_charge = QCheckBox("Reverse Charge")
        self.address = QTextEdit()
        self.shipping_address = QTextEdit()
        self.remarks = QTextEdit()

        fields = [
            ("Code", self.code, 180),
            ("Name", self.name, 240),
            (f"{self.title.split()[0]} Type", self.party_type_control, 180),
            ("Status", self.status, 140),
            ("GSTIN", self.gstin, 170),
            ("PAN", self.pan, 130),
            ("Phone / Mobile", self.phone, 150),
            ("Email", self.email, 200),
            ("Contact Person", self.contact, 160),
            ("City", self.city, 140),
            ("State", self.state, 140),
            ("PIN Code", self.pin_code, 110),
            ("Country", self.country, 130),
            ("Area / Route", self.area, 160),
            ("Place of Supply", self.place_supply, 150),
            ("Opening Balance", self.balance, 120),
            ("Balance Type", self.balance_type, 120),
            ("Credit Limit", self.credit_limit, 120),
            ("GST Treatment", self.gst_treatment, 150),
            ("Default Print Format", self.default_print_format, 160),
            ("HSN Code", self.hsn_code, 120),
            ("FSSAI No", self.fssai, 150),
            ("Drug License", self.drug_license, 150),
            ("Reverse Charge", self.reverse_charge, 140),
            ("Remarks", self.remarks, 260),
            ("Billing Address", self.address, 260),
            ("Shipping Address", self.shipping_address, 260),
        ]
        layout.addWidget(build_field_section(fields, spacing=6, margin=0))
        for _, widget, _ in fields:
            self.form_controls.append(widget)

        return frame

    def _list_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        bar = QHBoxLayout()
        title = QLabel(f"{self.title} List")
        title.setObjectName("cardTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search code, name, GSTIN, phone, city, state")
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
            rows = self.source.rows(
                f"""
                SELECT *
                FROM {self.table_name}
                ORDER BY id DESC
                LIMIT 500
                """
            )
            self.parties = rows
            self.source_status.setText(f"Source: {len(rows)} {self.party_type}s")
        except Exception as exc:
            self.parties = []
            self.source_status.setText(f"Source unavailable: {exc}")
        self._redraw_table()
        self._register_hotkeys()
        self._register_form_navigation()

    def _redraw_table(self) -> None:
        query = self.search.text().strip().lower()
        rows = []
        for party in self.parties:
            haystack = " ".join(str(value) for value in party.values()).lower()
            if not query or query in haystack:
                rows.append(party)
        headers = ["id", "code", "name", "customer_type", "gstin", "phone", "city", "state", "balance", "status"]
        if self.party_type == "supplier":
            headers = ["id", "code", "name", "supplier_type", "gstin", "phone", "city", "state", "balance", "status"]
        if not rows:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setItem(0, 0, QTableWidgetItem("No matching records."))
            return
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([self._pretty(header) for header in headers])
        for row_index, row in enumerate(rows):
            for column_index, header in enumerate(headers):
                value = row.get(header, "")
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
            party_id = int(id_item.text())
        except ValueError:
            return
        selected = next((party for party in self.parties if int(party.get("id") or 0) == party_id), None)
        if not selected:
            return
        self.current_id = party_id
        self.code.setText(str(selected.get("code") or ""))
        self.name.setText(str(selected.get("name") or ""))
        party_type_value = str(selected.get("customer_type") or selected.get("supplier_type") or "Retail")
        self.party_type_control.setCurrentText(party_type_value if party_type_value else "Retail")
        self.status.setCurrentText(str(selected.get("status") or "Active"))
        self.gstin.setText(str(selected.get("gstin") or ""))
        self.pan.setText(str(selected.get("pan") or ""))
        self.phone.setText(str(selected.get("phone") or ""))
        self.email.setText(str(selected.get("email") or ""))
        self.contact.setText(str(selected.get("contact_person") or ""))
        self.city.setText(str(selected.get("city") or ""))
        self.state.setText(str(selected.get("state") or ""))
        self.pin_code.setText(str(selected.get("pin_code") or ""))
        self.country.setText(str(selected.get("country") or "India"))
        self.area.setText(str(selected.get("area") or ""))
        self.place_supply.setText(str(selected.get("place_of_supply") or "Telangana"))
        self.balance.setText(self._display(selected.get("balance") or "0.00"))
        self.balance_type.setCurrentText(str(selected.get("balance_type") or "Debit"))
        self.credit_limit.setText(self._display(selected.get("credit_limit") or "0.00"))
        self.gst_treatment.setCurrentText(str(selected.get("gst_treatment") or "Regular"))
        self.default_print_format.setCurrentText(str(selected.get("default_print_format") or "Auto"))
        self.hsn_code.setText(str(selected.get("hsn_code") or ""))
        self.fssai.setText(str(selected.get("fssai_no") or ""))
        self.drug_license.setText(str(selected.get("drug_license_no") or ""))
        self.reverse_charge.setChecked(bool(selected.get("reverse_charge_applicable") or 0))
        self.remarks.setPlainText(str(selected.get("remarks") or ""))
        self.address.setPlainText(str(selected.get("address") or ""))
        self.shipping_address.setPlainText(str(selected.get("shipping_address") or ""))

    def clear_form(self) -> None:
        self.current_id = 0
        for widget in [
            self.code,
            self.name,
            self.gstin,
            self.pan,
            self.phone,
            self.email,
            self.contact,
            self.city,
            self.pin_code,
            self.country,
            self.area,
            self.place_supply,
            self.balance,
            self.credit_limit,
            self.hsn_code,
            self.fssai,
            self.drug_license,
            self.address,
            self.shipping_address,
            self.remarks,
        ]:
            if isinstance(widget, QTextEdit):
                widget.clear()
            else:
                widget.clear()
        self.party_type_control.setCurrentIndex(0)
        self.status.setCurrentText("Active")
        self.state.setText("Telangana")
        self.place_supply.setText("Telangana")
        self.balance_type.setCurrentText("Debit")
        self.gst_treatment.setCurrentIndex(0)
        self.default_print_format.setCurrentText("Auto")
        self.reverse_charge.setChecked(False)
        self.balance.setText("0.00")
        self.credit_limit.setText("0.00")
        self.country.setText("India")
        self.name.setFocus()

    def save_draft(self) -> None:
        payload = {
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "customer_type": self.party_type_control.currentText() if self.party_type_control else "",
            "supplier_type": self.party_type_control.currentText() if self.party_type_control else "",
            "status": self.status.currentText(),
            "gstin": self.gstin.text().strip().upper(),
            "pan": self.pan.text().strip().upper(),
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
            "contact_person": self.contact.text().strip(),
            "area": self.area.text().strip(),
            "city": self.city.text().strip(),
            "state": self.state.text().strip(),
            "pin_code": self.pin_code.text().strip(),
            "country": self.country.text().strip() or "India",
            "place_of_supply": self.place_supply.text().strip(),
            "balance": self.balance.text().strip(),
            "balance_type": self.balance_type.currentText(),
            "credit_limit": self.credit_limit.text().strip(),
            "gst_treatment": self.gst_treatment.currentText(),
            "default_print_format": self.default_print_format.currentText(),
            "hsn_code": self.hsn_code.text().strip(),
            "reverse_charge_applicable": self.reverse_charge.isChecked(),
            "fssai_no": self.fssai.text().strip(),
            "drug_license_no": self.drug_license.text().strip(),
            "address": self.address.toPlainText().strip(),
            "shipping_address": self.shipping_address.toPlainText().strip(),
            "remarks": self.remarks.toPlainText().strip(),
        }
        try:
            saved_id = self.repository.save_party(self.table_name, self.party_type, self.current_id, payload)
        except Exception as exc:
            QMessageBox.warning(self, self.title, f"{self.party_type.title()} could not be saved:\n{exc}")
            return
        self.current_id = saved_id
        self.refresh()
        QMessageBox.information(self, self.title, f"{self.party_type.title()} saved to local database.\nID: {saved_id}")

    def _set_combo_text(self, combo: QComboBox, value: str) -> None:
        index = combo.findText(value)
        if index < 0:
            combo.addItem(value)
            index = combo.findText(value)
        combo.setCurrentIndex(index)

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_draft)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.clear_form)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search.setFocus())
        QShortcut(QKeySequence("Esc"), self, activated=self.clear_form)

    def _register_form_navigation(self) -> None:
        for control in self.form_controls:
            control.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress and isinstance(obj, (QLineEdit, QComboBox, QTextEdit)):
            if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.focusPreviousChild()
                else:
                    self.focusNextChild()
                return True
        return super().eventFilter(obj, event)

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        return "" if value is None else str(value)

    def _pretty(self, value: str) -> str:
        return value.replace("_", " ").strip().title()
