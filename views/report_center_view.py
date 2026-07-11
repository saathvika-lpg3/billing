from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.ca_export_service import CaExportService
from services.gst_payload_service import GstPayloadService
from services.mysql_source import MySqlSource
from services.pdf_print import write_report_pdf, write_statement_pdf
from services.print_preview import show_print_preview
from services.share_service import prepare_email_document
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPGrid


REPORT_CATALOG = [
    ("Sales / Purchase", "Sales List", "sales_list"),
    ("Sales / Purchase", "Sales Register", "sales_register"),
    ("Sales / Purchase", "Purchase Register", "purchase_register"),
    ("Dispatch", "Daily Dispatch Summary", "daily_dispatch_summary"),
    ("Dispatch", "Item Loading Sheet", "item_loading_sheet"),
    ("Dispatch", "Route Loading Sheet", "route_loading_sheet"),
    ("Dispatch", "Pending Dispatch", "pending_dispatch"),
    ("Dispatch", "Loading Sheet", "loading_sheet"),
    ("Dispatch", "Customer Loading Sheet", "customer_loading_sheet"),
    ("Dispatch", "Dispatch Return Summary", "dispatch_return_summary"),
    ("Inventory", "Stock Reports", "stock"),
    ("Inventory", "Item Movement", "item_movement"),
    ("Inventory", "Stock Postings", "stock_postings_report"),
    ("Inventory", "Inventory Valuation", "inventory_valuation"),
    ("GST", "GST Reports", "gst_reports"),
    ("GST", "HSN Summary", "hsn_summary"),
    ("GST", "GST Return", "gst_return"),
    ("GST", "GST Postings", "gst_reports"),
    ("GST", "GST Adjustment", "gst_adjustment"),
    ("GST", "ITC Reconciliation", "itc_reconciliation"),
    ("GST", "GSTR-9 Annual", "gstr9_annual"),
    ("GST", "E-Invoice", "einvoice"),
    ("GST", "E-Way Bill", "eway_bill"),
    ("Accounts", "Profit & Loss", "erp_profit_loss"),
    ("Accounts", "Day Book", "day_book"),
    ("Accounts", "Account Closing", "account_closing"),
    ("Accounts", "Balance Sheet", "balance_sheet"),
    ("Accounts", "Trial Balance", "trial_balance"),
    ("Audit", "Audit Log", "audit_log"),
]


