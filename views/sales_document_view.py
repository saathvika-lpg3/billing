from __future__ import annotations

import json
from datetime import datetime
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
from services.business_rules import validate_item_line
from services.mysql_source import MySqlSource
from services.pdf_print import document_share_caption, write_transaction_pdf
from services.print_preview import show_print_preview
from services.sales_calculator import SalesCalculator, SalesLine, money
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
    DocumentCard,
    ERPFieldBox,
    ERPItemGrid,
    ERPTransactionGrid,
    ProductSearchCard,
    RemarksTermsCard,
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


SALES_DOCUMENTS = {
    "quotation": {
        "title": "Quotation",
        "subtitle": "Customer quote with item pricing and GST summary",
        "doc_label": "Quotation No",
        "party_label": "Customer",
        "list_key": "quotation_list",
        "doc_type": "quotation",
    },
    "sales_order": {
        "title": "Sales Order",
        "subtitle": "Order booking before billing and dispatch",
        "doc_label": "Order No",
        "party_label": "Customer",
        "list_key": "order_list",
        "doc_type": "sales_order",
    },
    "delivery_challan": {
        "title": "Delivery Challan",
        "subtitle": "Dispatch document with stock-aware item rows",
        "doc_label": "DC No",
        "party_label": "Customer",
        "list_key": "dc_list",
        "doc_type": "delivery_challan",
    },
    "sales_return": {
        "title": "Sales Return",
        "subtitle": "Customer return / credit note draft with GST summary",
        "doc_label": "Return No",
        "party_label": "Customer",
        "list_key": "return_list",
        "doc_type": "sales_return",
    },
}


