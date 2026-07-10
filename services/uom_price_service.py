from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class UomPriceService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS uoms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    name TEXT,
                    short_name TEXT,
                    decimals INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pack_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER DEFAULT 0,
                    from_uom TEXT,
                    to_uom TEXT,
                    factor REAL,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    name TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS product_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    price_level_code TEXT,
                    price REAL,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS party_price_defaults (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_table TEXT,
                    party_id INTEGER,
                    price_level_code TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    # UOM methods
    def save_uom(self, code: str, name: str, short_name: str = "", decimals: int = 0, is_active: bool = True) -> int:
        self.ensure_schema()
        if not code or not name:
            raise ValueError("UOM code and name are required.")
        if decimals < 0:
            raise ValueError("Decimals cannot be negative.")
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT id FROM uoms WHERE LOWER(code)=?", (code.lower(),)).fetchone()
            if row:
                conn.execute(
                    "UPDATE uoms SET name=?, short_name=?, decimals=?, is_active=?, updated_at=? WHERE id=?",
                    (name, short_name, int(decimals), 1 if is_active else 0, now, int(row[0])),
                )
                return int(row[0])
            cur = conn.execute(
                "INSERT INTO uoms (code,name,short_name,decimals,is_active,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                (code, name, short_name, int(decimals), 1 if is_active else 0, now, now),
            )
            return int(cur.lastrowid)

    def get_uom_by_code(self, code: str) -> dict[str, Any] | None:
        self.ensure_schema()
        if not code:
            return None
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT id,code,name,short_name,decimals,is_active FROM uoms WHERE LOWER(code)=?", (code.lower(),)).fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "code": row[1],
                "name": row[2],
                "short_name": row[3],
                "decimals": row[4],
                "is_active": bool(row[5]),
            }

    # Pack conversion
    def save_pack_conversion(self, from_uom: str, to_uom: str, factor: float, product_id: int = 0) -> int:
        self.ensure_schema()
        if not from_uom or not to_uom:
            raise ValueError("Both from_uom and to_uom are required.")
        try:
            factor_val = float(factor)
        except (TypeError, ValueError):
            raise ValueError("Conversion factor must be numeric.")
        if factor_val <= 0:
            raise ValueError("Conversion factor must be greater than zero.")
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            # allow multiple product-specific conversions; replace if exists for same tuple
            existing = conn.execute(
                "SELECT id FROM pack_conversions WHERE product_id=? AND LOWER(from_uom)=? AND LOWER(to_uom)=? LIMIT 1",
                (int(product_id), from_uom.lower(), to_uom.lower()),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE pack_conversions SET factor=?, updated_at=? WHERE id=?",
                    (factor_val, now, int(existing[0])),
                )
                return int(existing[0])
            cur = conn.execute(
                "INSERT INTO pack_conversions (product_id,from_uom,to_uom,factor,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (int(product_id), from_uom, to_uom, factor_val, now, now),
            )
            return int(cur.lastrowid)

    def get_conversion(self, from_uom: str, to_uom: str, product_id: int = 0) -> float | None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT factor FROM pack_conversions WHERE product_id=? AND LOWER(from_uom)=? AND LOWER(to_uom)=? LIMIT 1",
                (int(product_id), from_uom.lower(), to_uom.lower()),
            ).fetchone()
            if row:
                return float(row[0])
            # fallback to global (product_id=0)
            row = conn.execute(
                "SELECT factor FROM pack_conversions WHERE product_id=0 AND LOWER(from_uom)=? AND LOWER(to_uom)=? LIMIT 1",
                (from_uom.lower(), to_uom.lower()),
            ).fetchone()
            return float(row[0]) if row else None

    # Price levels
    def save_price_level(self, code: str, name: str) -> int:
        self.ensure_schema()
        if not code or not name:
            raise ValueError("Price level code and name required")
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute("SELECT id FROM price_levels WHERE LOWER(code)=? LIMIT 1", (code.lower(),)).fetchone()
            if existing:
                conn.execute("UPDATE price_levels SET name=?, updated_at=? WHERE id=?", (name, now, int(existing[0])))
                return int(existing[0])
            cur = conn.execute(
                "INSERT INTO price_levels (code,name,created_at,updated_at) VALUES (?,?,?,?)",
                (code, name, now, now),
            )
            return int(cur.lastrowid)

    def set_product_price(self, product_id: int, price_level_code: str, price: float) -> int:
        self.ensure_schema()
        try:
            price_val = float(price)
        except (TypeError, ValueError):
            raise ValueError("Price must be numeric")
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM product_prices WHERE product_id=? AND LOWER(price_level_code)=? LIMIT 1",
                (int(product_id), price_level_code.lower()),
            ).fetchone()
            if existing:
                conn.execute("UPDATE product_prices SET price=?, updated_at=? WHERE id=?", (price_val, now, int(existing[0])))
                return int(existing[0])
            cur = conn.execute(
                "INSERT INTO product_prices (product_id,price_level_code,price,created_at,updated_at) VALUES (?,?,?,?,?)",
                (int(product_id), price_level_code, price_val, now, now),
            )
            return int(cur.lastrowid)

    def get_product_price(self, product_id: int, price_level_code: str) -> float | None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT price FROM product_prices WHERE product_id=? AND LOWER(price_level_code)=? LIMIT 1",
                (int(product_id), price_level_code.lower()),
            ).fetchone()
            return float(row[0]) if row else None

    def set_party_default_price(self, party_table: str, party_id: int, price_level_code: str) -> int:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM party_price_defaults WHERE party_table=? AND party_id=? LIMIT 1",
                (party_table, int(party_id)),
            ).fetchone()
            if existing:
                conn.execute("UPDATE party_price_defaults SET price_level_code=?, updated_at=? WHERE id=?", (price_level_code, now, int(existing[0])))
                return int(existing[0])
            cur = conn.execute(
                "INSERT INTO party_price_defaults (party_table,party_id,price_level_code,created_at,updated_at) VALUES (?,?,?,?,?)",
                (party_table, int(party_id), price_level_code, now, now),
            )
            return int(cur.lastrowid)

    def get_party_default_price_level(self, party_table: str, party_id: int) -> str | None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT price_level_code FROM party_price_defaults WHERE party_table=? AND party_id=? LIMIT 1",
                (party_table, int(party_id)),
            ).fetchone()
            return row[0] if row else None
