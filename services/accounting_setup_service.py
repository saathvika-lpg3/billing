from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


TALLY_LEDGER_GROUPS: tuple[dict[str, Any], ...] = (
    {"code": "general", "name": "General", "parent_code": None, "nature": "other", "report_section": "other", "sort_order": 10},
    {"code": "capital_account", "name": "Capital Account", "parent_code": None, "nature": "equity", "report_section": "equity", "sort_order": 20},
    {"code": "reserves_surplus", "name": "Reserves & Surplus", "parent_code": "capital_account", "nature": "equity", "report_section": "equity", "sort_order": 30},
    {"code": "drawings", "name": "Drawings", "parent_code": "capital_account", "nature": "equity", "report_section": "equity", "sort_order": 40},
    {"code": "loans_liability", "name": "Loans (Liability)", "parent_code": None, "nature": "liability", "report_section": "liability", "sort_order": 80},
    {"code": "secured_loans", "name": "Secured Loans", "parent_code": "loans_liability", "nature": "liability", "report_section": "liability", "sort_order": 90},
    {"code": "unsecured_loans", "name": "Unsecured Loans", "parent_code": "loans_liability", "nature": "liability", "report_section": "liability", "sort_order": 100},
    {"code": "current_liabilities", "name": "Current Liabilities", "parent_code": None, "nature": "liability", "report_section": "liability", "sort_order": 120},
    {"code": "sundry_creditors", "name": "Sundry Creditors", "parent_code": "current_liabilities", "nature": "liability", "report_section": "liability", "sort_order": 130},
    {"code": "duties_taxes", "name": "Duties & Taxes", "parent_code": "current_liabilities", "nature": "liability", "report_section": "liability", "sort_order": 140},
    {"code": "provisions", "name": "Provisions", "parent_code": "current_liabilities", "nature": "liability", "report_section": "liability", "sort_order": 150},
    {"code": "fixed_assets", "name": "Fixed Assets", "parent_code": None, "nature": "asset", "report_section": "asset", "sort_order": 210},
    {"code": "investments", "name": "Investments", "parent_code": None, "nature": "asset", "report_section": "asset", "sort_order": 220},
    {"code": "current_assets", "name": "Current Assets", "parent_code": None, "nature": "asset", "report_section": "asset", "sort_order": 230},
    {"code": "bank_accounts", "name": "Bank Accounts", "parent_code": "current_assets", "nature": "asset", "report_section": "asset", "sort_order": 240},
    {"code": "cash_in_hand", "name": "Cash-in-hand", "parent_code": "current_assets", "nature": "asset", "report_section": "asset", "sort_order": 250},
    {"code": "deposits_asset", "name": "Deposits (Asset)", "parent_code": "current_assets", "nature": "asset", "report_section": "asset", "sort_order": 260},
    {"code": "loans_advances_asset", "name": "Loans & Advances (Asset)", "parent_code": "current_assets", "nature": "asset", "report_section": "asset", "sort_order": 270},
    {"code": "stock_in_hand", "name": "Stock-in-hand", "parent_code": "current_assets", "nature": "asset", "report_section": "asset", "sort_order": 280},
    {"code": "sundry_debtors", "name": "Sundry Debtors", "parent_code": "current_assets", "nature": "asset", "report_section": "asset", "sort_order": 290},
    {"code": "misc_expenses_asset", "name": "Misc. Expenses (Asset)", "parent_code": "current_assets", "nature": "asset", "report_section": "asset", "sort_order": 300},
    {"code": "sales_accounts", "name": "Sales Accounts", "parent_code": None, "nature": "income", "report_section": "income", "sort_order": 410},
    {"code": "purchase_accounts", "name": "Purchase Accounts", "parent_code": None, "nature": "expense", "report_section": "cogs", "sort_order": 420},
    {"code": "direct_incomes", "name": "Direct Incomes", "parent_code": None, "nature": "income", "report_section": "income", "sort_order": 430},
    {"code": "indirect_incomes", "name": "Indirect Incomes", "parent_code": None, "nature": "income", "report_section": "income", "sort_order": 440},
    {"code": "direct_expenses", "name": "Direct Expenses", "parent_code": None, "nature": "expense", "report_section": "cogs", "sort_order": 450},
    {"code": "indirect_expenses", "name": "Indirect Expenses", "parent_code": None, "nature": "expense", "report_section": "expense", "sort_order": 460},
    {"code": "suspense_account", "name": "Suspense Account", "parent_code": None, "nature": "other", "report_section": "other", "sort_order": 900},
)

TALLY_GROUP_NAMES: tuple[str, ...] = tuple(group["name"] for group in TALLY_LEDGER_GROUPS)

