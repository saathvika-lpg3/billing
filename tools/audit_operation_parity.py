from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from views.module_hub_view import (
    ACCOUNTS_OPERATIONS,
    ADMIN_OPERATIONS,
    DOCUMENT_OPERATIONS,
    INVENTORY_OPERATIONS,
    MASTERS_OPERATIONS,
    PURCHASE_OPERATIONS,
    REPORTS_OPERATIONS,
    SALES_OPERATIONS,
)


EXPECTED = {
    "Masters": [
        "Categories",
        "Products",
        "Customers",
        "Suppliers",
        "Brands",
        "Schemes / Offers",
        "Units",
        "GST Rates",
        "Excel Import",
        "Product Labels",
        "Employees",
    ],
    "Sales": [
        "Quotation",
        "Quotation List",
        "Sales Order",
        "Order List",
        "Sales Bill",
        "Sales List",
        "Delivery Challan",
        "DC List",
        "Sales Return",
        "Return List",
    ],
    "Document Center": [
        "Print Bills",
        "Print Batches",
        "Print Templates",
        "Product Labels",
        "Print Logs",
    ],
    "Purchase": [
        "Purchase Order",
        "PO List",
        "Buy Stock",
        "Purchase List",
        "Purchase Return",
        "Debit Notes",
        "Supplier Ledger",
    ],
    "Inventory": [
        "Stock",
        "Stock Entry",
        "Stock Transfer",
        "Transfer List",
        "Stock Adjustment",
        "Stock Alerts",
        "Negative Stock",
        "Expiry / Wastage",
        "Vehicle Stock Out",
        "Load Challans",
        "Route Settlement",
        "Warehouses",
        "Stock Movement",
    ],
    "Accounts": [
        "Receipts",
        "Payments",
        "Expenses",
        "Cash / Bank Book",
        "Journal Entry",
        "Ledger Heads",
        "Outstanding",
        "Aging Report",
        "Customer Ledger",
        "Ledger Groups",
        "Trial Balance",
        "Voucher Register",
        "Voucher Review",
        "Bank Reconciliation",
        "Cash Flow",
        "Fund Flow",
        "ERP Ledger",
        "ERP Day Book",
        "Account Closing",
        "Control Check",
        "Branches",
        "Cost Centers",
        "ERP Profit & Loss",
        "Balance Sheet",
        "Stock Ledger Adj.",
    ],
    "Reports": [
        "Sales Reports",
        "Purchase Reports",
        "Stock Reports",
        "Item Movement",
        "GST Reports",
        "GST Return",
        "E-Invoice",
        "E-Way Bill",
        "Profit & Loss",
        "Day Book",
        "Audit Log",
        "Daily Dispatch Summary",
        "Item Loading Sheet",
        "Route Loading Sheet",
        "Pending Dispatch",
        "Loading Sheet",
        "Customer Loading Sheet",
        "Dispatch Return Summary",
        "Account Closing",
        "Balance Sheet",
        "Trial Balance",
        "GST Postings",
        "Stock Postings",
        "Inventory Valuation",
        "GST Adjustment",
        "ITC Reconciliation",
        "GSTR-9 Annual",
    ],
    "Administration": [
        "Developer Admin",
        "Company",
        "Users",
        "Role Permissions",
        "Financial Years",
        "Print Settings",
        "Backup",
        "LAN Setup",
        "Dashboard Settings",
    ],
}


CURRENT = {
    "Masters": MASTERS_OPERATIONS,
    "Sales": SALES_OPERATIONS,
    "Document Center": DOCUMENT_OPERATIONS,
    "Purchase": PURCHASE_OPERATIONS,
    "Inventory": INVENTORY_OPERATIONS,
    "Accounts": ACCOUNTS_OPERATIONS,
    "Reports": REPORTS_OPERATIONS,
    "Administration": ADMIN_OPERATIONS,
}


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "docs" / "operation_parity_checklist.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PRM_GST Operation Parity Checklist",
        "",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        "This report compares the desktop top-menu operation labels against the PRM_GST menu set collected from the portal screenshots and source scan.",
        "",
    ]
    total_missing = 0
    total_preview = 0
    for group, expected_labels in EXPECTED.items():
        operations = CURRENT[group]
        current_labels = [operation.label for operation in operations]
        missing = [label for label in expected_labels if label not in current_labels]
        extras = [label for label in current_labels if label not in expected_labels]
        full_pages = [operation.label for operation in operations if operation.target_page]
        preview_pages = [operation.label for operation in operations if not operation.target_page]
        total_missing += len(missing)
        total_preview += len(preview_pages)
        lines.extend(
            [
                f"## {group}",
                "",
                f"- Expected options: {len(expected_labels)}",
                f"- Desktop options: {len(current_labels)}",
                f"- Missing labels: {', '.join(missing) if missing else 'None'}",
                f"- Extra desktop labels: {', '.join(extras) if extras else 'None'}",
                f"- Full workflow pages: {len(full_pages)}",
                f"- Preview/list/report pages: {len(preview_pages)}",
                "",
                "| Option | Desktop Status | Route Key |",
                "| --- | --- | --- |",
            ]
        )
        by_label = {operation.label: operation for operation in operations}
        for label in expected_labels:
            operation = by_label.get(label)
            if operation:
                status = "Full workflow" if operation.target_page else "Preview/list"
                lines.append(f"| {label} | {status} | `{operation.target_page or operation.key}` |")
            else:
                lines.append(f"| {label} | Missing | - |")
        lines.append("")
    lines.extend(
        [
            "## Summary",
            "",
            f"- Missing labels: {total_missing}",
            f"- Preview/list pages still needing deeper workflows: {total_preview}",
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
