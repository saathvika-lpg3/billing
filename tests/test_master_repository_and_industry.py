from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from services.accounting_setup_service import AccountingSetupService
from services.master_repository import MasterRepository


SOURCE_DB = Path(r"D:\PRM_GST_DESKTOP\database\prm_billing_inventory.db")


def _copy_db(tmp_path: Path) -> Path:
    target = tmp_path / "prm_billing_inventory.db"
    shutil.copy2(SOURCE_DB, target)
    return target


def test_master_repository_saves_product_party_and_unit(tmp_path: Path) -> None:
    db_path = _copy_db(tmp_path)
    repo = MasterRepository(db_path)
    repo.ensure_schema()

    unit_id = repo.save_simple("unit", 0, {"name": "QA TEST UNIT", "is_active": False})
    customer_id = repo.save_party(
        "customers",
        "customer",
        0,
        {
            "name": "QA Customer",
            "phone": "9000000000",
            "gstin": "",
            "area": "QA Route",
            "state": "Telangana",
            "place_of_supply": "Telangana",
            "balance": 10,
            "gst_treatment": "Regular",
            "reverse_charge_applicable": False,
            "address": "Billing",
            "shipping_address": "Shipping",
        },
    )
    product_id = repo.save_product(
        {
            "product_id": 0,
            "code": "QA-PRODUCT",
            "supplier_id": 0,
            "category_id": 1,
            "brand_id": 0,
            "name": "QA Product",
            "item_type": "Stock Item",
            "status": "Active",
            "hsn": "1905",
            "gst": 5,
            "sale_unit": "PCS",
            "purchase_unit": "PCS",
            "valuation_method": "weighted_average",
            "sku_alias": "QA",
            "lead_time_days": 0,
            "shelf_life_days": 45,
            "near_expiry_days": 7,
            "multi_uom": True,
            "pack_conversion": True,
            "batch_required": False,
            "expiry_required": False,
            "item_notes": "",
            "packs": [
                {
                    "pack_size": 1,
                    "pack_unit": "PCS",
                    "display_name": "1 PCS",
                    "barcode": "QA123",
                    "hsn": "1905",
                    "supplier_item_code": "QA-SKU",
                    "mrp": 20,
                    "ptr": 16,
                    "pts": 14,
                    "purchase_rate": 12,
                    "sale_rate": 15,
                    "dealer_rate": 14,
                    "distributor_rate": 13,
                    "wholesale_rate": 13,
                    "retail_rate": 15,
                    "box_qty": 1,
                    "opening_stock_qty": 5,
                    "current_stock_qty": 5,
                    "low_stock_alert": 1,
                    "reorder_qty": 2,
                    "scheme": "",
                    "is_default": 1,
                    "is_active": 1,
                }
            ],
        }
    )

    with sqlite3.connect(db_path) as conn:
        unit = conn.execute("SELECT name,is_active FROM units WHERE id=?", (unit_id,)).fetchone()
        customer = conn.execute("SELECT name,shipping_address FROM customers WHERE id=?", (customer_id,)).fetchone()
        product = conn.execute("SELECT name,code,stock,sale_rate FROM items WHERE id=?", (product_id,)).fetchone()
        pack_count = conn.execute("SELECT COUNT(*) FROM product_packs WHERE product_id=?", (product_id,)).fetchone()[0]

    assert unit == ("QA TEST UNIT", 0)
    assert customer == ("QA Customer", "Shipping")
    assert product == ("QA Product", "QA-PRODUCT", 5.0, 15.0)
    assert pack_count == 1

    with sqlite3.connect(db_path) as conn:
        item = conn.execute(
            "SELECT multi_uom, pack_conversion, shelf_life_days, near_expiry_days FROM items WHERE id=?",
            (product_id,),
        ).fetchone()
        pack = conn.execute(
            "SELECT ptr, pts, hsn, supplier_item_code FROM product_packs WHERE product_id=? LIMIT 1",
            (product_id,),
        ).fetchone()

    assert item == (1, 1, 45, 7)
    assert pack == (16.0, 14.0, "1905", "QA-SKU")


