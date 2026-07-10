from services.uom_price_service import UomPriceService
from services.mysql_source import MySqlSource
import tempfile
import os


def test_uom_and_conversion_and_pricing(tmp_path):
    db = tmp_path / "test_uom_price.db"
    svc = UomPriceService(str(db))
    svc.ensure_schema()

    # UOM
    uom_id = svc.save_uom("PCS", "Pieces", "pcs", decimals=0)
    assert uom_id > 0
    uom = svc.get_uom_by_code("pcs")
    assert uom and uom["code"].lower() == "pcs"

    # Pack conversion
    conv_id = svc.save_pack_conversion("PCS", "BOX", 12)
    assert conv_id > 0
    factor = svc.get_conversion("pcs", "box")
    assert factor == 12

    # Price levels
    pl_id = svc.save_price_level("MRP", "Maximum Retail Price")
    assert pl_id > 0

    # Product price
    pp_id = svc.set_product_price(1, "MRP", 123.45)
    assert pp_id > 0
    price = svc.get_product_price(1, "mrp")
    assert price == 123.45

    # Party default price
    pd_id = svc.set_party_default_price("customers", 1, "MRP")
    assert pd_id > 0
    code = svc.get_party_default_price_level("customers", 1)
    assert code == "MRP"
