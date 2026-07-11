from __future__ import annotations

import csv
import os
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QApplication,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.document_archive_service import DocumentArchiveService
from services.mysql_source import MySqlSource
from services.order_conversion_service import OrderConversionService
from services.pdf_print import document_share_caption, write_transaction_pdf
from services.print_preview import show_print_preview
from services.share_service import open_whatsapp_share, pdf_share_note, prepare_whatsapp_document
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPGrid


DOCUMENT_CATALOG = [
    ("Order Conversions", "order_conversions"),
    ("Print Bills", "print_bills"),
    ("Print Batches", "print_batches"),
    ("Print Templates", "print_templates"),
    ("Template Families", "print_template_families"),
    ("Product Labels", "product_labels"),
    ("Print Logs", "print_logs"),
]

PRINT_DOCUMENT_TYPES = [
    ("Sales Bills", "sales"),
    ("Purchase Bills", "purchases"),
    ("Quotations", "quotation"),
    ("Sales Orders", "sales_order"),
    ("Purchase Orders", "purchase_order"),
    ("Delivery Challans", "delivery_challan"),
    ("Sales Returns", "sales_return"),
    ("Purchase Returns", "purchase_return"),
]

PRINT_DOC_META = {
    "sales": {"table": "sales", "title": "Tax Invoice", "document_type": "sales_invoice", "party_label": "Bill To", "party_kind": "customer"},
    "purchases": {"table": "purchases", "title": "Purchase Invoice", "document_type": "purchase_invoice", "party_label": "Supplier", "party_kind": "supplier"},
    "quotation": {"table": "order_documents", "title": "Quotation", "document_type": "quotation", "party_label": "Party", "order_type": "quotation"},
    "sales_order": {"table": "order_documents", "title": "Sales Order", "document_type": "sales_order", "party_label": "Party", "order_type": "sales_order"},
    "purchase_order": {"table": "order_documents", "title": "Purchase Order", "document_type": "purchase_order", "party_label": "Supplier", "order_type": "purchase_order"},
    "delivery_challan": {"table": "order_documents", "title": "Delivery Challan", "document_type": "delivery_challan", "party_label": "Party", "order_type": "delivery_challan"},
    "sales_return": {"table": "sales_returns", "title": "Credit Note", "document_type": "sales_return", "party_label": "Customer"},
    "purchase_return": {"table": "purchase_returns", "title": "Debit Note", "document_type": "purchase_return", "party_label": "Supplier"},
}