def test_master_repository_saves_branch_warehouse_and_cost_center(tmp_path: Path) -> None:
    db_path = tmp_path / "masters.db"
    repo = MasterRepository(db_path)
    repo.ensure_schema()

    branch_id = repo.save_simple(
        "branch",
        0,
        {
            "code": "BRQA",
            "name": "QA Branch",
            "address": "Branch Street",
            "city": "Hyderabad",
            "state": "Telangana",
            "pin_code": "500001",
            "phone": "9000000000",
            "email": "branch@example.com",
            "gstin": "36AABCDE1234F1Z5",
            "is_default": True,
            "is_active": True,
        },
    )
    warehouse_id = repo.save_simple(
        "warehouse",
        0,
        {
            "code": "WHQA",
            "name": "QA Warehouse",
            "branch_id": branch_id,
            "address": "Warehouse Road",
            "contact_person": "Mr X",
            "phone": "9000000000",
            "is_active": True,
        },
    )
    cost_center_id = repo.save_simple(
        "cost_center",
        0,
        {
            "code": "CCQA",
            "name": "QA Cost Center",
            "type": "Department",
            "notes": "QA cost center",
            "is_active": True,
        },
    )

    with sqlite3.connect(db_path) as conn:
        branch = conn.execute(
            "SELECT code,name,state,is_active FROM branches WHERE id=?",
            (branch_id,),
        ).fetchone()
        warehouse = conn.execute(
            "SELECT code,name,branch_id,address,contact_person,phone,is_active FROM warehouses WHERE id=?",
            (warehouse_id,),
        ).fetchone()
        cost_center = conn.execute(
            "SELECT code,name,type,notes,is_active FROM cost_centers WHERE id=?",
            (cost_center_id,),
        ).fetchone()

    assert branch == ("BRQA", "QA Branch", "Telangana", 1)
    assert warehouse == ("WHQA", "QA Warehouse", branch_id, "Warehouse Road", "Mr X", "9000000000", 1)
    assert cost_center == ("CCQA", "QA Cost Center", "Department", "QA cost center", 1)


def test_master_repository_saves_route_salesman_vehicle_and_transporter(tmp_path: Path) -> None:
    db_path = tmp_path / "transport.db"
    repo = MasterRepository(db_path)
    repo.ensure_schema()

    salesman_id = repo.save_simple(
        "salesman",
        0,
        {
            "code": "SMQA",
            "name": "QA Salesman",
            "mobile": "9000000000",
            "email": "salesman@example.com",
            "address": "Route Beat",
            "is_active": True,
        },
    )
    vehicle_id = repo.save_simple(
        "vehicle",
        0,
        {
            "code": "VHQA",
            "vehicle_no": "TS09AB1234",
            "vehicle_type": "Van",
            "driver_name": "Ramesh",
            "driver_mobile": "9000000001",
            "capacity": 1500,
            "is_active": True,
        },
    )
    transporter_id = repo.save_simple(
        "transporter",
        0,
        {
            "code": "TPQA",
            "name": "QA Transport",
            "gstin": "36AABCDE1234F1Z5",
            "mobile": "9000000002",
            "address": "Transport Yard",
            "is_active": True,
        },
    )
    route_id = repo.save_simple(
        "route",
        0,
        {
            "code": "RTQA",
            "name": "QA Route",
            "area": "North Zone",
            "salesman_id": salesman_id,
            "vehicle_id": vehicle_id,
            "is_active": True,
        },
    )

    with sqlite3.connect(db_path) as conn:
        salesman = conn.execute(
            "SELECT code,name,mobile,email,address,is_active FROM salesmen WHERE id=?",
            (salesman_id,),
        ).fetchone()
        vehicle = conn.execute(
            "SELECT code,vehicle_no,vehicle_type,driver_name,driver_mobile,capacity,is_active FROM vehicles WHERE id=?",
            (vehicle_id,),
        ).fetchone()
        transporter = conn.execute(
            "SELECT code,name,gstin,mobile,address,is_active FROM transporters WHERE id=?",
            (transporter_id,),
        ).fetchone()
        route = conn.execute(
            "SELECT code,name,area,salesman_id,vehicle_id,is_active FROM routes WHERE id=?",
            (route_id,),
        ).fetchone()

    assert salesman == ("SMQA", "QA Salesman", "9000000000", "salesman@example.com", "Route Beat", 1)
    assert vehicle == ("VHQA", "TS09AB1234", "Van", "Ramesh", "9000000001", 1500.0, 1)
    assert transporter == ("TPQA", "QA Transport", "36AABCDE1234F1Z5", "9000000002", "Transport Yard", 1)
    assert route == ("RTQA", "QA Route", "North Zone", salesman_id, vehicle_id, 1)


