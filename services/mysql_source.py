
from __future__ import annotations

import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


_ACCOUNTING_CHECKED_PATHS: set[str] = set()


@dataclass(frozen=True)
class MySqlConfig:
    host: str = "localhost"
    user: str = "root"
    password: str = ""
    database: str = "prm_gst"
    charset: str = "utf8mb4"


class MySqlSource:
    def __init__(self, config: MySqlConfig | None = None) -> None:
        self.config = config or MySqlConfig()
        self._registered_connections: list[sqlite3.Connection] = []
        self._sqlite_connections: list[Any] = []
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent / "_internal"
        else:
            base_dir = Path(__file__).resolve().parents[1]
        default_sqlite = base_dir / "database" / "prm_billing_inventory.db"
        # Resolve canonical sqlite path with environment override
        self.sqlite_path = self._resolve_sqlite_path(os.environ.get("PRM_SQLITE_DB"), default_sqlite)
        self.use_sqlite = self.sqlite_path.exists() and os.environ.get("PRM_USE_SQLITE") != "1"
        if self.use_sqlite:
            self._ensure_accounting_setup_once()
            self._ensure_schema_once()
            try:
                # Run lightweight diagnostics and write a startup log
                from services.db_diagnostics import run_startup_db_diagnostics

                run_startup_db_diagnostics(self.sqlite_path, True)
            except Exception:
                pass

    def register_connection(self, conn: sqlite3.Connection | Any) -> None:
        if isinstance(conn, sqlite3.Connection):
            if conn not in self._registered_connections:
                self._registered_connections.append(conn)
            return
        if conn not in self._sqlite_connections:
            self._sqlite_connections.append(conn)

    def unregister_connection(self, conn: sqlite3.Connection | Any) -> None:
        if isinstance(conn, sqlite3.Connection):
            if conn in self._registered_connections:
                self._registered_connections.remove(conn)
            return
        if conn in self._sqlite_connections:
            self._sqlite_connections.remove(conn)

    def close_database_resources(self) -> None:
        for conn in list(self._registered_connections):
            try:
                conn.commit()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            finally:
                try:
                    self._registered_connections.remove(conn)
                except ValueError:
                    pass
        for conn in list(self._sqlite_connections):
            try:
                conn.close()
            except Exception:
                pass
            finally:
                try:
                    self._sqlite_connections.remove(conn)
                except ValueError:
                    pass

    def _ensure_accounting_setup_once(self) -> None:
        key = str(self.sqlite_path.resolve())
        if key in _ACCOUNTING_CHECKED_PATHS:
            return
        try:
            from services.accounting_setup_service import AccountingSetupService

            AccountingSetupService(self.sqlite_path).ensure_tally_accounting()
        except Exception:
            pass
        _ACCOUNTING_CHECKED_PATHS.add(key)

    def _resolve_sqlite_path(self, env_value: str | None, default: Path) -> Path:
        """Resolve a canonical sqlite DB path.

        Order:
        1. `PRM_SQLITE_DB` environment variable if set (expanded)
        2. default under project `database/prm_billing_inventory.db`
        """
        if env_value:
            p = Path(os.path.expandvars(str(env_value))).expanduser()
            try:
                return p.resolve()
            except Exception:
                return p
        try:
            return default.resolve()
        except Exception:
            return default

    def _ensure_schema_once(self) -> None:
        key = f"schema:{str(self.sqlite_path.resolve())}"
        if key in _ACCOUNTING_CHECKED_PATHS:
            return
        try:
            # Minimal bootstrap of essential tables to avoid circular imports
            sqlite_sql = [
                """
                CREATE TABLE IF NOT EXISTS company (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    business_name TEXT,
                    gstin TEXT,
                    pan TEXT,
                    fssai_no TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    invoice_prefix TEXT,
                    upi_id TEXT,
                    business_type_code TEXT,
                    invoice_template_code TEXT,
                    subscription_plan_code TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS license (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    install_code TEXT,
                    license_key TEXT,
                    client_name TEXT,
                    company_id INTEGER,
                    company_name TEXT,
                    business_type TEXT,
                    installation_key TEXT,
                    activation_date TEXT,
                    expiry_date TEXT,
                    status TEXT,
                    license_plan TEXT,
                    gstin TEXT,
                    max_users INTEGER,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    activated_at TEXT,
                    last_checked_at TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS dev_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    owner_name TEXT,
                    mobile TEXT,
                    email TEXT,
                    gst_number TEXT,
                    pan TEXT,
                    business_type_code TEXT,
                    subscription_plan_code TEXT,
                    invoice_template_code TEXT,
                    status TEXT,
                    license_key TEXT,
                    start_date TEXT,
                    expiry_date TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS company_profile_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    changed_at TEXT,
                    changed_by TEXT,
                    source TEXT,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    machine_id TEXT,
                    reason TEXT
                )
                """,
            ]
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.sqlite_path) as conn:
                for stmt in sqlite_sql:
                    conn.execute(stmt)
                self._ensure_column(conn, "print_templates", "orientation", "TEXT")
        except Exception:
            pass
        _ACCOUNTING_CHECKED_PATHS.add(key)

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        try:
            columns = {str(row[1]).lower() for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            if columns and column.lower() not in columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.Error:
            return

    def _connect(self):
        raise RuntimeError("This data source uses SQLite only; MySQL is not available.")

    def _table_columns(self, table_name: str) -> set[str]:
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                return {str(row[1]).lower() for row in rows}
        except Exception:
            return set()

    def rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        if self.use_sqlite:
            return self._sqlite_rows(sql, params)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())

    def _sqlite_rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        sqlite_sql = sql.replace("%s", "?")
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sqlite_sql, params)
            return [dict(row) for row in cur.fetchall()]

    def one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        rows = self.rows(sql, params)
        return rows[0] if rows else None

    def company(self) -> dict[str, Any]:
        return self.one("SELECT * FROM company LIMIT 1") or {}

    def global_search(self, query: str, limit: int = 25, offset: int = 0) -> dict[str, Any]:
        text = str(query or "").strip()
        lowered = text.lower()
        rows: list[dict[str, Any]] = self._search_route_rows(lowered)
        if len(lowered) >= 2:
            rows.extend(self._search_record_rows(text))
        total = len(rows)
        start = max(0, int(offset))
        end = start + max(1, int(limit))
        return {"total": total, "rows": rows[start:end]}

    def _search_route_rows(self, query: str) -> list[dict[str, Any]]:
        routes = [
            ("Sales Bill", "sales_bill", "invoice bill sales customer fast entry"),
            ("Sales List", "reports:sales_list", "bill invoice customer sales list"),
            ("Purchase Bill", "purchase_entry", "purchase supplier stock buy"),
            ("Purchase List", "reports:purchase_list", "purchase supplier invoice list"),
            ("Receipt", "receipt_entry", "customer collection receipt"),
            ("Payment", "payment_entry", "supplier payment voucher"),
            ("Print Bills", "document_center", "bulk print invoice documents"),
            ("Check Stock", "stock_dashboard", "stock inventory item"),
            ("Products", "product_master", "product item barcode hsn pack fmcg"),
            ("Customers", "customer_master", "customer party receivable"),
            ("Suppliers", "supplier_master", "supplier party payable"),
            ("Daily Dispatch Summary", "reports:daily_dispatch_summary", "dispatch route vehicle summary"),
            ("Loading Sheet", "reports:loading_sheet", "load challan dispatch loading sheet"),
            ("Item Loading Sheet", "reports:item_loading_sheet", "item loading picking sheet"),
            ("Dispatch Return", "dispatch_return_entry", "dispatch return damaged accepted route stock credit note"),
            ("ERP Profit & Loss", "reports:erp_profit_loss", "profit loss p and l ledger accounts"),
            ("Balance Sheet", "reports:balance_sheet", "balance sheet liabilities assets capital"),
            ("GST Return", "reports:gst_return", "gst return tax filing"),
            ("Reports", "reports", "business reports dashboard export"),
            ("Backup", "developer_console", "backup restore data"),
            ("Company Settings", "company_settings", "company client profile logo gstin fssai"),
        ]
        matches: list[dict[str, Any]] = []
        for label, target, keywords in routes:
            haystack = f"{label} {keywords}".lower()
            if not query or query in haystack:
                matches.append(
                    {
                        "type": "Menu",
                        "reference": label,
                        "date": "",
                        "party": "",
                        "amount": "",
                        "detail": keywords,
                        "target_page": target,
                    }
                )
        return matches

    def _search_record_rows(self, query: str) -> list[dict[str, Any]]:
        like = f"%{query}%"
        groups: list[tuple[str, str, tuple[Any, ...], str]] = [
            (
                "Sales Bill",
                """
                SELECT bill_no reference,bill_date date,customer_name party,grand_total amount,
                       COALESCE(pay_mode,'') detail
                FROM sales
                WHERE bill_no LIKE %s OR customer_name LIKE %s
                ORDER BY id DESC
                LIMIT 100
                """,
                (like, like),
                "reports:sales_list",
            ),
            (
                "Purchase Bill",
                """
                SELECT bill_no reference,bill_date date,supplier_name party,grand_total amount,
                       COALESCE(status,'') detail
                FROM purchases
                WHERE bill_no LIKE %s OR supplier_name LIKE %s
                ORDER BY id DESC
                LIMIT 100
                """,
                (like, like),
                "reports:purchase_list",
            ),
            (
                "Customer",
                """
                SELECT name reference,'' date,name party,balance amount,
                       'Phone: ' || COALESCE(phone,'') || ' | GSTIN: ' || COALESCE(gstin,'') detail
                FROM customers
                WHERE name LIKE %s OR phone LIKE %s OR gstin LIKE %s
                ORDER BY name
                LIMIT 100
                """,
                (like, like, like),
                "customer_master",
            ),
            (
                "Supplier",
                """
                SELECT name reference,'' date,name party,balance amount,
                       'Phone: ' || COALESCE(phone,'') || ' | GSTIN: ' || COALESCE(gstin,'') detail
                FROM suppliers
                WHERE name LIKE %s OR phone LIKE %s OR gstin LIKE %s
                ORDER BY name
                LIMIT 100
                """,
                (like, like, like),
                "supplier_master",
            ),
            (
                "Item",
                """
                SELECT i.name reference,'' date,COALESCE(s.name,'') party,COALESCE(i.stock,0) amount,
                       'Code: ' || COALESCE(i.code,'') || ' | HSN: ' || COALESCE(i.hsn,'') || ' | Barcode: ' || COALESCE(i.barcode,'') detail
                FROM items i
                LEFT JOIN suppliers s ON s.id=i.supplier_id
                WHERE i.name LIKE %s OR i.code LIKE %s OR i.barcode LIKE %s OR i.hsn LIKE %s
                ORDER BY i.name
                LIMIT 150
                """,
                (like, like, like, like),
                "product_master",
            ),
            (
                "Receipt",
                """
                SELECT receipt_no reference,receipt_date date,customer_name party,amount,
                       COALESCE(mode,'') detail
                FROM receipts
                WHERE receipt_no LIKE %s OR customer_name LIKE %s
                ORDER BY id DESC
                LIMIT 100
                """,
                (like, like),
                "receipt_entry",
            ),
            (
                "Payment",
                """
                SELECT payment_no reference,payment_date date,supplier_name party,amount,
                       COALESCE(mode,'') detail
                FROM payments
                WHERE payment_no LIKE %s OR supplier_name LIKE %s
                ORDER BY id DESC
                LIMIT 100
                """,
                (like, like),
                "payment_entry",
            ),
        ]
        found: list[dict[str, Any]] = []
        for result_type, sql, params, target in groups:
            try:
                for row in self.rows(sql, params):
                    found.append(
                        {
                            "type": result_type,
                            "reference": row.get("reference", ""),
                            "date": row.get("date", ""),
                            "party": row.get("party", ""),
                            "amount": row.get("amount", ""),
                            "detail": row.get("detail", ""),
                            "target_page": target,
                        }
                    )
            except Exception:
                continue
        found.sort(key=lambda row: (str(row.get("type", "")), str(row.get("date", ""))), reverse=True)
        return found

    def customers(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name,COALESCE(area,'') area,COALESCE(gstin,'') gstin,COALESCE(phone,'') phone,COALESCE(balance,0) balance,COALESCE(shipping_address,address,'') shipping_address FROM customers ORDER BY name LIMIT 2000")

    def suppliers(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name,COALESCE(gstin,'') gstin,COALESCE(phone,'') phone FROM suppliers ORDER BY name")

    def item_categories(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name,COALESCE(code,'') code,COALESCE(default_gst,0) default_gst FROM item_categories WHERE COALESCE(is_active,1)=1 ORDER BY sort_order,name")

    def brands(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name,COALESCE(master_type,'brand') master_type FROM business_masters WHERE COALESCE(is_active,1)=1 AND master_type IN ('brand','manufacturer') ORDER BY name")

    def units(self) -> list[dict[str, Any]]:
        return self.rows("SELECT name FROM units ORDER BY name")

    def tax_slabs(self) -> list[dict[str, Any]]:
        return self.rows("SELECT rate,COALESCE(name,'') name FROM tax_slabs WHERE COALESCE(is_active,1)=1 ORDER BY rate")

    def users(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name,COALESCE(role,'') role FROM users ORDER BY name")

    def warehouses(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name FROM warehouses ORDER BY name")

    def branches(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name FROM branches ORDER BY name")

    def cost_centers(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,name FROM cost_centers ORDER BY name")

    def salesmen(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,code,name,COALESCE(mobile,'') mobile,COALESCE(email,'') email FROM salesmen ORDER BY name")

    def vehicles(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,code,vehicle_no FROM vehicles ORDER BY code")

    def transporters(self) -> list[dict[str, Any]]:
        return self.rows("SELECT id,code,name,COALESCE(mobile,'') mobile FROM transporters ORDER BY name")

    def product_choices(self) -> list[dict[str, Any]]:
        item_columns = self._table_columns("items")
        pack_columns = self._table_columns("product_packs")

        item_code_expr = "COALESCE(i.code, '')" if "code" in item_columns else "''"
        item_hsn_expr = "COALESCE(i.hsn, '')" if "hsn" in item_columns else "''"
        item_gst_expr = "COALESCE(i.gst, 0)" if "gst" in item_columns else "0"
        item_supplier_expr = "COALESCE(i.supplier_id, 0)" if "supplier_id" in item_columns else "0"
        item_unit_expr = "COALESCE(i.unit, 'PCS')" if "unit" in item_columns else "'PCS'"
        item_mrp_expr = "COALESCE(i.mrp, 0)" if "mrp" in item_columns else "0"
        item_buy_rate_expr = "COALESCE(i.buy_rate, 0)" if "buy_rate" in item_columns else "0"
        item_sale_rate_expr = "COALESCE(i.sale_rate, 0)" if "sale_rate" in item_columns else "0"
        item_stock_expr = "COALESCE(i.stock, 0)" if "stock" in item_columns else "0"

        pack_display_expr = "COALESCE(NULLIF(pp.display_name, ''), '')" if "display_name" in pack_columns else "''"
        pack_barcode_expr = "COALESCE(pp.barcode, i.barcode, '')" if "barcode" in pack_columns else "COALESCE(i.barcode, '')"
        pack_unit_expr = "COALESCE(pp.pack_unit, i.unit, 'PCS')" if "pack_unit" in pack_columns else item_unit_expr
        pack_mrp_expr = f"COALESCE(pp.mrp, {item_mrp_expr}, 0)" if "mrp" in pack_columns else item_mrp_expr
        pack_purchase_expr = f"COALESCE(pp.purchase_rate, {item_buy_rate_expr}, 0)" if "purchase_rate" in pack_columns else item_buy_rate_expr
        pack_sale_expr = f"COALESCE(pp.sale_rate, {item_sale_rate_expr}, 0)" if "sale_rate" in pack_columns else item_sale_rate_expr
        pack_dealer_expr = f"COALESCE(pp.dealer_rate, pp.sale_rate, {item_sale_rate_expr}, 0)" if "dealer_rate" in pack_columns else pack_sale_expr
        pack_distributor_expr = f"COALESCE(pp.distributor_rate, pp.sale_rate, {item_sale_rate_expr}, 0)" if "distributor_rate" in pack_columns else pack_sale_expr
        pack_wholesale_expr = f"COALESCE(pp.wholesale_rate, pp.sale_rate, {item_sale_rate_expr}, 0)" if "wholesale_rate" in pack_columns else pack_sale_expr
        pack_retail_expr = f"COALESCE(pp.retail_rate, pp.sale_rate, {item_sale_rate_expr}, 0)" if "retail_rate" in pack_columns else pack_sale_expr
        pack_stock_expr = f"COALESCE(pp.current_stock_qty, {item_stock_expr}, 0)" if "current_stock_qty" in pack_columns else item_stock_expr
        pack_scheme_expr = "COALESCE(pp.scheme, '')" if "scheme" in pack_columns else "''"
        pack_id_expr = "COALESCE(pp.id, 0)" if "id" in pack_columns else "0"
        pack_size_expr = "COALESCE(pp.pack_size, 1)" if "pack_size" in pack_columns else "1"
        pack_is_default_expr = "COALESCE(pp.is_default, 0)" if "is_default" in pack_columns else "0"
        pack_is_active_expr = "COALESCE(pp.is_active, 1)" if "is_active" in pack_columns else "1"
        item_brand_expr = "COALESCE(i.brand_id, 0)" if "brand_id" in item_columns else "0"

        return self.rows(
            f"""
            SELECT
                i.id item_id,
                i.name item_name,
                {item_code_expr} item_code,
                {item_hsn_expr} hsn,
                {item_gst_expr} gst,
                {item_supplier_expr} supplier_id,
                COALESCE(s.name, '') supplier_name,
                {item_brand_expr} brand_id,
                '' brand_name,
                {pack_id_expr} pack_id,
                {pack_display_expr} pack_name,
                {pack_barcode_expr} barcode,
                {pack_unit_expr} unit,
                {pack_mrp_expr} mrp,
                {pack_purchase_expr} purchase_rate,
                {pack_sale_expr} sale_rate,
                {pack_dealer_expr} dealer_rate,
                {pack_distributor_expr} distributor_rate,
                {pack_wholesale_expr} wholesale_rate,
                {pack_retail_expr} retail_rate,
                {pack_stock_expr} stock_qty,
                {pack_scheme_expr} scheme,
                {pack_size_expr} pack_size
            FROM items i
            LEFT JOIN suppliers s ON s.id=i.supplier_id
            LEFT JOIN product_packs pp ON pp.product_id=i.id AND {pack_is_active_expr}=1
            WHERE COALESCE(i.status,'Active')='Active'
            ORDER BY i.name, {pack_is_default_expr} DESC, pp.id
            LIMIT 5000
            """
        )

    def product_master_rows(self, limit: int = 300) -> list[dict[str, Any]]:
        return self.rows(
            f"""
            SELECT
                i.id,
                COALESCE(i.code,'') code,
                COALESCE(i.name,'') name,
                COALESCE(i.hsn,'') hsn,
                COALESCE(i.unit,'') unit,
                COALESCE(i.sale_unit,'') sale_unit,
                COALESCE(i.purchase_unit,'') purchase_unit,
                COALESCE(i.gst,0) gst,
                COALESCE(i.mrp,0) mrp,
                COALESCE(i.sale_rate,0) sale_rate,
                COALESCE(i.buy_rate,0) buy_rate,
                COALESCE(i.stock,0) stock,
                COALESCE(i.min_stock,0) min_stock,
                COALESCE(i.reorder_qty,0) reorder_qty,
                COALESCE(i.lead_time_days,0) lead_time_days,
                COALESCE(i.pack_size,1) pack_size,
                COALESCE(i.box_qty,0) box_qty,
                COALESCE(i.standard_cost,0) standard_cost,
                COALESCE(i.valuation_method,'weighted_average') valuation_method,
                COALESCE(i.barcode,'') barcode,
                COALESCE(i.sale_unit,'') sale_unit,
                COALESCE(i.purchase_unit,'') purchase_unit,
                COALESCE(i.multi_uom,0) multi_uom,
                COALESCE(i.pack_conversion,0) pack_conversion,
                COALESCE(i.shelf_life_days,0) shelf_life_days,
                COALESCE(i.near_expiry_days,0) near_expiry_days,
                COALESCE(i.sku_alias,'') sku_alias,
                COALESCE(i.supplier_item_code,'') supplier_item_code,
                COALESCE(i.item_type,'Stock Item') item_type,
                COALESCE(i.status,'Active') status,
                COALESCE(i.batch_required,0) batch_required,
                COALESCE(i.expiry_required,0) expiry_required,
                COALESCE(i.item_notes,'') item_notes,
                COALESCE(i.supplier_id,0) supplier_id,
                COALESCE(i.category_id,0) category_id,
                COALESCE(i.brand_id,0) brand_id,
                COALESCE(s.name,'') supplier_name,
                COALESCE(ic.name,'') category_name,
                COALESCE(bm.name,'') brand_name,
                COALESCE(ppa.pack_count,0) pack_count,
                COALESCE(ppa.pack_stock_total,i.stock,0) pack_stock_total,
                COALESCE(ppd.display_name,'') default_pack_name,
                COALESCE(ppd.mrp,i.mrp,0) default_mrp,
                COALESCE(ppd.sale_rate,i.sale_rate,0) default_sale_rate,
                COALESCE(ppd.barcode,i.barcode,'') default_pack_barcode
            FROM items i
            LEFT JOIN suppliers s ON s.id=i.supplier_id
            LEFT JOIN item_categories ic ON ic.id=i.category_id
            LEFT JOIN business_masters bm ON bm.id=i.brand_id
            LEFT JOIN (
                SELECT product_id, COUNT(*) pack_count, COALESCE(SUM(current_stock_qty),0) pack_stock_total
                FROM product_packs
                WHERE COALESCE(is_active,1)=1
                GROUP BY product_id
            ) ppa ON ppa.product_id=i.id
            LEFT JOIN product_packs ppd ON ppd.id=(
                SELECT pp2.id
                FROM product_packs pp2
                WHERE pp2.product_id=i.id AND COALESCE(pp2.is_active,1)=1
                ORDER BY COALESCE(pp2.is_default,0) DESC, pp2.id ASC
                LIMIT 1
            )
            ORDER BY i.id DESC
            LIMIT {int(limit)}
            """
        )

    def product_pack_rows(self, product_id: int) -> list[dict[str, Any]]:
        return self.rows(
            """
            SELECT
                id, product_id,
                COALESCE(pack_size,1) pack_size,
                COALESCE(pack_unit,'PCS') pack_unit,
                COALESCE(display_name,'') display_name,
                COALESCE(barcode,'') barcode,
                COALESCE(supplier_item_code,'') supplier_item_code,
                COALESCE(hsn,'') hsn,
                COALESCE(mrp,0) mrp,
                COALESCE(purchase_rate,0) purchase_rate,
                COALESCE(sale_rate,0) sale_rate,
                COALESCE(dealer_rate,0) dealer_rate,
                COALESCE(distributor_rate,0) distributor_rate,
                COALESCE(wholesale_rate,0) wholesale_rate,
                COALESCE(retail_rate,0) retail_rate,
                COALESCE(standard_cost,0) standard_cost,
                COALESCE(box_qty,0) box_qty,
                COALESCE(opening_stock_qty,0) opening_stock_qty,
                COALESCE(current_stock_qty,0) current_stock_qty,
                COALESCE(low_stock_alert,0) low_stock_alert,
                COALESCE(reorder_qty,0) reorder_qty,
                COALESCE(scheme,'') scheme,
                COALESCE(is_default,0) is_default,
                COALESCE(is_active,1) is_active,
                COALESCE(ptr,0) ptr,
                COALESCE(pts,0) pts
            FROM product_packs
            WHERE product_id=%s
            ORDER BY COALESCE(is_default,0) DESC, id ASC
            """,
            (product_id,),
        )

    def sales_return_sources(self, limit: int = 300) -> list[dict[str, Any]]:
        return self.rows(
            """
            SELECT id,bill_no,bill_date,customer_id,customer_name,customer_area,warehouse_id,
                   pay_mode,grand_total,status,branch_name,cost_center_name
            FROM sales
            WHERE COALESCE(status,'Active')='Active'
            ORDER BY bill_date DESC,id DESC
            LIMIT %s
            """,
            (int(limit),),
        )

    def sales_return_source_lines(self, sale_id: int) -> list[dict[str, Any]]:
        return self.rows(
            """
            SELECT si.id source_item_id, si.sale_id source_doc_id, s.bill_no source_doc_no,
                   si.item_id, si.item_name, si.hsn, si.unit, si.mrp, si.qty original_qty,
                   si.free_qty original_free_qty, si.rate, si.gst, si.discount,
                   si.warehouse_id, si.pack_id,
                   COALESCE(si.pack_display_snapshot,'') pack_name,
                   COALESCE(si.pack_size_snapshot,1) pack_size,
                   COALESCE(pp.current_stock_qty,i.stock,0) stock_qty,
                   COALESCE(ret.returned_qty,0) returned_qty,
                   COALESCE(ret.returned_free_qty,0) returned_free_qty,
                   CASE WHEN COALESCE(si.qty,0)-COALESCE(ret.returned_qty,0) > 0
                        THEN COALESCE(si.qty,0)-COALESCE(ret.returned_qty,0) ELSE 0 END remaining_qty,
                   CASE WHEN COALESCE(si.free_qty,0)-COALESCE(ret.returned_free_qty,0) > 0
                        THEN COALESCE(si.free_qty,0)-COALESCE(ret.returned_free_qty,0) ELSE 0 END remaining_free_qty,
                   CASE WHEN COALESCE(si.igst,0) > 0 THEN 'igst' ELSE 'cgst_sgst' END tax_mode
            FROM sales_items si
            JOIN sales s ON s.id=si.sale_id
            LEFT JOIN items i ON i.id=si.item_id
            LEFT JOIN product_packs pp ON pp.id=si.pack_id
            LEFT JOIN (
                SELECT sri.sale_item_id, SUM(COALESCE(sri.qty,0)) returned_qty,
                       SUM(COALESCE(sri.free_qty,0)) returned_free_qty
                FROM sales_return_items sri
                JOIN sales_returns sr ON sr.id=sri.return_id
                WHERE COALESCE(sr.status,'Active')<>'Cancelled'
                GROUP BY sri.sale_item_id
            ) ret ON ret.sale_item_id=si.id
            WHERE si.sale_id=%s
            ORDER BY si.id
            """,
            (int(sale_id),),
        )

    def purchase_return_sources(self, limit: int = 300) -> list[dict[str, Any]]:
        return self.rows(
            """
            SELECT id,bill_no,bill_date,supplier_id,supplier_name,warehouse_id,pay_mode,
                   grand_total,status,branch_name,cost_center_name
            FROM purchases
            WHERE COALESCE(status,'Active')='Active'
            ORDER BY bill_date DESC,id DESC
            LIMIT %s
            """,
            (int(limit),),
        )

    def purchase_return_source_lines(self, purchase_id: int) -> list[dict[str, Any]]:
        return self.rows(
            """
            SELECT pi.id source_item_id, pi.purchase_id source_doc_id, p.bill_no source_doc_no,
                   pi.item_id, pi.item_name, pi.hsn, pi.unit, pi.mrp, pi.qty original_qty,
                   pi.free_qty original_free_qty, pi.rate, pi.gst, 0 discount,
                   pi.warehouse_id, pi.pack_id,
                   COALESCE(pi.pack_display_snapshot,'') pack_name,
                   COALESCE(pi.pack_size_snapshot,1) pack_size,
                   COALESCE(pp.current_stock_qty,i.stock,0) stock_qty,
                   COALESCE(ret.returned_qty,0) returned_qty,
                   COALESCE(ret.returned_free_qty,0) returned_free_qty,
                   CASE WHEN COALESCE(pi.qty,0)-COALESCE(ret.returned_qty,0) > 0
                        THEN COALESCE(pi.qty,0)-COALESCE(ret.returned_qty,0) ELSE 0 END remaining_qty,
                   CASE WHEN COALESCE(pi.free_qty,0)-COALESCE(ret.returned_free_qty,0) > 0
                        THEN COALESCE(pi.free_qty,0)-COALESCE(ret.returned_free_qty,0) ELSE 0 END remaining_free_qty,
                   CASE WHEN COALESCE(pi.igst,0) > 0 THEN 'igst' ELSE 'cgst_sgst' END tax_mode
            FROM purchase_items pi
            JOIN purchases p ON p.id=pi.purchase_id
            LEFT JOIN items i ON i.id=pi.item_id
            LEFT JOIN product_packs pp ON pp.id=pi.pack_id
            LEFT JOIN (
                SELECT pri.purchase_item_id, SUM(COALESCE(pri.qty,0)) returned_qty,
                       SUM(COALESCE(pri.free_qty,0)) returned_free_qty
                FROM purchase_return_items pri
                JOIN purchase_returns pr ON pr.id=pri.return_id
                WHERE COALESCE(pr.status,'Active')<>'Cancelled'
                GROUP BY pri.purchase_item_id
            ) ret ON ret.purchase_item_id=pi.id
            WHERE pi.purchase_id=%s
            ORDER BY pi.id
            """,
            (int(purchase_id),),
        )

    def dispatch_return_sources(self, source_table: str = "sales", limit: int = 300) -> list[dict[str, Any]]:
        if source_table == "stock_outs":
            return self.rows(
                """
                SELECT 'stock_outs' source_table,id,challan_no source_ref,challan_date source_date,
                       COALESCE(salesman_name,area,'') customer_name,area route,area area,
                       COALESCE(vehicle_no,'') vehicle,COALESCE(dispatch_status,'Pending Dispatch') dispatch_status,
                       COALESCE(total_qty,0) total_qty,0 grand_total
                FROM stock_outs
                WHERE COALESCE(status,'Active')<>'Cancelled'
                ORDER BY challan_date DESC,id DESC
                LIMIT %s
                """,
                (int(limit),),
            )
        return self.rows(
            """
            SELECT 'sales' source_table,id,bill_no source_ref,bill_date source_date,customer_name,
                   customer_area route,customer_area area,COALESCE(transport_details,'') vehicle,
                   COALESCE(dispatch_status,'Open') dispatch_status,
                   (SELECT COALESCE(SUM(qty),0) FROM sales_items WHERE sale_id=sales.id) total_qty,
                   COALESCE(grand_total,0) grand_total
            FROM sales
            WHERE COALESCE(status,'Active')<>'Cancelled'
            ORDER BY bill_date DESC,id DESC
            LIMIT %s
            """,
            (int(limit),),
        )

    def dispatch_return_source_lines(self, source_table: str, source_id: int) -> list[dict[str, Any]]:
        returned_sql = """
            SELECT dri.source_item_id,
                   SUM(COALESCE(dri.returned_qty,0)) returned_qty,
                   SUM(COALESCE(dri.free_qty,0)) returned_free_qty
            FROM dispatch_return_items dri
            JOIN dispatch_returns dr ON dr.id=dri.dispatch_return_id
            WHERE dri.source_table=%s AND dri.source_id=%s AND COALESCE(dr.status,'Active')<>'Cancelled'
            GROUP BY dri.source_item_id
        """
        if source_table == "stock_outs":
            return self.rows(
                f"""
                SELECT soi.id source_item_id,soi.stock_out_id source_doc_id,so.challan_no source_doc_no,
                       soi.warehouse_id,soi.item_id,soi.pack_id,COALESCE(soi.pack_display_snapshot,'') pack_name,
                       COALESCE(soi.pack_size_snapshot,1) pack_size,soi.item_name,soi.unit,'' company,
                       COALESCE(soi.qty,0) dispatched_qty,COALESCE(soi.free_qty,0) dispatched_free_qty,
                       COALESCE(soi.mrp,0) rate,COALESCE(soi.mrp,0) mrp,COALESCE(soi.hsn,'') hsn,
                       COALESCE(ret.returned_qty,0) returned_qty,COALESCE(ret.returned_free_qty,0) returned_free_qty,
                       CASE WHEN COALESCE(soi.qty,0)-COALESCE(ret.returned_qty,0) > 0
                            THEN COALESCE(soi.qty,0)-COALESCE(ret.returned_qty,0) ELSE 0 END available_qty,
                       CASE WHEN COALESCE(soi.free_qty,0)-COALESCE(ret.returned_free_qty,0) > 0
                            THEN COALESCE(soi.free_qty,0)-COALESCE(ret.returned_free_qty,0) ELSE 0 END available_free_qty,
                       COALESCE(soi.qty,0)*COALESCE(soi.mrp,0) value
                FROM stock_out_items soi
                JOIN stock_outs so ON so.id=soi.stock_out_id
                LEFT JOIN ({returned_sql}) ret ON ret.source_item_id=soi.id
                WHERE soi.stock_out_id=%s
                ORDER BY soi.id
                """,
                (source_table, int(source_id), int(source_id)),
            )
        return self.rows(
            f"""
            SELECT si.id source_item_id,si.sale_id source_doc_id,s.bill_no source_doc_no,
                   si.warehouse_id,si.item_id,si.pack_id,COALESCE(si.pack_display_snapshot,'') pack_name,
                   COALESCE(si.pack_size_snapshot,1) pack_size,si.item_name,si.unit,'' company,
                   COALESCE(si.qty,0) dispatched_qty,COALESCE(si.free_qty,0) dispatched_free_qty,
                   COALESCE(si.rate,0) rate,COALESCE(si.mrp,0) mrp,COALESCE(si.hsn,'') hsn,
                   COALESCE(ret.returned_qty,0) returned_qty,COALESCE(ret.returned_free_qty,0) returned_free_qty,
                   CASE WHEN COALESCE(si.qty,0)-COALESCE(ret.returned_qty,0) > 0
                        THEN COALESCE(si.qty,0)-COALESCE(ret.returned_qty,0) ELSE 0 END available_qty,
                   CASE WHEN COALESCE(si.free_qty,0)-COALESCE(ret.returned_free_qty,0) > 0
                        THEN COALESCE(si.free_qty,0)-COALESCE(ret.returned_free_qty,0) ELSE 0 END available_free_qty,
                   COALESCE(si.total,COALESCE(si.qty,0)*COALESCE(si.rate,0)) value
            FROM sales_items si
            JOIN sales s ON s.id=si.sale_id
            LEFT JOIN ({returned_sql}) ret ON ret.source_item_id=si.id
            WHERE si.sale_id=%s
            ORDER BY si.id
            """,
            (source_table, int(source_id), int(source_id)),
        )

    def operation_rows(
        self,
        key: str,
        limit: int = 200,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict[str, Any]]:
        if key in {"erp_profit_loss", "profit_loss"}:
            return self.erp_profit_loss_rows(from_date, to_date, limit)
        if key in {"balance_sheet", "erp_balance_sheet"}:
            return self.balance_sheet_rows(to_date, limit)
        queries = {
            "customers": "SELECT id,name,gstin,phone,area,state,balance,gst_treatment FROM customers ORDER BY id DESC LIMIT %s",
            "suppliers": "SELECT id,name,gstin,phone,state,balance FROM suppliers ORDER BY id DESC LIMIT %s",
            "categories": "SELECT id,code,name,default_gst,margin_percent,is_active FROM item_categories ORDER BY sort_order,name LIMIT %s",
            "brands": "SELECT id,master_type,code,name,phone,gstin,is_active FROM business_masters WHERE master_type IN ('brand','manufacturer') ORDER BY id DESC LIMIT %s",
            "units": "SELECT id,name,COALESCE(is_active,1) is_active FROM units ORDER BY name LIMIT %s",
            "gst_rates": "SELECT id,rate,name,is_active FROM tax_slabs ORDER BY rate LIMIT %s",
            "employees": "SELECT id,name,email,role,locked,last_login FROM users ORDER BY id DESC LIMIT %s",
            "schemes": "SELECT sr.id,i.name item_name,sr.min_qty,sr.free_qty,sr.sale_rate,sr.start_date,sr.end_date,sr.is_active FROM scheme_rules sr LEFT JOIN items i ON i.id=sr.item_id ORDER BY sr.id DESC LIMIT %s",
            "sales_list": "SELECT id,bill_no,bill_date,customer_name,grand_total,taxable,gst_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "quotation_list": "SELECT id,doc_no,doc_date,party_name,grand_total,status FROM order_documents WHERE doc_type='quotation' ORDER BY id DESC LIMIT %s",
            "order_list": "SELECT id,doc_no,doc_date,party_name,grand_total,status FROM order_documents WHERE doc_type='sales_order' ORDER BY id DESC LIMIT %s",
            "dc_list": "SELECT id,doc_no,doc_date,party_name,grand_total,status FROM order_documents WHERE doc_type='delivery_challan' ORDER BY id DESC LIMIT %s",
            "return_list": "SELECT id,return_no,return_date,customer_name,grand_total,status FROM sales_returns ORDER BY id DESC LIMIT %s",
            "purchase_list": "SELECT id,bill_no,bill_date,supplier_name,grand_total,taxable,gst_total,status FROM purchases ORDER BY id DESC LIMIT %s",
            "po_list": "SELECT id,doc_no,doc_date,party_name,grand_total,status FROM order_documents WHERE doc_type='purchase_order' ORDER BY id DESC LIMIT %s",
            "debit_notes": "SELECT id,return_no,return_date,supplier_name,grand_total,status FROM purchase_returns ORDER BY id DESC LIMIT %s",
            "stock": "SELECT i.id,i.name,i.hsn,i.unit,i.stock,i.min_stock,i.status,s.name supplier_name FROM items i LEFT JOIN suppliers s ON s.id=i.supplier_id ORDER BY i.name LIMIT %s",
            "warehouses": "SELECT id,name,address,is_default FROM warehouses ORDER BY id DESC LIMIT %s",
            "stock_entry": "SELECT sl.id,sl.entry_date,sl.kind,sl.ref_no,i.name item_name,sl.qty_in,sl.qty_out,sl.created_at FROM stock_log sl LEFT JOIN items i ON i.id=sl.item_id ORDER BY sl.id DESC LIMIT %s",
            "item_movement": "SELECT sl.id,sl.entry_date,sl.kind,sl.ref_no,i.name item_name,sl.qty_in,sl.qty_out,sl.created_at FROM stock_log sl LEFT JOIN items i ON i.id=sl.item_id ORDER BY sl.entry_date DESC,sl.id DESC LIMIT %s",
            "transfer_list": "SELECT st.id,st.transfer_no,st.transfer_date,fw.name from_warehouse,tw.name to_warehouse,st.total_qty,st.status FROM stock_transfers st LEFT JOIN warehouses fw ON fw.id=st.from_warehouse_id LEFT JOIN warehouses tw ON tw.id=st.to_warehouse_id ORDER BY st.id DESC LIMIT %s",
            "stock_adjustment": "SELECT sa.id,sa.adj_no,sa.adj_date,w.name warehouse,sa.item_name,sa.old_stock,sa.counted_stock,sa.difference_qty,sa.reason FROM stock_adjustments sa LEFT JOIN warehouses w ON w.id=sa.warehouse_id ORDER BY sa.id DESC LIMIT %s",
            "stock_alerts": "SELECT id,name,stock,min_stock,reorder_qty,status FROM items WHERE min_stock>0 AND stock<=min_stock ORDER BY name LIMIT %s",
            "negative_stock": "SELECT id,name,stock,unit,status FROM items WHERE stock<0 ORDER BY stock,name LIMIT %s",
            "expiry_wastage": "SELECT b.id,i.name item_name,b.batch_no,b.expiry_date,b.stock,b.batch_status FROM item_batches b JOIN items i ON i.id=b.item_id ORDER BY b.expiry_date IS NULL,b.expiry_date LIMIT %s",
            "stock_outs": "SELECT id,challan_no,challan_date,area,vehicle_no,driver_name,salesman_name,total_qty,total_free,dispatch_status,status FROM stock_outs ORDER BY challan_date DESC,id DESC LIMIT %s",
            "load_challans": "SELECT id,challan_no,challan_date,area,vehicle_no,driver_name,salesman_name,total_qty,total_free,dispatch_status,status FROM stock_outs ORDER BY challan_date DESC,id DESC LIMIT %s",
            "route_settlement": "SELECT id,settlement_no,settlement_date,area,salesman_name,total_bills,cash_sales,credit_sales,receipts_total,loaded_qty,loaded_free,outstanding_total,collected_cash,short_excess,status FROM route_settlements ORDER BY settlement_date DESC,id DESC LIMIT %s",
            "receipts": "SELECT id,receipt_no,receipt_date,customer_name,amount,mode,status FROM receipts ORDER BY id DESC LIMIT %s",
            "payments": "SELECT id,payment_no,payment_date,supplier_name,amount,mode,status FROM payments ORDER BY id DESC LIMIT %s",
            "expenses": "SELECT id,expense_no,expense_date,ledger_name,amount,mode,status FROM expenses ORDER BY id DESC LIMIT %s",
            "cash_bank": "SELECT id,voucher_date,ledger_name,debit,credit,source_ref,status FROM ledger_postings WHERE ledger_name LIKE '%Cash%' OR ledger_name LIKE '%Bank%' ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "journal": "SELECT id,entry_no,entry_date,voucher_type,debit_ledger,credit_ledger,amount,narration,status FROM journal_entries ORDER BY id DESC LIMIT %s",
            "ledgers": "SELECT id,name,group_name,opening_dr,opening_cr,is_system FROM account_ledgers ORDER BY group_name,name LIMIT %s",
            "ledger_groups": "SELECT id,code,name,parent_code,nature,report_section,is_active FROM ledger_groups WHERE COALESCE(is_active,1)=1 ORDER BY sort_order,name LIMIT %s",
            "outstanding": "SELECT 'Customer' party_type,id,name,phone,area,state,balance FROM customers WHERE COALESCE(balance,0)<>0 UNION ALL SELECT 'Supplier' party_type,id,name,phone,'' area,state,balance FROM suppliers WHERE COALESCE(balance,0)<>0 ORDER BY balance DESC LIMIT %s",
            "aging_report": "SELECT 'Customer' party_type,id,name,balance,ABS(balance) abs_balance,CASE WHEN COALESCE(balance,0)>0 THEN 'Receivable' ELSE 'Advance / Credit' END bucket FROM customers WHERE COALESCE(balance,0)<>0 UNION ALL SELECT 'Supplier' party_type,id,name,balance,ABS(balance) abs_balance,CASE WHEN COALESCE(balance,0)>0 THEN 'Payable' ELSE 'Advance / Debit' END bucket FROM suppliers WHERE COALESCE(balance,0)<>0 ORDER BY abs_balance DESC LIMIT %s",
            "customer_ledger": "SELECT id,voucher_date,ledger_name,debit,credit,source_table,source_ref,status FROM ledger_postings WHERE party_type='customer' ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "supplier_ledger": "SELECT id,voucher_date,ledger_name,debit,credit,source_table,source_ref,status FROM ledger_postings WHERE party_type='supplier' ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "trial_balance": "SELECT ledger_name,ROUND(SUM(COALESCE(debit,0)),2) debit,ROUND(SUM(COALESCE(credit,0)),2) credit,ROUND(SUM(COALESCE(debit,0)-COALESCE(credit,0)),2) closing_balance FROM ledger_postings GROUP BY ledger_name ORDER BY ledger_name LIMIT %s",
            "vouchers": "SELECT id,voucher_no,voucher_date,voucher_type_code,party_name,narration,total_debit,total_credit,status,approval_status FROM voucher_headers ORDER BY id DESC LIMIT %s",
            "voucher_review": "SELECT id,voucher_no,voucher_date,voucher_type_code,party_name,total_debit,total_credit,status,approval_status FROM voucher_headers ORDER BY approval_status,status,voucher_date DESC LIMIT %s",
            "bank_reconciliation": "SELECT id,bank_ledger,voucher_date,source_ref,debit,credit,clearance_status,cleared_date,bank_reference,notes FROM bank_reconciliations ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "cash_flow": "SELECT voucher_date,source_ref,ledger_name,ROUND(SUM(COALESCE(debit,0)),2) cash_in,ROUND(SUM(COALESCE(credit,0)),2) cash_out FROM ledger_postings WHERE ledger_name LIKE '%Cash%' OR ledger_name LIKE '%Bank%' GROUP BY voucher_date,source_ref,ledger_name ORDER BY voucher_date DESC LIMIT %s",
            "fund_flow": "SELECT ledger_name,ROUND(SUM(COALESCE(debit,0)-COALESCE(credit,0)),2) net_movement FROM ledger_postings GROUP BY ledger_name HAVING net_movement<>0 ORDER BY ABS(net_movement) DESC LIMIT %s",
            "erp_ledger": "SELECT id,voucher_date,ledger_name,debit,credit,party_type,source_table,source_ref,status FROM ledger_postings ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "erp_day_book": "SELECT id,voucher_no,voucher_date,voucher_type_code,party_name,narration,total_debit,total_credit,status FROM voucher_headers ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "account_closing": "SELECT id,company_name,financial_year_label,closing_type,period_label,from_date,to_date,status,closed_at FROM closing_periods ORDER BY id DESC LIMIT %s",
            "control_check": "SELECT 'Ledger balance difference' check_name,ROUND(SUM(COALESCE(debit,0)),2) debit,ROUND(SUM(COALESCE(credit,0)),2) credit,ROUND(SUM(COALESCE(debit,0)-COALESCE(credit,0)),2) difference FROM ledger_postings UNION ALL SELECT 'Stock value movement',ROUND(SUM(COALESCE(value_in,0)),2),ROUND(SUM(COALESCE(value_out,0)),2),ROUND(SUM(COALESCE(value_in,0)-COALESCE(value_out,0)),2) FROM stock_postings LIMIT %s",
            "stock_ledger_adj": "SELECT id,adjustment_no,adjustment_date,stock_register_value,stock_ledger_value,difference_amount,narration,created_at FROM stock_valuation_adjustments ORDER BY id DESC LIMIT %s",
            "branches": "SELECT id,name,code,gstin,state,is_default,is_active FROM branches ORDER BY id DESC LIMIT %s",
            "cost_centers": "SELECT id,name,is_active FROM cost_centers ORDER BY id DESC LIMIT %s",
            "gst_return": "SELECT id,return_type,period_from,period_to,taxable_value,net_cgst,net_sgst,net_igst,status FROM gst_return_filings ORDER BY id DESC LIMIT %s",
            "gst_reports": "SELECT id,voucher_date,source_table,source_ref,party_type,hsn_sac,tax_rate,taxable,cgst,sgst,igst,input_output,status FROM gst_postings ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "einvoice": "SELECT id,invoice_no,ack_date,irn,ack_no,status,created_at FROM einvoices ORDER BY id DESC LIMIT %s",
            "eway_bill": "SELECT id,invoice_no,eway_no,eway_date,valid_until,vehicle_no,status FROM eway_bills ORDER BY id DESC LIMIT %s",
            "daily_dispatch_summary": "SELECT id,challan_no,challan_date,area,vehicle_no,driver_name,salesman_name,total_qty,total_free,dispatch_status,status FROM stock_outs ORDER BY challan_date DESC,id DESC LIMIT %s",
            "item_loading_sheet": "SELECT so.challan_date,so.challan_no,so.area,so.vehicle_no,si.item_name,si.unit,si.mrp,si.qty,si.free_qty,si.total_qty,so.dispatch_status FROM stock_out_items si JOIN stock_outs so ON so.id=si.stock_out_id ORDER BY so.challan_date DESC,si.item_name LIMIT %s",
            "route_loading_sheet": "SELECT so.area,si.item_name,si.unit,ROUND(SUM(COALESCE(si.qty,0)),3) qty,ROUND(SUM(COALESCE(si.free_qty,0)),3) free_qty,ROUND(SUM(COALESCE(si.total_qty,0)),3) total_qty FROM stock_out_items si JOIN stock_outs so ON so.id=si.stock_out_id GROUP BY so.area,si.item_name,si.unit ORDER BY so.area,si.item_name LIMIT %s",
            "pending_dispatch": "SELECT id,challan_no,challan_date,area,vehicle_no,total_qty,dispatch_status,status FROM stock_outs WHERE COALESCE(dispatch_status,'Pending Dispatch')<>'Completed' ORDER BY challan_date DESC,id DESC LIMIT %s",
            "loading_sheet": "SELECT id,challan_no,challan_date,area,vehicle_no,driver_name,total_qty,total_free,dispatch_status FROM stock_outs ORDER BY challan_date DESC,id DESC LIMIT %s",
            "customer_loading_sheet": "SELECT id,bill_no,bill_date,customer_name,customer_area,grand_total,dispatch_status,status FROM sales ORDER BY bill_date DESC,id DESC LIMIT %s",
            "dispatch_return_summary": "SELECT id,return_no,return_date,source_ref,customer_name,route,vehicle,total_dispatched_qty,total_returned_qty,total_value,status FROM dispatch_returns ORDER BY return_date DESC,id DESC LIMIT %s",
            "inventory_valuation": "SELECT id,name,unit,stock,standard_cost,ROUND(COALESCE(stock,0)*COALESCE(standard_cost,0),2) stock_value,status FROM items ORDER BY stock_value DESC LIMIT %s",
            "gst_adjustment": "SELECT id,adjustment_no,adjustment_date,return_type,period_from,period_to,adjustment_type,mode,branch_name,total_amount,status FROM gst_adjustments ORDER BY id DESC LIMIT %s",
            "itc_reconciliation": "SELECT id,source_type,return_period,supplier_gstin,supplier_name,invoice_no,invoice_date,taxable,cgst,sgst,igst,total,match_status,difference_gst FROM gst_itc_reconciliations ORDER BY id DESC LIMIT %s",
            "gstr9_annual": "SELECT id,label,start_date,end_date,is_locked,locked_at FROM financial_years ORDER BY id DESC LIMIT %s",
            "stock_postings_report": "SELECT id,voucher_date,item_name,qty_in,qty_out,rate,value_in,value_out,source_table,source_ref,status FROM stock_postings ORDER BY voucher_date DESC,id DESC LIMIT %s",
            "audit_log": "SELECT id,user_name,action,ref_type,ref_no,created_at FROM audit_logs ORDER BY id DESC LIMIT %s",
            "product_labels": "SELECT i.id item_id,i.name item_name,COALESCE(pp.display_name,i.unit,'PCS') pack_name,COALESCE(pp.barcode,i.barcode,'') barcode,COALESCE(pp.mrp,i.mrp,0) mrp,COALESCE(pp.sale_rate,i.sale_rate,0) sale_rate,COALESCE(pp.current_stock_qty,i.stock,0) stock_qty,COALESCE(pp.is_active,1) is_active FROM items i LEFT JOIN product_packs pp ON pp.product_id=i.id ORDER BY i.name,pp.id LIMIT %s",
            "print_bills": "SELECT id,bill_no,bill_date,customer_name,grand_total,status,created_at FROM sales ORDER BY id DESC LIMIT %s",
            "print_batches": "SELECT id,batch_no,document_type,print_scope,document_count,reprint_reason,status,printed_by_user_name,created_at FROM print_batches ORDER BY id DESC LIMIT %s",
            "print_logs": "SELECT id,user_name,module,document_type,document_no,party_name,action,created_at,batch_id FROM print_logs ORDER BY id DESC LIMIT %s",
            "print_templates": "SELECT pt.id,pt.template_code,pt.template_name,pt.document_type,pt.paper_size,COALESCE(pt.orientation,'') AS orientation,pt.print_mode,pt.is_default,pt.is_active,pt.updated_at,tf.family_name FROM print_templates pt LEFT JOIN print_template_families tf ON tf.id=pt.family_id ORDER BY pt.document_type,pt.template_name LIMIT %s",
            "print_template_families": "SELECT id,business_type,family_code,family_name,description,default_paper_size,default_print_mode,supports_thermal,supports_a4,is_default,is_active FROM print_template_families ORDER BY family_name LIMIT %s",
            "company": "SELECT id,name,business_name,gstin,phone,email,city,state,invoice_prefix,upi_id,business_type_code,subscription_plan_code FROM company ORDER BY id LIMIT %s",
            "role_permissions": "SELECT id,role_name,permission_key,allowed FROM role_permissions ORDER BY role_name,permission_key LIMIT %s",
            "financial_years": "SELECT id,label,start_date,end_date,is_locked,locked_at,created_at FROM financial_years ORDER BY id DESC LIMIT %s",
            "print_settings": "SELECT setting_key,setting_value,updated_at FROM app_settings WHERE setting_key LIKE '%print%' OR setting_key LIKE '%invoice%' OR setting_key LIKE '%template%' ORDER BY setting_key LIMIT %s",
            "backup": "SELECT id,action,file_path,status,message,created_at FROM backup_logs ORDER BY id DESC LIMIT %s",
            "lan_setup": "SELECT setting_key,setting_value,updated_at FROM app_settings WHERE setting_key LIKE '%lan%' OR setting_key LIKE '%server%' OR setting_key LIKE '%backup_path%' ORDER BY setting_key LIMIT %s",
            "dashboard_settings": "SELECT setting_key,setting_value,updated_at FROM app_settings WHERE setting_key LIKE '%dashboard%' OR setting_key LIKE '%home%' OR setting_key LIKE '%theme%' ORDER BY setting_key LIMIT %s",
            "developer_admin": "SELECT id,install_code,client_name,company_name,business_type,expiry_date,status,max_users,updated_at FROM license ORDER BY id DESC LIMIT %s",
            "users": "SELECT id,name,email,role,locked,last_login FROM users ORDER BY id DESC LIMIT %s",
            "business_types": "SELECT id,code,name,invoice_template_code,module_codes,field_config,is_active FROM dev_business_types ORDER BY is_active DESC,name LIMIT %s",
            "pos_billing": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "electronics_pos_billing": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "pharmacy_retail_billing": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "pharmacy_wholesale_billing": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "pos_dine_in": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "pos_take_away": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "pos_delivery": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "kot_new": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "ready_orders": "SELECT id,doc_no,doc_date,party_name,grand_total,status FROM order_documents ORDER BY id DESC LIMIT %s",
            "restaurant_categories": "SELECT id,name,sort_order,is_active,created_at FROM restaurant_categories ORDER BY sort_order,name LIMIT %s",
            "restaurant_tables": "SELECT id,table_no,floor_area,capacity,status,notes FROM restaurant_tables ORDER BY table_no LIMIT %s",
            "real_estate_units": "SELECT id,project_name,property_type,unit_no,area_sqft,rate,total_value,status,created_at FROM real_estate_units ORDER BY id DESC LIMIT %s",
            "property_types": "SELECT id,project_name,property_type,unit_no,area_sqft,rate,total_value,status,created_at FROM real_estate_units ORDER BY property_type,unit_no LIMIT %s",
            "real_estate_leads": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type='real_estate_lead' ORDER BY id DESC LIMIT %s",
            "real_estate_followups": "SELECT id,record_no,record_date,party_name,phone,reference,status,due_date,notes FROM business_registers WHERE record_type='real_estate_followup' ORDER BY id DESC LIMIT %s",
            "real_estate_site_visits": "SELECT id,record_no,record_date,party_name,phone,reference,status,due_date,notes FROM business_registers WHERE record_type='real_estate_site_visit' ORDER BY id DESC LIMIT %s",
            "real_estate_enquiries": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,notes FROM business_registers WHERE record_type='real_estate_enquiry' ORDER BY id DESC LIMIT %s",
            "real_estate_new_booking": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type='real_estate_booking' ORDER BY id DESC LIMIT %s",
            "real_estate_agreements": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,notes FROM business_registers WHERE record_type='real_estate_agreement' ORDER BY id DESC LIMIT %s",
            "real_estate_installments": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type='real_estate_installment' ORDER BY id DESC LIMIT %s",
            "real_estate_refunds": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,notes FROM business_registers WHERE record_type='real_estate_refund' ORDER BY id DESC LIMIT %s",
            "real_estate_commissions": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type='real_estate_commission' ORDER BY id DESC LIMIT %s",
            "real_estate_sales_reports": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type LIKE 'real_estate_%' ORDER BY id DESC LIMIT %s",
            "manufacturing_boms": "SELECT id,bom_no,name,finished_item_name,finished_qty,unit,status,created_at FROM production_boms ORDER BY id DESC LIMIT %s",
            "manufacturing_work_orders": "SELECT id,production_no,production_date,bom_name,finished_item_name,planned_qty,finished_qty,status,created_at FROM production_runs ORDER BY id DESC LIMIT %s",
            "manufacturing_production_orders": "SELECT id,production_no,production_date,bom_name,finished_item_name,planned_qty,finished_qty,status,created_at FROM production_runs ORDER BY id DESC LIMIT %s",
            "production_runs": "SELECT id,production_no,production_date,bom_name,finished_item_name,planned_qty,finished_qty,total_input_value,finished_value,variance_value,status FROM production_runs ORDER BY id DESC LIMIT %s",
            "manufacturing_job_work": "SELECT id,record_no,record_date,party_name,reference,status,amount,notes FROM business_registers WHERE record_type='manufacturing_job_work' ORDER BY id DESC LIMIT %s",
            "manufacturing_quality_checks": "SELECT id,record_no,record_date,party_name,reference,status,notes FROM business_registers WHERE record_type='manufacturing_quality_check' ORDER BY id DESC LIMIT %s",
            "manufacturing_reports": "SELECT id,production_no,production_date,bom_name,finished_item_name,planned_qty,finished_qty,total_input_value,finished_value,variance_value,status FROM production_runs ORDER BY id DESC LIMIT %s",
            "prescription_entry": "SELECT id,record_no,record_date,party_name,phone,reference,status,notes FROM business_registers WHERE record_type='prescription' ORDER BY id DESC LIMIT %s",
            "prescription_billing": "SELECT id,bill_no,bill_date,customer_name,grand_total,pay_mode,status FROM sales ORDER BY id DESC LIMIT %s",
            "patient_history": "SELECT id,record_no,record_date,party_name,phone,reference,status,notes FROM business_registers WHERE record_type='patient_history' ORDER BY id DESC LIMIT %s",
            "serial_numbers": "SELECT id,record_no,record_date,party_name,reference,status,notes FROM business_registers WHERE record_type='serial_number' ORDER BY id DESC LIMIT %s",
            "warranty_tracking": "SELECT id,record_no,record_date,party_name,phone,reference,status,due_date,notes FROM business_registers WHERE record_type='warranty_tracking' ORDER BY id DESC LIMIT %s",
            "complaints": "SELECT id,record_no,record_date,party_name,phone,reference,status,due_date,notes FROM business_registers WHERE record_type='complaint' ORDER BY id DESC LIMIT %s",
            "job_cards": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type='job_card' ORDER BY id DESC LIMIT %s",
            "repairs": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type='repair' ORDER BY id DESC LIMIT %s",
            "warranty_claims": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type='warranty_claim' ORDER BY id DESC LIMIT %s",
            "warranty_reports": "SELECT id,record_no,record_date,party_name,phone,reference,status,amount,due_date,notes FROM business_registers WHERE record_type LIKE 'warranty%' ORDER BY id DESC LIMIT %s",
            "refill_reminders": "SELECT id,record_no,record_date,party_name,phone,reference,status,due_date,notes FROM business_registers WHERE record_type='refill_reminder' ORDER BY id DESC LIMIT %s",
        }
        sql = queries.get(key)
        if not sql:
            return []
        return self.rows(sql, (int(limit),))

    def erp_profit_loss_rows(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        start = from_date or date.today().replace(day=1).isoformat()
        end = to_date or date.today().isoformat()
        summary = self._profit_loss_summary(start, end)
        debit_rows: list[dict[str, Any]] = []
        credit_rows: list[dict[str, Any]] = []
        opening_stock = self._stock_register_value(start)
        closing_stock = self._stock_register_value(end)
        debit_rows.append(self._statement_row("Debit", "Opening Stock", "Stock In Hand", opening_stock, "Summary"))
        debit_rows.extend(
            self._statement_row("Debit", row["ledger"], row["group_name"], row["amount"], "Purchase Accounts")
            for row in summary["sections"]["cogs"]
        )
        debit_rows.extend(
            self._statement_row("Debit", row["ledger"], row["group_name"], row["amount"], "Indirect Expenses")
            for row in summary["sections"]["expense"]
        )
        debit_rows.extend(
            self._statement_row("Debit", row["ledger"], row["group_name"], row["amount"], "Other Debit Balances")
            for row in summary["sections"]["other_debit"]
        )
        credit_rows.extend(
            self._statement_row("Credit", row["ledger"], row["group_name"], row["amount"], "Sales Accounts")
            for row in summary["sections"]["income"]
        )
        credit_rows.append(self._statement_row("Credit", "Closing Stock", "Stock In Hand", closing_stock, "Summary"))
        credit_rows.extend(
            self._statement_row("Credit", row["ledger"], row["group_name"], row["amount"], "Indirect Incomes")
            for row in summary["sections"]["other_credit"]
        )

        debit_before_profit = sum(float(row["amount"] or 0) for row in debit_rows)
        credit_before_profit = sum(float(row["amount"] or 0) for row in credit_rows)
        gross_profit = round(float(summary["totals"]["income"]) + closing_stock - opening_stock - float(summary["totals"]["cogs"]), 2)
        net_profit = round(credit_before_profit - debit_before_profit, 2)
        if gross_profit >= 0:
            debit_rows.insert(2 if len(debit_rows) > 1 else len(debit_rows), self._statement_row("Debit", "Gross Profit c/o", "Trading", gross_profit, "Summary"))
            credit_rows.append(self._statement_row("Credit", "Gross Profit b/f", "Trading", gross_profit, "Summary"))
        else:
            credit_rows.append(self._statement_row("Credit", "Gross Loss c/o", "Trading", abs(gross_profit), "Summary"))
            debit_rows.append(self._statement_row("Debit", "Gross Loss b/f", "Trading", abs(gross_profit), "Summary"))
        if net_profit >= 0:
            debit_rows.append(self._statement_row("Debit", "Net Profit", "Transferred to Balance Sheet", net_profit, "Summary"))
        else:
            credit_rows.append(self._statement_row("Credit", "Net Loss", "Transferred to Balance Sheet", abs(net_profit), "Summary"))

        statement_total = max(sum(float(row["amount"] or 0) for row in debit_rows), sum(float(row["amount"] or 0) for row in credit_rows))
        rows = [
            {
                "statement": "Profit & Loss A/c",
                "period": f"{start} to {end}",
                "side": row["side"],
                "particulars": row["particulars"],
                "group_name": row["group_name"],
                "section": row["section"],
                "amount": round(float(row["amount"] or 0), 2),
            }
            for row in [*debit_rows, *credit_rows]
            if abs(float(row["amount"] or 0)) >= 0.005 or row["particulars"] in {"Opening Stock", "Closing Stock"}
        ]
        rows.append(self._statement_row("Control", "Debit Total", "", statement_total, "Total", statement="Profit & Loss A/c", period=f"{start} to {end}"))
        rows.append(self._statement_row("Control", "Credit Total", "", statement_total, "Total", statement="Profit & Loss A/c", period=f"{start} to {end}"))
        return rows[: max(1, int(limit))]

    def erp_profit_loss_statement(self, from_date: str | None = None, to_date: str | None = None) -> dict[str, Any]:
        start = from_date or date.today().replace(day=1).isoformat()
        end = to_date or date.today().isoformat()
        summary = self._profit_loss_summary(start, end)
        opening_stock = self._stock_register_value(start)
        closing_stock = self._stock_register_value(end)
        income_total = float(summary["totals"]["income"])
        cogs_total = float(summary["totals"]["cogs"])
        expense_total = float(summary["totals"]["expense"])
        other_income_total = float(summary["totals"]["other_credit"])
        other_expense_total = float(summary["totals"]["other_debit"])
        gross_profit = round(income_total + closing_stock - opening_stock - cogs_total, 2)
        net_profit = round(gross_profit + other_income_total - expense_total - other_expense_total, 2)
        trading_debit_total = round(opening_stock + cogs_total + max(gross_profit, 0), 2)
        trading_credit_total = round(income_total + closing_stock + max(-gross_profit, 0), 2)
        gross_margin = round((gross_profit / income_total) * 100, 2) if income_total else 0.0
        net_margin = round((net_profit / income_total) * 100, 2) if income_total else 0.0
        statement_total = max(
            round(opening_stock + cogs_total + abs(gross_profit) + expense_total + other_expense_total + max(net_profit, 0), 2),
            round(income_total + closing_stock + abs(gross_profit) + other_income_total + max(-net_profit, 0), 2),
        )
        left_groups = [
            self._statement_group("Opening Stock", opening_stock, [], open=False, note="Opening stock is taken from the stock register."),
            self._statement_group("Purchase Accounts", cogs_total, summary["sections"]["cogs"], open=True),
            self._statement_group("Gross Profit c/o" if gross_profit >= 0 else "Gross Loss b/f", abs(gross_profit), [], open=False, note="Carried through the trading statement."),
            self._statement_group("Indirect Expenses", expense_total, summary["sections"]["expense"], open=True),
        ]
        if other_expense_total > 0:
            left_groups.append(self._statement_group("Other Debit Balances", other_expense_total, summary["sections"]["other_debit"], open=True))
        if net_profit >= 0:
            left_groups.append(self._statement_group("Net Profit", net_profit, [], open=False, note="Transferred to Balance Sheet."))

        right_groups = [
            self._statement_group("Sales Accounts", income_total, summary["sections"]["income"], open=True),
            self._statement_group("Closing Stock", closing_stock, self._stock_detail_rows(), open=False),
            self._statement_group("Gross Profit b/f" if gross_profit >= 0 else "Gross Loss c/o", abs(gross_profit), [], open=False, note="Brought forward from the trading statement."),
        ]
        if other_income_total > 0:
            right_groups.append(self._statement_group("Indirect Incomes", other_income_total, summary["sections"]["other_credit"], open=True))
        if net_profit < 0:
            right_groups.append(self._statement_group("Net Loss", abs(net_profit), [], open=False, note="Transferred to Balance Sheet."))

        return {
            "title": "Profit & Loss A/c",
            "period": f"{start} to {end}",
            "left_heading": "Particulars",
            "right_heading": "Particulars",
            "left_groups": left_groups,
            "right_groups": right_groups,
            "left_total": statement_total,
            "right_total": statement_total,
            "support_title": "Supporting Analysis",
            "controls": [
                {"label": "Trading Debit Total", "group_name": "Opening Stock + Purchases + Gross Profit", "amount": trading_debit_total},
                {"label": "Trading Credit Total", "group_name": "Sales + Closing Stock + Gross Loss", "amount": trading_credit_total},
                {"label": "Ledger Income", "group_name": "Sales and direct income ledgers", "amount": income_total},
                {"label": "Purchase / COGS Ledger", "group_name": "Purchase and direct expense ledgers", "amount": cogs_total},
                {"label": "Expense Ledgers", "group_name": "Indirect expenses", "amount": expense_total},
                {"label": "Other Income", "amount": other_income_total},
                {"label": "Other Debit Balances", "amount": other_expense_total},
                {"label": "Gross Profit" if gross_profit >= 0 else "Gross Loss", "group_name": f"{gross_margin:.2f}% of sales", "amount": gross_profit},
                {"label": "Net Profit" if net_profit >= 0 else "Net Loss", "group_name": f"{net_margin:.2f}% of sales", "amount": net_profit},
                {"label": "Closing Stock", "group_name": "Stock register valuation", "amount": closing_stock},
            ],
        }

    def balance_sheet_rows(self, as_on: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
        end = as_on or date.today().isoformat()
        ledger_rows = self._ledger_statement_rows(None, end)
        pl = self._profit_loss_summary("1900-01-01", end)
        assets: list[dict[str, Any]] = []
        liabilities: list[dict[str, Any]] = []
        equity: list[dict[str, Any]] = []
        unclassified: list[dict[str, Any]] = []
        for row in ledger_rows:
            section = str(row.get("section") or "other")
            debit = float(row.get("debit") or 0)
            credit = float(row.get("credit") or 0)
            if section in {"income", "cogs", "expense"}:
                continue
            if section == "asset":
                amount = round(debit - credit, 2)
                target = assets if amount >= 0 else liabilities
            elif section == "liability":
                amount = round(credit - debit, 2)
                target = liabilities if amount >= 0 else assets
            elif section == "equity":
                amount = round(credit - debit, 2)
                target = equity
            else:
                amount = round(debit - credit, 2)
                target = assets if amount >= 0 else liabilities
            if abs(amount) >= 0.005:
                target.append({"ledger": row["ledger"], "group_name": row["group_name"], "amount": abs(amount), "section": section})
        retained = round(float(pl["net_profit"]), 2)
        if retained >= 0.005:
            equity.append({"ledger": "Current Profit" if retained >= 0 else "Current Loss", "group_name": "Retained Earnings", "amount": retained, "section": "equity"})
        elif retained <= -0.005:
            assets.append({"ledger": "Profit & Loss A/c (Debit Balance)", "group_name": "Current Loss", "amount": abs(retained), "section": "asset"})
        asset_total = round(sum(float(row["amount"]) for row in assets), 2)
        liability_total = round(sum(float(row["amount"]) for row in liabilities), 2)
        equity_total = round(sum(float(row["amount"]) for row in equity), 2)
        right_total = round(liability_total + equity_total, 2)
        statement_total = max(asset_total, right_total)
        rows: list[dict[str, Any]] = []
        for row in [*equity, *liabilities]:
            rows.append(self._statement_row("Liabilities", row["ledger"], row["group_name"], row["amount"], row["section"], statement="Balance Sheet", period=f"As on {end}"))
        if asset_total > right_total:
            rows.append(self._statement_row("Liabilities", "Difference in Opening Balances", "Control", asset_total - right_total, "Control", statement="Balance Sheet", period=f"As on {end}"))
        for row in assets:
            rows.append(self._statement_row("Assets", row["ledger"], row["group_name"], row["amount"], row["section"], statement="Balance Sheet", period=f"As on {end}"))
        if right_total > asset_total:
            rows.append(self._statement_row("Assets", "Difference in Opening Balances", "Control", right_total - asset_total, "Control", statement="Balance Sheet", period=f"As on {end}"))
        for row in unclassified:
            rows.append(self._statement_row("Review", row["ledger"], row["group_name"], row["amount"], "Unclassified", statement="Balance Sheet", period=f"As on {end}"))
        rows.extend(
            [
                self._statement_row("Control", "Total Assets", "", statement_total, "Total", statement="Balance Sheet", period=f"As on {end}"),
                self._statement_row("Control", "Liabilities + Equity", "", statement_total, "Total", statement="Balance Sheet", period=f"As on {end}"),
                self._statement_row("Control", "Difference", "", round(asset_total - right_total, 2), "Control", statement="Balance Sheet", period=f"As on {end}"),
                self._statement_row("Control", "Stock Register Value", "", self._stock_register_value(end), "Control", statement="Balance Sheet", period=f"As on {end}"),
            ]
        )
        return rows[: max(1, int(limit))]

    def balance_sheet_statement(self, as_on: str | None = None) -> dict[str, Any]:
        end = as_on or date.today().isoformat()
        sections = self._balance_sheet_sections(end)
        asset_total = sections["asset_total"]
        liability_total = sections["liability_total"]
        equity_total = sections["equity_total"]
        right_total = round(liability_total + equity_total, 2)
        difference = round(asset_total - right_total, 2)
        statement_total = max(asset_total, right_total)
        left_groups = [
            *self._group_statement_rows(sections["equity"], "Capital Account", open_all=True),
            *self._group_statement_rows(sections["liabilities"], "Liabilities", open_all=True),
        ]
        right_groups = self._group_statement_rows(sections["assets"], "Assets", open_all=True)
        if asset_total > right_total:
            left_groups.append(self._statement_group("Difference in Opening Balances", asset_total - right_total, [], open=False, note="Control difference added to balance the statement."))
        if right_total > asset_total:
            right_groups.append(self._statement_group("Difference in Opening Balances", right_total - asset_total, [], open=False, note="Control difference added to balance the statement."))

        stock_register_value = self._stock_register_value(end)
        stock_ledger_value = self._stock_ledger_value(end)
        current_assets = round(sum(float(row.get("amount") or 0) for row in sections["assets"] if self._is_current_asset_group(row.get("group_name"))), 2)
        current_liabilities = round(sum(float(row.get("amount") or 0) for row in sections["liabilities"] if self._is_current_liability_group(row.get("group_name"))), 2)
        working_capital = round(current_assets - current_liabilities, 2)
        controls = [
            {"label": "Total Assets", "group_name": "Balance Sheet asset side", "amount": asset_total},
            {"label": "Liabilities + Capital", "group_name": "Capital, current profit and outside liabilities", "amount": right_total},
            {"label": "Difference", "group_name": "Should be zero after ledger and stock control posting", "amount": difference},
            {"label": "Current Assets", "group_name": "Stock, debtors, cash/bank and recoverable balances", "amount": current_assets},
            {"label": "Current Liabilities", "group_name": "Creditors, duties/taxes, provisions and payables", "amount": current_liabilities},
            {"label": "Working Capital", "group_name": "Current Assets minus Current Liabilities", "amount": working_capital},
            {"label": "Capital / Equity", "group_name": "Owner funds and retained profit", "amount": equity_total},
            {"label": "Stock Register Value", "group_name": "Inventory master valuation", "amount": stock_register_value},
            {"label": "Stock In Hand Ledger", "group_name": "Financial ledger value", "amount": stock_ledger_value},
            {"label": "Stock Adjustment Needed", "group_name": "Register value minus financial ledger", "amount": round(stock_register_value - stock_ledger_value, 2)},
        ]
        for row in sections["unclassified"]:
            controls.append(
                {
                    "label": f"Unclassified: {row.get('ledger') or ''}",
                    "group_name": row.get("group_name") or "",
                    "amount": row.get("amount") or 0,
                }
            )
        return {
            "title": "Balance Sheet",
            "period": f"As on {end}",
            "left_heading": "Liabilities",
            "right_heading": "Assets",
            "left_groups": left_groups,
            "right_groups": right_groups,
            "left_total": statement_total,
            "right_total": statement_total,
            "support_title": "Ledger Controls And Stock Check",
            "controls": controls,
        }

    def _balance_sheet_sections(self, as_on: str) -> dict[str, Any]:
        ledger_rows = self._ledger_statement_rows(None, as_on)
        pl = self._profit_loss_summary("1900-01-01", as_on)
        assets: list[dict[str, Any]] = []
        liabilities: list[dict[str, Any]] = []
        equity: list[dict[str, Any]] = []
        unclassified: list[dict[str, Any]] = []
        for row in ledger_rows:
            section = str(row.get("section") or "other")
            debit = float(row.get("debit") or 0)
            credit = float(row.get("credit") or 0)
            if section in {"income", "cogs", "expense"}:
                continue
            if section == "asset":
                amount = round(debit - credit, 2)
                target = assets if amount >= 0 else liabilities
            elif section == "liability":
                amount = round(credit - debit, 2)
                target = liabilities if amount >= 0 else assets
            elif section == "equity":
                amount = round(credit - debit, 2)
                target = equity
            else:
                amount = round(debit - credit, 2)
                target = assets if amount >= 0 else liabilities
            if abs(amount) >= 0.005:
                target.append({"ledger": row["ledger"], "group_name": row["group_name"], "amount": abs(amount), "section": section})
        retained = round(float(pl["net_profit"]), 2)
        if retained >= 0.005:
            equity.append({"ledger": "Current Profit", "group_name": "Retained Earnings", "amount": retained, "section": "equity"})
        elif retained <= -0.005:
            assets.append({"ledger": "Profit & Loss A/c (Debit Balance)", "group_name": "Current Loss", "amount": abs(retained), "section": "asset"})
        return {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "unclassified": unclassified,
            "asset_total": round(sum(float(row["amount"]) for row in assets), 2),
            "liability_total": round(sum(float(row["amount"]) for row in liabilities), 2),
            "equity_total": round(sum(float(row["amount"]) for row in equity), 2),
        }

    def _ledger_statement_rows(self, from_date: str | None = None, to_date: str | None = None) -> list[dict[str, Any]]:
        where = ["LOWER(COALESCE(lp.status,'posted')) NOT IN ('cancelled','void','deleted')"]
        params: list[Any] = []
        if from_date:
            where.append("lp.voucher_date >= %s")
            params.append(from_date)
        if to_date:
            where.append("lp.voucher_date <= %s")
            params.append(to_date)
        sql = f"""
            SELECT
                lp.ledger_name ledger,
                COALESCE(al.group_name,'General') group_name,
                COALESCE(lg.report_section,'other') section,
                ROUND(SUM(COALESCE(lp.debit,0)),2) debit,
                ROUND(SUM(COALESCE(lp.credit,0)),2) credit
            FROM ledger_postings lp
            LEFT JOIN account_ledgers al ON al.name=lp.ledger_name
            LEFT JOIN ledger_groups lg ON lg.name=al.group_name
            WHERE {' AND '.join(where)}
            GROUP BY lp.ledger_name,COALESCE(al.group_name,'General'),COALESCE(lg.report_section,'other')
            ORDER BY COALESCE(lg.sort_order,900),COALESCE(al.group_name,'General'),lp.ledger_name
        """
        rows = self.rows(sql, tuple(params))
        for row in rows:
            section = str(row.get("section") or "other")
            if section == "other":
                section = self._guess_report_section(str(row.get("group_name") or ""), str(row.get("ledger") or ""))
            row["section"] = section
        return rows

    def _profit_loss_summary(self, from_date: str, to_date: str) -> dict[str, Any]:
        sections: dict[str, list[dict[str, Any]]] = {
            "income": [],
            "cogs": [],
            "expense": [],
            "other_credit": [],
            "other_debit": [],
        }
        totals = {"income": 0.0, "cogs": 0.0, "expense": 0.0, "other_credit": 0.0, "other_debit": 0.0}
        for row in self._ledger_statement_rows(from_date, to_date):
            section = str(row.get("section") or "other")
            debit = float(row.get("debit") or 0)
            credit = float(row.get("credit") or 0)
            if section == "income":
                amount = round(credit - debit, 2)
            elif section in {"cogs", "expense"}:
                amount = round(debit - credit, 2)
            else:
                raw = round(credit - debit, 2)
                section = "other_credit" if raw >= 0 else "other_debit"
                amount = abs(raw)
            if abs(amount) < 0.005:
                continue
            record = {"ledger": row["ledger"], "group_name": row["group_name"], "amount": amount}
            sections[section].append(record)
            totals[section] += amount
        for key in totals:
            totals[key] = round(totals[key], 2)
        gross_profit = round(totals["income"] - totals["cogs"], 2)
        net_profit = round(gross_profit + totals["other_credit"] - totals["expense"] - totals["other_debit"], 2)
        return {"sections": sections, "totals": totals, "gross_profit": gross_profit, "net_profit": net_profit}

    @staticmethod
    def _statement_row(
        side: str,
        particulars: str,
        group_name: str,
        amount: float,
        section: str,
        statement: str = "",
        period: str = "",
    ) -> dict[str, Any]:
        row = {
            "side": side,
            "particulars": particulars,
            "group_name": group_name,
            "section": section,
            "amount": round(float(amount or 0), 2),
        }
        if statement:
            row = {"statement": statement, "period": period, **row}
        return row

    @staticmethod
    def _statement_group(
        label: str,
        amount: float,
        details: list[dict[str, Any]],
        *,
        open: bool = False,
        note: str = "",
    ) -> dict[str, Any]:
        clean_details = [
            {
                "ledger": str(row.get("ledger") or row.get("name") or row.get("item_name") or "Ledger"),
                "group_name": str(row.get("group_name") or ""),
                "amount": round(float(row.get("amount") or row.get("buy_value") or row.get("profit") or 0), 2),
            }
            for row in details
        ]
        return {
            "label": label,
            "amount": round(float(amount or 0), 2),
            "details": clean_details,
            "open": open,
            "note": note,
        }

    def _group_statement_rows(
        self,
        rows: list[dict[str, Any]],
        fallback_group: str,
        *,
        open_first: bool = False,
        open_all: bool = False,
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            group = str(row.get("group_name") or fallback_group).strip() or fallback_group
            grouped.setdefault(group, []).append(row)
        out: list[dict[str, Any]] = []
        for index, (group, details) in enumerate(grouped.items()):
            amount = round(sum(float(row.get("amount") or 0) for row in details), 2)
            out.append(self._statement_group(group, amount, details, open=open_all or (open_first and index == 0)))
        return out

    @staticmethod
    def _is_current_asset_group(group_name: Any) -> bool:
        group = str(group_name or "").strip().lower()
        return group in {
            "bank accounts",
            "cash-in-hand",
            "current assets",
            "deposits (asset)",
            "loans & advances (asset)",
            "stock-in-hand",
            "sundry debtors",
            "duties & taxes",
        }

    @staticmethod
    def _is_current_liability_group(group_name: Any) -> bool:
        group = str(group_name or "").strip().lower()
        return group in {
            "current liabilities",
            "duties & taxes",
            "loans (liability)",
            "provisions",
            "sundry creditors",
            "secured loans",
            "unsecured loans",
        }

    @staticmethod
    def _guess_report_section(group_name: str, ledger_name: str) -> str:
        text = f"{group_name} {ledger_name}".lower()
        group = group_name.strip().lower()
        if group in {
            "bank accounts",
            "cash-in-hand",
            "current assets",
            "deposits (asset)",
            "fixed assets",
            "investments",
            "loans & advances (asset)",
            "misc. expenses (asset)",
            "stock-in-hand",
            "sundry debtors",
        }:
            return "asset"
        if group in {
            "current liabilities",
            "duties & taxes",
            "loans (liability)",
            "provisions",
            "secured loans",
            "sundry creditors",
            "unsecured loans",
        }:
            return "liability"
        if group in {"capital account", "drawings", "reserves & surplus"}:
            return "equity"
        if group in {"direct incomes", "indirect incomes", "sales accounts"}:
            return "income"
        if group in {"direct expenses", "purchase accounts"}:
            return "cogs"
        if group == "indirect expenses":
            return "expense"
        if any(word in text for word in ["cash", "bank", "asset", "stock in hand", "stock-in-hand", "debtor", "customer", "receivable"]):
            return "asset"
        if any(word in text for word in ["liability", "creditor", "duties", "tax", "loan", "supplier", "payable"]):
            return "liability"
        if any(word in text for word in ["capital", "drawing", "retained", "equity"]):
            return "equity"
        if any(word in text for word in ["income", "sales", "service charge"]):
            return "income"
        if any(word in text for word in ["purchase", "direct expense", "cost of goods", "cogs"]):
            return "cogs"
        if "expense" in text or "discount" in text:
            return "expense"
        return "other"

    def _stock_register_value(self, _as_on: str | None = None) -> float:
        row = self.one(
            """
            SELECT ROUND(COALESCE(SUM(COALESCE(stock,0) * COALESCE(NULLIF(standard_cost,0), buy_rate, 0)),0),2) value
            FROM items
            WHERE COALESCE(status,'Active')='Active'
            """
        ) or {}
        try:
            return round(float(row.get("value") or 0), 2)
        except (TypeError, ValueError):
            return 0.0

    def _stock_ledger_value(self, as_on: str | None = None) -> float:
        end = as_on or date.today().isoformat()
        row = self.one(
            """
            SELECT ROUND(COALESCE(SUM(COALESCE(debit,0)-COALESCE(credit,0)),0),2) value
            FROM ledger_postings
            WHERE ledger_name='Stock In Hand'
              AND voucher_date<=%s
              AND LOWER(COALESCE(status,'posted')) NOT IN ('cancelled','void','deleted')
            """,
            (end,),
        ) or {}
        try:
            return round(float(row.get("value") or 0), 2)
        except (TypeError, ValueError):
            return 0.0

    def _stock_detail_rows(self, limit: int = 80) -> list[dict[str, Any]]:
        rows = self.rows(
            """
            SELECT name,unit,stock,
                   ROUND(COALESCE(stock,0) * COALESCE(NULLIF(standard_cost,0), buy_rate, 0),2) amount
            FROM items
            WHERE COALESCE(stock,0)<>0
            ORDER BY amount DESC,name
            LIMIT %s
            """,
            (int(limit),),
        )
        details: list[dict[str, Any]] = []
        for row in rows:
            qty = row.get("stock") or 0
            unit = str(row.get("unit") or "").strip()
            if isinstance(qty, (int, float)):
                qty_text = f"{qty:g}"
            else:
                qty_text = str(qty)
            details.append(
                {
                    "ledger": str(row.get("name") or "Stock"),
                    "group_name": f"Qty {qty_text} {unit}".strip(),
                    "amount": round(float(row.get("amount") or 0), 2),
                }
            )
        return details

    def stock_summary(self) -> dict[str, Any]:
        return {
            "items": self.one("SELECT COUNT(*) count, COALESCE(SUM(stock),0) qty FROM items") or {},
            "packs": self.one("SELECT COUNT(*) count, COALESCE(SUM(current_stock_qty),0) qty FROM product_packs WHERE COALESCE(is_active,1)=1") or {},
            "alerts": self.one("SELECT COUNT(*) count FROM items WHERE min_stock>0 AND stock<=min_stock") or {},
            "negative": self.one("SELECT COUNT(*) count FROM items WHERE stock<0") or {},
            "warehouses": self.one("SELECT COUNT(*) count FROM warehouses") or {},
            "batches": self.one("SELECT COUNT(*) count FROM item_batches WHERE stock<>0") or {},
        }