class DocumentCenterView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.conversions = OrderConversionService(self.source.sqlite_path)
        self.archive = DocumentArchiveService(config, self.source.sqlite_path)
        self.rows: list[dict[str, Any]] = []
        self.visible_rows: list[dict[str, Any]] = []
        self._build()
        self.run_view()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        root.addWidget(self._title_bar())
        root.addWidget(self._filter_bar())
        root.addWidget(self._table_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Document Center", "Print bills, templates, label batches and print audit history")
        header.setMaximumHeight(58)
        header.status_label.setText("Ready")
        self.status_label = header.status_label
        return header

    def _filter_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        self.filter_card = frame
        frame.setMaximumHeight(264)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)
        self.filter_hint = QLabel("Select document type, period and filters, then click Show Bills. Tick rows before Print Selected, Bulk Print Visible or WhatsApp.")
        self.filter_hint.setObjectName("hintText")
        self.filter_hint.setWordWrap(True)
        self.filter_hint.setToolTip("Use the dropdowns to choose document type and period. Type party, payment mode or search text, then click Show Bills.")
        layout.addWidget(self.filter_hint)
        self.view_selector = QComboBox()
        for label, key in DOCUMENT_CATALOG:
            self.view_selector.addItem(label, key)
        self.view_selector.currentIndexChanged.connect(self._view_changed)
        self.print_doc_type = QComboBox()
        for label, key in PRINT_DOCUMENT_TYPES:
            self.print_doc_type.addItem(label, key)
        self.date_preset = QComboBox()
        self.date_preset.addItem("Today", "today")
        self.date_preset.addItem("This Month", "this_month")
        self.date_preset.addItem("All Dates", "all")
        self.date_preset.addItem("Custom", "custom")
        self.date_preset.currentIndexChanged.connect(self._preset_changed)
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate())
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "Cancelled", "Open", "Accepted", "Ready", "Closed"])
        self.print_status = QComboBox()
        self.print_status.addItems(["All", "Unprinted", "Printed"])
        self.party_filter = QLineEdit()
        self.party_filter.setPlaceholderText("Customer / supplier / party")
        self.pay_filter = QLineEdit()
        self.pay_filter.setPlaceholderText("Payment mode")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter visible document rows")
        self.search.textChanged.connect(self._redraw_table)
        self._set_filter_control_sizes()
        self.show_button = QPushButton("Show Bills")
        self.show_button.clicked.connect(self.run_view)
        self.select_all = QCheckBox("Select all visible")
        self.select_all.setToolTip("Tick or clear all visible bill rows below.")
        self.select_all.stateChanged.connect(self._toggle_select_all)
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        top_row.addWidget(self._inline_field("View", self.view_selector, 210))
        top_row.addWidget(self._inline_field("Print Type", self.print_doc_type, 210))
        top_row.addWidget(self._inline_field("Period", self.date_preset, 150))
        top_row.addWidget(self._inline_field("From", self.from_date, 150))
        top_row.addWidget(self._inline_field("To", self.to_date, 150))
        top_row.addStretch(1)
        layout.addLayout(top_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        filter_row.addWidget(self._inline_field("Party", self.party_filter, 320), stretch=2)
        filter_row.addWidget(self._inline_field("Status", self.status_filter, 150))
        filter_row.addWidget(self._inline_field("Print", self.print_status, 150))
        filter_row.addWidget(self._inline_field("Pay", self.pay_filter, 190))
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        search_row.addWidget(self._inline_field("Search", self.search, 260), stretch=1)
        self.show_button.setMinimumHeight(28)
        self.show_button.setMinimumWidth(96)
        search_row.addWidget(self.show_button)
        search_row.addStretch(2)
        layout.addLayout(search_row)

        self.action_toolbar = CompactActionToolbar(
            [
                ActionSpec("Export CSV", self.export_csv, "Export the visible rows to CSV."),
                ActionSpec("Convert Selected", self.convert_selected, "Convert the selected order into its target transaction."),
                ActionSpec("Mark Accepted", lambda: self.set_selected_status("Accepted"), "Mark the selected order as Accepted."),
                ActionSpec("Mark Ready", lambda: self.set_selected_status("Ready"), "Mark the selected order as Ready."),
                ActionSpec("Close", lambda: self.set_selected_status("Closed"), "Close the selected order without conversion.", role="destructive"),
                ActionSpec("Print Selected", self.print_selected_pdf, "Print preview for checked or selected bills."),
                ActionSpec("Bulk Print Visible", self.bulk_print_visible, "Create one print preview for every visible bill row."),
                ActionSpec("WhatsApp", self.share_selected_pdf, "Prepare the checked or selected bill PDF for WhatsApp sharing.", role="positive"),
            ]
        )
        self.export_button = self.action_toolbar.button("Export CSV")
        self.convert_button = self.action_toolbar.button("Convert Selected")
        self.accept_button = self.action_toolbar.button("Mark Accepted")
        self.ready_button = self.action_toolbar.button("Mark Ready")
        self.close_button = self.action_toolbar.button("Close")
        self.print_button = self.action_toolbar.button("Print Selected")
        self.bulk_button = self.action_toolbar.button("Bulk Print Visible")
        self.whatsapp_button = self.action_toolbar.button("WhatsApp")
        action_row = QHBoxLayout()
        action_row.setSpacing(6)
        action_row.addWidget(self.select_all)
        action_row.addWidget(self.action_toolbar, stretch=1)
        layout.addLayout(action_row)
        self._set_filter_tooltips()
        self._view_changed()
        return frame

    def _inline_field(self, label: str, widget: QWidget, width: int) -> QWidget:
        box = ERPFieldBox(label, widget)
        widget.setMinimumWidth(self._compact_filter_width(widget, width))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return box

    def _compact_filter_width(self, widget: QWidget, width: int) -> int:
        if widget in (self.view_selector, self.print_doc_type):
            return 200
        if widget in (self.date_preset, self.from_date, self.to_date, self.status_filter, self.print_status):
            return 140
        if widget is self.party_filter:
            return 220
        if widget is self.pay_filter:
            return 160
        return min(width, 260)

    def _set_filter_tooltips(self) -> None:
        tooltips = [
            (self.view_selector, "Choose the document work area, for example Print Bills or Order Conversions."),
            (self.print_doc_type, "Choose which bill, order, quotation, challan or return type to load."),
            (self.date_preset, "Choose Today, This Month, All Dates or Custom date filtering."),
            (self.from_date, "Starting bill date for the document search."),
            (self.to_date, "Ending bill date for the document search."),
            (self.party_filter, "Type customer, supplier, party name or area to narrow the list."),
            (self.status_filter, "Filter documents by workflow status."),
            (self.print_status, "Show all documents, only printed documents or only unprinted documents."),
            (self.pay_filter, "Filter by payment mode such as Cash, Credit, UPI or Bank."),
            (self.search, "Search inside the rows already loaded below."),
            (self.show_button, "Load bills using the selected filters."),
            (self.export_button, "Export the visible rows to CSV."),
            (self.convert_button, "Convert quotation or sales order to Sales Bill, or purchase order to Purchase."),
            (self.accept_button, "Mark the selected quotation or order as Accepted."),
            (self.ready_button, "Mark the selected quotation or order as Ready."),
            (self.close_button, "Close the selected quotation or order without conversion."),
            (self.print_button, "Print preview for the checked or selected bills."),
            (self.bulk_button, "Create one print preview for every visible bill row."),
            (self.whatsapp_button, "Prepare the checked or selected bill PDF for WhatsApp sharing."),
        ]
        for widget, tooltip in tooltips:
            widget.setToolTip(tooltip)

    def _set_filter_control_sizes(self) -> None:
        sizes = {
            self.view_selector: 210,
            self.print_doc_type: 210,
            self.date_preset: 150,
            self.from_date: 150,
            self.to_date: 150,
            self.status_filter: 150,
            self.print_status: 150,
            self.party_filter: 320,
            self.pay_filter: 190,
            self.search: 260,
        }
        for widget, width in sizes.items():
            widget.setMinimumWidth(self._compact_filter_width(widget, width))
            widget.setMinimumHeight(24)
            widget.setMaximumHeight(30)
        for combo in [self.view_selector, self.print_doc_type, self.date_preset, self.status_filter, self.print_status]:
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(10)

    def _table_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        return frame

    def _view_changed(self) -> None:
        key = str(self.view_selector.currentData())
        is_print = key == "print_bills"
        is_flow = key == "order_conversions"
        if hasattr(self, "filter_hint"):
            self.filter_hint.setText(
                "Select quotation, sales order or purchase order, click Show Bills, then use Convert Selected or the status buttons."
                if is_flow
                else "Select document type, period and filters, then click Show Bills. Tick rows before Print Selected, Bulk Print Visible or WhatsApp."
            )
        for widget in [
            self.print_doc_type,
            self.date_preset,
            self.from_date,
            self.to_date,
            self.status_filter,
            self.print_status,
            self.party_filter,
            self.pay_filter,
        ]:
            widget.setEnabled(is_print)
        self.select_all.setVisible(is_print)
        self.select_all.setEnabled(is_print and self.table.rowCount() > 0)
        for button in [self.print_button, self.bulk_button, self.whatsapp_button]:
            button.setVisible(is_print)
            button.setEnabled(is_print)
        for button in [self.convert_button, self.accept_button, self.ready_button, self.close_button]:
            button.setVisible(is_flow)
            button.setEnabled(is_flow)

    def _toggle_select_all(self, state: int) -> None:
        if str(self.view_selector.currentData()) != "print_bills":
            return
        checked = state == Qt.CheckState.Checked.value
        for row_index in range(self.table.rowCount()):
            item = self.table.item(row_index, 0)
            if item and item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _reset_select_all(self, enabled: bool) -> None:
        self.select_all.blockSignals(True)
        self.select_all.setChecked(False)
        self.select_all.setEnabled(enabled and str(self.view_selector.currentData()) == "print_bills")
        self.select_all.blockSignals(False)

    def _preset_changed(self) -> None:
        preset = str(self.date_preset.currentData())
        today = QDate.currentDate()
        if preset == "today":
            self.from_date.setDate(today)
            self.to_date.setDate(today)
        elif preset == "this_month":
            self.from_date.setDate(QDate(today.year(), today.month(), 1))
            self.to_date.setDate(today)

    def run_view(self) -> None:
        key = str(self.view_selector.currentData())
        try:
            if key == "print_bills":
                self.rows = self._load_print_rows(1000)
            else:
                self.rows = self.conversions.candidates(1000) if key == "order_conversions" else self.source.operation_rows(key, 1000)
            self.status_label.setText(f"{self.view_selector.currentText()} | {len(self.rows)} rows")
        except Exception as exc:
            self.rows = [{"Status": f"Source unavailable: {exc}"}]
            self.status_label.setText("Source unavailable")
        self._redraw_table()

    def _load_print_rows(self, limit: int = 1000) -> list[dict[str, Any]]:
        state = self._print_filter_state()
        doc_type = state["doc_type"]
        meta = PRINT_DOC_META[doc_type]
        table = str(meta["table"])
        where: list[str] = []
        params: list[Any] = []
        date_field = "bill_date"
        party_fields = ["party_name"]
        pay_field = "pay_mode"
        if table == "order_documents":
            date_field = "doc_date"
            party_fields = ["party_name", "area"]
            where.append("LOWER(REPLACE(doc_type,' ','_'))=?")
            params.append(str(meta["order_type"]))
            select_sql = """
                SELECT id,doc_no bill_no,doc_date bill_date,party_id,party_name,area party_area,
                       employee_name,pay_mode,status,cgst_total,sgst_total,igst_total,gst_total,
                       grand_total,0 print_count,'' last_printed_at,'' last_printed_by,
                       'order_documents' document_table,doc_type source_type
                FROM order_documents
            """
        elif table == "sales_returns":
            date_field = "return_date"
            party_fields = ["customer_name"]
            pay_field = ""
            select_sql = """
                SELECT id,return_no bill_no,return_date bill_date,customer_id party_id,customer_name party_name,
                       '' party_area,'' employee_name,'' pay_mode,status,cgst_total,sgst_total,igst_total,
                       gst_total,grand_total,0 print_count,'' last_printed_at,'' last_printed_by,
                       'sales_returns' document_table,'sales_return' source_type
                FROM sales_returns
            """
        elif table == "purchase_returns":
            date_field = "return_date"
            party_fields = ["supplier_name"]
            pay_field = ""
            select_sql = """
                SELECT id,return_no bill_no,return_date bill_date,supplier_id party_id,supplier_name party_name,
                       '' party_area,'' employee_name,'' pay_mode,status,cgst_total,sgst_total,igst_total,
                       gst_total,grand_total,0 print_count,'' last_printed_at,'' last_printed_by,
                       'purchase_returns' document_table,'purchase_return' source_type
                FROM purchase_returns
            """
        elif table == "purchases":
            party_fields = ["supplier_name"]
            select_sql = """
                SELECT id,bill_no,bill_date,supplier_id party_id,supplier_name party_name,'' party_area,
                       employee_name,pay_mode,status,cgst_total,sgst_total,igst_total,gst_total,
                       grand_total,COALESCE(print_count,0) print_count,last_printed_at,last_printed_by,
                       'purchases' document_table,'purchases' source_type
                FROM purchases
            """
        else:
            party_fields = ["customer_name", "customer_area"]
            select_sql = """
                SELECT id,bill_no,bill_date,customer_id party_id,customer_name party_name,customer_area party_area,
                       employee_name,pay_mode,status,cgst_total,sgst_total,igst_total,gst_total,
                       grand_total,COALESCE(print_count,0) print_count,last_printed_at,last_printed_by,
                       'sales' document_table,'sales' source_type
                FROM sales
            """
        if state["from"]:
            where.append(f"{date_field} >= ?")
            params.append(state["from"])
        if state["to"]:
            where.append(f"{date_field} <= ?")
            params.append(state["to"])
        if state["status"] != "All":
            where.append("status = ?")
            params.append(state["status"])
        if state["print_status"] == "Unprinted" and table in {"sales", "purchases"}:
            where.append("COALESCE(print_count,0)=0")
        elif state["print_status"] == "Printed" and table in {"sales", "purchases"}:
            where.append("COALESCE(print_count,0)>0")
        if state["party"]:
            like = f"%{state['party']}%"
            where.append("(" + " OR ".join(f"{field} LIKE ?" for field in party_fields) + ")")
            params.extend([like] * len(party_fields))
        if state["pay"] and pay_field:
            where.append(f"{pay_field} LIKE ?")
            params.append(f"%{state['pay']}%")
        sql = select_sql + (" WHERE " + " AND ".join(where) if where else "") + f" ORDER BY {date_field} DESC,id DESC LIMIT ?"
        params.append(int(limit))
        rows = self.source.rows(sql, tuple(params))
        return rows

    def _print_filter_state(self) -> dict[str, str]:
        preset = str(self.date_preset.currentData() or "today")
        use_dates = preset != "all"
        return {
            "doc_type": str(self.print_doc_type.currentData() or "sales"),
            "preset": preset,
            "from": self.from_date.date().toString("yyyy-MM-dd") if use_dates else "",
            "to": self.to_date.date().toString("yyyy-MM-dd") if use_dates else "",
            "status": self.status_filter.currentText(),
            "print_status": self.print_status.currentText(),
            "party": self.party_filter.text().strip(),
            "pay": self.pay_filter.text().strip(),
            "search": self.search.text().strip(),
        }

    def open_view(self, key: str) -> None:
        for index in range(self.view_selector.count()):
            if self.view_selector.itemData(index) == key:
                self.view_selector.setCurrentIndex(index)
                self.run_view()
                return
        self.run_view()

    def open_document_record(self, doc_type: str, record_id: int) -> None:
        for index in range(self.view_selector.count()):
            if self.view_selector.itemData(index) == "print_bills":
                self.view_selector.setCurrentIndex(index)
                break
        for index in range(self.print_doc_type.count()):
            if self.print_doc_type.itemData(index) == doc_type:
                self.print_doc_type.setCurrentIndex(index)
                break
        for index in range(self.date_preset.count()):
            if self.date_preset.itemData(index) == "all":
                self.date_preset.setCurrentIndex(index)
                break
        self.status_filter.setCurrentText("All")
        self.print_status.setCurrentText("All")
        self.party_filter.clear()
        self.pay_filter.clear()
        self.search.clear()
        self.run_view()
        if self._select_visible_record(record_id):
            self.status_label.setText(f"{self.print_doc_type.currentText()} | selected #{record_id}")
        else:
            self.status_label.setText(f"{self.print_doc_type.currentText()} | document #{record_id} not visible")

    def _select_visible_record(self, record_id: int) -> bool:
        for row_index, row in enumerate(self.visible_rows):
            if int(row.get("id") or 0) != record_id:
                continue
            self.table.clearSelection()
            self.table.selectRow(row_index)
            self.table.setFocus()
            item = self.table.item(row_index, 1 if self.table.columnCount() > 1 else 0)
            if item is not None:
                self.table.scrollToItem(item)
            return True
        return False

    def export_csv(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "Document Center", "Open a document view before export.")
            return
        default_name = f"{self.view_selector.currentText().replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = self.config.project_root / "reports" / default_name
        default_path.parent.mkdir(parents=True, exist_ok=True)
        path_text, _ = QFileDialog.getSaveFileName(self, "Export Document View", str(default_path), "CSV Files (*.csv)")
        if not path_text:
            return
        headers = list(self.rows[0].keys())
        with open(path_text, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows({key: self._display(row.get(key, "")) for key in headers} for row in self.rows)
        QMessageBox.information(self, "Document Center", f"Document view exported:\n{path_text}")

    def print_selected_pdf(self) -> None:
        if str(self.view_selector.currentData()) != "print_bills":
            QMessageBox.information(self, "Document Center", "Choose Print Bills, then select one or more bills.")
            return
        rows = self._selected_rows()
        if not rows:
            QMessageBox.information(self, "Document Center", "Select one or more bills first.")
            return
        try:
            path = self._create_print_preview_pdf(rows, "Selected")
        except ValueError as exc:
            QMessageBox.information(self, "Document Center", str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, "Document Center", f"PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, "Document Print Preview")

    def bulk_print_visible(self) -> None:
        if str(self.view_selector.currentData()) != "print_bills":
            QMessageBox.information(self, "Document Center", "Choose Print Bills before bulk print.")
            return
        rows = list(self.visible_rows)
        if not rows:
            QMessageBox.information(self, "Document Center", "No visible bills to bulk print.")
            return
        if len(rows) > 300:
            QMessageBox.information(self, "Document Center", "Bulk preview is limited to 300 documents. Narrow the filter first.")
            return
        try:
            path = self._create_print_preview_pdf(rows, "Visible Filter")
        except Exception as exc:
            QMessageBox.warning(self, "Document Center", f"Bulk print failed:\n{exc}")
            return
        show_print_preview(self, path, "Bulk Print Preview")

    def share_selected_pdf(self) -> None:
        try:
            selected = self._selected_rows()
            if len(selected) > 1:
                raise ValueError("Select only one bill for WhatsApp sharing.")
            path, caption, phone = self._create_selected_pdf()
            QApplication.clipboard().setText(f"{caption}\nPDF: {path}")
            try:
                os.startfile(str(path.parent))
            except OSError:
                pass
            result = prepare_whatsapp_document(phone, caption, path)
            if not result.get("ok"):
                if result.get("code") != "missing_phone":
                    open_whatsapp_share(phone, caption)
                detail = str(result.get("message") or "Automatic PDF attachment was not completed.")
                QMessageBox.information(self, "Document Center WhatsApp", f"{detail}\n\n{pdf_share_note(path)}")
                return
        except ValueError as exc:
            QMessageBox.information(self, "Document Center", str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, "Document Center", f"WhatsApp PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Document Center WhatsApp", str(result.get("message") or pdf_share_note(path)))

    def _create_selected_pdf(self) -> tuple[Path, str, str]:
        key = str(self.view_selector.currentData())
        if key != "print_bills":
            raise ValueError("Choose Print Bills, then select one bill.")
        row = self._selected_row()
        if not row:
            raise ValueError("Select one bill first.")
        return self._create_document_pdf(row, None, "WhatsApp Share")

    def _selected_row(self) -> dict[str, Any] | None:
        rows = self._selected_rows()
        return rows[0] if rows else None

    def _selected_rows(self) -> list[dict[str, Any]]:
        checked_rows: list[dict[str, Any]] = []
        has_checkbox_column = self.table.columnCount() > 0 and self.table.horizontalHeaderItem(0) and self.table.horizontalHeaderItem(0).text() == "Select"
        if has_checkbox_column:
            for row_index in range(self.table.rowCount()):
                item = self.table.item(row_index, 0)
                if item and item.checkState() == Qt.CheckState.Checked and 0 <= row_index < len(self.visible_rows):
                    checked_rows.append(self.visible_rows[row_index])
            if checked_rows:
                return checked_rows
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return []
        rows: list[dict[str, Any]] = []
        for model_index in sorted(selected, key=lambda index: index.row()):
            row_index = model_index.row()
            if 0 <= row_index < len(self.visible_rows):
                rows.append(self.visible_rows[row_index])
        return rows

    def _create_print_preview_pdf(self, rows: list[dict[str, Any]], scope: str) -> Path:
        if not rows:
            raise ValueError("No documents selected for print.")
        state = self._print_filter_state()
        doc_type = state["doc_type"]
        batch_id = self.archive.create_print_batch(doc_type, scope, state, len(rows), "")
        paths = self._create_document_pdfs(rows, batch_id, f"Bulk Print Preview - {scope}")
        if len(paths) == 1:
            return paths[0]
        meta = {
            "module": "document_center",
            "document_type": f"{doc_type}_bulk",
            "doc_no": f"{doc_type}_{scope}_{len(paths)}_documents",
            "doc_date": datetime.now().strftime("%Y-%m-%d"),
            "report_name": f"{PRINT_DOC_META[doc_type]['title']} {scope} Batch",
            "category": "Print Batches",
        }
        target = self.archive.archive_path(meta, "pdf")
        self.archive.merge_pdfs(paths, target)
        self.archive.log_archive(meta, [target], "Success", f"Merged {len(paths)} documents into one print preview.", "Bulk Print Preview")
        return target

    def _create_document_pdfs(self, rows: list[dict[str, Any]], batch_id: int | None, action: str) -> list[Path]:
        paths: list[Path] = []
        for row in rows:
            path, _, _ = self._create_document_pdf(row, batch_id, action)
            paths.append(path)
        if not paths:
            raise ValueError("Selected documents do not have valid IDs.")
        return paths

    def _create_document_pdf(self, row: dict[str, Any], batch_id: int | None, action: str) -> tuple[Path, str, str]:
        source_type = self._source_type(row.get("source_type") or self._print_filter_state()["doc_type"])
        if source_type == "sales":
            return self._create_sales_pdf(int(row.get("id") or 0), batch_id, action)
        if source_type == "purchases":
            return self._create_purchase_pdf(int(row.get("id") or 0), batch_id, action)
        if source_type in {"quotation", "sales_order", "purchase_order", "delivery_challan"}:
            return self._create_order_pdf(int(row.get("id") or 0), source_type, batch_id, action)
        if source_type == "sales_return":
            return self._create_return_pdf(int(row.get("id") or 0), "sales_return", batch_id, action)
        if source_type == "purchase_return":
            return self._create_return_pdf(int(row.get("id") or 0), "purchase_return", batch_id, action)
        raise ValueError("Selected document type is not printable yet.")

    def _source_type(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_")

    def _create_sales_pdf(self, sale_id: int, batch_id: int | None = None, action: str = "Print Preview") -> tuple[Path, str, str]:
        db_path = self.source.sqlite_path
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            company_row = conn.execute("SELECT * FROM company LIMIT 1").fetchone()
            sale_row = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
            if not company_row or not sale_row:
                raise ValueError("Selected bill was not found.")
            company = dict(company_row)
            sale = dict(sale_row)
            items = [dict(row) for row in conn.execute("SELECT * FROM sales_items WHERE sale_id=? ORDER BY id", (sale_id,))]
            customer = None
            if sale.get("customer_id"):
                customer = conn.execute("SELECT * FROM customers WHERE id=?", (sale.get("customer_id"),)).fetchone()
        customer_data = dict(customer) if customer else {}
        lines = []
        for item in items:
            lines.append(
                {
                    "item": f"{item.get('item_name') or ''} / {item.get('pack_display_snapshot') or item.get('unit') or ''}",
                    "hsn": item.get("hsn"),
                    "qty": item.get("qty"),
                    "free": item.get("free_qty"),
                    "unit": item.get("unit"),
                    "mrp": item.get("mrp"),
                    "rate": item.get("rate"),
                    "disc": item.get("discount"),
                    "taxable": item.get("taxable"),
                    "cgst": item.get("cgst"),
                    "sgst": item.get("sgst"),
                    "igst": item.get("igst"),
                    "gst": item.get("gst"),
                    "amount": item.get("total"),
                }
            )
        header = {
            "no": sale.get("bill_no"),
            "date": sale.get("bill_date"),
            "party_name": sale.get("customer_name"),
            "party_gstin": customer_data.get("gstin") or "",
            "party_phone": customer_data.get("phone") or "",
            "address": customer_data.get("address") or "",
            "area": sale.get("customer_area") or customer_data.get("area") or "",
            "payment": sale.get("pay_mode"),
            "warehouse": "Main Store",
            "employee": sale.get("employee_name") or "Administrator",
            "shipping": sale.get("shipping_address"),
            "po_no": sale.get("po_no"),
            "transport": sale.get("transport_details"),
            "credit_terms": sale.get("credit_terms"),
        }
        totals = {
            "taxable": sale.get("taxable"),
            "discount": sum(float(item.get("discount") or 0) for item in items),
            "cgst": sale.get("cgst_total"),
            "sgst": sale.get("sgst_total"),
            "igst": sale.get("igst_total"),
            "gst_total": sale.get("gst_total"),
            "round_off": sale.get("round_off"),
            "grand_total": sale.get("grand_total"),
        }
        archive_meta = self._archive_meta("Sales Invoice", sale.get("bill_no") or sale_id, sale.get("bill_date"), sale.get("customer_name"), company)
        path = self.archive.archive_path(archive_meta, "pdf")
        write_transaction_pdf(
            path,
            "Tax Invoice",
            company,
            header,
            lines,
            totals,
            document_type="sales_invoice",
            party_label="Bill To",
            ship_to=str(sale.get("shipping_address") or ""),
            db_path=db_path,
        )
        self.archive.log_archive(archive_meta, [path], "Success", "Sales invoice PDF archived.", action)
        self.archive.record_print("sales", sale_id, "Sales Invoice", str(sale.get("bill_no") or sale_id), str(sale.get("customer_name") or ""), batch_id=batch_id, action=action)
        caption = document_share_caption("Tax Invoice", str(sale.get("bill_no") or sale_id), str(sale.get("customer_name") or ""), sale.get("grand_total"), company, path)
        return path, caption, str(customer_data.get("phone") or "")

    def _create_purchase_pdf(self, purchase_id: int, batch_id: int | None = None, action: str = "Print Preview") -> tuple[Path, str, str]:
        db_path = self.source.sqlite_path
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            company_row = conn.execute("SELECT * FROM company LIMIT 1").fetchone()
            purchase_row = conn.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,)).fetchone()
            if not company_row or not purchase_row:
                raise ValueError("Selected purchase bill was not found.")
            company = dict(company_row)
            purchase = dict(purchase_row)
            items = [dict(row) for row in conn.execute("SELECT * FROM purchase_items WHERE purchase_id=? ORDER BY id", (purchase_id,))]
            supplier = None
            if purchase.get("supplier_id"):
                supplier = conn.execute("SELECT * FROM suppliers WHERE id=?", (purchase.get("supplier_id"),)).fetchone()
        supplier_data = dict(supplier) if supplier else {}
        lines = [self._line_from_item(item) for item in items]
        header = {
            "no": purchase.get("bill_no"),
            "date": purchase.get("bill_date"),
            "party_name": purchase.get("supplier_name"),
            "party_gstin": supplier_data.get("gstin") or "",
            "party_phone": supplier_data.get("phone") or "",
            "address": supplier_data.get("address") or "",
            "payment": purchase.get("pay_mode"),
            "warehouse": "Main Store",
            "employee": purchase.get("employee_name") or "Administrator",
        }
        totals = self._totals_from_header(purchase)
        archive_meta = self._archive_meta("Purchase Invoice", purchase.get("bill_no") or purchase_id, purchase.get("bill_date"), purchase.get("supplier_name"), company)
        path = self.archive.archive_path(archive_meta, "pdf")
        write_transaction_pdf(
            path,
            "Purchase Invoice",
            company,
            header,
            lines,
            totals,
            document_type="purchase_invoice",
            party_label="Supplier",
            ship_to=str(company.get("address") or ""),
            db_path=db_path,
        )
        self.archive.log_archive(archive_meta, [path], "Success", "Purchase invoice PDF archived.", action)
        self.archive.record_print("purchases", purchase_id, "Purchase Invoice", str(purchase.get("bill_no") or purchase_id), str(purchase.get("supplier_name") or ""), batch_id=batch_id, action=action)
        caption = document_share_caption("Purchase Invoice", str(purchase.get("bill_no") or purchase_id), str(purchase.get("supplier_name") or ""), purchase.get("grand_total"), company, path)
        return path, caption, str(supplier_data.get("phone") or "")

    def _create_order_pdf(self, doc_id: int, source_type: str, batch_id: int | None = None, action: str = "Print Preview") -> tuple[Path, str, str]:
        db_path = self.source.sqlite_path
        meta = PRINT_DOC_META[source_type]
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            company_row = conn.execute("SELECT * FROM company LIMIT 1").fetchone()
            doc_row = conn.execute("SELECT * FROM order_documents WHERE id=?", (doc_id,)).fetchone()
            if not company_row or not doc_row:
                raise ValueError("Selected order document was not found.")
            company = dict(company_row)
            doc = dict(doc_row)
            items = [dict(row) for row in conn.execute("SELECT * FROM order_document_items WHERE order_document_id=? ORDER BY id", (doc_id,))]
        lines = [self._line_from_item(item) for item in items]
        header = {
            "no": doc.get("doc_no"),
            "date": doc.get("doc_date"),
            "party_name": doc.get("party_name"),
            "address": "",
            "area": doc.get("area") or "",
            "payment": doc.get("pay_mode"),
            "warehouse": "Main Store",
            "employee": doc.get("employee_name") or "Administrator",
            "credit_terms": doc.get("notes") or "",
        }
        totals = self._totals_from_header(doc)
        archive_meta = self._archive_meta(str(meta["title"]), doc.get("doc_no") or doc_id, doc.get("doc_date"), doc.get("party_name"), company, document_key=str(meta["document_type"]))
        path = self.archive.archive_path(archive_meta, "pdf")
        write_transaction_pdf(
            path,
            str(meta["title"]),
            company,
            header,
            lines,
            totals,
            document_type=str(meta["document_type"]),
            party_label=str(meta["party_label"]),
            ship_to="",
            db_path=db_path,
        )
        self.archive.log_archive(archive_meta, [path], "Success", f"{meta['title']} PDF archived.", action)
        self.archive.record_print("order_documents", doc_id, str(meta["title"]), str(doc.get("doc_no") or doc_id), str(doc.get("party_name") or ""), batch_id=batch_id, action=action)
        caption = document_share_caption(str(meta["title"]), str(doc.get("doc_no") or doc_id), str(doc.get("party_name") or ""), doc.get("grand_total"), company, path)
        return path, caption, ""

    def _create_return_pdf(self, return_id: int, source_type: str, batch_id: int | None = None, action: str = "Print Preview") -> tuple[Path, str, str]:
        db_path = self.source.sqlite_path
        is_sales = source_type == "sales_return"
        table = "sales_returns" if is_sales else "purchase_returns"
        item_table = "sales_return_items" if is_sales else "purchase_return_items"
        title = "Credit Note" if is_sales else "Debit Note"
        party_label = "Customer" if is_sales else "Supplier"
        party_name_field = "customer_name" if is_sales else "supplier_name"
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            company_row = conn.execute("SELECT * FROM company LIMIT 1").fetchone()
            return_row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (return_id,)).fetchone()
            if not company_row or not return_row:
                raise ValueError("Selected return document was not found.")
            company = dict(company_row)
            ret = dict(return_row)
            items = [dict(row) for row in conn.execute(f"SELECT * FROM {item_table} WHERE return_id=? ORDER BY id", (return_id,))]
        lines = [self._line_from_item(item) for item in items]
        header = {
            "no": ret.get("return_no"),
            "date": ret.get("return_date"),
            "party_name": ret.get(party_name_field),
            "address": "",
            "payment": "",
            "warehouse": "Main Store",
            "credit_terms": ret.get("reason") or "",
        }
        totals = self._totals_from_header(ret)
        archive_meta = self._archive_meta(title, ret.get("return_no") or return_id, ret.get("return_date"), ret.get(party_name_field), company, document_key=source_type)
        path = self.archive.archive_path(archive_meta, "pdf")
        write_transaction_pdf(
            path,
            title,
            company,
            header,
            lines,
            totals,
            document_type=source_type,
            party_label=party_label,
            ship_to="",
            db_path=db_path,
        )
        self.archive.log_archive(archive_meta, [path], "Success", f"{title} PDF archived.", action)
        self.archive.record_print(table, return_id, title, str(ret.get("return_no") or return_id), str(ret.get(party_name_field) or ""), batch_id=batch_id, action=action)
        caption = document_share_caption(title, str(ret.get("return_no") or return_id), str(ret.get(party_name_field) or ""), ret.get("grand_total"), company, path)
        return path, caption, ""

    def _archive_meta(
        self,
        title: str,
        doc_no: Any,
        doc_date: Any,
        party_name: Any,
        company: dict[str, Any],
        *,
        document_key: str = "",
    ) -> dict[str, Any]:
        return {
            "module": "document_center",
            "document_type": document_key or title,
            "doc_no": str(doc_no or "Document"),
            "doc_date": str(doc_date or datetime.now().strftime("%Y-%m-%d")),
            "party_name": str(party_name or ""),
            "company_id": company.get("id") or 0,
            "company_name": company.get("name") or company.get("business_name") or "",
        }

    def _line_from_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "item": f"{item.get('item_name') or ''} / {item.get('pack_display_snapshot') or item.get('unit') or ''}",
            "hsn": item.get("hsn"),
            "qty": item.get("qty"),
            "free": item.get("free_qty"),
            "unit": item.get("unit"),
            "mrp": item.get("mrp"),
            "rate": item.get("rate"),
            "disc": item.get("discount"),
            "taxable": item.get("taxable"),
            "cgst": item.get("cgst"),
            "sgst": item.get("sgst"),
            "igst": item.get("igst"),
            "gst": item.get("gst"),
            "amount": item.get("total"),
        }

    def _totals_from_header(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "taxable": row.get("taxable"),
            "discount": row.get("discount") or 0,
            "cgst": row.get("cgst_total"),
            "sgst": row.get("sgst_total"),
            "igst": row.get("igst_total"),
            "gst_total": row.get("gst_total"),
            "round_off": row.get("round_off"),
            "grand_total": row.get("grand_total"),
        }

    def _redraw_table(self) -> None:
        query = self.search.text().strip().lower()
        filtered = [row for row in self.rows if not query or query in " ".join(str(v) for v in row.values()).lower()]
        self.visible_rows = filtered
        if not filtered:
            self._reset_select_all(False)
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setItem(0, 0, QTableWidgetItem("No matching document rows."))
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            return
        headers = list(filtered[0].keys())
        include_selection = str(self.view_selector.currentData()) == "print_bills"
        self._reset_select_all(include_selection)
        table_headers = (["__select__"] if include_selection else []) + headers
        visible_headers = (["Select"] if include_selection else []) + [header.replace("_", " ").title() for header in headers]
        self.table.setColumnCount(len(table_headers))
        self.table.setRowCount(len(filtered))
        self.table.setHorizontalHeaderLabels(visible_headers)
        for row_index, row in enumerate(filtered):
            offset = 0
            if include_selection:
                check_item = QTableWidgetItem("")
                check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                check_item.setCheckState(Qt.CheckState.Unchecked)
                check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, 0, check_item)
                offset = 1
            for column_index, header in enumerate(headers):
                value = row.get(header)
                item = QTableWidgetItem(self._display(value))
                if isinstance(value, (int, float, Decimal)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column_index + offset, item)
        self.table.resizeRowsToContents()
        self._apply_column_widths(table_headers)

    def _apply_column_widths(self, headers: list[str]) -> None:
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header_view.setStretchLastSection(True)
        compact = {"__select__": 64, "select": 64, "id": 56, "#": 48, "qty": 70}
        medium = {
            "bill_no": 138,
            "doc_no": 138,
            "bill_date": 112,
            "doc_date": 112,
            "status": 108,
            "grand_total": 118,
            "pay_mode": 110,
        }
        wide = {"customer_name": 250, "supplier_name": 250, "party_name": 250, "template_name": 240}
        for index, raw_header in enumerate(headers):
            key = raw_header.strip().lower()
            if key in compact:
                self.table.setColumnWidth(index, compact[key])
            elif key in medium:
                self.table.setColumnWidth(index, medium[key])
            elif key in wide:
                self.table.setColumnWidth(index, wide[key])
            else:
                self.table.setColumnWidth(index, 150)

    def convert_selected(self) -> None:
        if str(self.view_selector.currentData()) != "order_conversions":
            QMessageBox.information(self, "Document Center", "Choose Order Conversions first.")
            return
        row = self._selected_order_row("convert")
        if not row:
            return
        doc_id = int(row.get("id") or 0)
        doc_type = self._source_type(row.get("doc_type"))
        try:
            if doc_type == "purchase_order":
                bill_no, ok = QInputDialog.getText(self, "Convert Purchase Order", "Supplier invoice no:", text=str(row.get("doc_no") or ""))
                if not ok:
                    return
                result = self.conversions.convert_to_purchase(doc_id, bill_no)
            else:
                if QMessageBox.question(self, "Convert Order", "Convert selected document to sales bill?") != QMessageBox.StandardButton.Yes:
                    return
                result = self.conversions.convert_to_sales(doc_id)
        except Exception as exc:
            QMessageBox.warning(self, "Document Center", f"Conversion failed:\n{exc}")
            return
        self.run_view()
        QMessageBox.information(self, "Document Center", f"Converted to {result['bill_no']}.\nTotal: Rs {float(result['grand_total']):,.2f}")

    def set_selected_status(self, status: str) -> None:
        if str(self.view_selector.currentData()) != "order_conversions":
            QMessageBox.information(self, "Document Center", "Choose Order Conversions first.")
            return
        row = self._selected_order_row("update status")
        if not row:
            return
        doc_id = int(row.get("id") or 0)
        try:
            self.conversions.set_status(doc_id, status)
        except Exception as exc:
            QMessageBox.warning(self, "Document Center", f"Status could not be changed:\n{exc}")
            return
        self.run_view()
        QMessageBox.information(self, "Document Center", f"{row.get('doc_no') or 'Document'} marked {status}.")

    def _selected_order_row(self, action: str) -> dict[str, Any] | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Document Center", f"Select one order document to {action}.")
            return None
        row_index = selected[0].row()
        if row_index < 0 or row_index >= len(self.visible_rows):
            return None
        return self.visible_rows[row_index]

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        return "" if value is None else str(value)