GROUP_ALIASES = {
    "capital": "Capital Account",
    "retained earnings": "Reserves & Surplus",
    "cash / bank": "Bank Accounts",
    "cash and bank": "Bank Accounts",
    "income": "Sales Accounts",
    "indirect income": "Indirect Incomes",
    "purchase": "Purchase Accounts",
    "direct expense": "Direct Expenses",
    "indirect expense": "Indirect Expenses",
    "asset": "Current Assets",
    "stock in hand": "Stock-in-hand",
    "liability": "Current Liabilities",
}

SYSTEM_LEDGER_GROUPS = {
    "cash": "Cash-in-hand",
    "bank": "Bank Accounts",
    "upi": "Bank Accounts",
    "card": "Bank Accounts",
    "cheque": "Bank Accounts",
    "sales": "Sales Accounts",
    "sales return": "Sales Accounts",
    "purchase": "Purchase Accounts",
    "purchase return": "Purchase Accounts",
    "output gst": "Duties & Taxes",
    "input gst": "Duties & Taxes",
    "output cgst": "Duties & Taxes",
    "output sgst": "Duties & Taxes",
    "output igst": "Duties & Taxes",
    "input cgst": "Duties & Taxes",
    "input sgst": "Duties & Taxes",
    "input igst": "Duties & Taxes",
    "output cess": "Duties & Taxes",
    "input cess": "Duties & Taxes",
    "round off": "Indirect Incomes",
    "service charge income": "Indirect Incomes",
    "capital": "Capital Account",
    "drawings": "Drawings",
    "opening balance equity": "Capital Account",
    "retained earnings": "Reserves & Surplus",
    "stock in hand": "Stock-in-hand",
    "stock in hand - raw material": "Stock-in-hand",
    "stock in hand - finished goods": "Stock-in-hand",
    "stock adjustment": "Indirect Expenses",
    "production variance": "Indirect Expenses",
}


def tally_group_names() -> tuple[str, ...]:
    return TALLY_GROUP_NAMES


class AccountingSetupService:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)

    def ensure_tally_accounting(self) -> None:
        if not self.db_path.exists():
            return
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_accounting_tables(conn)
            for group in TALLY_LEDGER_GROUPS:
                self._upsert_group(conn, group, now)
            self._normalize_ledger_groups(conn)
            self._normalize_ledgers(conn)

    def _ensure_accounting_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT,
                parent_code TEXT,
                nature TEXT,
                report_section TEXT,
                sort_order INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS account_ledgers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                code TEXT,
                group_name TEXT,
                opening_dr REAL DEFAULT 0,
                opening_cr REAL DEFAULT 0,
                is_system INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

    def _upsert_group(self, conn: sqlite3.Connection, group: dict[str, Any], now: str) -> None:
        row = conn.execute(
            """
            SELECT id
            FROM ledger_groups
            WHERE LOWER(COALESCE(code,''))=LOWER(?) OR LOWER(COALESCE(name,''))=LOWER(?)
            ORDER BY id
            LIMIT 1
            """,
            (group["code"], group["name"]),
        ).fetchone()
        values = (
            group["code"],
            group["name"],
            group["parent_code"],
            group["nature"],
            group["report_section"],
            int(group["sort_order"]),
            1,
            1,
            now,
        )
        if row:
            conn.execute(
                """
                UPDATE ledger_groups
                SET code=?, name=?, parent_code=?, nature=?, report_section=?,
                    sort_order=?, is_system=?, is_active=?, updated_at=?
                WHERE id=?
                """,
                (*values, int(row[0])),
            )
            return
        conn.execute(
            """
            INSERT INTO ledger_groups(
                code,name,parent_code,nature,report_section,sort_order,is_system,is_active,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (*values[:-1], now, now),
        )

    def _normalize_ledger_groups(self, conn: sqlite3.Connection) -> None:
        active_names = {name.lower() for name in TALLY_GROUP_NAMES}
        alias_names = tuple(GROUP_ALIASES.keys())
        if not alias_names:
            return
        placeholders = ",".join("?" for _ in alias_names)
        conn.execute(
            f"""
            UPDATE ledger_groups
            SET is_active=0, updated_at=?
            WHERE LOWER(COALESCE(name,'')) IN ({placeholders})
              AND LOWER(COALESCE(name,'')) NOT IN ({','.join('?' for _ in active_names)})
            """,
            (datetime.now().isoformat(timespec="seconds"), *alias_names, *active_names),
        )

    def _normalize_ledgers(self, conn: sqlite3.Connection) -> None:
        for old_group, new_group in GROUP_ALIASES.items():
            conn.execute(
                "UPDATE account_ledgers SET group_name=? WHERE LOWER(TRIM(COALESCE(group_name,'')))=?",
                (new_group, old_group),
            )
        for ledger_name, group_name in SYSTEM_LEDGER_GROUPS.items():
            conn.execute(
                "UPDATE account_ledgers SET group_name=? WHERE LOWER(TRIM(COALESCE(name,'')))=?",
                (group_name, ledger_name),
            )
