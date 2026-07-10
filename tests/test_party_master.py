from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from services.master_repository import MasterRepository


SOURCE_DB = Path(r"D:\PRM_GST_DESKTOP\database\prm_billing_inventory.db")


def _copy_db(tmp_path: Path) -> Path:
    target = tmp_path / "prm_billing_inventory.db"
    shutil.copy2(SOURCE_DB, target)
    return target


def _base_payload(code: str = "C001") -> dict:
    return {
        "code": code,
        "name": "QA Test Party",
        "customer_type": "Retail",
        "address": "Billing Addr",
        "city": "Hyderabad",
        "state": "Telangana",
        "status": "Active",
        "balance": 0,
        "balance_type": "Debit",
        "credit_limit": 0,
        "place_of_supply": "Telangana",
    }


def test_save_customer_and_supplier(tmp_path: Path) -> None:
    repo = MasterRepository(tmp_path / "party.db")
    repo.ensure_schema()

    cust_id = repo.save_party("customers", "customer", 0, {**_base_payload("CUST1")})
    supp_id = repo.save_party("suppliers", "supplier", 0, {**_base_payload("SUPP1")})

    assert int(cust_id) > 0
    assert int(supp_id) > 0

    with sqlite3.connect(tmp_path / "party.db") as conn:
        cust = conn.execute("SELECT code,name,status FROM customers WHERE id=?", (cust_id,)).fetchone()
        supp = conn.execute("SELECT code,name,status FROM suppliers WHERE id=?", (supp_id,)).fetchone()

    assert cust[0] == "CUST1"
    assert supp[0] == "SUPP1"


def test_duplicate_party_code_prevention(tmp_path: Path) -> None:
    repo = MasterRepository(tmp_path / "dup.db")
    repo.ensure_schema()
    payload = _base_payload("DUP1")
    repo.save_party("customers", "customer", 0, payload)

    with pytest.raises(ValueError) as exc:
        repo.save_party("customers", "customer", 0, _base_payload("DUP1"))
    assert "Code already exists" in str(exc.value) or "Code already exists for this party" in str(exc.value)


def test_gstin_pan_email_validation(tmp_path: Path) -> None:
    repo = MasterRepository(tmp_path / "validate.db")
    repo.ensure_schema()
    payload = _base_payload("V001")
    payload["gstin"] = "INVALIDGST"
    payload["pan"] = "BADPAN"
    payload["email"] = "not-an-email"

    errors = repo.validate_party_payload("customers", payload)
    assert any("GSTIN is invalid" in e or "GSTIN is invalid." in e for e in errors)
    assert any("PAN is invalid" in e or "PAN is invalid." in e for e in errors)
    assert any("Email is invalid" in e or "Email is invalid." in e for e in errors)


def test_numeric_validation(tmp_path: Path) -> None:
    repo = MasterRepository(tmp_path / "numeric.db")
    repo.ensure_schema()
    payload = _base_payload("N001")
    payload["balance"] = -10
    payload["credit_limit"] = "abc"

    errors = repo.validate_party_payload("customers", payload)
    assert any("Opening balance cannot be negative" in e or "Opening balance cannot be negative." in e for e in errors)
    assert any("Credit limit must be numeric" in e or "Credit limit must be numeric." in e for e in errors)


def test_inactive_party_save(tmp_path: Path) -> None:
    repo = MasterRepository(tmp_path / "inactive.db")
    repo.ensure_schema()
    payload = _base_payload("I001")
    payload["status"] = "Inactive"
    pid = repo.save_party("customers", "customer", 0, payload)
    with sqlite3.connect(tmp_path / "inactive.db") as conn:
        row = conn.execute("SELECT status FROM customers WHERE id=?", (pid,)).fetchone()
    assert row[0] == "Inactive"


def test_migration_compatibility(tmp_path: Path) -> None:
    db_path = _copy_db(tmp_path)
    repo = MasterRepository(db_path)
    # ensure_schema should execute without raising and add columns idempotently
    repo.ensure_schema()
    # basic sanity: customers table should exist and be queryable
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT name FROM customers LIMIT 1").fetchone()
    assert row is not None
