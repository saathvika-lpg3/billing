from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QMessageBox

from config.app_config import AppConfig
from views.sales_document_view import SalesDocumentView


PURCHASE_DOCUMENTS = {
    "purchase_order": {
        "title": "Purchase Order",
        "subtitle": "Supplier order with pack-aware items and GST summary",
        "doc_label": "PO No",
        "party_label": "Supplier",
        "list_key": "po_list",
        "doc_type": "purchase_order",
    },
    "purchase_return": {
        "title": "Purchase Return",
        "subtitle": "Supplier debit note draft with returned item rows",
        "doc_label": "Debit Note No",
        "party_label": "Supplier",
        "list_key": "debit_notes",
        "doc_type": "purchase_return",
    },
}


class PurchaseDocumentView(SalesDocumentView):
    document_catalog = PURCHASE_DOCUMENTS

    def __init__(self, config: AppConfig, mode: str) -> None:
        super().__init__(config, mode)

    def _load_source_data(self) -> None:
        try:
            self.company = self.source.company()
            self.customers = self.source.suppliers()
            self.products = self.source.product_choices()
            warehouses = self.source.warehouses()
            self.recent_rows = self.source.operation_rows(str(self.meta["list_key"]), 100)
            if self._is_return_mode():
                self.source_rows = self.source.purchase_return_sources()
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            return
        supplier_labels = [f"{row.get('name','')} | {row.get('state','')} | Due {float(row.get('balance') or 0):.2f}" for row in self.customers]
        self.customer_by_label = dict(zip(supplier_labels, self.customers))
        self.customer.addItems(["Select Supplier", *supplier_labels])
        states = sorted({str(row.get("state") or "") for row in self.customers if row.get("state")})
        self.area.addItems(["All Suppliers", *states])
        self.warehouse.addItems([row.get("name", "") for row in warehouses] or ["Main Store"])
        self.units = ["PCS"]
        units = self.source.units()
        self.units = [str(u.get("name") or "").strip() for u in units if str(u.get("name") or "").strip()] or ["PCS"]
        self.unit.clear()
        self.unit.addItems(self.units)
        product_labels = [self._product_label(row) for row in self.products]
        self.product_by_label = dict(zip(product_labels, self.products))
        self.product.addItems(product_labels)
        if self._is_return_mode():
            self._fill_source_selector()
        self.source_status.setText(f"{len(self.customers)} suppliers | {len(self.products)} packs | {len(self.recent_rows)} recent")

    def _product_changed(self, label: str) -> None:
        row: dict[str, Any] | None = self.product_by_label.get(label)
        if not row:
            return
        self.hsn.setText(str(row.get("hsn") or ""))
        unit_value = str(row.get("unit") or "PCS")
        if unit_value not in self.units:
            self.units.append(unit_value)
            self.unit.addItem(unit_value)
        self.unit.setCurrentText(unit_value)
        self.mrp.setText(f"{float(row.get('mrp') or 0):.2f}")
        self.rate.setText(f"{float(row.get('purchase_rate') or row.get('buy_rate') or row.get('mrp') or 0):.2f}")
        self.gst.setCurrentText(f"{float(row.get('gst') or 0):.2f}")

    def save_draft(self) -> None:
        if self.customer.currentText() == "Select Supplier":
            QMessageBox.warning(self, str(self.meta["title"]), "Select a supplier before saving.")
            self.customer.setFocus()
            return
        super().save_draft()
