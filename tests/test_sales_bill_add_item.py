from __future__ import annotations

import os
import sqlite3
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem

from config.app_config import AppConfig
from services.mysql_source import MySqlSource
from views.sales_bill_view import SalesBillView


_APP: QApplication | None = None
PROJECT_ROOT = Path(r"D:\PRM_GST_DESKTOP")


def app() -> QApplication:
    global _APP
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def config() -> AppConfig:
    return AppConfig(project_root=PROJECT_ROOT, source_root=Path(r"D:\PRM_GST_DESKTOP"))


def test_add_item_with_missing_product_fields_does_not_raise(monkeypatch) -> None:
    app()
    view = SalesBillView(config())
    monkeypatch.setattr(view, "_require_customer", lambda: True)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    try:
        view.product.addItem("Missing Field Product")
        view.product.setCurrentText("Missing Field Product")
        view.product_by_label["Missing Field Product"] = {
            "item_name": "Missing Field Product",
            "pack_name": "",
            "hsn": None,
            "unit": None,
            "stock_qty": object(),
            "item_id": object(),
            "pack_id": object(),
            "pack_size": object(),
            "gst": None,
            "mrp": None,
            "sale_rate": None,
            "wholesale_rate": None,
            "distributor_rate": None,
            "retail_rate": None,
            "dealer_rate": None,
            "scheme": None,
        }
        view.qty.setText("1")
        view.rate.setText("10")
        view.gst.setCurrentText("18")
        view.mrp.setText("")
        view.discount.setText("0")
        view.free_qty.setText("0")
        view.scheme.setText("0")

        view.add_line()

        assert view.computed_lines == []
    finally:
        view.close()


def test_add_item_with_empty_product_cache_shows_warning(monkeypatch) -> None:
    app()
    view = SalesBillView(config())
    monkeypatch.setattr(view, "_require_customer", lambda: True)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    try:
        view.product_by_label.clear()
        view.product.setCurrentText("")
        view.add_line()
        assert view.computed_lines == []
    finally:
        view.close()


def test_add_item_with_valid_product_adds_line(monkeypatch) -> None:
    app()
    view = SalesBillView(config())
    monkeypatch.setattr(view, "_require_customer", lambda: True)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    try:
        view.product.addItem("Valid Product")
        view.product.setCurrentText("Valid Product")
        view.product_by_label["Valid Product"] = {
            "item_name": "Valid Product",
            "pack_name": "Pack",
            "hsn": "1234",
            "unit": "PCS",
            "stock_qty": 20,
            "item_id": 1,
            "pack_id": 2,
            "pack_size": 1,
            "gst": 18,
            "mrp": 100,
            "sale_rate": 90,
            "wholesale_rate": 85,
            "distributor_rate": 80,
            "retail_rate": 95,
            "dealer_rate": 88,
            "scheme": 0,
        }
        view.qty.setText("2")
        view.rate.setText("90")
        view.gst.setCurrentText("18")
        view.mrp.setText("100")
        view.discount.setText("0")
        view.free_qty.setText("0")
        view.scheme.setText("0")

        view.add_line()

        assert len(view.computed_lines) == 1
        assert view.computed_lines[0].source.item_name == "Valid Product"
    finally:
        view.close()


def test_product_choices_reads_sqlite_tables_only(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "prm_billing_inventory.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, code TEXT, hsn TEXT, gst REAL, supplier_id INTEGER, barcode TEXT, mrp REAL, buy_rate REAL, sale_rate REAL, unit TEXT, stock REAL, status TEXT)")
        conn.execute("CREATE TABLE suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        conn.execute("CREATE TABLE product_packs (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, display_name TEXT, pack_size REAL, pack_unit TEXT, mrp REAL, purchase_rate REAL, sale_rate REAL, dealer_rate REAL, distributor_rate REAL, wholesale_rate REAL, retail_rate REAL, current_stock_qty REAL, scheme TEXT, is_active INTEGER, is_default INTEGER)")
        conn.execute("INSERT INTO suppliers (id, name) VALUES (1, 'ACME')")
        conn.execute("INSERT INTO items (id, name, code, hsn, gst, supplier_id, barcode, mrp, buy_rate, sale_rate, unit, stock, status) VALUES (1, 'Widget', 'W1', 'HSN1', 18.0, 1, 'B1', 100.0, 80.0, 90.0, 'PCS', 10.0, 'Active')")
        conn.execute("INSERT INTO product_packs (id, product_id, display_name, pack_size, pack_unit, mrp, purchase_rate, sale_rate, dealer_rate, distributor_rate, wholesale_rate, retail_rate, current_stock_qty, scheme, is_active, is_default) VALUES (1, 1, 'Widget Pack', 1.0, 'PCS', 100.0, 80.0, 90.0, 88.0, 85.0, 82.0, 95.0, 10.0, '0', 1, 1)")
        conn.commit()

    monkeypatch.setenv("PRM_SQLITE_DB", str(db_path))
    monkeypatch.setenv("PRM_USE_SQLITE", "0")
    source = MySqlSource()
    rows = source.product_choices()

    assert len(rows) == 1
    assert rows[0]["item_name"] == "Widget"
    assert rows[0]["supplier_name"] == "ACME"
    assert rows[0]["pack_name"] == "Widget Pack"


def test_sales_bill_grid_tab_moves_to_next_editable_cell() -> None:
    app()
    view = SalesBillView(config())
    try:
        view.table.setRowCount(1)
        view.table.setColumnCount(12)
        view.table.setHorizontalHeaderLabels(["#", "Item Description", "HSN", "Qty", "Unit", "MRP", "Rate", "SCH", "Disc", "Taxable", "GST", "Amount"])
        view.table.set_editable_columns({3, 4, 5, 6, 7, 8, 10})
        item = QTableWidgetItem("1")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        view.table.setItem(0, 3, item)
        view.table.setFocus()
        view.table.setCurrentCell(0, 3)

        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
        view.table.keyPressEvent(event)

        assert view.table.currentColumn() == 4
    finally:
        view.close()


def test_runtime_data_source_module_has_no_pysqlite_import() -> None:
    import services.mysql_source as module

    assert "import pysqlite" not in Path(module.__file__).read_text(encoding="utf-8")
