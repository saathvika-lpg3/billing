from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from services.mysql_source import MySqlSource


class ImportService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or MySqlSource().sqlite_path)

    def post_rows(self, import_type: str, rows: list[dict[str, Any]]) -> dict[str, int]:
        key = import_type.strip().lower()
        counters = {"inserted": 0, "updated": 0, "skipped": 0}
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                for row in rows:
                    if key == "products":
                        self._import_product(conn, row, counters)
                    elif key == "product packs":
                        self._import_pack(conn, row, counters)
                    elif key == "customers":
                        self._import_party(conn, "customers", row, counters)
                    elif key == "suppliers":
                        self._import_party(conn, "suppliers", row, counters)
                    elif key == "opening stock":
                        self._import_opening_stock(conn, row, counters)
                    elif key == "schemes":
                        self._import_scheme(conn, row, counters)
                    else:
                        counters["skipped"] += 1
        return counters

    def _import_product(self, conn: sqlite3.Connection, row: dict[str, Any], counters: dict[str, int]) -> int | None:
        name = self._text(row, "name", "product", "item", "item_name", "product_name")
        if not name:
            counters["skipped"] += 1
            return None
        code = self._text(row, "code", "item_code", "product_code")
        existing = self._find_item(conn, code, name)
        values = {
            "code": code,
            "name": name,
            "hsn": self._text(row, "hsn", "hsn_sac"),
            "unit": self._text(row, "unit", default="PCS"),
            "gst": self._number(row, "gst", "gst_rate", "tax"),
            "mrp": self._number(row, "mrp"),
            "sale_rate": self._number(row, "sale_rate", "sale", "rate"),
            "buy_rate": self._number(row, "buy_rate", "purchase_rate", "purchase"),
            "stock": self._number(row, "stock", "opening_stock", "current_stock"),
            "min_stock": self._number(row, "min_stock", "low_stock"),
            "barcode": self._text(row, "barcode"),
            "status": self._text(row, "status", default="Active"),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        if existing:
            conn.execute(
                """
                UPDATE items SET code=?,name=?,hsn=?,unit=?,gst=?,mrp=?,sale_rate=?,buy_rate=?,
                    stock=?,min_stock=?,barcode=?,status=?
                WHERE id=?
                """,
                (
                    values["code"],
                    values["name"],
                    values["hsn"],
                    values["unit"],
                    values["gst"],
                    values["mrp"],
                    values["sale_rate"],
                    values["buy_rate"],
                    values["stock"],
                    values["min_stock"],
                    values["barcode"],
                    values["status"],
                    existing["id"],
                ),
            )
            counters["updated"] += 1
            return int(existing["id"])
        cursor = conn.execute(
            """
            INSERT INTO items(code,name,hsn,unit,gst,mrp,sale_rate,buy_rate,stock,min_stock,barcode,status,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            tuple(values[column] for column in ("code", "name", "hsn", "unit", "gst", "mrp", "sale_rate", "buy_rate", "stock", "min_stock", "barcode", "status", "created_at")),
        )
        counters["inserted"] += 1
        return int(cursor.lastrowid)

    def _import_pack(self, conn: sqlite3.Connection, row: dict[str, Any], counters: dict[str, int]) -> None:
        item_id = self._item_id_from_row(conn, row, counters)
        if not item_id:
            return
        barcode = self._text(row, "barcode")
        display = self._text(row, "display_name", "pack", "pack_name") or f"{self._number(row, 'pack_size', default=1):g} {self._text(row, 'unit', 'pack_unit', default='PCS')}"
        existing = None
        if barcode:
            existing = conn.execute("SELECT id FROM product_packs WHERE barcode=? LIMIT 1", (barcode,)).fetchone()
        if not existing:
            existing = conn.execute("SELECT id FROM product_packs WHERE product_id=? AND display_name=? LIMIT 1", (item_id, display)).fetchone()
        values = (
            item_id,
            self._number(row, "pack_size", default=1),
            self._text(row, "unit", "pack_unit", default="PCS"),
            display,
            barcode,
            self._text(row, "supplier_item_code"),
            self._text(row, "hsn"),
            self._number(row, "mrp"),
            self._number(row, "purchase_rate", "purchase"),
            self._number(row, "sale_rate", "sale", "rate"),
            self._number(row, "dealer_rate", "dealer"),
            self._number(row, "distributor_rate", "distributor"),
            self._number(row, "wholesale_rate", "wholesale"),
            self._number(row, "retail_rate", "retail"),
            self._number(row, "opening_stock", "current_stock", "stock"),
            self._number(row, "current_stock", "stock"),
            self._number(row, "low_stock_alert", "low_stock"),
            self._number(row, "reorder_qty", "reorder"),
            self._text(row, "scheme"),
            1 if self._text(row, "default", "is_default").lower() in {"1", "yes", "true", "default"} else 0,
            1,
            datetime.now().isoformat(timespec="seconds"),
        )
        if existing:
            conn.execute(
                """
                UPDATE product_packs SET product_id=?,pack_size=?,pack_unit=?,display_name=?,barcode=?,
                    supplier_item_code=?,hsn=?,mrp=?,purchase_rate=?,sale_rate=?,dealer_rate=?,
                    distributor_rate=?,wholesale_rate=?,retail_rate=?,opening_stock_qty=?,current_stock_qty=?,
                    low_stock_alert=?,reorder_qty=?,scheme=?,is_default=?,is_active=?,updated_at=?
                WHERE id=?
                """,
                values + (existing["id"],),
            )
            counters["updated"] += 1
        else:
            conn.execute(
                """
                INSERT INTO product_packs(
                    product_id,pack_size,pack_unit,display_name,barcode,supplier_item_code,hsn,mrp,
                    purchase_rate,sale_rate,dealer_rate,distributor_rate,wholesale_rate,retail_rate,
                    opening_stock_qty,current_stock_qty,low_stock_alert,reorder_qty,scheme,is_default,
                    is_active,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                values,
            )
            counters["inserted"] += 1

    def _import_party(self, conn: sqlite3.Connection, table: str, row: dict[str, Any], counters: dict[str, int]) -> None:
        name = self._text(row, "name", "party", "customer", "supplier")
        if not name:
            counters["skipped"] += 1
            return
        gstin = self._text(row, "gstin", "gst_number")
        phone = self._text(row, "phone", "mobile")
        existing = None
        if gstin:
            existing = conn.execute(f"SELECT id FROM {table} WHERE gstin=? LIMIT 1", (gstin,)).fetchone()
        if not existing and phone:
            existing = conn.execute(f"SELECT id FROM {table} WHERE phone=? LIMIT 1", (phone,)).fetchone()
        if not existing:
            existing = conn.execute(f"SELECT id FROM {table} WHERE name=? LIMIT 1", (name,)).fetchone()
        common_tail = (
            self._text(row, "state"),
            self._number(row, "balance", "opening_balance"),
            datetime.now().isoformat(timespec="seconds"),
            self._text(row, "contact_person", "contact"),
            self._text(row, "place_of_supply"),
            self._text(row, "fssai_no", "fssai"),
            self._text(row, "drug_license_no", "drug_license"),
            self._text(row, "gst_treatment", default="Regular"),
            1 if self._text(row, "reverse_charge").lower() in {"1", "yes", "true"} else 0,
        )
        if table == "customers":
            values = (name, gstin, phone, self._text(row, "area"), self._text(row, "address")) + common_tail
            if existing:
                conn.execute(
                    """
                    UPDATE customers SET name=?,gstin=?,phone=?,area=?,address=?,state=?,balance=?,
                        created_at=?,contact_person=?,place_of_supply=?,fssai_no=?,drug_license_no=?,
                        gst_treatment=?,reverse_charge_applicable=?
                    WHERE id=?
                    """,
                    values + (existing["id"],),
                )
                counters["updated"] += 1
            else:
                conn.execute(
                    """
                    INSERT INTO customers(
                        name,gstin,phone,area,address,state,balance,created_at,contact_person,
                        place_of_supply,fssai_no,drug_license_no,gst_treatment,reverse_charge_applicable
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    values,
                )
                counters["inserted"] += 1
            return
        values = (name, gstin, phone, self._text(row, "address")) + common_tail
        if existing:
            conn.execute(
                """
                UPDATE suppliers SET name=?,gstin=?,phone=?,address=?,state=?,balance=?,created_at=?,
                    contact_person=?,place_of_supply=?,fssai_no=?,drug_license_no=?,gst_treatment=?,
                    reverse_charge_applicable=?
                WHERE id=?
                """,
                values + (existing["id"],),
            )
            counters["updated"] += 1
        else:
            conn.execute(
                """
                INSERT INTO suppliers(
                    name,gstin,phone,address,state,balance,created_at,contact_person,place_of_supply,
                    fssai_no,drug_license_no,gst_treatment,reverse_charge_applicable
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                values,
            )
            counters["inserted"] += 1

    def _import_opening_stock(self, conn: sqlite3.Connection, row: dict[str, Any], counters: dict[str, int]) -> None:
        item_id = self._item_id_from_row(conn, row, counters)
        if not item_id:
            return
        qty = self._number(row, "stock", "qty", "opening_stock", "current_stock")
        pack_id = self._pack_id_from_row(conn, row, item_id)
        conn.execute("UPDATE items SET stock=? WHERE id=?", (qty, item_id))
        if pack_id:
            conn.execute("UPDATE product_packs SET current_stock_qty=?, opening_stock_qty=? WHERE id=?", (qty, qty, pack_id))
        conn.execute(
            "INSERT INTO stock_log(item_id,kind,ref_no,qty_in,qty_out,entry_date,created_at,pack_id) VALUES(?,?,?,?,?,?,?,?)",
            (item_id, "opening_import", "IMPORT", qty, 0, datetime.now().strftime("%Y-%m-%d"), datetime.now().isoformat(timespec="seconds"), pack_id),
        )
        counters["updated"] += 1

    def _import_scheme(self, conn: sqlite3.Connection, row: dict[str, Any], counters: dict[str, int]) -> None:
        item_id = self._item_id_from_row(conn, row, counters)
        if not item_id:
            return
        conn.execute(
            """
            INSERT INTO scheme_rules(item_id,min_qty,free_qty,sale_rate,start_date,end_date,notes,is_active,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                item_id,
                self._number(row, "min_qty", "minimum_qty", default=1),
                self._number(row, "free_qty", "scheme_qty"),
                self._number(row, "sale_rate", "rate"),
                self._text(row, "start_date"),
                self._text(row, "end_date"),
                self._text(row, "notes", "scheme"),
                1,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        counters["inserted"] += 1

    def _item_id_from_row(self, conn: sqlite3.Connection, row: dict[str, Any], counters: dict[str, int]) -> int | None:
        code = self._text(row, "code", "item_code", "product_code")
        name = self._text(row, "name", "product", "item", "item_name", "product_name")
        existing = self._find_item(conn, code, name)
        if existing:
            return int(existing["id"])
        return self._import_product(conn, row, counters)

    def _pack_id_from_row(self, conn: sqlite3.Connection, row: dict[str, Any], item_id: int) -> int:
        barcode = self._text(row, "barcode")
        if barcode:
            found = conn.execute("SELECT id FROM product_packs WHERE barcode=? LIMIT 1", (barcode,)).fetchone()
            if found:
                return int(found["id"])
        display = self._text(row, "display_name", "pack", "pack_name")
        if display:
            found = conn.execute("SELECT id FROM product_packs WHERE product_id=? AND display_name=? LIMIT 1", (item_id, display)).fetchone()
            if found:
                return int(found["id"])
        return 0

    def _find_item(self, conn: sqlite3.Connection, code: str, name: str) -> sqlite3.Row | None:
        if code:
            found = conn.execute("SELECT id FROM items WHERE code=? LIMIT 1", (code,)).fetchone()
            if found:
                return found
        if name:
            return conn.execute("SELECT id FROM items WHERE name=? LIMIT 1", (name,)).fetchone()
        return None

    def _text(self, row: dict[str, Any], *names: str, default: str = "") -> str:
        normalized = {self._normalize(key): value for key, value in row.items()}
        for name in names:
            value = normalized.get(self._normalize(name))
            if value is not None and str(value).strip() != "":
                return str(value).strip()
        return default

    def _number(self, row: dict[str, Any], *names: str, default: float = 0) -> float:
        value = self._text(row, *names)
        if not value:
            return float(default)
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            return float(default)

    def _normalize(self, value: str) -> str:
        return "".join(ch for ch in str(value).lower() if ch.isalnum())
