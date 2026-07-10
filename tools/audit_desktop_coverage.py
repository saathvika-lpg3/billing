from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CoverageRow:
    module: str
    prm_option: str
    desktop_target: str
    status: str
    notes: str


ROWS = [
    CoverageRow("Masters", "Categories", "Category Master", "Done", "Desktop master form and live list."),
    CoverageRow("Masters", "Products", "Product Master", "Done", "FMCG packs, barcode, GST, batch/expiry and stock fields."),
    CoverageRow("Masters", "Customers", "Customer Master", "Done", "Desktop party form and live PRM rows."),
    CoverageRow("Masters", "Suppliers", "Supplier Master", "Done", "Desktop party form and live PRM rows."),
    CoverageRow("Masters", "Brands", "Brand Master", "Done", "Brand/manufacturer master."),
    CoverageRow("Masters", "Schemes / Offers", "Scheme Master", "Done", "Desktop scheme draft workflow with product-pack selection."),
    CoverageRow("Masters", "Units", "Unit Master", "Done", "Desktop master form."),
    CoverageRow("Masters", "GST Rates", "GST Rate Master", "Done", "Desktop master form."),
    CoverageRow("Masters", "Excel Import", "Excel Import", "Done", "CSV/XLSX preview and posting for products, packs, parties, opening stock and schemes."),
    CoverageRow("Masters", "Product Labels", "Product Labels / Barcode", "Done", "Label batch preparation and CSV export."),
    CoverageRow("Masters", "Employees", "Employee / User Master", "Done", "Staff user draft workflow and live user list."),
    CoverageRow("Sales", "Quotation", "Quotation Entry", "Done", "Desktop sales document entry with conversion to sales bill."),
    CoverageRow("Sales", "Quotation List", "Sales Hub", "Done", "Live order_documents quotation rows."),
    CoverageRow("Sales", "Sales Order", "Sales Order Entry", "Done", "Desktop sales document entry with conversion to sales bill."),
    CoverageRow("Sales", "Order List", "Sales Hub", "Done", "Live sales order rows."),
    CoverageRow("Sales", "Sales Invoice", "Sales Bill", "Done", "Desktop operator invoice with GST calculations and drafts."),
    CoverageRow("Sales", "Sales List", "Sales Hub / Report Center", "Done", "Live sales rows."),
    CoverageRow("Sales", "Delivery Challan", "Delivery Challan Entry", "Done", "Desktop delivery document with conversion to sales bill."),
    CoverageRow("Sales", "DC List", "Sales Hub", "Done", "Live delivery challan rows."),
    CoverageRow("Sales", "Sales Return", "Sales Return Entry", "Done", "Source-bill return loading, editable quantities and posting."),
    CoverageRow("Sales", "Return List", "Sales Hub", "Done", "Live sales return rows."),
    CoverageRow("Document Center", "Order Conversions", "Document Center", "Done", "Open quotation/order/PO conversion to posted sales or purchase."),
    CoverageRow("Document Center", "Print Bills", "Document Center", "Done", "Live printable sales bill list."),
    CoverageRow("Document Center", "Print Templates", "Document Center", "Done", "Live print_templates/families rows."),
    CoverageRow("Document Center", "Product Labels", "Product Labels / Barcode", "Done", "Desktop label batch screen."),
    CoverageRow("Purchase", "Purchase Order", "Purchase Order Entry", "Done", "Desktop purchase document entry with conversion to purchase."),
    CoverageRow("Purchase", "PO List", "Purchase Hub", "Done", "Live purchase order rows."),
    CoverageRow("Purchase", "Purchase Invoice", "Purchase Entry", "Done", "Desktop purchase entry and draft save."),
    CoverageRow("Purchase", "Purchase List", "Purchase Hub / Report Center", "Done", "Live purchase rows."),
    CoverageRow("Purchase", "Purchase Return", "Purchase Return Entry", "Done", "Source-purchase return loading, editable quantities and posting."),
    CoverageRow("Purchase", "Debit Notes", "Purchase Hub", "Done", "Live purchase return rows."),
    CoverageRow("Purchase", "Supplier Ledger", "Purchase Hub / Accounts", "Done", "Live supplier ledger rows."),
    CoverageRow("Inventory", "Stock", "Stock Dashboard", "Done", "Stock cards and live stock rows."),
    CoverageRow("Inventory", "Stock Entry", "Stock Entry", "Done", "Desktop warehouse item entry draft workflow."),
    CoverageRow("Inventory", "Stock Transfer", "Stock Transfer", "Done", "Desktop transfer draft workflow."),
    CoverageRow("Inventory", "Transfer List", "Inventory Hub", "Done", "Live transfer rows."),
    CoverageRow("Inventory", "Stock Adjustment", "Stock Adjustment", "Done", "Desktop physical count draft workflow."),
    CoverageRow("Inventory", "Stock Alerts", "Stock Dashboard", "Done", "Live low-stock rows."),
    CoverageRow("Inventory", "Negative Stock", "Stock Dashboard", "Done", "Live negative-stock rows."),
    CoverageRow("Inventory", "Expiry / Wastage", "Inventory Hub", "Done", "Live batch expiry rows."),
    CoverageRow("Inventory", "Stock Out", "Stock Out / Load Challan", "Done", "Desktop route load draft workflow."),
    CoverageRow("Inventory", "Load Challans", "Inventory Hub", "Done", "Live stock_outs rows."),
    CoverageRow("Inventory", "Route Settlement", "Route Settlement", "Done", "Desktop settlement draft workflow."),
    CoverageRow("Inventory", "Warehouses", "Warehouse Master", "Done", "Desktop warehouse master."),
    CoverageRow("Inventory", "Stock Movement", "Inventory Hub / Report Center", "Done", "Live stock_log rows."),
    CoverageRow("Accounts", "Receipts", "Receipt Entry", "Done", "Desktop receipt draft workflow."),
    CoverageRow("Accounts", "Payments", "Payment Entry", "Done", "Desktop payment draft workflow."),
    CoverageRow("Accounts", "Expenses", "Expense Entry", "Done", "Desktop expense draft workflow."),
    CoverageRow("Accounts", "Cash/Bank Book", "Accounts Hub", "Done", "Live cash/bank ledger rows."),
    CoverageRow("Accounts", "Journal Entry", "Journal Entry", "Done", "Desktop journal draft workflow."),
    CoverageRow("Accounts", "Ledger Heads", "Ledger Head Master", "Done", "Desktop ledger master draft workflow."),
    CoverageRow("Accounts", "Outstanding", "Accounts Hub", "Done", "Live customer/supplier outstanding rows."),
    CoverageRow("Accounts", "Aging Report", "Accounts Hub", "Done", "Live aging rows."),
    CoverageRow("Accounts", "Customer Ledger", "Accounts Hub", "Done", "Live customer ledger rows."),
    CoverageRow("Accounts", "Ledger Groups", "Accounts Hub", "Done", "Live ledger group rows."),
    CoverageRow("Accounts", "Trial Balance", "Accounts Hub / Report Center", "Done", "Live ledger totals."),
    CoverageRow("Accounts", "Voucher Register", "Accounts Hub", "Done", "Live voucher rows."),
    CoverageRow("Accounts", "Voucher Review", "Accounts Hub", "Done", "Live voucher review rows."),
    CoverageRow("Accounts", "Bank Reconciliation", "Accounts Hub", "Done", "Live bank reconciliation rows."),
    CoverageRow("Accounts", "Cash Flow", "Accounts Hub", "Done", "Live cash flow rows."),
    CoverageRow("Accounts", "Fund Flow", "Accounts Hub", "Done", "Live fund flow rows."),
    CoverageRow("Accounts", "ERP Ledger", "Accounts Hub", "Done", "Live full ledger rows."),
    CoverageRow("Accounts", "ERP Day Book", "Accounts Hub", "Done", "Live day book rows."),
    CoverageRow("Accounts", "Account Closing", "Accounts Hub / Report Center", "Done", "Live closing periods."),
    CoverageRow("Accounts", "Control Check", "Accounts Hub", "Done", "Live ledger and stock control checks."),
    CoverageRow("Accounts", "Branches", "Branch Master", "Done", "Desktop branch master."),
    CoverageRow("Accounts", "Cost Centers", "Cost Center Master", "Done", "Desktop cost center master."),
    CoverageRow("Accounts", "ERP Profit & Loss", "Accounts Hub", "Done", "Live P&L rows."),
    CoverageRow("Accounts", "Balance Sheet", "Accounts Hub / Report Center", "Done", "Live balance rows."),
    CoverageRow("Accounts", "Stock Ledger Adj.", "Accounts Hub", "Done", "Live stock valuation adjustment rows."),
    CoverageRow("Reports", "Sales Reports", "Report Center", "Done", "Live sales rows with CSV/PDF export."),
    CoverageRow("Reports", "Purchase Reports", "Report Center", "Done", "Live purchase rows with CSV/PDF export."),
    CoverageRow("Reports", "Stock Reports", "Report Center", "Done", "Live stock rows with PDF export."),
    CoverageRow("Reports", "Item Movement", "Report Center", "Done", "Live stock movement rows."),
    CoverageRow("Reports", "GST Reports", "Report Center", "Done", "Live GST postings."),
    CoverageRow("Reports", "GST Return", "Report Center", "Done", "Live GST return filings."),
    CoverageRow("Reports", "E-Invoice", "Report Center", "Done", "Live e-invoice rows and offline GST JSON preparation."),
    CoverageRow("Reports", "E-Way Bill", "Report Center", "Done", "Live e-way bill rows and offline GST JSON preparation."),
    CoverageRow("Reports", "Profit & Loss", "Report Center", "Done", "Live P&L rows."),
    CoverageRow("Reports", "Day Book", "Report Center", "Done", "Live voucher day book."),
    CoverageRow("Reports", "Audit Log", "Report Center", "Done", "Live audit rows."),
    CoverageRow("Reports", "Daily Dispatch Summary", "Report Center", "Done", "Live stock_outs summary."),
    CoverageRow("Reports", "Item Loading Sheet", "Report Center", "Done", "Live item loading rows."),
    CoverageRow("Reports", "Route Loading Sheet", "Report Center", "Done", "Live grouped route loading rows."),
    CoverageRow("Reports", "Pending Dispatch", "Report Center", "Done", "Live pending dispatch rows."),
    CoverageRow("Reports", "Loading Sheet", "Report Center", "Done", "Live loading rows."),
    CoverageRow("Reports", "Customer Loading Sheet", "Report Center", "Done", "Live customer dispatch rows."),
    CoverageRow("Reports", "Dispatch Return Summary", "Report Center", "Done", "Live dispatch return rows."),
    CoverageRow("Reports", "GST Postings", "Report Center", "Done", "Live GST postings."),
    CoverageRow("Reports", "Stock Postings", "Report Center", "Done", "Live stock postings."),
    CoverageRow("Reports", "Inventory Valuation", "Report Center", "Done", "Live inventory valuation."),
    CoverageRow("Reports", "GST Adjustment", "Report Center", "Done", "Live GST adjustment rows."),
    CoverageRow("Reports", "ITC Reconciliation", "Report Center", "Done", "Live ITC reconciliation rows."),
    CoverageRow("Reports", "GSTR-9 Annual", "Report Center", "Done", "Live financial-year basis rows."),
    CoverageRow("Administration", "Developer Admin", "Administration Hub", "Done", "Live license/developer rows."),
    CoverageRow("Administration", "Users", "Employee / User Master", "Done", "Desktop staff user master."),
    CoverageRow("Administration", "Permissions", "Administration Hub", "Done", "Live role permissions with desktop editor posting."),
    CoverageRow("Administration", "Financial Years", "Administration Hub", "Done", "Live financial-year rows."),
    CoverageRow("Administration", "Print Settings", "Administration Hub / Document Center", "Done", "Print template editor with PDF preview and HTML/CSS export."),
    CoverageRow("Administration", "Backup", "Administration Hub", "Done", "JSON backup, encrypted .pgst backup and restore wizard."),
    CoverageRow("Administration", "LAN Setup", "Administration Hub", "Done", "Desktop mode removes XAMPP requirement; setup values visible."),
    CoverageRow("Administration", "Company", "Company Settings", "Done", "Desktop company settings draft workflow."),
    CoverageRow("Administration", "Dashboard Settings", "Administration Hub", "Done", "Live dashboard settings rows."),
]


def build_markdown(rows: list[CoverageRow]) -> str:
    done = sum(1 for row in rows if row.status == "Done")
    staged = sum(1 for row in rows if row.status == "Staged")
    lines = [
        "# PRM_GST Desktop Coverage Checklist",
        "",
        f"Generated rows: {len(rows)}",
        f"Done: {done}",
        f"Staged: {staged}",
        "",
        "| Module | PRM_GST option | Desktop target | Status | Notes |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row.module} | {row.prm_option} | {row.desktop_target} | {row.status} | {row.notes} |")
    lines.append("")
    lines.append("Live government API submission for E-Invoice/E-Way remains credential-dependent; desktop offline JSON preparation is available.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "docs" / "DESKTOP_COVERAGE_CHECKLIST.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(ROWS), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
