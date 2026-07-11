
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.business_rules import validate_item_line
from services.mysql_source import MySqlSource
from services.pdf_print import document_share_caption, write_transaction_pdf
from services.print_preview import show_print_preview
from services.sales_calculator import ComputedLine, SalesCalculator, SalesLine, money
from services.share_service import (
    communication_message,
    document_message_context,
    open_whatsapp_share,
    pdf_share_note,
    prepare_email_document,
    prepare_whatsapp_document,
)
from services.transaction_repository import TransactionRepository
from services.ui_profile_adapter import control_attribute_map_from_profile
from widgets.erp_components import (
    ERPFieldBox,
    ERPItemGrid,
    ProductSearchCard,
    TransactionDetailsDeck,
    TransactionHeader,
    TransactionGridPanel,
    TransactionPageLayout,
    TransactionSectionCard,
    TransactionSummaryDeck,
    TransactionTaxSummaryPanel,
    TransactionTotalsPanel,
    TransactionToolbar,
)

logger = logging.getLogger(__name__)


class SalesBillView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.repository = TransactionRepository(self.source.sqlite_path)
        self.company: dict[str, Any] = {}
        self.customers: list[dict[str, Any]] = []
        self.products: list[dict[str, Any]] = []
        self.warehouses: list[dict[str, Any]] = []
        self.branches: list[dict[str, Any]] = []
        self.product_by_label: dict[str, dict[str, Any]] = {}
        self.customer_by_label: dict[str, dict[str, Any]] = {}
        self.warehouse_by_name: dict[str, dict[str, Any]] = {}
        self.branch_by_name: dict[str, dict[str, Any]] = {}
        self.computed_lines = []
        self.editing_sale_id: int | None = None
        self.units: list[str] = []
        self._updating_table = False
        self.employee_text = ""
        self.area_text = ""
        self.warehouse_text = ""
        self.branch_text = ""
        self.cost_center_text = ""
        self.shipping_text = ""
        self.po_no_text = ""
        self.transport_text = ""
        self.credit_terms_text = ""
        self._build()
        self._load_source_data()
        self._register_hotkeys()

    def _build(self) -> None:
        page = TransactionPageLayout(self)
        page.add_header(self._title_bar())
        page.add_toolbar(self._action_toolbar())
        page.add_section(self._header_card())
        page.add_section(self._item_entry_card())
        page.add_grid(self._line_table())
        page.add_summary(self._summary_card())

    def _title_bar(self) -> QWidget:
        header = TransactionHeader(
            "Sales Bill",
            "Desktop sales entry | F4 add row | Ctrl+S draft | Del delete row | dblclick to edit values",
            self,
        )
        self.source_status = header.status_label
        return header

    def _prepare_control(self, widget: QWidget, minimum_width: int = 96, fixed_height: int = 28) -> QWidget:
        widget.setMinimumWidth(min(minimum_width, 120))
        if not isinstance(widget, QTextEdit):
            widget.setFixedHeight(fixed_height)
        else:
            widget.setMinimumHeight(min(fixed_height, 48))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if isinstance(widget, QComboBox):
            widget.setMaxVisibleItems(18)
            widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 8))
            widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        return widget

    def _field(self, label: str, widget: QWidget, minimum_width: int = 120) -> QWidget:
        self._prepare_control(widget, minimum_width=minimum_width)
        return ERPFieldBox(label, widget, self)

    def _action_toolbar(self) -> QWidget:
        return TransactionToolbar(
            [
                ("New", self.clear_bill),
                ("Save", self.save_draft),
                ("Preview", self.print_draft_pdf),
                ("Print", self.print_draft_pdf),
                ("PDF", self.print_draft_pdf),
                ("WhatsApp", self.share_draft_whatsapp),
                ("Email", self.email_draft_pdf),
                ("Close", self.close),
                ("Delete", self.remove_selected_line),
            ],
            self,
        )

    def _header_card(self) -> QWidget:
        host = TransactionDetailsDeck(self)
        self.bill_no = QLineEdit(f"DSK-{date.today():%y%m%d}-0001")
        self.bill_date = QDateEdit()
        self.bill_date.setCalendarPopup(True)
        self.bill_date.setDisplayFormat("dd/MM/yyyy")
        self.bill_date.setDate(QDate.currentDate())
        self.employee = QComboBox(host)
        self.area = QComboBox(host)
        self.area.setEditable(True)
        self.area.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer = QComboBox(host)
        self.customer.setEditable(True)
        self.customer.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.warehouse = QComboBox(host)
        self.branch = QComboBox(host)
        self.cost_center = QComboBox(host)
        for advanced_control in (self.employee, self.warehouse, self.branch, self.cost_center):
            advanced_control.hide()
        self.payment = QComboBox(host)
        self.payment.addItems(["Cash", "UPI", "Card", "Credit", "Bank"])
        self.price_level = QComboBox(host)
        self.price_level.addItems(["Distributor", "Wholesale", "Retail", "Dealer", "MRP"])
        self.supplier_filter = QComboBox(host)
        self.supplier_filter.setEditable(True)
        self.supplier_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.details_btn = QPushButton("More Details")
        self.details_btn.setMinimumHeight(28)
        self.details_btn.clicked.connect(self.open_more_details)
        self.document_status = QLabel("New")
        self.document_status.setObjectName("caption")
        self.document_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.print_template = self._print_template_selector()

        party_card, party_grid = self._header_section("Customer Information", "customer")
        party_grid.addWidget(self._field("Customer *", self.customer, 260), 0, 0, 1, 2)
        party_grid.addWidget(self._field("Area / Beat", self.area, 180), 1, 0)
        party_grid.addWidget(self._field("Payment", self.payment, 120), 1, 1)

        detail_card, detail_grid = self._header_section("Other Details", "document")
        detail_grid.addWidget(self._field("Bill No", self.bill_no, 140), 0, 0)
        detail_grid.addWidget(self._field("Date", self.bill_date, 120), 0, 1)
        detail_grid.addWidget(self._field("Price Level", self.price_level, 130), 1, 0, 1, 2)

        info_card, info_grid = self._header_section("Additional Information", "additional")
        info_grid.addWidget(self._field("Status", self.document_status, 100), 0, 0)
        info_grid.addWidget(self._field("Document Details", self.details_btn, 140), 0, 1)
        info_grid.addWidget(self._field("Print Template", self.print_template, 180), 1, 0, 1, 2)

        host.add_card(party_card, stretch=2)
        host.add_card(detail_card, stretch=2)
        host.add_card(info_card, stretch=3)
        self.customer.currentTextChanged.connect(self._customer_changed)
        self.area.currentTextChanged.connect(lambda text: setattr(self, "area_text", text.strip()))
        return host

    def _header_section(self, title: str, role: str) -> tuple[QWidget, QGridLayout]:
        card = TransactionSectionCard(role)
        card.setMinimumHeight(108)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(5)
        heading = QLabel(title)
        heading.setObjectName("cardTitle")
        layout.addWidget(heading)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(5)
        layout.addLayout(grid)
        return card, grid

    def _print_template_selector(self) -> QComboBox:
        selector = QComboBox()
        selector.setMinimumWidth(120)
        try:
            import sqlite3

            with sqlite3.connect(self.source.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT DISTINCT template_code, template_name FROM print_templates "
                    "WHERE COALESCE(is_active,1)=1 ORDER BY template_name"
                ).fetchall()
            items = [f"{row['template_name']} ({row['template_code']})" for row in rows]
            current_code = str(self.company.get("invoice_template_code") or "")
            if current_code:
                items.insert(0, f"Company ({current_code})")
            selector.addItems(items or ["Default"])
        except Exception:
            selector.addItem("Default")
        return selector

    def _item_entry_card(self) -> QWidget:
        frame = ProductSearchCard()
        frame.setMinimumHeight(112)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        self.product = QComboBox()
        self.product.setEditable(False)
        self.product.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.hsn = QLineEdit()
        self.qty = QLineEdit("1")
        self.free_qty = QLineEdit("0")
        self.unit = QComboBox()
        self.unit.setEditable(False)
        self.unit.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mrp = QLineEdit("0")
        self.rate = QLineEdit("0")
        self.scheme = QLineEdit("0")
        self.discount = QLineEdit("0")
        self.gst = QComboBox()
        self.gst.setEditable(False)
        self.gst.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.add_row_btn = QPushButton("Add Item Row  F4")
        self.add_row_btn.setMinimumHeight(28)
        self.add_row_btn.clicked.connect(self.add_line)
        grid.addWidget(self._field("Product Search", self.product, 440), 0, 0, 1, 5)
        grid.addWidget(self._field("Supplier / Brand", self.supplier_filter, 150), 0, 5, 1, 2)
        grid.addWidget(self._field("HSN", self.hsn, 76), 0, 7)
        grid.addWidget(self._field("Qty", self.qty, 74), 1, 0)
        grid.addWidget(self._field("Unit", self.unit, 78), 1, 1)
        grid.addWidget(self._field("MRP", self.mrp, 90), 1, 2)
        grid.addWidget(self._field("Rate", self.rate, 90), 1, 3)
        grid.addWidget(self._field("SCH", self.free_qty, 74), 1, 4)
        grid.addWidget(self._field("Disc Rs", self.discount, 90), 1, 5)
        grid.addWidget(self._field("GST %", self.gst, 80), 1, 6)
        grid.addWidget(self.add_row_btn, 1, 7)
        grid.setColumnStretch(0, 2)
        for col in range(1, 8):
            grid.setColumnStretch(col, 1)
        self.product.currentTextChanged.connect(self._product_changed)
        return frame

    def open_more_details(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Sales Bill - More Details")
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        employee = QComboBox(dialog)
        employee.addItems([self.employee.itemText(i) for i in range(self.employee.count())])
        employee.setCurrentText(self.employee_text or self.employee.currentText())
        area = QComboBox(dialog)
        area.addItems([self.area.itemText(i) for i in range(self.area.count())])
        area.setCurrentText(self.area_text or self.area.currentText())
        warehouse = QComboBox(dialog)
        warehouse.addItems([self.warehouse.itemText(i) for i in range(self.warehouse.count())])
        warehouse.setCurrentText(self.warehouse_text or self.warehouse.currentText())
        branch = QComboBox(dialog)
        branch.addItems([self.branch.itemText(i) for i in range(self.branch.count())])
        branch.setCurrentText(self.branch_text or self.branch.currentText())
        cost_center = QComboBox(dialog)
        cost_center.addItems([self.cost_center.itemText(i) for i in range(self.cost_center.count())])
        cost_center.setCurrentText(self.cost_center_text or self.cost_center.currentText())
        po_no = QLineEdit(self.po_no_text, dialog)
        transport = QLineEdit(self.transport_text, dialog)
        credit_terms = QLineEdit(self.credit_terms_text, dialog)
        shipping = QTextEdit(dialog)
        shipping.setMinimumHeight(55)
        shipping.setMaximumHeight(90)
        shipping.setPlainText(self.shipping_text)
        form.addRow("Employee", employee)
        form.addRow("Area / Route", area)
        form.addRow("Warehouse", warehouse)
        form.addRow("Branch", branch)
        form.addRow("Cost Center", cost_center)
        form.addRow("PO Number", po_no)
        form.addRow("Transport", transport)
        form.addRow("Credit Terms", credit_terms)
        form.addRow("Ship To Address", shipping)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.employee_text = employee.currentText().strip()
            self.area_text = area.currentText().strip()
            self.warehouse_text = warehouse.currentText().strip()
            self.branch_text = branch.currentText().strip()
            self.cost_center_text = cost_center.currentText().strip()
            self.po_no_text = po_no.text().strip()
            self.transport_text = transport.text().strip()
            self.credit_terms_text = credit_terms.text().strip()
            self.shipping_text = shipping.toPlainText().strip()
            suffix = "set" if any((self.employee_text, self.area_text, self.warehouse_text, self.branch_text, self.cost_center_text, self.po_no_text, self.transport_text, self.credit_terms_text, self.shipping_text)) else "empty"
            self.details_btn.setText(f"More Details ({suffix})")

    def _line_table(self) -> QWidget:
        self.table = ERPItemGrid(0, 12)
        headers = ["#", "Item Description", "HSN", "Qty", "Unit", "MRP", "Rate", "SCH", "Disc", "Taxable", "GST", "Amount"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setMinimumHeight(60)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._line_table_item_changed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        editable_columns = {3, 4, 5, 6, 7, 8, 10}
        self.table.set_editable_columns(editable_columns)
        for col, width in {0: 46, 1: 260, 2: 90, 3: 85, 4: 85, 5: 90, 6: 95, 7: 95, 8: 95, 9: 110, 10: 85, 11: 115}.items():
            self.table.setColumnWidth(col, width)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.set_command_handlers(
            {
                "add_row": self.add_line,
                "product_search": lambda: self.product.setFocus(),
                "save": self.save_draft,
                "preview": self.print_draft_pdf,
                "print": self.print_draft_pdf,
                "remove_row": self.remove_selected_line,
            }
        )
        return TransactionGridPanel(
            self.table,
            {
                "add_row": self.add_line,
                "delete_row": self.remove_selected_line,
                "import": None,
                "scan_barcode": lambda: self.product.setFocus(),
            },
            parent=self,
        )

    def _summary_card(self) -> QWidget:
        deck = TransactionSummaryDeck(self)
        self.totals_panel = TransactionTotalsPanel()
        self.tax_summary_panel = TransactionTaxSummaryPanel()
        self.total_summary = self.totals_panel.labels["grand_total"]
        deck.add_card(self.totals_panel, stretch=5)
        deck.add_card(self.tax_summary_panel, stretch=2)
        return deck

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("F4"), self, activated=self.add_line)
        QShortcut(QKeySequence("Alt+B"), self, activated=lambda: self.product.setFocus())
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_draft)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.print_draft_pdf)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.share_draft_whatsapp)
        QShortcut(QKeySequence("Delete"), self, activated=self.remove_selected_line)

    def _load_source_data(self) -> None:
        try:
            self.company = self.source.company()
            self.customers = self.source.customers()
            self.products = self.source.product_choices()
            users = self.source.users()
            self.warehouses = self.source.warehouses()
            self.branches = self.source.branches()
            cost_centers = self.source.cost_centers()
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            return
        self.employee.addItems([f"{u.get('name', u.get('username', ''))} - {u.get('role','')}" for u in users] or ["Administrator"])
        self.warehouse_by_name = {str(row.get("name") or ""): row for row in self.warehouses}
        self.branch_by_name = {str(row.get("name") or ""): row for row in self.branches}
        self.warehouse.addItems(list(self.warehouse_by_name) or ["Main Store"])
        self.branch.addItems(list(self.branch_by_name) or ["Main Branch"])
        self.cost_center.addItems([c.get("name", "") for c in cost_centers] or ["No Cost Center"])
        areas = sorted({str(c.get("area") or "") for c in self.customers if c.get("area")})
        self.area.addItems(["All Areas", *areas])
        customer_labels = [f"{c.get('name','')} | {c.get('area','')} | Due {float(c.get('balance') or 0):.2f}" for c in self.customers]
        self.customer_by_label = dict(zip(customer_labels, self.customers))
        units = self.source.units()
        self.units = [str(u.get("name") or "").strip() for u in units if str(u.get("name") or "").strip()] or ["PCS"]
        self.unit.clear()
        self.unit.addItems(self.units)
        gst_rates = self.source.tax_slabs()
        self.gst_rates = [str(r.get("rate") or "0").strip() for r in gst_rates]
        self.gst.clear()
        self.gst.addItems(self.gst_rates if self.gst_rates else ["0"])
        self.customer.addItems(["Select Customer", *customer_labels])
        customer_completer = self.customer.completer()
        if customer_completer:
            customer_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            customer_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        areas = sorted({str(c.get("area") or "") for c in self.customers if c.get("area")})
        self.area.addItems(["All Areas", *areas])
        area_completer = self.area.completer()
        if area_completer:
            area_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            area_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        suppliers = sorted({str(p.get("supplier_name") or "") for p in self.products if p.get("supplier_name")})
        self.supplier_filter.addItems(["All Products", *suppliers])
        supplier_filter_completer = self.supplier_filter.completer()
        if supplier_filter_completer:
            supplier_filter_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            supplier_filter_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        product_labels = [self._product_label(p) for p in self.products]
        self.product_by_label = dict(zip(product_labels, self.products))
        self.product.addItems(product_labels)
        completer = self.product.completer()
        if completer:
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.employee_text = self.employee.currentText()
        self.area_text = self.area.currentText()
        self.warehouse_text = self.warehouse.currentText()
        self.branch_text = self.branch.currentText()
        self.cost_center_text = self.cost_center.currentText()
        self.source_status.setText(f"{len(self.customers)} customers | {len(self.products)} packs")
        # Apply profile-driven control attributes (visibility/required/enabled)
        try:
            profile_code = str(self.company.get("business_type_code") or self.company.get("business_type") or "distributor_wholesale")
            control_map = control_attribute_map_from_profile(profile_code, [
                "product",
                "hsn",
                "qty",
                "free_qty",
                "unit",
                "mrp",
                "rate",
                "scheme",
                "discount",
                "gst",
                "warehouse",
                "branch",
                "cost_center",
                "employee",
                "area",
            ])
            # map adapter keys to widgets
            widget_map = {
                "product": self.product,
                "hsn": self.hsn,
                "qty": self.qty,
                "free_qty": self.free_qty,
                "unit": self.unit,
                "mrp": self.mrp,
                "rate": self.rate,
                "scheme": self.free_qty,  # alias: scheme -> free_qty
                "discount": self.discount,
                "gst": self.gst,
                "warehouse": self.warehouse,
                "branch": self.branch,
                "cost_center": self.cost_center,
                "employee": self.employee,
                "area": self.area,
            }
            try:
                # Prefer centralized runner when available
                from services.ui_adapter_runner import apply_profile_to_widgets

                apply_profile_to_widgets(profile_code, widget_map)
            except Exception:
                for key, widget in widget_map.items():
                    attrs = control_map.get(key)
                    if not attrs:
                        continue
                    try:
                        widget.setVisible(bool(attrs.get("visible", True)))
                        widget.setEnabled(bool(attrs.get("enabled", True)))
                        if attrs.get("required"):
                            try:
                                from widgets.form_layout_helpers import mark_widget_required

                                mark_widget_required(widget)
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception:
            pass
        for advanced_control in (self.employee, self.warehouse, self.branch, self.cost_center):
            advanced_control.hide()

    def _product_label(self, row: dict[str, Any]) -> str:
        return f"{row.get('item_name','')} | {row.get('pack_name','')} | Stock {float(row.get('stock_qty') or 0):.3f} | {row.get('supplier_name','')}"

    def _customer_changed(self, label: str) -> None:
        customer = self.customer_by_label.get(label)
        if not customer:
            self.shipping_text = ""
            return
        self.shipping_text = str(customer.get("shipping_address") or "")
        customer_area = str(customer.get("area") or "").strip()
        if customer_area:
            if self.area.findText(customer_area) < 0:
                self.area.addItem(customer_area)
            self.area.setCurrentText(customer_area)
            self.area_text = customer_area
        if self.shipping_text:
            self.details_btn.setText("More Details (set)")

    def _product_changed(self, label: str) -> None:
        row = self.product_by_label.get(label)
        if not row:
            return
        self.hsn.setText(str(row.get("hsn") or ""))
        unit_value = str(row.get("unit") or "PCS")
        if unit_value not in self.units:
            self.units.append(unit_value)
            self.unit.addItem(unit_value)
        self.unit.setCurrentText(unit_value)
        self.mrp.setText(f"{float(row.get('mrp') or 0):.2f}")
        self.gst.setCurrentText(f"{float(row.get('gst') or 0):.2f}")
        level = self.price_level.currentText().lower()
        rate_key = {
            "distributor": "distributor_rate",
            "wholesale": "wholesale_rate",
            "retail": "retail_rate",
            "dealer": "dealer_rate",
            "mrp": "mrp",
        }.get(level, "sale_rate")
        self.rate.setText(f"{float(row.get(rate_key) or row.get('sale_rate') or 0):.2f}")
        self.free_qty.setText(str(row.get("scheme") or "0"))

    def _coerce_float(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return float(default)
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return float(default)
                return float(text)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _coerce_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None:
                return int(default)
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return int(default)
                return int(float(text))
            return int(float(value))
        except (TypeError, ValueError):
            return int(default)

    def add_line(self) -> None:
        if not self._require_customer():
            return
        if not self.product_by_label:
            QMessageBox.warning(self, "Sales Bill", "No product data is currently loaded. Please try again after the product list finishes loading.")
            return
        selected_label = str(self.product.currentText() or "").strip()
        if not selected_label:
            QMessageBox.warning(self, "Sales Bill", "Select a product before adding a row.")
            return
        product = self.product_by_label.get(selected_label)
        if not product:
            QMessageBox.warning(self, "Sales Bill", "The selected product is not available in the current product list. Please choose another product.")
            return
        try:
            qty = self._coerce_float(self.qty.text(), 0.0)
            free_qty = self._coerce_float(self.free_qty.text(), 0.0)
            rate = self._coerce_float(self.rate.text(), 0.0)
            discount = self._coerce_float(self.discount.text(), 0.0)
            gst_rate = self._coerce_float(self.gst.currentText(), self._coerce_float(product.get("gst"), 0.0))
            mrp_value = self._coerce_float(self.mrp.text(), self._coerce_float(product.get("mrp"), 0.0))
            scheme_value = self._coerce_float(self.scheme.text(), self._coerce_float(product.get("scheme"), 0.0))
            item_name = str(product.get("item_name") or selected_label or "").strip() or selected_label
            pack_name = str(product.get("pack_name") or "").strip()
            hsn_value = str(self.hsn.text() or product.get("hsn") or "").strip()
            unit_value = str(self.unit.currentText() or product.get("unit") or "PCS").strip() or "PCS"
            stock_qty = self._coerce_float(product.get("stock_qty"), 0.0)
            validation_errors = validate_item_line(
                str(self.company.get("business_type_code") or self.company.get("business_type") or ""),
                {
                    "item_name": item_name,
                    "hsn": hsn_value,
                    "unit": unit_value,
                    "qty": qty,
                    "free_qty": free_qty,
                    "mrp": mrp_value,
                    "rate": rate,
                    "gst_rate": gst_rate,
                    "stock_qty": stock_qty,
                },
                stock_check=True,
            )
            if validation_errors:
                QMessageBox.warning(self, "Sales Bill", "\n".join(validation_errors))
                return
            line = SalesLine(
                item_name=item_name,
                pack_name=pack_name,
                hsn=hsn_value,
                unit=unit_value,
                qty=qty,
                free_qty=free_qty,
                mrp=mrp_value,
                rate=rate,
                scheme=scheme_value,
                discount_amount=discount,
                gst_rate=gst_rate,
                item_id=self._coerce_int(product.get("item_id"), 0),
                pack_id=self._coerce_int(product.get("pack_id"), 0),
                pack_size=self._coerce_float(product.get("pack_size"), 1.0),
                stock_qty=stock_qty,
            )
        except Exception:
            logger.exception("Unexpected error while adding sales bill line")
            QMessageBox.warning(self, "Sales Bill", "Unable to add the item right now. Please review the selected product details and try again.")
            return
        if line.qty <= 0:
            QMessageBox.warning(self, "Sales Bill", "Quantity must be greater than zero.")
            return
        calculator = SalesCalculator(str(self.company.get("state") or ""))
        computed = calculator.compute_line(line)
        self.computed_lines.append(computed)
        self._redraw_lines()
        self.qty.setText("1")
        self.discount.setText("0")
        self.table.setFocus()
        last_row = max(0, self.table.rowCount() - 1)
        self.table.setCurrentCell(last_row, 3)
        item = self.table.item(last_row, 3)
        if item is None:
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(last_row, 3, item)
        self.table.editItem(item)

    def _line_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_table:
            return
        row_index = item.row()
        if row_index < 0 or row_index >= len(self.computed_lines):
            return
        line = self.computed_lines[row_index].source
        try:
            if item.column() == 3:
                line.qty = max(float(item.text() or 0), 0.0)
            elif item.column() == 4:
                line.unit = str(item.text() or "").strip() or "PCS"
            elif item.column() == 5:
                line.mrp = max(float(item.text() or 0), 0.0)
            elif item.column() == 6:
                line.rate = max(float(item.text() or 0), 0.0)
            elif item.column() == 7:
                line.free_qty = max(float(item.text() or 0), 0.0)
            elif item.column() == 8:
                line.discount_amount = max(float(item.text() or 0), 0.0)
            elif item.column() == 10:
                line.gst_rate = max(float(item.text() or 0), 0.0)
            else:
                return
        except ValueError:
            return
        calculator = SalesCalculator(str(self.company.get("state") or ""))
        self.computed_lines[row_index] = calculator.compute_line(line)
        self._redraw_lines()

    def remove_selected_line(self) -> None:
        selected = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)
        if not selected:
            current_row = self.table.currentRow()
            if current_row >= 0:
                selected = [current_row]
            else:
                return
        for row_index in selected:
            if 0 <= row_index < len(self.computed_lines):
                self.computed_lines.pop(row_index)
        self._redraw_lines()
        if self.computed_lines:
            self.table.setFocus()
            self.table.setCurrentCell(max(0, min(self.table.rowCount() - 1, 0)), 3)

    def _redraw_lines(self) -> None:
        self._updating_table = True
        self.table.setRowCount(len(self.computed_lines))
        editable_columns = {3, 4, 5, 6, 7, 8, 10}
        for index, row in enumerate(self.computed_lines):
            values = [
                str(index + 1), row.source.item_name + " / " + row.source.pack_name, row.source.hsn,
                f"{row.source.qty:.3f}", row.source.unit, f"{row.source.mrp:.2f}",
                f"{row.source.rate:.2f}", f"{row.source.free_qty:.3f}", f"{row.source.discount_amount:.2f}",
                f"{row.taxable:.2f}", f"{row.source.gst_rate:.2f}", f"{row.line_total:.2f}",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in editable_columns:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col not in {1, 2, 4}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(index, col, item)
        self.table.resizeColumnsToContents()
        if self.table.rowCount() > 0 and self.table.currentRow() < 0:
            self.table.setCurrentCell(0, 3)
        self._updating_table = False
        totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
        self.totals_panel.set_totals(self.computed_lines, totals)
        self.tax_summary_panel.set_lines(self.computed_lines, totals)

    def clear_bill(self) -> None:
        self.editing_sale_id = None
        self.computed_lines.clear()
        self._redraw_lines()
        self.document_status.setText("New")
        self.source_status.setText(f"{len(self.customers)} customers | {len(self.products)} packs")

    def save_draft(self) -> None:
        if not self._require_customer():
            return
        if not self.computed_lines:
            QMessageBox.information(self, "Sales Bill", "Add at least one item row before saving.")
            return
        drafts = self.config.project_root / "drafts"
        drafts.mkdir(exist_ok=True)
        totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
        payload = self._transaction_payload(totals)
        path = drafts / f"sales_bill_saved_{datetime.now():%Y%m%d_%H%M%S}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
        try:
            if self.editing_sale_id is None:
                sale_id = self.repository.save_sales(payload["header"], self.computed_lines, totals)
                action = "saved"
            else:
                sale_id = self.repository.edit_sales(
                    self.editing_sale_id,
                    payload["header"],
                    self.computed_lines,
                    totals,
                )
                action = "updated"
        except Exception as exc:
            QMessageBox.warning(self, "Sales Bill Save", f"Bill could not be saved:\n{exc}")
            return
        self.editing_sale_id = sale_id
        self.document_status.setText("Active")
        self.source_status.setText(f"Editing saved sale #{sale_id}")
        QMessageBox.information(
            self,
            "Sales Bill Saved",
            f"Bill {action} in the local database.\nSale ID: {sale_id}\nAudit copy:\n{path}",
        )

    def _transaction_payload(self, totals: dict[str, float]) -> dict[str, Any]:
        customer = self._selected_customer() or {}
        customer_name = str(customer.get("name") or self.customer.currentText())
        warehouse_name = self.warehouse_text or self.warehouse.currentText()
        warehouse = self.warehouse_by_name.get(warehouse_name, {})
        header = {
            "bill_no": self.bill_no.text(),
            "bill_date": self.bill_date.date().toString("yyyy-MM-dd"),
            "customer": self.customer.currentText(),
            "customer_id": customer.get("id") or 0,
            "customer_name": customer_name,
            "customer_area": customer.get("area") or self.area_text,
            "party_type": "customer",
            "party_id": customer.get("id") or 0,
            "party_name": customer_name,
            "payment": self.payment.currentText(),
            "price_level": self.price_level.currentText(),
            "employee": self.employee_text,
            "area": self.area_text,
            "warehouse_id": warehouse.get("id") or 0,
            "warehouse": warehouse_name,
            "branch": self.branch_text,
            "cost_center": self.cost_center_text,
            "shipping": self.shipping_text,
            "po_no": self.po_no_text,
            "transport": self.transport_text,
            "credit_terms": self.credit_terms_text,
        }
        return {
            "header": header,
            "totals": totals,
            "lines": [row.__dict__ | {"source": row.source.__dict__} for row in self.computed_lines],
        }

    def load_for_edit(self, sale_id: int) -> None:
        payload = self.repository.load_document_for_edit("sales", int(sale_id))
        header = payload["header"]
        self.editing_sale_id = int(header["id"])
        self.bill_no.setText(str(header.get("bill_no") or ""))
        saved_date = QDate.fromString(str(header.get("bill_date") or ""), "yyyy-MM-dd")
        if saved_date.isValid():
            self.bill_date.setDate(saved_date)
        customer_id = int(header.get("customer_id") or 0)
        for label, customer in self.customer_by_label.items():
            if int(customer.get("id") or 0) == customer_id:
                self.customer.setCurrentText(label)
                break
        self.payment.setCurrentText(str(header.get("pay_mode") or "Credit"))
        warehouse_id = int(header.get("warehouse_id") or 0)
        for name, warehouse in self.warehouse_by_name.items():
            if int(warehouse.get("id") or 0) == warehouse_id:
                self.warehouse.setCurrentText(name)
                self.warehouse_text = name
                break
        self.branch_text = str(header.get("branch_name") or "")
        if self.branch_text:
            self.branch.setCurrentText(self.branch_text)
        self.cost_center_text = str(header.get("cost_center_name") or "")
        self.employee_text = str(header.get("employee_name") or "")
        self.shipping_text = str(header.get("shipping_address") or "")
        self.po_no_text = str(header.get("po_no") or "")
        self.transport_text = str(header.get("transport_details") or "")
        self.credit_terms_text = str(header.get("credit_terms") or "")
        self.computed_lines = [self._saved_line_for_edit(row) for row in payload["lines"]]
        self._redraw_lines()
        self.document_status.setText(f"Editing #{sale_id}")
        self.source_status.setText(f"Editing sale #{sale_id} | saving will reverse and repost once")

    @staticmethod
    def _saved_line_for_edit(row: dict[str, Any]) -> ComputedLine:
        source = SalesLine(
            item_name=str(row.get("item_name") or ""),
            pack_name=str(row.get("pack_display_snapshot") or ""),
            hsn=str(row.get("hsn") or ""),
            unit=str(row.get("unit") or "PCS"),
            qty=float(row.get("qty") or 0),
            free_qty=float(row.get("free_qty") or 0),
            mrp=float(row.get("mrp") or 0),
            rate=float(row.get("rate") or 0),
            scheme=0,
            discount_amount=float(row.get("discount") or 0),
            gst_rate=float(row.get("gst") or 0),
            item_id=int(row.get("item_id") or 0),
            pack_id=int(row.get("pack_id") or 0),
            pack_size=float(row.get("pack_size_snapshot") or 1),
        )
        taxable = float(row.get("taxable") or 0)
        return ComputedLine(
            source=source,
            gross=round(taxable + source.discount_amount, 2),
            taxable=taxable,
            cgst=float(row.get("cgst") or 0),
            sgst=float(row.get("sgst") or 0),
            igst=float(row.get("igst") or 0),
            gst_total=float(row.get("gst_amt") or 0),
            line_total=float(row.get("total") or 0),
        )

    def print_draft_pdf(self) -> None:
        if not self._require_customer():
            return
        if not self.computed_lines:
            QMessageBox.information(self, "Sales Bill", "Add at least one item row before printing.")
            return
        try:
            path, _, _ = self._create_draft_pdf()
        except Exception as exc:
            QMessageBox.warning(self, "Sales Bill Print", f"PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, "Sales Bill Print Preview")

    def share_draft_whatsapp(self) -> None:
        if not self._require_customer():
            return
        if not self.computed_lines:
            QMessageBox.information(self, "Sales Bill", "Add at least one item row before sharing.")
            return
        try:
            path, caption, phone = self._create_draft_pdf()
            customer = self._selected_customer() or {}
            totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
            customer_name = str(customer.get("name") or self.customer.currentText())
            message = self._communication_message("whatsapp", "Tax Invoice", self.bill_no.text(), customer_name, totals["grand_total"], caption, path)
            caption = message["body"]
            QApplication.clipboard().setText(f"{caption}\nPDF: {path}")
            result = prepare_whatsapp_document(phone, caption, path)
            if not result.get("ok"):
                if result.get("code") != "missing_phone":
                    open_whatsapp_share(phone, caption)
                QMessageBox.information(self, "Sales Bill WhatsApp", f"{result.get('message')}\n\n{pdf_share_note(path)}")
                return
        except Exception as exc:
            QMessageBox.warning(self, "Sales Bill WhatsApp", f"Share PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Sales Bill WhatsApp", str(result.get("message") or pdf_share_note(path)))

    def email_draft_pdf(self) -> None:
        if not self._require_customer():
            return
        if not self.computed_lines:
            QMessageBox.information(self, "Sales Bill", "Add at least one item row before emailing.")
            return
        try:
            path, caption, _ = self._create_draft_pdf()
            customer = self._selected_customer() or {}
            totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
            customer_name = str(customer.get("name") or self.customer.currentText())
            message = self._communication_message("email", "Tax Invoice", self.bill_no.text(), customer_name, totals["grand_total"], caption, path)
            result = prepare_email_document(
                customer.get("email") or "",
                message["subject"],
                message["body"],
                path,
                db_path=self.source.sqlite_path,
            )
            if not result.get("ok"):
                QMessageBox.warning(self, "Sales Bill Email", str(result.get("message") or "Email could not be prepared."))
                return
        except Exception as exc:
            QMessageBox.warning(self, "Sales Bill Email", f"Email PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Sales Bill Email", str(result.get("message") or pdf_share_note(path)))

    def _create_draft_pdf(self) -> tuple[Path, str, str]:
        totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
        lines = [
            {
                "item": f"{row.source.item_name} / {row.source.pack_name}",
                "hsn": row.source.hsn,
                "qty": row.source.qty,
                "free": row.source.free_qty,
                "unit": row.source.unit,
                "mrp": row.source.mrp,
                "rate": row.source.rate,
                "disc": row.source.discount_amount,
                "taxable": row.taxable,
                "cgst": row.cgst,
                "sgst": row.sgst,
                "igst": row.igst,
                "gst": row.source.gst_rate,
                "amount": row.line_total,
            }
            for row in self.computed_lines
        ]
        customer = self._selected_customer() or {}
        customer_name = str(customer.get("name") or self.customer.currentText())
        header = {
            "no": self.bill_no.text(),
            "date": self.bill_date.date().toString("yyyy-MM-dd"),
            "party": customer_name,
            "party_name": customer_name,
            "customer_name": customer_name,
            "party_gstin": customer.get("gstin") or "",
            "party_phone": customer.get("phone") or "",
            "address": customer.get("address") or "",
            "area": customer.get("area") or self.area_text,
            "payment": self.payment.currentText(),
            "warehouse": self.warehouse_text or self.warehouse.currentText(),
            "employee": self.employee_text,
            "shipping": self.shipping_text,
            "po_no": self.po_no_text,
            "transport": self.transport_text,
            "credit_terms": self.credit_terms_text,
        }
        prints = self.config.project_root / "prints"
        path = prints / f"sales_bill_{self.bill_no.text().replace('/', '_').replace(' ', '_')}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        # Prepare company copy so we can set a per-print invoice_template_code without mutating UI state
        company_copy = self.company.copy() if isinstance(self.company, dict) else dict(self.company)
        try:
            sel = str(self.print_template.currentText() or "").strip()
            # If user picked an explicit template in the form "Name (code)", extract code
            if sel and sel not in {"Default", "Company (" + str(company_copy.get('invoice_template_code') or '') + ")"}:
                import re

                m = re.search(r"\(([^)]+)\)$", sel)
                if m:
                    company_copy["invoice_template_code"] = m.group(1)
        except Exception:
            pass

        write_transaction_pdf(
            path,
            "Tax Invoice",
            company_copy,
            header,
            lines,
            totals,
            document_type="sales_invoice",
            party_label="Bill To",
            ship_to=self.shipping_text,
            db_path=self.source.sqlite_path,
        )
        caption = document_share_caption("Tax Invoice", self.bill_no.text(), customer_name, totals["grand_total"], self.company, path)
        return path, caption, str(customer.get("phone") or "")

    def _communication_message(
        self,
        channel: str,
        title: str,
        document_no: str,
        party_name: str,
        amount: object,
        fallback_body: str,
        path: Path,
    ) -> dict[str, str]:
        context = document_message_context(
            title=title,
            document_no=document_no,
            party_name=party_name,
            amount=amount,
            company=self.company,
            pdf_path=path,
        )
        return communication_message(
            channel=channel,
            document_type="sales_invoice",
            context=context,
            fallback_subject=f"{title} {document_no}",
            fallback_body=fallback_body,
            db_path=self.source.sqlite_path,
        )

    def _selected_customer(self) -> dict[str, Any] | None:
        return self.customer_by_label.get(self.customer.currentText())

    def _require_customer(self) -> bool:
        if self._selected_customer():
            return True
        QMessageBox.warning(self, "Sales Bill", "Select a customer before item entry.")
        self.customer.setFocus()
        return False
