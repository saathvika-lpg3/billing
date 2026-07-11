from __future__ import annotations

import sqlite3

from services.master_repository import MasterRepository
from services.mysql_source import MySqlSource
from services.sales_calculator import SalesCalculator, SalesLine


def _pack() -> dict[str, object]:
    return {
        "pack_size": 1,
        "pack_unit": "PCS",
        "display_name": "1 PCS",
        "mrp": 120,
        "purchase_rate": 80,
        "sale_rate": 100,
        "is_default": 1,
        "is_active": 1,
    }


def _source_for(db_path, monkeypatch) -> MySqlSource:
    monkeypatch.setenv("PRM_SQLITE_DB", str(db_path))
    monkeypatch.setenv("PRM_USE_SQLITE", "0")
    return MySqlSource()


def test_tax_dropdown_combines_gst_rate_and_tax_code_masters(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "tax-master.db"
    repository = MasterRepository(db_path)
    repository.ensure_schema()
    repository.save_simple("gst_rate", 0, {"rate": 5, "name": "GST 5", "is_active": True})
    repository.save_simple(
        "tax_master",
        0,
        {
            "tax_code": "GST12",
            "tax_name": "GST 12",
            "hsn_sac": "1905",
            "gst_rate": 12,
            "cgst": 6,
            "sgst": 6,
            "igst": 0,
            "is_active": True,
        },
    )
    rates = _source_for(db_path, monkeypatch).tax_slabs()
    assert [row["rate"] for row in rates] == [5.0, 12.0]


def test_product_choice_resolves_tax_code_then_category_for_legacy_zero_gst(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "product-gst.db"
    repository = MasterRepository(db_path)
    repository.ensure_schema()
    category_id = repository.save_simple(
        "category",
        0,
        {"code": "FOOD", "name": "Food", "default_gst": 5, "is_active": True},
    )
    repository.save_simple(
        "tax_master",
        0,
        {
            "tax_code": "HSN1905",
            "tax_name": "Bakery GST",
            "hsn_sac": "1905",
            "gst_rate": 12,
            "cgst": 6,
            "sgst": 6,
            "igst": 0,
            "is_active": True,
        },
    )
    first = repository.save_product(
        {
            "code": "GST-HSN",
            "name": "Tax-code Product",
            "category_id": category_id,
            "hsn": "1905",
            "gst": 0,
            "sale_unit": "PCS",
            "purchase_unit": "PCS",
            "packs": [_pack()],
        }
    )
    second = repository.save_product(
        {
            "code": "GST-CAT",
            "name": "Category Product",
            "category_id": category_id,
            "hsn": "2106",
            "gst": 0,
            "sale_unit": "PCS",
            "purchase_unit": "PCS",
            "packs": [_pack()],
        }
    )

    rows = _source_for(db_path, monkeypatch).product_choices()
    by_id = {int(row["item_id"]): float(row["gst"]) for row in rows}
    assert by_id[first] == 12
    assert by_id[second] == 5


def test_resolved_nonzero_gst_calculates_intra_and_interstate_totals() -> None:
    line = SalesLine("GST Product", "1 PCS", "1905", "PCS", 2, 0, 120, 100, 0, 0, 12)
    calculator = SalesCalculator("Telangana")
    local = calculator.compute_line(line, place_of_supply="Telangana")
    interstate = calculator.compute_line(line, place_of_supply="Karnataka")

    assert (local.taxable, local.cgst, local.sgst, local.igst, local.gst_total) == (200, 12, 12, 0, 24)
    assert (interstate.taxable, interstate.cgst, interstate.sgst, interstate.igst, interstate.gst_total) == (
        200,
        0,
        0,
        24,
        24,
    )
    assert calculator.totals([interstate])["gst_total"] == 24


def test_party_place_of_supply_is_available_to_transaction_pages(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "party-place.db"
    repository = MasterRepository(db_path)
    repository.ensure_schema()
    customer_id = repository.save_party(
        "customers",
        "customer",
        0,
        {"name": "Interstate Buyer", "state": "Karnataka", "place_of_supply": "Karnataka", "status": "Active"},
    )
    supplier_id = repository.save_party(
        "suppliers",
        "supplier",
        0,
        {"name": "Interstate Supplier", "state": "Tamil Nadu", "place_of_supply": "Tamil Nadu", "status": "Active"},
    )
    source = _source_for(db_path, monkeypatch)
    assert {row["id"]: row["place_of_supply"] for row in source.customers()}[customer_id] == "Karnataka"
    assert {row["id"]: row["place_of_supply"] for row in source.suppliers()}[supplier_id] == "Tamil Nadu"

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT place_of_supply FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == "Karnataka"