class ReportCenterView(QWidget):
    TOTALABLE_HEADERS = frozenset(
        {
            "qty", "quantity", "free_qty", "total_qty", "total_free",
            "weight", "total_weight", "boxes", "box_qty", "cartons", "carton_qty",
            "invoice_value", "taxable", "gst_total", "grand_total", "net_amount",
            "amount", "total", "value", "total_value", "total_dispatched_qty",
            "total_returned_qty", "collected_amount", "balance",
        }
    )

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.gst_payloads = GstPayloadService(self.source.sqlite_path)
        self.ca_export = CaExportService(self.source.sqlite_path)
        self.rows: list[dict[str, Any]] = []
        self.visible_rows: list[dict[str, Any]] = []
        self.page_index = 0
        self.page_size = 100
        self._build()
        self.run_report()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._filter_bar())
        root.addWidget(self._table_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Report Center", "Fast report preview, search, PDF/CSV export and GST JSON preparation")
        header.setMaximumHeight(58)
        header.status_label.setText("Ready")
        self.status_label = header.status_label
        return header

    def _filter_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        self.filter_frame = frame
        frame.setMinimumHeight(122)
        frame.setMaximumHeight(154)
        layout = QGridLayout(frame)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setHorizontalSpacing(7)
        layout.setVerticalSpacing(4)
        self.report_group = QComboBox()
        self.report_group.setMinimumWidth(150)
        self.report_group.setToolTip("Choose the report family, such as Accounts, GST, Inventory or Dispatch.")
        self.report_group.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.report_group.addItems(["All Reports", *self._report_groups()])
        self.report_group.currentTextChanged.connect(self._fill_report_combo)
        self.report = QComboBox()
        self.report.setMinimumWidth(170)
        self.report.setToolTip("Choose the exact report to run.")
        self.report.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.report.currentIndexChanged.connect(self._update_ca_export_visibility)
        self._fill_report_combo()
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setMinimumWidth(120)
        self.from_date.setToolTip("Starting date for this report.")
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setMinimumWidth(120)
        self.to_date.setToolTip("Ending date for this report.")
        self.search = QLineEdit()
        self.search.setMinimumWidth(170)
        self.search.setMaximumWidth(280)
        self.search.setPlaceholderText("Filter visible report rows")
        self.search.setToolTip("Type a bill number, party, ledger, item or amount to filter the current report.")
        self.search.textChanged.connect(self._reset_page_and_redraw)
        self.ca_export_what = QComboBox()
        self.ca_export_what.addItems([
            "CA to decide after review",
            "ITR-1 Sahaj - salary / pension / one house property",
            "ITR-2 - capital gains / multiple income, no business",
            "ITR-3 - business or profession with books",
            "ITR-4 Sugam - presumptive business or profession",
            "ITR-5 - firm / LLP / AOP / BOI",
            "ITR-6 - company return",
            "ITR-7 - trust / institution return",
        ])
        self.ca_export_format = QComboBox()
        self.ca_export_format.addItems(["Excel", "JSON"])
        self.ca_export_email = QLineEdit()
        self.ca_export_email.setPlaceholderText("CA Email ID")
        self.ca_export_email.setMinimumWidth(170)
        self.assessment_year = QLineEdit()
        self.assessment_year.setPlaceholderText("AY 2027-28")
        self.assessment_year.setMinimumWidth(120)
        self.ca_export_button = QPushButton("Export CA File")
        self.ca_export_button.clicked.connect(self.export_ca_file)
        self.ca_export_panel = QWidget()
        ca_layout = QHBoxLayout(self.ca_export_panel)
        ca_layout.setContentsMargins(0, 0, 0, 0)
        ca_layout.setSpacing(5)
        ca_layout.addWidget(self._field("ITR For CA Export", self.ca_export_what))
        ca_layout.addWidget(self._field("Export Format", self.ca_export_format))
        ca_layout.addWidget(self._field("Assessment Year", self.assessment_year))
        ca_layout.addWidget(self._field("CA Email", self.ca_export_email))
        ca_layout.addWidget(self.ca_export_button)
        self.ca_export_panel.setVisible(False)
        self.first_button = QPushButton("First")
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.last_button = QPushButton("Last")
        self.first_button.clicked.connect(lambda: self._set_page(0))
        self.prev_button.clicked.connect(lambda: self._set_page(self.page_index - 1))
        self.next_button.clicked.connect(lambda: self._set_page(self.page_index + 1))
        self.last_button.clicked.connect(self._last_page)
        self.page_label = QLabel("Page 1")
        self.page_label.setObjectName("caption")
        self.action_toolbar = CompactActionToolbar(
            [
                ActionSpec("Run", self.run_report, "Run the selected report with the selected date range.", role="primary"),
                ActionSpec("Print", self.print_report, "Open a print preview for selected or visible report rows."),
                ActionSpec("Email", self.email_report, "Create the report PDF and open an email with the file attached."),
                ActionSpec("Export CSV", self.export_csv, "Export the visible report rows to CSV."),
                ActionSpec("Export PDF", self.export_pdf, "Save the visible report rows as a PDF."),
                ActionSpec("Prepare GST JSON", self.prepare_gst_json, "Prepare GST JSON for E-Invoice or E-Way Bill reports."),
            ]
        )
        pages = QWidget()
        pages_layout = QHBoxLayout(pages)
        pages_layout.setContentsMargins(0, 0, 0, 0)
        pages_layout.setSpacing(5)
        for button in (self.first_button, self.prev_button, self.next_button, self.last_button):
            pages_layout.addWidget(button)
        pages_layout.addWidget(self.page_label)
        pages_layout.addStretch(1)
        layout.addWidget(self._field("Report Group", self.report_group), 0, 0)
        layout.addWidget(self._field("Report Name", self.report), 0, 1)
        layout.addWidget(self._field("From Date", self.from_date), 0, 2)
        layout.addWidget(self._field("To Date", self.to_date), 0, 3)
        layout.addWidget(self._field("Search", self.search), 1, 0, 1, 2)
        layout.addWidget(pages, 1, 2, 1, 2)
        layout.addWidget(self.action_toolbar, 2, 0, 1, 4)
        layout.addWidget(self.ca_export_panel, 3, 0, 1, 4)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)
        return frame

    def _field(self, label_text: str, widget: QWidget) -> QWidget:
        field = ERPFieldBox(label_text, widget)
        if widget.toolTip():
            field.findChild(QLabel).setToolTip(widget.toolTip())
        return field

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
        self.table.setAlternatingRowColors(True)
        self.statement_panel = QFrame()
        self.statement_panel.setObjectName("statementPanel")
        statement_layout = QVBoxLayout(self.statement_panel)
        statement_layout.setContentsMargins(0, 0, 0, 0)
        statement_layout.setSpacing(5)
        self.statement_title = QLabel("Statement")
        self.statement_title.setObjectName("cardTitle")
        self.statement_caption = QLabel("")
        self.statement_caption.setObjectName("caption")
        statement_layout.addWidget(self.statement_title)
        statement_layout.addWidget(self.statement_caption)
        statement_columns = QHBoxLayout()
        statement_columns.setSpacing(6)
        self.statement_left = self._statement_tree()
        self.statement_right = self._statement_tree()
        self.statement_left.setMinimumHeight(230)
        self.statement_right.setMinimumHeight(230)
        statement_columns.addWidget(self.statement_left, stretch=1)
        statement_columns.addWidget(self.statement_right, stretch=1)
        statement_layout.addLayout(statement_columns, stretch=4)
        self.statement_control = self._statement_tree()
        self.statement_control.setMinimumHeight(220)
        self.statement_control.setMaximumHeight(260)
        statement_layout.addWidget(self.statement_control, stretch=2)
        layout.addWidget(self.statement_panel, stretch=1)
        self.statement_panel.hide()
        return frame

    def _statement_tree(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(True)
        tree.setIndentation(18)
        tree.setUniformRowHeights(True)
        tree.setWordWrap(False)
        tree.setColumnCount(3)
        tree.setHeaderLabels(["Particulars", "Details", "Amount"])
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tree.header().setMinimumSectionSize(80)
        tree.header().setStretchLastSection(False)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        return tree

    def run_report(self) -> None:
        key = str(self.report.currentData())
        try:
            self.rows = self.source.operation_rows(
                key,
                5000,
                self.from_date.date().toString("yyyy-MM-dd"),
                self.to_date.date().toString("yyyy-MM-dd"),
            )
            self.page_index = 0
            self.status_label.setText(f"{self.report.currentText()} | {len(self.rows)} rows")
        except Exception as exc:
            self.rows = [{"Status": f"Source unavailable: {exc}"}]
            self.page_index = 0
            self.status_label.setText("Source unavailable")
        self._redraw_table()

    def open_report(self, key: str) -> None:
        for group, _label, report_key in REPORT_CATALOG:
            if report_key == key:
                self.report_group.setCurrentText(group)
                break
        for index in range(self.report.count()):
            if self.report.itemData(index) == key:
                self.report.setCurrentIndex(index)
                self.run_report()
                return
        self.run_report()

    def _report_groups(self) -> list[str]:
        groups: list[str] = []
        for group, _label, _key in REPORT_CATALOG:
            if group not in groups:
                groups.append(group)
        return groups

    def _fill_report_combo(self, _group: str = "") -> None:
        selected_key = self.report.currentData() if hasattr(self, "report") else None
        group_filter = self.report_group.currentText() if hasattr(self, "report_group") else "All Reports"
        self.report.blockSignals(True)
        self.report.clear()
        for group, label, key in REPORT_CATALOG:
            if group_filter != "All Reports" and group != group_filter:
                continue
            self.report.addItem(label, key)
        if selected_key:
            for index in range(self.report.count()):
                if self.report.itemData(index) == selected_key:
                    self.report.setCurrentIndex(index)
                    break
        self.report.blockSignals(False)

    def _redraw_table(self) -> None:
        if self._is_statement_report():
            self._redraw_statement()
            return
        self.statement_panel.hide()
        self.table.show()
        filtered_all = self._filtered_rows()
        total = len(filtered_all)
        max_page = max(0, (total - 1) // self.page_size)
        self.page_index = max(0, min(self.page_index, max_page))
        start = self.page_index * self.page_size
        filtered = filtered_all[start : start + self.page_size]
        self.visible_rows = filtered
        if not filtered:
            self.visible_rows = []
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setItem(0, 0, QTableWidgetItem("No matching report rows."))
            self._update_page_label(0)
            return
        headers = list(filtered[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(filtered))
        self.table.setHorizontalHeaderLabels([self._pretty(header) for header in headers])
        for row_index, row in enumerate(filtered):
            for column_index, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(self._display(value))
                if isinstance(value, (int, float, Decimal)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column_index, item)
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if str(self.report.currentData()) in {"daily_dispatch_summary", "item_loading_sheet", "route_loading_sheet", "loading_sheet", "customer_loading_sheet"}:
            self._append_grand_total_row(filtered, headers)
        self._update_page_label(total)

    def _is_statement_report(self) -> bool:
        return str(self.report.currentData()) in {"erp_profit_loss", "profit_loss", "balance_sheet", "erp_balance_sheet"}

    def _current_statement_data(self) -> dict[str, Any]:
        key = str(self.report.currentData())
        if key in {"erp_profit_loss", "profit_loss"}:
            return self.source.erp_profit_loss_statement(
                self.from_date.date().toString("yyyy-MM-dd"),
                self.to_date.date().toString("yyyy-MM-dd"),
            )
        return self.source.balance_sheet_statement(self.to_date.date().toString("yyyy-MM-dd"))

    def _write_current_pdf(self, path: Path, rows: list[dict[str, Any]], *, print_rows: bool = False) -> None:
        if self._is_statement_report():
            write_statement_pdf(
                path,
                self.report.currentText(),
                self.source.company(),
                self._current_statement_data(),
                db_path=self.source.sqlite_path,
            )
            return
        payload_rows = [{key: self._display(value) for key, value in row.items()} for row in rows] if print_rows else rows
        filters = {
            "From": self.from_date.date().toString("yyyy-MM-dd"),
            "To": self.to_date.date().toString("yyyy-MM-dd"),
            "Search": self.search.text().strip(),
        }
        if print_rows:
            filters["Rows"] = str(len(rows))
        write_report_pdf(
            path,
            self.report.currentText(),
            self.source.company(),
            payload_rows,
            filters,
            db_path=self.source.sqlite_path,
        )

    def _redraw_statement(self) -> None:
        self.table.hide()
        self.statement_panel.show()
        query = self.search.text().strip().lower()
        statement = self._current_statement_data()
        self.statement_title.setText(str(statement.get("title") or self.report.currentText()))
        self.statement_caption.setText(str(statement.get("period") or ""))
        self._populate_statement_tree(
            self.statement_left,
            str(statement.get("left_heading") or "Particulars"),
            statement.get("left_groups") or [],
            float(statement.get("left_total") or 0),
            query,
        )
        self._populate_statement_tree(
            self.statement_right,
            str(statement.get("right_heading") or "Particulars"),
            statement.get("right_groups") or [],
            float(statement.get("right_total") or 0),
            query,
        )
        self._populate_control_tree(
            str(statement.get("support_title") or "Supporting Analysis"),
            statement.get("controls") or [],
            query,
        )
        self.visible_rows = self._filtered_rows()
        self._update_statement_label(statement)

    def _populate_statement_tree(
        self,
        tree: QTreeWidget,
        heading: str,
        groups: list[dict[str, Any]],
        total: float,
        query: str,
    ) -> None:
        tree.clear()
        tree.setHeaderLabels([heading, "Details", "Amount"])
        shown = 0
        for group in groups:
            if not self._statement_group_matches(group, query):
                continue
            group_item = QTreeWidgetItem([str(group.get("label") or ""), "", self._money(group.get("amount"))])
            self._style_statement_item(group_item, bold=True)
            details = list(group.get("details") or [])
            if details:
                for detail in details:
                    if query and query not in " ".join(str(value) for value in detail.values()).lower() and query not in str(group.get("label") or "").lower():
                        continue
                    child = QTreeWidgetItem(
                        [
                            str(detail.get("ledger") or ""),
                            str(detail.get("group_name") or ""),
                            self._money(detail.get("amount")),
                        ]
                    )
                    child.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    group_item.addChild(child)
            elif group.get("note"):
                child = QTreeWidgetItem([str(group.get("note") or ""), "", ""])
                group_item.addChild(child)
            tree.addTopLevelItem(group_item)
            group_item.setExpanded(bool(group.get("open")))
            shown += 1
        total_item = QTreeWidgetItem(["Total", "", self._money(total)])
        self._style_statement_item(total_item, bold=True)
        tree.addTopLevelItem(total_item)
        if shown == 0:
            empty = QTreeWidgetItem(["No matching statement rows.", "", ""])
            tree.insertTopLevelItem(0, empty)
        tree.resizeColumnToContents(2)
        tree.resizeColumnToContents(1)

    def _populate_control_tree(self, title: str, controls: list[dict[str, Any]], query: str) -> None:
        self.statement_control.clear()
        self.statement_control.setHeaderLabels([title, "Details", "Amount"])
        root = QTreeWidgetItem([title, "", ""])
        self._style_statement_item(root, bold=True)
        for row in controls:
            haystack = " ".join(str(value) for value in row.values()).lower()
            if query and query not in haystack:
                continue
            child = QTreeWidgetItem(
                [
                    str(row.get("label") or ""),
                    str(row.get("group_name") or ""),
                    self._money(row.get("amount")),
                ]
            )
            child.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            root.addChild(child)
        self.statement_control.addTopLevelItem(root)
        root.setExpanded(True)
        self.statement_control.setVisible(root.childCount() > 0)

    def _style_statement_item(self, item: QTreeWidgetItem, *, bold: bool = False) -> None:
        if bold:
            font = QFont()
            font.setBold(True)
            for column in range(item.columnCount()):
                item.setFont(column, font)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _statement_group_matches(self, group: dict[str, Any], query: str) -> bool:
        if not query:
            return True
        if query in f"{group.get('label') or ''} {group.get('amount') or ''}".lower():
            return True
        return any(query in " ".join(str(value) for value in detail.values()).lower() for detail in group.get("details") or [])

    def _update_statement_label(self, statement: dict[str, Any]) -> None:
        left_count = len(statement.get("left_groups") or [])
        right_count = len(statement.get("right_groups") or [])
        self.page_label.setText(f"Statement view | {left_count + right_count} groups")
        self.first_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)

    def export_csv(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "Report Center", "Run a report before export.")
            return
        rows = self._filtered_rows()
        if not rows:
            QMessageBox.information(self, "Report Center", "No visible rows to export.")
            return
        default_name = f"{self.report.currentText().replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = self.config.project_root / "reports" / default_name
        default_path.parent.mkdir(parents=True, exist_ok=True)
        path_text, _ = QFileDialog.getSaveFileName(self, "Export Report", str(default_path), "CSV Files (*.csv)")
        if not path_text:
            return
        headers = list(rows[0].keys())
        with open(path_text, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: self._display(row.get(key, "")) for key in headers})
        QMessageBox.information(self, "Report Center", f"Report exported:\n{path_text}")

    def export_pdf(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "Report Center", "Run a report before export.")
            return
        rows = self._filtered_rows()
        if not rows:
            QMessageBox.information(self, "Report Center", "No visible rows to export.")
            return
        default_name = f"{self.report.currentText().replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        default_path = self.config.project_root / "reports" / default_name
        default_path.parent.mkdir(parents=True, exist_ok=True)
        path_text, _ = QFileDialog.getSaveFileName(self, "Export Report PDF", str(default_path), "PDF Files (*.pdf)")
        if not path_text:
            return
        self._write_current_pdf(Path(path_text), rows)
        QMessageBox.information(self, "Report Center", f"PDF exported:\n{path_text}")

    def print_report(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "Report Center", "Run a report before print.")
            return
        rows = self._selected_rows() or self._filtered_rows()
        if not rows:
            QMessageBox.information(self, "Report Center", "No visible rows to print.")
            return
        default_name = f"{self.report.currentText().replace(' ', '_').lower()}_print_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        default_path = self.config.project_root / "reports" / default_name
        default_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._write_current_pdf(default_path, rows, print_rows=True)
        except Exception as exc:
            QMessageBox.warning(self, "Report Center", f"Report print failed:\n{exc}")
            return
        show_print_preview(self, default_path, f"{self.report.currentText()} Print Preview")

    def email_report(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "Report Center", "Run a report before email.")
            return
        rows = self._selected_rows() or self._filtered_rows()
        if not rows:
            QMessageBox.information(self, "Report Center", "No visible rows to email.")
            return
        safe_name = self.report.currentText().replace(" ", "_").lower()
        path = self.config.project_root / "reports" / "email" / f"{safe_name}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        try:
            self._write_current_pdf(path, rows, print_rows=True)
            result = prepare_email_document(
                "",
                self.report.currentText(),
                f"Please find the {self.report.currentText()} PDF attached.",
                path,
                db_path=self.source.sqlite_path,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Report Center", f"Report email could not be prepared:\n{exc}")
            return
        message = str(result.get("message") or "Email handoff completed.")
        if result.get("ok"):
            QMessageBox.information(self, "Report Center", message)
        else:
            QMessageBox.warning(self, "Report Center", message)

    def prepare_gst_json(self) -> None:
        key = str(self.report.currentData())
        if key not in {"einvoice", "eway_bill"}:
            QMessageBox.information(self, "GST JSON", "Choose E-Invoice or E-Way Bill report first.")
            return
        try:
            result = self.gst_payloads.prepare_pending(key, self.config.project_root / "reports" / "gst_payloads", 50)
        except Exception as exc:
            QMessageBox.warning(self, "GST JSON", f"GST JSON preparation failed:\n{exc}")
            return
        self.run_report()
        QMessageBox.information(
            self,
            "GST JSON",
            f"Prepared {result['prepared']} file(s).\nFolder: {self.config.project_root / 'reports' / 'gst_payloads'}",
        )

    def export_ca_file(self) -> None:
        if str(self.report.currentData()) != "account_closing":
            QMessageBox.information(self, "CA Export", "Select the Account Closing report before exporting a CA file.")
            return
        if not self.rows:
            QMessageBox.information(self, "CA Export", "Run the Account Closing report first.")
            return
        selected = self._selected_rows()
        if len(selected) != 1:
            QMessageBox.information(self, "CA Export", "Select exactly one closing period row to export.")
            return
        closing_period = selected[0]
        export_format = self.ca_export_format.currentText().lower()
        ca_email = self.ca_export_email.text().strip()
        assessment_year = self.assessment_year.text().strip()
        itr_form = self.ca_export_what.currentText()
        try:
            result = self.ca_export.prepare_export(
                closing_period=closing_period,
                output_dir=self.config.project_root / "reports" / "ca_export",
                export_format=export_format,
                ca_email=ca_email,
                itr_form=itr_form,
                assessment_year=assessment_year,
                schema_version="inventory",
            )
        except Exception as exc:
            QMessageBox.warning(self, "CA Export", f"CA export failed:\n{exc}")
            return
        QMessageBox.information(
            self,
            "CA Export",
            f"CA export created:\n{result['file_path']}"
            + (f"\nCA Email: {ca_email}" if ca_email else ""),
        )

    def _update_ca_export_visibility(self) -> None:
        visible = str(self.report.currentData()) == "account_closing"
        self.ca_export_panel.setVisible(visible)
        self._sync_ca_export_panel_height(visible)

    def _sync_ca_export_panel_height(self, visible: bool | None = None) -> None:
        if not hasattr(self, "filter_frame"):
            return
        panel_visible = self.ca_export_panel.isVisible() if visible is None else visible
        if panel_visible:
            self.filter_frame.setMinimumHeight(168)
            self.filter_frame.setMaximumHeight(208)
        else:
            self.filter_frame.setMinimumHeight(122)
            self.filter_frame.setMaximumHeight(154)
        self.filter_frame.updateGeometry()

    def _filtered_rows(self) -> list[dict[str, Any]]:
        query = self.search.text().strip().lower()
        filtered = []
        for row in self.rows:
            haystack = " ".join(str(value) for value in row.values()).lower()
            if not query or query in haystack:
                filtered.append(row)
        return filtered

    def _selected_rows(self) -> list[dict[str, Any]]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return []
        rows: list[dict[str, Any]] = []
        for model_index in sorted(selected, key=lambda index: index.row()):
            row_index = model_index.row()
            if 0 <= row_index < len(self.visible_rows):
                rows.append(self.visible_rows[row_index])
        return rows

    def _reset_page_and_redraw(self) -> None:
        self.page_index = 0
        self._redraw_table()

    def _set_page(self, page_index: int) -> None:
        self.page_index = max(0, page_index)
        self._redraw_table()

    def _last_page(self) -> None:
        total = len(self._filtered_rows())
        self.page_index = max(0, (total - 1) // self.page_size)
        self._redraw_table()

    def _update_page_label(self, total: int) -> None:
        if total <= 0:
            self.page_label.setText("0 records")
            self.first_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.last_button.setEnabled(False)
            return
        start = self.page_index * self.page_size + 1
        end = min(total, start + self.page_size - 1)
        pages = ((total - 1) // self.page_size) + 1
        self.page_label.setText(f"{start}-{end} of {total} | Page {self.page_index + 1} of {pages}")
        self.first_button.setEnabled(self.page_index > 0)
        self.prev_button.setEnabled(self.page_index > 0)
        self.next_button.setEnabled(self.page_index + 1 < pages)
        self.last_button.setEnabled(self.page_index + 1 < pages)

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        return "" if value is None else str(value)

    def _money(self, value: Any) -> str:
        try:
            number = float(value or 0)
            if number < 0:
                return f"({abs(number):,.2f})"
            return f"{number:,.2f}"
        except (TypeError, ValueError):
            return ""

    def _append_grand_total_row(self, rows: list[dict[str, Any]], headers: list[str]) -> None:
        if not rows:
            return
        numeric_headers = self._numeric_total_headers(rows, headers)
        if not numeric_headers:
            return
        totals: dict[str, Any] = {header: sum(float(row.get(header) or 0) for row in rows) for header in numeric_headers}
        footer = {header: "" for header in headers}
        footer_label = "Grand Total"
        footer[list(headers)[0]] = footer_label
        for header in numeric_headers:
            footer[header] = totals[header]
        self.table.insertRow(self.table.rowCount())
        row_index = self.table.rowCount() - 1
        for col_index, header in enumerate(headers):
            item = QTableWidgetItem(self._display(footer.get(header, "")))
            if header in numeric_headers:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if col_index == 0:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.table.setItem(row_index, col_index, item)
        self.table.resizeRowsToContents()

    @classmethod
    def _numeric_total_headers(cls, rows: list[dict[str, Any]], headers: list[str]) -> list[str]:
        return [
            header
            for header in headers
            if header.strip().lower() in cls.TOTALABLE_HEADERS
            and all(isinstance(row.get(header), (int, float, Decimal)) for row in rows)
        ]

    def _pretty(self, value: str) -> str:
        return value.replace("_", " ").strip().title()