class SalesDocumentView(QWidget):
    document_catalog = SALES_DOCUMENTS
    headers = ["#", "Item", "HSN", "Qty", "Unit", "MRP", "Rate", "SCH", "Disc", "Taxable", "GST %", "Amount"]

    def __init__(self, config: AppConfig, mode: str) -> None:
        super().__init__()
        if mode not in self.document_catalog:
            raise ValueError(f"Unknown sales document mode: {mode}")
        self.config = config
        self.mode = mode
        self.meta = self.document_catalog[mode]
        self.source = MySqlSource()
        self.repository = TransactionRepository()
        self.company: dict[str, Any] = {}
        self.customers: list[dict[str, Any]] = []
        self.products: list[dict[str, Any]] = []
        self.product_by_label: dict[str, dict[str, Any]] = {}
        self.customer_by_label: dict[str, dict[str, Any]] = {}
        self.source_by_label: dict[str, dict[str, Any]] = {}
        self.source_rows: list[dict[str, Any]] = []
        self.selected_source: dict[str, Any] = {}
        self.computed_lines = []
        self.recent_rows: list[dict[str, Any]] = []
        self._updating_table = False
        self._build()
        self._load_source_data()
        if not self._is_return_mode():
            self._generate_doc_no()
        self._update_summary()
        self._register_hotkeys()

    def _build(self) -> None:
        page = TransactionPageLayout(self)
        page.add_header(self._title_bar())
        page.add_toolbar(self._action_toolbar())
        page.add_section(self._header_card())
        if self._is_return_mode():
            page.add_section(self._source_return_card())
        page.add_section(self._item_card())
        page.add_grid(self._table_card())
        page.add_summary(self._summary_card())

    def _title_bar(self) -> QWidget:
        header = TransactionHeader(
            str(self.meta["title"]),
            f"{self.meta['subtitle']} | F4 add row | Ctrl+S save | Del delete row | dblclick to edit values",
            self,
        )
        self.source_status = header.status_label
        return header

    def _action_toolbar(self) -> QWidget:
        return TransactionToolbar(
            [
                ("New", self.clear_document),
                ("Save", self.save_draft),
                ("Preview", self.print_document_pdf),
                ("Print", self.print_document_pdf),
                ("PDF", self.print_document_pdf),
                ("WhatsApp", self.share_document_whatsapp),
                ("Email", self.email_document_pdf),
                ("Close", self.close),
                ("Delete", self.remove_selected_line),
            ],
            self,
        )

    def _prepare(self, widget: QWidget, width: int = 96) -> QWidget:
        widget.setMinimumWidth(min(width, 120))
        if isinstance(widget, QTextEdit):
            widget.setMinimumHeight(40)
            widget.setMaximumHeight(70)
        else:
            widget.setFixedHeight(28)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if isinstance(widget, QComboBox):
            widget.setMaxVisibleItems(18)
            widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 8))
        return widget

    def _field(self, label: str, widget: QWidget, width: int = 100) -> QWidget:
        self._prepare(widget, width)
        return ERPFieldBox(label, widget, self)

    def _header_card(self) -> QWidget:
        host = TransactionDetailsDeck(self)
        self.doc_no = QLineEdit()
        self.doc_date = QDateEdit()
        self.doc_date.setCalendarPopup(True)
        self.doc_date.setDate(QDate.currentDate())
        self.customer = QComboBox()
        self.customer.setEditable(True)
        self.customer.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer.currentTextChanged.connect(self._party_changed)
        self.area = QComboBox()
        self.area.setEditable(True)
        self.area.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.warehouse = QComboBox()
        self.pay_mode = QComboBox()
        self.pay_mode.addItems(["Cash", "Credit", "UPI", "Bank", "Card"])
        self.status = QComboBox()
        if self._is_return_mode():
            self.status.addItems(["Active", "Draft", "Cancelled"])
        else:
            self.status.addItems(["Open", "Accepted", "Ready", "Closed", "Converted", "Cancelled"])
        self.valid_until = QDateEdit()
        self.valid_until.setCalendarPopup(True)
        self.valid_until.setDate(QDate.currentDate().addDays(7))
        self.notes = QTextEdit()

        customer_card, customer_grid = self._header_section("Customer Information", "customer")
        customer_grid.addWidget(self._field(str(self.meta.get("party_label", "Customer")), self.customer, 220), 0, 0)
        customer_grid.addWidget(self._field("Area / Route", self.area, 150), 1, 0)

        detail_card, detail_grid = self._header_section("Other Details", "document")
        detail_grid.addWidget(self._field(str(self.meta["doc_label"]), self.doc_no, 140), 0, 0)
        detail_grid.addWidget(self._field("Date", self.doc_date, 120), 0, 1)
        detail_grid.addWidget(self._field("Warehouse", self.warehouse, 160), 1, 0)
        detail_grid.addWidget(self._field("Payment", self.pay_mode, 120), 1, 1)

        info_card, info_grid = self._header_section("Additional Information", "additional")
        info_grid.addWidget(self._field("Status", self.status, 120), 0, 0)
        info_grid.addWidget(self._field("Valid / Delivery", self.valid_until, 120), 0, 1)
        info_grid.addWidget(self._field("Notes", self.notes, 240), 1, 0, 1, 2)
        self.notes.setMinimumHeight(38)
        self.notes.setMaximumHeight(44)

        host.add_card(customer_card, stretch=2)
        host.add_card(detail_card, stretch=2)
        host.add_card(info_card, stretch=3)
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

    def _source_return_card(self) -> QWidget:
        frame = DocumentCard()
        frame.setMaximumHeight(64)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 5, 8, 5)
        self.source_doc = QComboBox()
        self.source_doc.setMinimumContentsLength(28)
        self.source_doc.setMaxVisibleItems(18)
        load_button = QPushButton("Load Original Items")
        load_button.clicked.connect(self.load_source_document)
        self.source_hint = QLabel("Select original bill, load remaining items, then edit Qty/SCH in the grid.")
        self.source_hint.setObjectName("caption")
        self.source_hint.setWordWrap(True)
        layout.addWidget(QLabel("Original Bill"))
        layout.addWidget(self.source_doc, stretch=3)
        layout.addWidget(load_button)
        layout.addWidget(self.source_hint, stretch=2)
        return frame

    def _item_card(self) -> QWidget:
        frame = ProductSearchCard()
        frame.setMinimumHeight(112)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        self.product = QComboBox()
        self.product.setEditable(False)
        self.product.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.product.currentTextChanged.connect(self._product_changed)
        self.hsn = QLineEdit()
        self.qty = QLineEdit("1")
        self.free_qty = QLineEdit("0")
        self.unit = QComboBox()
        self.unit.setEditable(False)
        self.unit.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mrp = QLineEdit("0.00")
        self.rate = QLineEdit("0.00")
        self.discount = QLineEdit("0.00")
        self.gst = QComboBox()
        self.gst.setEditable(False)
        self.gst.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        add_button = QPushButton("Add Row  F4")
        add_button.clicked.connect(self.add_line)

        grid.addWidget(self._field("Product Search", self.product, 360), 0, 0, 1, 5)
        grid.addWidget(self._field("HSN", self.hsn, 80), 0, 5)
        grid.addWidget(self._field("Qty", self.qty, 70), 1, 0)
        grid.addWidget(self._field("Unit", self.unit, 80), 1, 1)
        grid.addWidget(self._field("MRP", self.mrp, 80), 1, 2)
        grid.addWidget(self._field("Rate", self.rate, 80), 1, 3)
        grid.addWidget(self._field("SCH", self.free_qty, 70), 1, 4)
        grid.addWidget(self._field("Disc", self.discount, 80), 1, 5)
        grid.addWidget(self._field("GST %", self.gst, 80), 1, 6)
        grid.addWidget(add_button, 1, 7)
        grid.setColumnStretch(0, 2)
        for column in range(1, 8):
            grid.setColumnStretch(column, 1)
        return frame

    def _table_card(self) -> QWidget:
        self.table = ERPItemGrid(0, len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.itemChanged.connect(self._line_table_item_changed)
        # editable columns for document tables (qty, unit, mrp, rate, sch, disc, gst)
        editable_columns = {3, 4, 5, 6, 7, 8, 10}
        self.table.set_editable_columns(editable_columns)
        for col, width in {0: 46, 1: 320, 2: 90, 3: 84, 4: 80, 5: 90, 6: 95, 7: 95, 8: 95, 9: 110, 10: 85, 11: 115}.items():
            self.table.setColumnWidth(col, width)
        self.table.set_command_handlers(
            {
                "add_row": self.add_line,
                "product_search": lambda: self.product.setFocus(),
                "save": self.save_draft,
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

        remarks_card, self.remarks = self._memo_summary_card("Remarks", "Type remarks here...")
        terms_card, self.terms = self._memo_summary_card("Terms & Conditions", "Type terms and conditions here...")
        totals_card = self._totals_summary_card()
        tax_card = self._tax_summary_card()

        deck.add_card(remarks_card, stretch=1)
        deck.add_card(terms_card, stretch=1)
        deck.add_card(totals_card, stretch=7)
        deck.add_card(tax_card, stretch=2)
        return deck

    def _memo_summary_card(self, title: str, placeholder: str) -> tuple[QWidget, QTextEdit]:
        card = RemarksTermsCard()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 5, 8, 6)
        layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        editor = QTextEdit()
        editor.setPlaceholderText(placeholder)
        editor.setMinimumHeight(42)
        editor.setMaximumHeight(58)
        editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(title_label)
        layout.addWidget(editor)
        return card, editor

    def _totals_summary_card(self) -> QWidget:
        self.totals_panel = TransactionTotalsPanel()
        self.total_items = self.totals_panel.labels["total_qty"]
        self.taxable_total = self.totals_panel.labels["taxable"]
        self.gst_total = self.totals_panel.labels["gst_total"]
        self.round_off = self.totals_panel.labels["round_off"]
        self.grand_total = self.totals_panel.labels["grand_total"]
        return self.totals_panel

    def _tax_summary_card(self) -> QWidget:
        self.tax_summary_panel = TransactionTaxSummaryPanel()
        self.tax_summary_table = self.tax_summary_panel.table
        return self.tax_summary_panel

    def _load_source_data(self) -> None:
        try:
            self.company = self.source.company()
            self.customers = self.source.customers()
            self.products = self.source.product_choices()
            warehouses = self.source.warehouses()
            self.recent_rows = self.source.operation_rows(str(self.meta["list_key"]), 100)
            if self._is_return_mode():
                self.source_rows = self.source.sales_return_sources()
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            return
        customer_labels = [f"{row.get('name','')} | {row.get('area','')} | Due {float(row.get('balance') or 0):.2f}" for row in self.customers]
        self.customer_by_label = dict(zip(customer_labels, self.customers))
        self.customer.addItems(["Select Customer", *customer_labels])
        customer_completer = self.customer.completer()
        if customer_completer:
            customer_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            customer_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        areas = sorted({str(row.get("area") or "") for row in self.customers if row.get("area")})
        self.area.addItems(["All Areas", *areas])
        area_completer = self.area.completer()
        if area_completer:
            area_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            area_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.warehouse.addItems([row.get("name", "") for row in warehouses] or ["Main Store"])
        product_labels = [self._product_label(row) for row in self.products]
        self.product_by_label = dict(zip(product_labels, self.products))
        self.units = ["PCS"]
        units = self.source.units()
        self.units = [str(u.get("name") or "").strip() for u in units if str(u.get("name") or "").strip()] or ["PCS"]
        self.unit.clear()
        self.unit.addItems(self.units)
        gst_rates = self.source.tax_slabs()
        self.gst_rates = [str(r.get("rate") or "0").strip() for r in gst_rates]
        self.gst.clear()
        self.gst.addItems(self.gst_rates if self.gst_rates else ["0"])
        self.product.addItems(product_labels)
        product_completer = self.product.completer()
        if product_completer:
            product_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            product_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        if self._is_return_mode():
            self._fill_source_selector()
        self.source_status.setText(f"{len(self.customers)} customers | {len(self.products)} packs | {len(self.recent_rows)} recent")
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
                "discount",
                "gst",
                "warehouse",
                "area",
            ])
            widget_map = {
                "product": self.product,
                "hsn": self.hsn,
                "qty": self.qty,
                "free_qty": self.free_qty,
                "unit": self.unit,
                "mrp": self.mrp,
                "rate": self.rate,
                "discount": self.discount,
                "gst": self.gst,
                "warehouse": self.warehouse,
                "area": self.area,
            }
            try:
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

    def _is_return_mode(self) -> bool:
        return str(self.meta.get("doc_type")) in {"sales_return", "purchase_return"}

    def _fill_source_selector(self) -> None:
        labels = [self._source_label(row) for row in self.source_rows]
        self.source_by_label = dict(zip(labels, self.source_rows))
        self.source_doc.clear()
        placeholder = "Choose original bill" if self.meta.get("doc_type") == "sales_return" else "Choose original purchase"
        self.source_doc.addItems([placeholder, *labels])

    def _source_label(self, row: dict[str, Any]) -> str:
        party = row.get("customer_name") or row.get("supplier_name") or ""
        return f"{row.get('bill_no','')} | {row.get('bill_date','')} | {party} | Rs {float(row.get('grand_total') or 0):.2f}"

    def load_source_document(self) -> None:
        source_row = self.source_by_label.get(self.source_doc.currentText())
        if not source_row:
            QMessageBox.information(self, str(self.meta["title"]), "Choose an original bill first.")
            return
        try:
            if self.meta.get("doc_type") == "sales_return":
                rows = self.source.sales_return_source_lines(int(source_row.get("id") or 0))
            else:
                rows = self.source.purchase_return_source_lines(int(source_row.get("id") or 0))
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Original bill could not be loaded:\n{exc}")
            return
        self.selected_source = source_row
        self._select_party_from_source(source_row)
        self.computed_lines = []
        calculator = SalesCalculator(str(self.company.get("state") or ""))
        for row in rows:
            remaining_qty = float(row.get("remaining_qty") or 0)
            remaining_free = float(row.get("remaining_free_qty") or 0)
            if remaining_qty <= 0 and remaining_free <= 0:
                continue
            line = self._line_from_source_row(row, remaining_qty, remaining_free)
            place = "Interstate" if line.tax_mode == "igst" else ""
            self.computed_lines.append(calculator.compute_line(line, place_of_supply=place))
        self._redraw_lines()
        self.source_hint.setText(f"Loaded {len(self.computed_lines)} returnable item row(s). Edit Qty/SCH before Save.")
        if not self.doc_no.text().strip():
            prefix = "RET" if self.meta.get("doc_type") == "sales_return" else "DNT"
            self.doc_no.setText(f"{prefix}-{datetime.now():%y%m%d-%H%M%S}")

    def _line_from_source_row(self, row: dict[str, Any], qty: float, free_qty: float) -> SalesLine:
        return SalesLine(
            item_name=str(row.get("item_name") or ""),
            pack_name=str(row.get("pack_name") or ""),
            hsn=str(row.get("hsn") or ""),
            unit=str(row.get("unit") or "PCS"),
            qty=qty,
            free_qty=free_qty,
            mrp=float(row.get("mrp") or 0),
            rate=float(row.get("rate") or 0),
            scheme=0,
            discount_amount=float(row.get("discount") or 0),
            gst_rate=float(row.get("gst") or 0),
            item_id=int(float(row.get("item_id") or 0)),
            pack_id=int(float(row.get("pack_id") or 0)),
            pack_size=float(row.get("pack_size") or 1),
            stock_qty=float(row.get("stock_qty") or 0),
            source_item_id=int(float(row.get("source_item_id") or 0)),
            source_doc_id=int(float(row.get("source_doc_id") or 0)),
            source_doc_no=str(row.get("source_doc_no") or ""),
            max_qty=float(row.get("remaining_qty") or 0),
            max_free_qty=float(row.get("remaining_free_qty") or 0),
            tax_mode=str(row.get("tax_mode") or ""),
        )

    def _select_party_from_source(self, source_row: dict[str, Any]) -> None:
        target_id = source_row.get("customer_id") if self.meta.get("doc_type") == "sales_return" else source_row.get("supplier_id")
        for label, row in self.customer_by_label.items():
            if str(row.get("id") or "") == str(target_id or ""):
                self.customer.setCurrentText(label)
                break
        area = source_row.get("customer_area") or source_row.get("branch_name") or ""
        if area and self.area.findText(str(area)) >= 0:
            self.area.setCurrentText(str(area))

    def _product_label(self, row: dict[str, Any]) -> str:
        return f"{row.get('item_name','')} | {row.get('pack_name','')} | Stock {float(row.get('stock_qty') or 0):.3f} | {row.get('supplier_name','')}"

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
        self.rate.setText(f"{float(row.get('sale_rate') or row.get('mrp') or 0):.2f}")
        self.gst.setCurrentText(f"{float(row.get('gst') or 0):.2f}")

    def add_line(self) -> None:
        if self._is_return_mode():
            QMessageBox.information(self, str(self.meta["title"]), "Use Original Bill > Load Original Items for returns.")
            self.source_doc.setFocus()
            return
        if not self._require_party():
            return
        product = self.product_by_label.get(self.product.currentText())
        if not product:
            QMessageBox.warning(self, str(self.meta["title"]), "Select a product before adding a row.")
            return
        try:
            qty = float(self.qty.text() or 0)
            free_qty = float(self.free_qty.text() or 0)
            rate = float(self.rate.text() or 0)
            discount = float(self.discount.text() or 0)
            gst_rate = float(self.gst.currentText() or 0)
            validation_errors = validate_item_line(
                str(self.company.get("business_type_code") or self.company.get("business_type") or ""),
                {
                    "item_name": product.get("item_name"),
                    "hsn": self.hsn.text().strip(),
                    "unit": self.unit.currentText().strip(),
                    "qty": qty,
                    "free_qty": free_qty,
                    "mrp": float(self.mrp.text() or 0),
                    "rate": rate,
                    "gst_rate": gst_rate,
                    "stock_qty": product.get("stock_qty"),
                },
                stock_check=self.mode in {"delivery_challan", "sales_return"},
            )
            if validation_errors:
                QMessageBox.warning(self, str(self.meta["title"]), "\n".join(validation_errors))
                return
            line = SalesLine(
                item_name=str(product.get("item_name") or ""),
                pack_name=str(product.get("pack_name") or ""),
                hsn=self.hsn.text().strip(),
                unit=self.unit.currentText().strip() or "PCS",
                qty=qty,
                free_qty=free_qty,
                mrp=float(self.mrp.text() or 0),
                rate=rate,
                scheme=0,
                discount_amount=discount,
                gst_rate=gst_rate,
                item_id=int(float(product.get("item_id") or 0)),
                pack_id=int(float(product.get("pack_id") or 0)),
                pack_size=float(product.get("pack_size") or 1),
                stock_qty=float(product.get("stock_qty") or 0),
            )
        except ValueError:
            QMessageBox.warning(self, str(self.meta["title"]), "Qty, rate, discount and GST must be numbers.")
            return
        if line.qty <= 0:
            QMessageBox.warning(self, str(self.meta["title"]), "Quantity must be greater than zero.")
            return
        calculator = SalesCalculator(str(self.company.get("state") or ""))
        self.computed_lines.append(
            calculator.compute_line(line, place_of_supply=self._line_place_of_supply(line))
        )
        self._redraw_lines()
        self.qty.setText("1")
        self.free_qty.setText("0")
        self.discount.setText("0.00")
        self.product.setFocus()

    def _redraw_lines(self) -> None:
        self._updating_table = True
        self.table.setRowCount(len(self.computed_lines))
        for index, row in enumerate(self.computed_lines):
            item_text = f"{row.source.item_name} / {row.source.pack_name}"
            if self._is_return_mode() and row.source.source_doc_no:
                item_text = f"{item_text} | {row.source.source_doc_no} | Max Qty/SCH {row.source.max_qty:.3f}+{row.source.max_free_qty:.3f}"
            values = [
                str(index + 1),
                item_text,
                row.source.hsn,
                f"{row.source.qty:.3f}",
                row.source.unit,
                f"{row.source.mrp:.2f}",
                f"{row.source.rate:.2f}",
                f"{row.source.free_qty:.3f}",
                f"{row.source.discount_amount:.2f}",
                f"{row.taxable:.2f}",
                f"{row.source.gst_rate:.2f}",
                f"{row.line_total:.2f}",
            ]
            editable_columns = {3, 4, 5, 6, 7, 8, 10}
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in editable_columns:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column not in {1, 2, 4}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(index, column, item)
        self.table.resizeRowsToContents()
        self._updating_table = False
        self._update_summary()

    def _line_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_table:
            return
        row_index = item.row()
        if row_index < 0 or row_index >= len(self.computed_lines):
            return
        line = self.computed_lines[row_index].source
        try:
            if item.column() == 3:
                value = max(float(item.text() or 0), 0.0)
                if self._is_return_mode():
                    value = min(value, line.max_qty or value)
                line.qty = value
            elif item.column() == 4:
                line.unit = str(item.text() or "").strip() or "PCS"
            elif item.column() == 5:
                line.mrp = max(float(item.text() or 0), 0.0)
            elif item.column() == 6:
                line.rate = max(float(item.text() or 0), 0.0)
            elif item.column() == 7:
                value = max(float(item.text() or 0), 0.0)
                if self._is_return_mode():
                    value = min(value, line.max_free_qty or value)
                line.free_qty = value
            elif item.column() == 8:
                line.discount_amount = max(float(item.text() or 0), 0.0)
            elif item.column() == 10:
                line.gst_rate = max(float(item.text() or 0), 0.0)
            else:
                return
        except ValueError:
            return
        calculator = SalesCalculator(str(self.company.get("state") or ""))
        place = self._line_place_of_supply(line)
        self.computed_lines[row_index] = calculator.compute_line(line, place_of_supply=place)
        self._redraw_lines()

    def remove_selected_line(self) -> None:
        selected = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)
        if not selected:
            return
        for row_index in selected:
            if 0 <= row_index < len(self.computed_lines):
                self.computed_lines.pop(row_index)
        self._redraw_lines()

    def _line_place_of_supply(self, line: SalesLine | None = None) -> str:
        if line is not None and line.tax_mode:
            return "Interstate" if line.tax_mode == "igst" else str(self.company.get("state") or "")
        party = self.customer_by_label.get(self.customer.currentText(), {})
        return str(party.get("place_of_supply") or party.get("state") or "").strip()

    def _party_changed(self, _label: str) -> None:
        if not self.computed_lines:
            return
        calculator = SalesCalculator(str(self.company.get("state") or ""))
        self.computed_lines = [
            calculator.compute_line(row.source, place_of_supply=self._line_place_of_supply(row.source))
            for row in self.computed_lines
        ]
        self._redraw_lines()

    def _update_summary(self) -> None:
        totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
        self.totals_panel.set_totals(self.computed_lines, totals)
        self.tax_summary_panel.set_lines(self.computed_lines, totals)

    def _update_tax_summary_table(self, totals: dict[str, float]) -> None:
        self.tax_summary_panel.set_lines(self.computed_lines, totals)

    def clear_document(self) -> None:
        self.doc_no.clear()
        self.doc_date.setDate(QDate.currentDate())
        self.valid_until.setDate(QDate.currentDate().addDays(7))
        self.notes.clear()
        self.remarks.clear()
        self.terms.clear()
        self.selected_source = {}
        if self._is_return_mode():
            self.source_doc.setCurrentIndex(0)
        self.source_hint.setText("Select original bill, load remaining items, then edit Qty/SCH in the grid.")
        self.computed_lines.clear()
        self._redraw_lines()
        if not self._is_return_mode():
            self._generate_doc_no()
        self.doc_no.setFocus()

    def save_draft(self) -> None:
        if not self.doc_no.text().strip():
            if self._is_return_mode():
                QMessageBox.warning(self, str(self.meta["title"]), f"{self.meta['doc_label']} is required.")
                self.doc_no.setFocus()
                return
            self._generate_doc_no()
        if self._is_return_mode() and not self.selected_source:
            QMessageBox.warning(self, str(self.meta["title"]), "Load the original bill before saving this return.")
            self.source_doc.setFocus()
            return
        if not self._is_return_mode() and not self._require_party():
            return
        if self._is_return_mode() and not self._validate_return_lines():
            return
        if not self.computed_lines:
            QMessageBox.warning(self, str(self.meta["title"]), "Add at least one item row.")
            self.product.setFocus()
            return
        totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
        payload = self._transaction_payload(totals)
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = drafts_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            doc_type = str(self.meta["doc_type"])
            if doc_type == "sales_return":
                saved_id = self.repository.save_sales_return(payload["header"], self.computed_lines, totals)
            elif doc_type == "purchase_return":
                saved_id = self.repository.save_purchase_return(payload["header"], self.computed_lines, totals)
            else:
                saved_id = self.repository.save_order_document(payload["header"], self.computed_lines, totals)
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Document could not be saved:\n{exc}")
            return
        QMessageBox.information(
            self,
            str(self.meta["title"]),
            f"Saved to local database.\nID: {saved_id}\n{self._workflow_after_save_note()}\nAudit copy:\n{path}",
        )

    def print_document_pdf(self) -> None:
        if not self._can_output_document("previewing"):
            return
        try:
            path, _, _ = self._create_document_pdf()
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, f"{self.meta['title']} Print Preview")

    def share_document_whatsapp(self) -> None:
        if not self._can_output_document("sharing"):
            return
        try:
            path, caption, phone = self._create_document_pdf()
            message = self._communication_message("whatsapp", caption, path)
            caption = message["body"]
            QApplication.clipboard().setText(f"{caption}\nPDF: {path}")
            result = prepare_whatsapp_document(phone, caption, path)
            if not result.get("ok"):
                if result.get("code") != "missing_phone":
                    open_whatsapp_share(phone, caption)
                QMessageBox.information(self, str(self.meta["title"]), f"{result.get('message')}\n\n{pdf_share_note(path)}")
                return
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Share PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, str(self.meta["title"]), str(result.get("message") or pdf_share_note(path)))

    def email_document_pdf(self) -> None:
        if not self._can_output_document("emailing"):
            return
        try:
            path, caption, _ = self._create_document_pdf()
            party = self.customer_by_label.get(self.customer.currentText(), {})
            message = self._communication_message("email", caption, path)
            result = prepare_email_document(
                party.get("email") or "",
                message["subject"],
                message["body"],
                path,
                db_path=self.source.sqlite_path,
            )
            if not result.get("ok"):
                QMessageBox.warning(self, str(self.meta["title"]), str(result.get("message") or "Email could not be prepared."))
                return
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Email PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, str(self.meta["title"]), str(result.get("message") or pdf_share_note(path)))

    def _can_output_document(self, action: str) -> bool:
        if not self.doc_no.text().strip():
            if self._is_return_mode():
                QMessageBox.warning(self, str(self.meta["title"]), f"{self.meta['doc_label']} is required.")
                self.doc_no.setFocus()
                return False
            self._generate_doc_no()
        if self._is_return_mode() and not self.selected_source:
            QMessageBox.warning(self, str(self.meta["title"]), "Load the original bill before preparing this return PDF.")
            self.source_doc.setFocus()
            return False
        if not self._is_return_mode() and not self._require_party():
            return False
        if self._is_return_mode() and not self._validate_return_lines():
            return False
        if not self.computed_lines:
            QMessageBox.information(self, str(self.meta["title"]), f"Add at least one item row before {action}.")
            self.product.setFocus()
            return False
        return True

    def _create_document_pdf(self) -> tuple[Path, str, str]:
        totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
        payload = self._transaction_payload(totals)
        source_header = payload["header"]
        party = self.customer_by_label.get(self.customer.currentText(), {})
        selected = self.selected_source or {}
        party_name = str(source_header.get("party_name") or party.get("name") or self.customer.currentText())
        phone = str(
            party.get("phone")
            or party.get("mobile")
            or selected.get("phone")
            or selected.get("customer_phone")
            or selected.get("supplier_phone")
            or ""
        )
        header = dict(source_header)
        header.update(
            {
                "no": source_header.get("doc_no") or self.doc_no.text(),
                "date": source_header.get("doc_date") or self.doc_date.date().toString("yyyy-MM-dd"),
                "party": party_name,
                "party_name": party_name,
                "customer_name": party_name,
                "supplier_name": party_name,
                "party_gstin": party.get("gstin")
                or selected.get("gstin")
                or selected.get("customer_gstin")
                or selected.get("supplier_gstin")
                or "",
                "party_phone": phone,
                "address": party.get("address") or selected.get("address") or selected.get("party_address") or "",
                "area": source_header.get("area") or party.get("area") or "",
                "payment": source_header.get("payment") or self.pay_mode.currentText(),
                "warehouse": source_header.get("warehouse") or self.warehouse.currentText(),
                "shipping": selected.get("shipping_address") or selected.get("address") or "",
                "employee": source_header.get("employee") or "Administrator",
                "transport": selected.get("transport") or selected.get("transport_details") or "",
            }
        )
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
        prints = self.config.project_root / "prints"
        safe_doc = str(header.get("no") or self.doc_no.text()).replace("/", "_").replace(" ", "_")
        path = prints / f"{self.mode}_{safe_doc}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        title = str(self.meta["title"])
        doc_type = str(self.meta.get("doc_type") or self.mode)
        party_label = "Supplier" if str(source_header.get("party_type") or "").lower() == "supplier" else "Bill To"
        ship_to = str(self.company.get("address") or "") if party_label == "Supplier" else str(header.get("shipping") or "")
        write_transaction_pdf(
            path,
            title,
            self.company,
            header,
            lines,
            totals,
            document_type=doc_type,
            party_label=party_label,
            ship_to=ship_to,
            db_path=self.source.sqlite_path,
        )
        caption = document_share_caption(title, str(header.get("no") or ""), party_name, totals["grand_total"], self.company, path)
        return path, caption, phone

    def _communication_message(self, channel: str, fallback_body: str, path: Path) -> dict[str, str]:
        totals = SalesCalculator(str(self.company.get("state") or "")).totals(self.computed_lines)
        payload = self._transaction_payload(totals)
        header = payload["header"]
        party = self.customer_by_label.get(self.customer.currentText(), {})
        selected = self.selected_source or {}
        party_name = str(header.get("party_name") or party.get("name") or selected.get("party_name") or self.customer.currentText())
        title = str(self.meta["title"])
        document_no = str(header.get("doc_no") or self.doc_no.text())
        doc_type = str(self.meta.get("doc_type") or self.mode)
        context = document_message_context(
            title=title,
            document_no=document_no,
            party_name=party_name,
            amount=totals["grand_total"],
            company=self.company,
            pdf_path=path,
        )
        return communication_message(
            channel=channel,
            document_type=doc_type,
            context=context,
            fallback_subject=f"{title} {document_no}",
            fallback_body=fallback_body,
            db_path=self.source.sqlite_path,
        )

    def _workflow_after_save_note(self) -> str:
        doc_type = str(self.meta.get("doc_type") or "")
        if doc_type in {"quotation", "sales_order"}:
            return "Next: Document Center > Order Conversions > Make Sales Bill."
        if doc_type == "purchase_order":
            return "Next: Document Center > Order Conversions > Make Purchase."
        if doc_type == "delivery_challan":
            return "Next: print the challan, then use Dispatch Return if goods come back."
        if doc_type in {"sales_return", "purchase_return"}:
            return "Voucher and ledger posting completed with this save."
        return "Workflow posting completed."

    def _validate_return_lines(self) -> bool:
        usable = []
        for row in self.computed_lines:
            if row.source.qty <= 0:
                continue
            if row.source.qty > row.source.max_qty + 0.0001:
                QMessageBox.warning(self, str(self.meta["title"]), f"Qty is more than remaining quantity for {row.source.item_name}.")
                return False
            if row.source.free_qty > row.source.max_free_qty + 0.0001:
                QMessageBox.warning(self, str(self.meta["title"]), f"SCH qty is more than remaining SCH quantity for {row.source.item_name}.")
                return False
            usable.append(row)
        if not usable:
            QMessageBox.warning(self, str(self.meta["title"]), "Keep at least one return row with quantity greater than zero.")
            return False
        self.computed_lines = usable
        self._redraw_lines()
        return True

    def _transaction_payload(self, totals: dict[str, float]) -> dict[str, Any]:
        party = self.customer_by_label.get(self.customer.currentText(), {})
        doc_type = str(self.meta["doc_type"])
        party_type = "supplier" if doc_type.startswith("purchase") else "customer"
        default_party = "Supplier" if party_type == "supplier" else "Customer"
        party_name = str(party.get("name") or self.customer.currentText() or default_party)
        if party_name in {"Cash Customer", "Choose Supplier", "Select Customer", "Select Supplier"}:
            party_name = default_party
        source_doc_id = int(self.selected_source.get("id") or 0) if self.selected_source else 0
        source_doc_no = str(self.selected_source.get("bill_no") or "") if self.selected_source else ""
        if self.selected_source and doc_type == "sales_return":
            party_name = str(self.selected_source.get("customer_name") or party_name)
            party_id = self.selected_source.get("customer_id") or party.get("id") or 0
            area = self.selected_source.get("customer_area") or self.area.currentText()
            warehouse_id = self.selected_source.get("warehouse_id") or 0
            payment = self.selected_source.get("pay_mode") or self.pay_mode.currentText()
        elif self.selected_source and doc_type == "purchase_return":
            party_name = str(self.selected_source.get("supplier_name") or party_name)
            party_id = self.selected_source.get("supplier_id") or party.get("id") or 0
            area = self.area.currentText()
            warehouse_id = self.selected_source.get("warehouse_id") or 0
            payment = self.selected_source.get("pay_mode") or self.pay_mode.currentText()
        else:
            party_id = party.get("id") or 0
            area = self.area.currentText()
            warehouse_id = 0
            payment = self.pay_mode.currentText()
        header = {
            "doc_no": self.doc_no.text().strip(),
            "doc_date": self.doc_date.date().toString("yyyy-MM-dd"),
            "doc_type": doc_type,
            "party_type": party_type,
            "party_id": party_id,
            "party_name": party_name,
            "area": area,
            "warehouse": self.warehouse.currentText(),
            "warehouse_id": warehouse_id,
            "payment": payment,
            "valid_until": self.valid_until.date().toString("yyyy-MM-dd"),
            "delivery_date": self.valid_until.date().toString("yyyy-MM-dd"),
            "status": self.status.currentText(),
            "notes": self.notes.toPlainText().strip(),
            "price_level": "Purchase" if party_type == "supplier" else "Retail",
            "branch": str(self.selected_source.get("branch_name") or "") if self.selected_source else "",
            "cost_center": str(self.selected_source.get("cost_center_name") or "") if self.selected_source else "",
            "employee": "",
            "source_doc_id": source_doc_id,
            "source_doc_no": source_doc_no,
            "sale_id": source_doc_id if doc_type == "sales_return" else 0,
            "purchase_id": source_doc_id if doc_type == "purchase_return" else 0,
        }
        return {
            "source": "desktop_sales_document",
            "mode": self.mode,
            "doc_type": doc_type,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "header": header,
            "lines": [
                {
                    "item_name": row.source.item_name,
                    "pack_name": row.source.pack_name,
                    "hsn": row.source.hsn,
                    "unit": row.source.unit,
                    "qty": row.source.qty,
                    "free_qty": row.source.free_qty,
                    "mrp": row.source.mrp,
                    "rate": row.source.rate,
                    "discount_amount": row.source.discount_amount,
                    "gst_rate": row.source.gst_rate,
                    "taxable": row.taxable,
                    "gst_total": row.gst_total,
                    "line_total": row.line_total,
                    "source_item_id": row.source.source_item_id,
                    "source_doc_id": row.source.source_doc_id,
                    "source_doc_no": row.source.source_doc_no,
                    "max_qty": row.source.max_qty,
                    "max_free_qty": row.source.max_free_qty,
                }
                for row in self.computed_lines
            ],
            "totals": totals,
        }

    def _require_party(self) -> bool:
        if self.customer_by_label.get(self.customer.currentText()):
            return True
        label = str(self.meta.get("party_label", "Party")).lower()
        QMessageBox.warning(self, str(self.meta["title"]), f"Select a {label} before item entry.")
        self.customer.setFocus()
        return False

    def _generate_doc_no(self) -> str:
        if self.doc_no.text().strip():
            return self.doc_no.text().strip()
        prefixes = {
            "quotation": "QUO",
            "sales_order": "ORD",
            "delivery_challan": "DC",
            "purchase_order": "PO",
            "purchase_return": "DNT",
        }
        prefix = prefixes.get(str(self.meta.get("doc_type")) or "", "DOC")
        generated = f"{prefix}-{datetime.now():%y%m%d-%H%M%S}"
        self.doc_no.setText(generated)
        return generated

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("F4"), self, activated=self.add_line)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_draft)
        QShortcut(QKeySequence("F8"), self, activated=self.save_draft)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.print_document_pdf)
        QShortcut(QKeySequence("F9"), self, activated=self.print_document_pdf)
        QShortcut(QKeySequence("F10"), self, activated=self.print_document_pdf)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.clear_document)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.product.setFocus())
        QShortcut(QKeySequence("F3"), self, activated=lambda: self.product.setFocus())
        QShortcut(QKeySequence("Delete"), self, activated=self.remove_selected_line)
