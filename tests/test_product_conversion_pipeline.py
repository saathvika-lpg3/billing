from __future__ import annotations

import sqlite3

import pytest

from services.master_repository import MasterRepository
from services.uom_price_service import UomPriceService


def _pack(unit: str = "PCS", size: float = 1, *, default: bool = True) -> dict[str, object]:
    return {
        "pack_size": size,
        "pack_unit": unit,
        "display_name": f"{size:g} {unit}",
        "barcode": "",
        "mrp": 100,
        "ptr": 82,
        "pts": 78,
        "purchase_rate": 75,
        "sale_rate": 90,
        "opening_stock_qty": 0,
        "current_stock_qty": 0,
        "low_stock_alert": 0,
        "reorder_qty": 0,
        "is_default": 1 if default else 0,
        "is_active": 1,
    }


def _payload(code: str = "UOM-1") -> dict[str, object]:
    return {
        "code": code,
        "name": "Conversion Product",
        "hsn": "1905",
        "gst": 5,
        "sale_unit": "PCS",
        "purchase_unit": "PCS",
        "conversion_factor": 1,
        "multi_uom": False,
        "pack_conversion": False,
        "packs": [_pack()],
    }


def test_single_uom_product_does_not_require_pack_conversion(tmp_path) -> None:
    repository = MasterRepository(tmp_path / "single-uom.db")
    product_id = repository.save_product(_payload())
    assert product_id > 0
    assert UomPriceService(repository.db_path).get_conversion("PCS", "PCS", product_id) is None


def test_different_purchase_and_sale_uom_requires_explicit_conversion(tmp_path) -> None:
    repository = MasterRepository(tmp_path / "conversion-required.db")
    payload = _payload()
    payload["purchase_unit"] = "BOX"

    errors = repository.validate_product_payload(payload)
    assert "Enable Pack Conversion when Sale UoM and Purchase UoM differ." in errors
    with pytest.raises(ValueError, match="Enable Pack Conversion"):
        repository.save_product(payload)

    with sqlite3.connect(repository.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0


def test_purchase_to_sale_conversion_is_saved_and_replaced_atomically(tmp_path) -> None:
    repository = MasterRepository(tmp_path / "conversion-save.db")
    payload = _payload()
    payload.update({"purchase_unit": "BOX", "pack_conversion": True, "conversion_factor": 12})
    product_id = repository.save_product(payload)

    service = UomPriceService(repository.db_path)
    assert service.get_conversion("BOX", "PCS", product_id) == 12

    payload.update({"product_id": product_id, "conversion_factor": 24})
    repository.save_product(payload)
    assert service.get_conversion("BOX", "PCS", product_id) == 24
    with sqlite3.connect(repository.db_path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM pack_conversions WHERE product_id=?",
            (product_id,),
        ).fetchone()[0] == 1


def test_explicit_purchase_factor_wins_when_pack_row_uses_purchase_uom(tmp_path) -> None:
    repository = MasterRepository(tmp_path / "explicit-factor.db")
    payload = _payload()
    payload.update(
        {
            "purchase_unit": "BOX",
            "pack_conversion": True,
            "multi_uom": True,
            "conversion_factor": 12,
            "packs": [_pack("BOX", 1)],
        }
    )
    product_id = repository.save_product(payload)
    assert UomPriceService(repository.db_path).get_conversion("BOX", "PCS", product_id) == 12


def test_multi_uom_pack_rows_create_product_specific_conversion_map(tmp_path) -> None:
    repository = MasterRepository(tmp_path / "multi-uom.db")
    payload = _payload()
    payload.update(
        {
            "multi_uom": True,
            "pack_conversion": True,
            "packs": [_pack(), _pack("CARTON", 24, default=False)],
        }
    )
    product_id = repository.save_product(payload)
    service = UomPriceService(repository.db_path)
    assert service.get_conversion("CARTON", "PCS", product_id) == 24


def test_alternate_pack_unit_is_rejected_without_multi_uom(tmp_path) -> None:
    repository = MasterRepository(tmp_path / "multi-uom-required.db")
    payload = _payload()
    payload["packs"] = [_pack(), _pack("CARTON", 24, default=False)]
    errors = repository.validate_product_payload(payload)
    assert "Enable Multi-UOM when active package rows use more than one unit." in errors
    assert "Enable Pack Conversion for active package units that differ from the Sale UoM." in errors