def test_master_repository_saves_bank_tax_and_payment_terms(tmp_path: Path) -> None:
    db_path = tmp_path / "commercial.db"
    repo = MasterRepository(db_path)
    repo.ensure_schema()

    bank_id = repo.save_simple(
        "bank",
        0,
        {
            "code": "BNKQA",
            "name": "QA Bank",
            "account_number": "123456789012",
            "ifsc": "ABCD0123456",
            "branch": "Main Branch",
            "account_type": "Current",
            "opening_balance": 10000,
            "is_active": True,
        },
    )
    tax_id = repo.save_simple(
        "tax_master",
        0,
        {
            "tax_code": "GST18",
            "tax_name": "GST 18%",
            "hsn_sac": "9983",
            "gst_rate": 18,
            "cgst": 9,
            "sgst": 9,
            "igst": 0,
            "cess": 0,
            "effective_from": "2026-07-01",
            "is_active": True,
        },
    )
    term_id = repo.save_simple(
        "payment_term",
        0,
        {
            "code": "PT30",
            "name": "Net 30",
            "credit_days": 30,
            "due_date_rule": "30 Days from Invoice",
            "discount_percent": 2,
            "is_active": True,
        },
    )

    with sqlite3.connect(db_path) as conn:
        bank = conn.execute(
            "SELECT code,name,account_number,ifsc,branch,account_type,opening_balance,is_active FROM banks WHERE id=?",
            (bank_id,),
        ).fetchone()
        tax = conn.execute(
            "SELECT tax_code,tax_name,hsn_sac,gst_rate,cgst,sgst,igst,cess,effective_from,is_active FROM tax_codes WHERE id=?",
            (tax_id,),
        ).fetchone()
        term = conn.execute(
            "SELECT code,name,credit_days,due_date_rule,discount_percent,is_active FROM payment_terms WHERE id=?",
            (term_id,),
        ).fetchone()

    assert bank == ("BNKQA", "QA Bank", "123456789012", "ABCD0123456", "Main Branch", "Current", 10000.0, 1)
    assert tax == ("GST18", "GST 18%", "9983", 18.0, 9.0, 9.0, 0.0, 0.0, "2026-07-01", 1)
    assert term == ("PT30", "Net 30", 30, "30 Days from Invoice", 2.0, 1)


def test_product_validation_rejects_duplicate_pack_barcodes(tmp_path: Path) -> None:
    repo = MasterRepository(tmp_path / "validate.db")
    errors = repo.validate_product_payload(
        {
            "product_id": 0,
            "code": "DUP-BARCODE",
            "supplier_id": 0,
            "category_id": 1,
            "brand_id": 0,
            "name": "Duplicate Barcode Test",
            "hsn": "1801",
            "gst": 5,
            "sale_unit": "PCS",
            "purchase_unit": "PCS",
            "packs": [
                {"pack_size": 1, "pack_unit": "PCS", "barcode": "ABC123", "mrp": 10, "purchase_rate": 8, "sale_rate": 9, "is_active": 1, "is_default": 1},
                {"pack_size": 2, "pack_unit": "PCS", "barcode": "ABC123", "mrp": 20, "purchase_rate": 16, "sale_rate": 18, "is_active": 1, "is_default": 0},
            ],
        }
    )
    assert any("Duplicate barcode" in error for error in errors)


def test_company_settings_save_fssai_syncs_developer_profile(tmp_path: Path) -> None:
    db_path = _copy_db(tmp_path)
    repo = MasterRepository(db_path)

    company_id = repo.save_simple(
        "company",
        1,
        {
            "name": "QA Licensed Company",
            "business_name": "QA Billing",
            "gstin": "",
            "fssai_no": "12345678901234",
            "phone": "9000000000",
            "email": "qa@example.com",
            "invoice_prefix": "QA",
        },
    )

    with sqlite3.connect(db_path) as conn:
        company = conn.execute("SELECT name,gstin,fssai_no,invoice_prefix FROM company WHERE id=?", (company_id,)).fetchone()
        dev = conn.execute("SELECT company_name,fssai_no,invoice_template_code FROM dev_companies WHERE company_name='QA Licensed Company' LIMIT 1").fetchone()

    assert company == ("QA Licensed Company", "", "12345678901234", "QA")
    assert dev == ("QA Licensed Company", "12345678901234", "wholesale_tax_invoice")


def test_tally_account_groups_and_system_ledgers_are_seeded(tmp_path: Path) -> None:
    db_path = _copy_db(tmp_path)
    AccountingSetupService(db_path).ensure_tally_accounting()

    with sqlite3.connect(db_path) as conn:
        group_names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM ledger_groups WHERE COALESCE(is_active,1)=1"
            )
        }
        ledgers = dict(
            conn.execute(
                """
                SELECT name, group_name
                FROM account_ledgers
                WHERE name IN (
                    'Cash','Bank','Sales','Purchase','Output GST',
                    'Stock In Hand','Retained Earnings','Stock Adjustment'
                )
                """
            ).fetchall()
        )

    assert {
        "Capital Account",
        "Bank Accounts",
        "Cash-in-hand",
        "Sundry Debtors",
        "Sundry Creditors",
        "Sales Accounts",
        "Purchase Accounts",
        "Stock-in-hand",
        "Duties & Taxes",
        "Indirect Expenses",
        "Indirect Incomes",
    }.issubset(group_names)
    assert ledgers["Cash"] == "Cash-in-hand"
    assert ledgers["Bank"] == "Bank Accounts"
    assert ledgers["Sales"] == "Sales Accounts"
    assert ledgers["Purchase"] == "Purchase Accounts"
    assert ledgers["Output GST"] == "Duties & Taxes"
    assert ledgers["Stock In Hand"] == "Stock-in-hand"
    assert ledgers["Retained Earnings"] == "Reserves & Surplus"
    assert ledgers["Stock Adjustment"] == "Indirect Expenses"
