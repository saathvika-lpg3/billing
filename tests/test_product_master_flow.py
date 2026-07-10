import sqlite3

from services.master_repository import MasterRepository


def test_product_save_and_safe_deactivate(tmp_path):
    db_path = tmp_path / "product_master_test.db"
    repository = MasterRepository(db_path)

    payload = {
        "code": "P-1001",
        "supplier_id": 0,
        "category_id": 0,
        "brand_id": 0,
        "name": "Test Product",
        "hsn": "1801",
        "gst": 18.0,
        "item_type": "Stock Item",
        "status": "Active",
        "sku_alias": "TP1",
        "sale_unit": "PCS",
        "purchase_unit": "PCS",
        "unit": "PCS",
        "batch_required": False,
        "expiry_required": False,
        "item_notes": "Regression test",
        "packs": [
            {
                "pack_size": 1,
                "pack_unit": "PCS",
                "display_name": "1 PCS",
                "barcode": "TEST123",
                "mrp": 100.0,
                "purchase_rate": 80.0,
                "sale_rate": 95.0,
                "dealer_rate": 90.0,
                "distributor_rate": 88.0,
                "wholesale_rate": 92.0,
                "retail_rate": 95.0,
                "box_qty": 10,
                "opening_stock_qty": 50,
                "current_stock_qty": 50,
                "low_stock_alert": 5,
                "reorder_qty": 20,
                "is_default": 1,
                "is_active": 1,
            }
        ],
    }

    product_id = repository.save_product(payload)
    assert product_id > 0

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT code, name, hsn, gst, unit, sale_unit, purchase_unit, barcode FROM items WHERE id=?",
            (product_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == "P-1001"
    assert row[2] == "1801"
    assert row[3] == 18.0
    assert row[4] == "PCS"
    assert row[5] == "PCS"
    assert row[6] == "PCS"

    repository.deactivate_product(product_id)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT status FROM items WHERE id=?", (product_id,)).fetchone()

    assert row is not None
    assert row[0] == "Inactive"
