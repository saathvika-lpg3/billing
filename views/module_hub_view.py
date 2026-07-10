from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from config.app_config import AppConfig
from services.mysql_source import MySqlSource
from services.pdf_print import write_report_pdf
from services.print_preview import show_print_preview
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPToolbar, ERPGrid


@dataclass(frozen=True)
class ModuleOperation:
    label: str
    key: str
    status: str = "Preview"
    target_page: str | None = None
    category: str = ""


class ModuleHubView(QWidget):
    LIST_REPORT_DOCUMENT_TYPES = {
        "sales_list": "sales_invoice",
        "quotation_list": "quotation",
        "order_list": "sales_order",
        "dc_list": "delivery_challan",
        "purchase_list": "purchase_invoice",
    }

    def __init__(
        self,
        config: AppConfig,
        title: str,
        subtitle: str,
        operations: list[ModuleOperation],
        open_page: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.title = title
        self.subtitle = subtitle
        self.operations = operations
        self.open_page_callback = open_page
        self.current_operation = operations[0] if operations else ModuleOperation("No operations", "none")
        self.rows: list[dict[str, Any]] = []
        self.visible_rows: list[dict[str, Any]] = []
        self._build()
        if operations:
            self.open_operation(operations[0])

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        self.operation_panel = self._operation_grid()
        root.addWidget(self.operation_panel)
        root.addWidget(self._data_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader(self.title, self.subtitle)
        header.setMaximumHeight(62)
        header.status_label.setText("")
        self.status_label = header.status_label
        return header

    def _operation_grid(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        has_categories = any(operation.category for operation in self.operations)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(5)
        row = 0
        col = 0
        current_category = ""
        for index, operation in enumerate(self.operations):
            if has_categories and operation.category != current_category:
                if col:
                    row += 1
                    col = 0
                current_category = operation.category
                label = QLabel(current_category or "General")
                label.setObjectName("fieldLabel")
                grid.addWidget(label, row, 0, 1, 5)
                row += 1
            button = QPushButton(operation.label)
            button.setObjectName("quickButton")
            button.setMinimumHeight(28)
            button.clicked.connect(lambda checked=False, op=operation: self.activate_operation(op))
            if has_categories:
                grid.addWidget(button, row, col)
                col += 1
                if col >= 5:
                    row += 1
                    col = 0
            else:
                grid.addWidget(button, index // 5, index % 5)
        for col in range(5):
            grid.setColumnStretch(col, 1)
        scroll = QScrollArea()
        scroll.setObjectName("card")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMaximumHeight(260 if has_categories else 132)
        scroll.setWidget(frame)
        return scroll

    def _data_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        bar = QHBoxLayout()
        self.operation_title = QLabel("Operation")
        self.operation_title.setObjectName("cardTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter current rows")
        self.search.textChanged.connect(self._redraw_table)
        toolbar = ERPToolbar(
            [
                ("Refresh", lambda: self.open_operation(self.current_operation)),
                ("Show Options", self.show_options),
                ("Print", self.print_visible_rows),
                ("Export CSV", self.export_csv),
                ("Export PDF", self.export_pdf),
            ]
        )
        bar.addWidget(self.operation_title)
        bar.addStretch(1)
        bar.addWidget(self.search)
        bar.addWidget(toolbar)
        layout.addLayout(bar)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setDefaultSectionSize(26)
        layout.addWidget(self.table, stretch=1)
        return frame

    def activate_operation(self, operation: ModuleOperation) -> None:
        if operation.target_page and self.open_page_callback:
            self.open_page_callback(operation.target_page)
            return
        self.open_operation(operation)

    def open_operation(self, operation: ModuleOperation) -> None:
        self.current_operation = operation
        self.operation_title.setText(operation.label)
        self.search.clear()
        self.operation_panel.setVisible(bool(operation.target_page))
        try:
            self.rows = self.source.operation_rows(operation.key)
            self.status_label.setText(f"{operation.status} | {len(self.rows)} rows")
        except Exception as exc:
            self.rows = []
            self.status_label.setText(f"Source unavailable: {exc}")
        self._redraw_table()

    def show_options(self) -> None:
        self.operation_panel.setVisible(True)

    def _redraw_table(self) -> None:
        query = self.search.text().strip().lower()
        filtered = []
        for row in self.rows:
            haystack = " ".join(str(value) for value in row.values()).lower()
            if not query or query in haystack:
                filtered.append(row)
        self.visible_rows = filtered
        if not filtered:
            self.visible_rows = []
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            message = "No rows found for this operation."
            if self.current_operation.status != "Preview":
                message = f"{self.current_operation.status}: detailed desktop workflow is queued."
            self.table.setItem(0, 0, QTableWidgetItem(message))
            return
        headers = list(filtered[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(filtered))
        self.table.setHorizontalHeaderLabels([self._pretty(header) for header in headers])
        for row_index, row in enumerate(filtered):
            for col_index, header in enumerate(headers):
                item = QTableWidgetItem(str(row.get(header, "")))
                if isinstance(row.get(header), (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()

    def print_visible_rows(self) -> None:
        rows = self._selected_rows() or self._filtered_rows()
        if not rows:
            QMessageBox.information(self, self.title, "No visible rows to print.")
            return
        default_path = self._default_export_path("pdf")
        document_type = self.LIST_REPORT_DOCUMENT_TYPES.get(str(self.current_operation.key))
        try:
            write_report_pdf(
                default_path,
                self.current_operation.label,
                self.source.company(),
                [{key: self._display(value) for key, value in row.items()} for row in rows],
                {
                    "Module": self.title,
                    "Operation": self.current_operation.label,
                    "Rows": str(len(rows)),
                    "Search": self.search.text().strip(),
                },
                db_path=self.source.sqlite_path,
                document_type=document_type,
            )
        except Exception as exc:
            QMessageBox.warning(self, self.title, f"Print PDF failed:\n{exc}")
            return
        show_print_preview(self, default_path, f"{self.current_operation.label} Print Preview")

    def export_csv(self) -> None:
        rows = self._filtered_rows()
        if not rows:
            QMessageBox.information(self, self.title, "No visible rows to export.")
            return
        default_path = self._default_export_path("csv")
        path_text, _ = QFileDialog.getSaveFileName(self, "Export CSV", str(default_path), "CSV Files (*.csv)")
        if not path_text:
            return
        headers = list(rows[0].keys())
        with open(path_text, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: self._display(row.get(key, "")) for key in headers})
        QMessageBox.information(self, self.title, f"CSV exported:\n{path_text}")

    def export_pdf(self) -> None:
        rows = self._filtered_rows()
        if not rows:
            QMessageBox.information(self, self.title, "No visible rows to export.")
            return
        default_path = self._default_export_path("pdf")
        path_text, _ = QFileDialog.getSaveFileName(self, "Export PDF", str(default_path), "PDF Files (*.pdf)")
        if not path_text:
            return
        document_type = self.LIST_REPORT_DOCUMENT_TYPES.get(str(self.current_operation.key))
        try:
            write_report_pdf(
                Path(path_text),
                self.current_operation.label,
                self.source.company(),
                [{key: self._display(value) for key, value in row.items()} for row in rows],
                {"Module": self.title, "Operation": self.current_operation.label},
                db_path=self.source.sqlite_path,
                document_type=document_type,
            )
        except Exception as exc:
            QMessageBox.warning(self, self.title, f"PDF export failed:\n{exc}")
            return
        QMessageBox.information(self, self.title, f"PDF exported:\n{path_text}")

    def _filtered_rows(self) -> list[dict[str, Any]]:
        query = self.search.text().strip().lower()
        rows = []
        for row in self.rows:
            haystack = " ".join(str(value) for value in row.values()).lower()
            if not query or query in haystack:
                rows.append(row)
        return rows

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

    def _default_export_path(self, extension: str) -> Path:
        name = f"{self.title}_{self.current_operation.label}_{datetime.now():%Y%m%d_%H%M%S}"
        safe = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_").lower()
        folder = self.config.project_root / "reports"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{safe}.{extension}"

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        return "" if value is None else str(value)

    def _pretty(self, value: str) -> str:
        return value.replace("_", " ").strip().title()


MASTERS_OPERATIONS = [
    ModuleOperation("Categories", "categories", "Use Category Master", "category_master"),
    ModuleOperation("Products", "products", "Use Product Master", "product_master"),
    ModuleOperation("Customers", "customers", "Use Customer Master", "customer_master"),
    ModuleOperation("Suppliers", "suppliers", "Use Supplier Master", "supplier_master"),
    ModuleOperation("Brands", "brands", "Use Brand Master", "brand_master"),
    ModuleOperation("Schemes / Offers", "schemes", "Use Scheme Master", "scheme_master"),
    ModuleOperation("Units", "units", "Use Unit Master", "unit_master"),
    ModuleOperation("GST Rates", "gst_rates", "Use GST Rate Master", "gst_rate_master"),
    ModuleOperation("Banks", "banks", "Use Bank Master", "bank_master"),
    ModuleOperation("Tax Codes", "tax_codes", "Use Tax Code Master", "tax_master"),
    ModuleOperation("Payment Terms", "payment_terms", "Use Payment Terms Master", "payment_term_master"),
    ModuleOperation("Excel Import", "master_import", "Use Excel Import", "excel_import"),
    ModuleOperation("Product Labels", "product_labels", "Use Product Labels", "product_labels"),
    ModuleOperation("Employees", "employees", "Use Employee Master", "employee_master"),
]

SALES_OPERATIONS = [
    ModuleOperation("Sales Bill", "sales_bill", "Use Sales Bill tab", "sales_bill"),
    ModuleOperation("Sales List", "sales_list"),
    ModuleOperation("Quotation", "quotation_entry", "Use Quotation", "quotation_entry"),
    ModuleOperation("Quotation List", "quotation_list"),
    ModuleOperation("Sales Order", "sales_order", "Use Sales Order", "sales_order_entry"),
    ModuleOperation("Order List", "order_list"),
    ModuleOperation("Delivery Challan", "delivery_challan", "Use Delivery Challan", "delivery_challan_entry"),
    ModuleOperation("DC List", "dc_list"),
    ModuleOperation("Sales Return", "sales_return", "Use Sales Return", "sales_return_entry"),
    ModuleOperation("Return List", "return_list"),
]

PURCHASE_OPERATIONS = [
    ModuleOperation("Buy Stock", "purchase_entry", "Use Purchase Entry", "purchase_entry"),
    ModuleOperation("Purchase List", "purchase_list"),
    ModuleOperation("Purchase Order", "purchase_order", "Use Purchase Order", "purchase_order_entry"),
    ModuleOperation("PO List", "po_list"),
    ModuleOperation("Purchase Return", "purchase_return", "Use Purchase Return", "purchase_return_entry"),
    ModuleOperation("Debit Notes", "debit_notes"),
    ModuleOperation("Supplier Ledger", "supplier_ledger"),
]

INVENTORY_OPERATIONS = [
    ModuleOperation("Stock", "stock", "Use Stock Dashboard", "stock_dashboard"),
    ModuleOperation("Stock Entry", "stock_entry", "Use Stock Entry", "stock_entry_entry"),
    ModuleOperation("Stock Transfer", "stock_transfer", "Use Stock Transfer", "stock_transfer_entry"),
    ModuleOperation("Transfer List", "transfer_list"),
    ModuleOperation("Stock Adjustment", "stock_adjustment", "Use Stock Adjustment", "stock_adjustment_entry"),
    ModuleOperation("Stock Alerts", "stock_alerts", "Use Stock Dashboard", "stock_dashboard"),
    ModuleOperation("Negative Stock", "negative_stock", "Use Stock Dashboard", "stock_dashboard"),
    ModuleOperation("Expiry / Wastage", "expiry_wastage"),
    ModuleOperation("Vehicle Stock Out", "stock_outs", "Use Stock Out", "stock_out_entry"),
    ModuleOperation("Load Challans", "load_challans"),
    ModuleOperation("Dispatch Return", "dispatch_return_entry", "Use Dispatch Return", "dispatch_return_entry"),
    ModuleOperation("Route Settlement", "route_settlement", "Use Route Settlement", "route_settlement"),
    ModuleOperation("Warehouses", "warehouses", "Use Warehouse Master", "warehouse_master"),
    ModuleOperation("Stock Movement", "stock_entry"),
]

ACCOUNTS_OPERATIONS = [
    ModuleOperation("Receipts", "receipts", "Use Receipt Entry", "receipt_entry", "Entry"),
    ModuleOperation("Payments", "payments", "Use Payment Entry", "payment_entry", "Entry"),
    ModuleOperation("Expenses", "expenses", "Use Expense Entry", "expense_entry", "Entry"),
    ModuleOperation("Journal Entry", "journal", "Use Journal Entry", "journal_entry", "Entry"),
    ModuleOperation("Cash / Bank Book", "cash_bank", category="Books"),
    ModuleOperation("ERP Day Book", "erp_day_book", category="Books"),
    ModuleOperation("Voucher Register", "vouchers", category="Books"),
    ModuleOperation("Voucher Review", "voucher_review", category="Books"),
    ModuleOperation("Ledger Heads", "ledgers", "Use Ledger Master", "ledger_master", "Ledgers"),
    ModuleOperation("Ledger Groups", "ledger_groups", category="Ledgers"),
    ModuleOperation("Customer Ledger", "customer_ledger", category="Ledgers"),
    ModuleOperation("ERP Ledger", "erp_ledger", category="Ledgers"),
    ModuleOperation("Outstanding", "outstanding", category="Statements"),
    ModuleOperation("Aging Report", "aging_report", category="Statements"),
    ModuleOperation("Trial Balance", "trial_balance", category="Statements"),
    ModuleOperation("Profit & Loss", "erp_profit_loss", category="Statements"),
    ModuleOperation("Balance Sheet", "balance_sheet", category="Statements"),
    ModuleOperation("Cash Flow", "cash_flow", category="Statements"),
    ModuleOperation("Fund Flow", "fund_flow", category="Statements"),
    ModuleOperation("Bank Reconciliation", "bank_reconciliation", category="Control"),
    ModuleOperation("Account Closing", "account_closing", "Preview", "reports:account_closing", "Control"),
    ModuleOperation("Control Check", "control_check", category="Control"),
    ModuleOperation("Stock Ledger Adj.", "stock_ledger_adj", category="Control"),
    ModuleOperation("Branches", "branches", "Use Branch Master", "branch_master", "Setup"),
    ModuleOperation("Cost Centers", "cost_centers", "Use Cost Center Master", "cost_center_master", "Setup"),
    ModuleOperation("Routes", "routes", "Use Route Master", "route_master", "Setup"),
    ModuleOperation("Salesmen", "salesmen", "Use Salesman Master", "salesman_master", "Setup"),
    ModuleOperation("Vehicles", "vehicles", "Use Vehicle Master", "vehicle_master", "Setup"),
    ModuleOperation("Transporters", "transporters", "Use Transporter Master", "transporter_master", "Setup"),
    ModuleOperation("Banks", "banks", "Use Bank Master", "bank_master", "Setup"),
    ModuleOperation("Tax Codes", "tax_codes", "Use Tax Code Master", "tax_master", "Setup"),
    ModuleOperation("Payment Terms", "payment_terms", "Use Payment Terms Master", "payment_term_master", "Setup"),
]

REPORTS_OPERATIONS = [
    ModuleOperation("Sales Reports", "sales_list", category="Sales / Purchase"),
    ModuleOperation("Purchase Reports", "purchase_list", category="Sales / Purchase"),
    ModuleOperation("Daily Dispatch Summary", "daily_dispatch_summary", category="Dispatch"),
    ModuleOperation("Item Loading Sheet", "item_loading_sheet", category="Dispatch"),
    ModuleOperation("Route Loading Sheet", "route_loading_sheet", category="Dispatch"),
    ModuleOperation("Pending Dispatch", "pending_dispatch", category="Dispatch"),
    ModuleOperation("Loading Sheet", "loading_sheet", category="Dispatch"),
    ModuleOperation("Customer Loading Sheet", "customer_loading_sheet", category="Dispatch"),
    ModuleOperation("Dispatch Return", "dispatch_return_entry", "Use Dispatch Return", "dispatch_return_entry", "Dispatch"),
    ModuleOperation("Dispatch Return Summary", "dispatch_return_summary", category="Dispatch"),
    ModuleOperation("Stock Reports", "stock", category="Inventory"),
    ModuleOperation("Item Movement", "item_movement", category="Inventory"),
    ModuleOperation("Stock Postings", "stock_postings_report", category="Inventory"),
    ModuleOperation("Inventory Valuation", "inventory_valuation", category="Inventory"),
    ModuleOperation("GST Reports", "gst_reports", category="GST"),
    ModuleOperation("GST Return", "gst_return", category="GST"),
    ModuleOperation("GST Postings", "gst_reports", category="GST"),
    ModuleOperation("GST Adjustment", "gst_adjustment", category="GST"),
    ModuleOperation("ITC Reconciliation", "itc_reconciliation", category="GST"),
    ModuleOperation("GSTR-9 Annual", "gstr9_annual", category="GST"),
    ModuleOperation("E-Invoice", "einvoice", category="GST"),
    ModuleOperation("E-Way Bill", "eway_bill", category="GST"),
    ModuleOperation("Profit & Loss", "erp_profit_loss", category="Accounts"),
    ModuleOperation("Day Book", "vouchers", category="Accounts"),
    ModuleOperation("Account Closing", "account_closing", "Preview", "reports:account_closing", "Accounts"),
    ModuleOperation("Balance Sheet", "balance_sheet", category="Accounts"),
    ModuleOperation("Trial Balance", "trial_balance", category="Accounts"),
    ModuleOperation("Audit Log", "audit_log", category="Audit"),
]

ADMIN_OPERATIONS = [
    ModuleOperation("Developer Admin", "developer_admin", "Open Developer Console", "developer_console"),
    ModuleOperation("Company", "company", "Use Company Settings", "company_settings"),
    ModuleOperation("Users", "users", "Use Employee Master", "employee_master"),
    ModuleOperation("Role Permissions", "role_permissions", "Open Developer Console", "developer_console"),
    ModuleOperation("Financial Years", "financial_years", "Manage fiscal years", "financial_years"),
    ModuleOperation("Numbering Series", "numbering_series", "Manage numbering series", "numbering_series"),
    ModuleOperation("Print Settings", "print_settings", "Open Developer Console", "developer_console"),
    ModuleOperation("Backup", "backup", "Open Developer Console", "developer_console"),
    ModuleOperation("LAN Setup", "lan_setup", "Open Developer Console", "developer_console"),
    ModuleOperation("Dashboard Settings", "dashboard_settings", "Open Developer Console", "developer_console"),
]

INDUSTRY_OPERATIONS = [
    ModuleOperation("Business Types", "business_types", category="Setup"),
    ModuleOperation("POS Billing", "pos_billing", category="Retail / POS"),
    ModuleOperation("Electronics POS", "electronics_pos_billing", category="Retail / POS"),
    ModuleOperation("Pharmacy Retail", "pharmacy_retail_billing", category="Retail / POS"),
    ModuleOperation("Pharmacy Wholesale", "pharmacy_wholesale_billing", category="Retail / POS"),
    ModuleOperation("Dine In", "pos_dine_in", category="Restaurant"),
    ModuleOperation("Take Away", "pos_take_away", category="Restaurant"),
    ModuleOperation("Delivery POS", "pos_delivery", category="Restaurant"),
    ModuleOperation("KOT", "kot_new", category="Restaurant"),
    ModuleOperation("Ready Orders", "ready_orders", category="Restaurant"),
    ModuleOperation("Restaurant Categories", "restaurant_categories", category="Restaurant"),
    ModuleOperation("Restaurant Tables", "restaurant_tables", category="Restaurant"),
    ModuleOperation("Prescription Entry", "prescription_entry", category="Pharmacy"),
    ModuleOperation("Prescription Billing", "prescription_billing", category="Pharmacy"),
    ModuleOperation("Patient History", "patient_history", category="Pharmacy"),
    ModuleOperation("Doctors", "doctors", category="Pharmacy"),
    ModuleOperation("Property Types", "property_types", category="Real Estate"),
    ModuleOperation("Real Estate Units", "real_estate_units", category="Real Estate"),
    ModuleOperation("Leads", "real_estate_leads", category="Real Estate"),
    ModuleOperation("Followups", "real_estate_followups", category="Real Estate"),
    ModuleOperation("Site Visits", "real_estate_site_visits", category="Real Estate"),
    ModuleOperation("Enquiries", "real_estate_enquiries", category="Real Estate"),
    ModuleOperation("New Booking", "real_estate_new_booking", category="Real Estate"),
    ModuleOperation("Agreements", "real_estate_agreements", category="Real Estate"),
    ModuleOperation("Installments", "real_estate_installments", category="Real Estate"),
    ModuleOperation("Refunds", "real_estate_refunds", category="Real Estate"),
    ModuleOperation("Commissions", "real_estate_commissions", category="Real Estate"),
    ModuleOperation("Real Estate Reports", "real_estate_sales_reports", category="Real Estate"),
    ModuleOperation("BOMs", "manufacturing_boms", category="Manufacturing"),
    ModuleOperation("Work Orders", "manufacturing_work_orders", category="Manufacturing"),
    ModuleOperation("Production Orders", "manufacturing_production_orders", category="Manufacturing"),
    ModuleOperation("Production Runs", "production_runs", category="Manufacturing"),
    ModuleOperation("Job Work", "manufacturing_job_work", category="Manufacturing"),
    ModuleOperation("Quality Checks", "manufacturing_quality_checks", category="Manufacturing"),
    ModuleOperation("Manufacturing Reports", "manufacturing_reports", category="Manufacturing"),
    ModuleOperation("Serial Numbers", "serial_numbers", category="Service / Warranty"),
    ModuleOperation("Warranty Tracking", "warranty_tracking", category="Service / Warranty"),
    ModuleOperation("Complaints", "complaints", category="Service / Warranty"),
    ModuleOperation("Job Cards", "job_cards", category="Service / Warranty"),
    ModuleOperation("Repairs", "repairs", category="Service / Warranty"),
    ModuleOperation("Warranty Claims", "warranty_claims", category="Service / Warranty"),
    ModuleOperation("Warranty Reports", "warranty_reports", category="Service / Warranty"),
    ModuleOperation("Refill Reminders", "refill_reminders", category="Service / Warranty"),
]

DOCUMENT_OPERATIONS = [
    ModuleOperation("Print Bills", "print_bills", "Use Document Center", "document_center"),
    ModuleOperation("Print Batches", "print_batches"),
    ModuleOperation("Print Templates", "print_templates"),
    ModuleOperation("Product Labels", "product_labels", "Use Product Labels", "product_labels"),
    ModuleOperation("Print Logs", "print_logs"),
]
