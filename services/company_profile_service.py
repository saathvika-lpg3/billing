from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from services.business_rules import normalize_business_type
from services.mysql_source import MySqlSource


class CompanyProfileService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else MySqlSource().sqlite_path

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            # Ensure base tables exist before attempting ALTERs
            conn.execute(
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
                    upi_id TEXT
                )
                """
            )
            conn.execute(
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
                """
            )
            conn.execute(
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
                """
            )
            # Ensure audit table exists so admin/developer saves can write audit rows
            conn.execute(
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
                """
            )
            for table, column, definition in [
                ("company", "fssai_no", "TEXT"),
                ("company", "pan", "TEXT"),
                ("company", "logo_path", "TEXT"),
                ("company", "owner_name", "TEXT"),
                ("company", "mobile", "TEXT"),
                ("company", "business_type_code", "TEXT"),
                ("company", "invoice_template_code", "TEXT"),
                ("company", "subscription_plan_code", "TEXT"),
                ("company", "drug_license_no", "TEXT"),
                ("dev_companies", "fssai_no", "TEXT"),
                ("dev_companies", "pan", "TEXT"),
                ("dev_companies", "drug_license_no", "TEXT"),
                ("dev_companies", "other_registrations", "TEXT"),
                ("license", "license_plan", "TEXT"),
                ("license", "gstin", "TEXT"),
            ]:
                self._add_column(conn, table, column, definition)

    def business_types(self) -> list[dict[str, Any]]:
        self.ensure_schema()
        try:
            rows = self._rows(
                """
                SELECT code,name,invoice_template_code
                FROM dev_business_types
                WHERE COALESCE(is_active,1)=1
                ORDER BY name
                """
            )
        except sqlite3.OperationalError:
            rows = []
        if rows:
            return rows
        return [
            {"code": "distributor_wholesale", "name": "Distributor / Wholesale", "invoice_template_code": "wholesale_tax_invoice"},
            {"code": "retail_supermarket", "name": "Retail / Supermarket", "invoice_template_code": "retail_pos_bill"},
            {"code": "pharmacy_medical", "name": "Medical Shop / Pharmacy", "invoice_template_code": "pharmacy_retail_bill"},
            {"code": "electronics_mobile", "name": "Electronics / Mobile", "invoice_template_code": "electronics_sales_invoice"},
            {"code": "restaurant_food", "name": "Restaurant / Food Billing", "invoice_template_code": "restaurant_table_bill"},
            {"code": "hotel_restaurant", "name": "Hotel / Restaurant", "invoice_template_code": "restaurant_table_bill"},
            {"code": "service_business", "name": "Service / Repair Business", "invoice_template_code": "service_job_card"},
            {"code": "warehouse_based", "name": "Warehouse-Based Business", "invoice_template_code": "warehouse_gst_invoice"},
        ]

    def template_for_business_type(self, business_type_code: str) -> str:
        code = normalize_business_type(str(business_type_code or "").strip() or "distributor_wholesale")
        for row in self.business_types():
            row_code = normalize_business_type(str(row.get("code") or "").strip())
            if row_code == code:
                return str(row.get("invoice_template_code") or "wholesale_tax_invoice")
        return "wholesale_tax_invoice" if code == "distributor_wholesale" else "sales_invoice"

    def template_name_for_code(self, template_code: str) -> str:
        if not template_code:
            return ""
        rows = self._rows(
            "SELECT template_name FROM print_templates WHERE LOWER(template_code) = LOWER(?) LIMIT 1",
            (str(template_code).strip(),),
        )
        if rows:
            return str(rows[0].get("template_name") or template_code)
        return str(template_code)

    def current_profile(self) -> dict[str, Any]:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            company = self._first(conn, "SELECT * FROM company ORDER BY id LIMIT 1")
            license_row = None
            if company:
                license_row = self._first(
                    conn,
                    """
                    SELECT * FROM license
                    WHERE company_id=?
                    ORDER BY CASE WHEN LOWER(COALESCE(status,''))='active' THEN 0 ELSE 1 END,
                             COALESCE(updated_at,created_at,activated_at,'') DESC, id DESC
                    LIMIT 1
                    """,
                    (company["id"],),
                )
            if not license_row:
                license_row = self._first(
                    conn,
                    """
                    SELECT * FROM license
                    ORDER BY CASE WHEN LOWER(COALESCE(status,''))='active' THEN 0 ELSE 1 END,
                             COALESCE(updated_at,created_at,activated_at,'') DESC, id DESC
                    LIMIT 1
                    """,
                )
            dev = None
            if license_row and license_row["license_key"]:
                dev = self._first(conn, "SELECT * FROM dev_companies WHERE license_key=? ORDER BY id DESC LIMIT 1", (license_row["license_key"],))
            if not dev and company:
                dev = self._first(conn, "SELECT * FROM dev_companies WHERE company_name=? ORDER BY id DESC LIMIT 1", (company["name"],))

        company_data = dict(company) if company else {}
        license_data = dict(license_row) if license_row else {}
        dev_data = dict(dev) if dev else {}
        business_type = (
            company_data.get("business_type_code")
            or license_data.get("business_type")
            or dev_data.get("business_type_code")
            or "distributor_wholesale"
        )
        template_source = "company" if company_data.get("invoice_template_code") else "dev" if dev_data.get("invoice_template_code") else "business_type"
        template = (
            company_data.get("invoice_template_code")
            or dev_data.get("invoice_template_code")
            or self.template_for_business_type(str(business_type))
        )
        return {
            "invoice_template_code_source": template_source,
            "company_id": company_data.get("id") or 0,
            "license_id": license_data.get("id") or 0,
            "dev_company_id": dev_data.get("id") or 0,
            "company_name": company_data.get("name") or license_data.get("company_name") or dev_data.get("company_name") or "",
            "business_name": company_data.get("business_name") or "",
            "logo_path": company_data.get("logo_path") or "",
            "owner_name": company_data.get("owner_name") or dev_data.get("owner_name") or "",
            "phone": company_data.get("phone") or dev_data.get("mobile") or "",
            "mobile": company_data.get("mobile") or dev_data.get("mobile") or "",
            "email": company_data.get("email") or dev_data.get("email") or "",
            "address": company_data.get("address") or dev_data.get("address") or "",
            "city": company_data.get("city") or "",
            "state": company_data.get("state") or dev_data.get("state") or "",
            "gstin": company_data.get("gstin") or license_data.get("gstin") or dev_data.get("gst_number") or "",
            "pan": company_data.get("pan") or dev_data.get("pan") or "",
            "fssai_no": company_data.get("fssai_no") or dev_data.get("fssai_no") or "",
            "drug_license_no": company_data.get("drug_license_no") or dev_data.get("drug_license_no") or "",
            "invoice_prefix": company_data.get("invoice_prefix") or dev_data.get("invoice_prefix") or "",
            "business_type_code": business_type,
            "invoice_template_code": template,
            "subscription_plan_code": company_data.get("subscription_plan_code") or license_data.get("license_plan") or dev_data.get("subscription_plan_code") or "basic",
            "license_key": license_data.get("license_key") or dev_data.get("license_key") or "",
            "installation_key": license_data.get("installation_key") or license_data.get("install_code") or "",
            "activation_date": license_data.get("activation_date") or dev_data.get("start_date") or license_data.get("activated_at") or "",
            "expiry_date": license_data.get("expiry_date") or dev_data.get("expiry_date") or "",
            "status": license_data.get("status") or dev_data.get("license_status") or "active",
            "max_users": license_data.get("max_users") or 1,
            "notes": license_data.get("notes") or dev_data.get("notes") or "",
        }

    def save_profile(self, data: dict[str, Any], developer: bool = False) -> int:
        self.ensure_schema()
        profile = self.current_profile()
        # Enforce admin-only allowed fields when not a developer update
        if not developer:
            allowed = {
                "company_name",
                "name",
                "business_name",
                "logo_path",
                "phone",
                "mobile",
                "email",
                "website",
                "address",
                "city",
                "state",
                "pin_code",
                "country",
                "contact_person",
                "invoice_prefix",
                "gstin",
                "pan",
                "fssai_no",
                "upi_id",
                "owner_name",
            }
            data = {k: v for k, v in data.items() if k in allowed}
            audit_allowed_keys = allowed
        else:
            audit_allowed_keys = None

        merged = profile | data
        now = datetime.now().isoformat(timespec="seconds")
        business_type = str(merged.get("business_type_code") or "distributor_wholesale").strip()
        invoice_template_code = str(data.get("invoice_template_code") or "").strip()
        if not invoice_template_code:
            if profile.get("invoice_template_code_source") in {"company", "dev"}:
                invoice_template_code = str(profile.get("invoice_template_code") or "").strip()
            else:
                invoice_template_code = self.template_for_business_type(business_type)
        merged["invoice_template_code"] = invoice_template_code
        plan = str(merged.get("subscription_plan_code") or "basic").strip().lower()
        status = str(merged.get("status") or "active").strip().lower()
        company_name = str(merged.get("company_name") or merged.get("name") or "").strip()
        if not company_name:
            raise ValueError("Company name is required.")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                company_id = int(merged.get("company_id") or 0)
                company_row = {
                    "name": company_name,
                    "business_name": merged.get("business_name") or "",
                    "logo_path": merged.get("logo_path") or "",
                    "owner_name": merged.get("owner_name") or "",
                    "phone": merged.get("phone") or merged.get("mobile") or "",
                    "mobile": merged.get("mobile") or merged.get("phone") or "",
                    "email": merged.get("email") or "",
                    "address": merged.get("address") or "",
                    "city": merged.get("city") or "",
                    "state": merged.get("state") or "",
                    "gstin": merged.get("gstin") or "",
                    "pan": merged.get("pan") or "",
                    "fssai_no": merged.get("fssai_no") or "",
                    "drug_license_no": merged.get("drug_license_no") or "",
                    "invoice_prefix": merged.get("invoice_prefix") or "",
                    "business_type_code": business_type,
                    "invoice_template_code": invoice_template_code,
                    "subscription_plan_code": plan,
                }
                # Prune company_row to actual table columns to avoid INSERT/UPDATE errors
                existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(company)").fetchall()]
                company_row = {k: v for k, v in company_row.items() if k in existing_cols}
                # Prepare audit: compare previous company values to merged values
                try:
                    prev = self._first(conn, "SELECT * FROM company ORDER BY id LIMIT 1")
                    prev_dict = dict(prev) if prev else {}
                except Exception:
                    prev_dict = {}
                # If this is an admin-managed save (developer==False), do not modify license/dev rows
                if company_id:
                    self._update(conn, "company", company_row, company_id)
                else:
                    company_id = self._insert(conn, "company", company_row)

                # Audit changed fields (only log fields that actually changed)
                try:
                    from services.developer_audit_service import DeveloperAuditService

                    audit = DeveloperAuditService(self.db_path)
                except Exception:
                    audit = None
                if audit:
                    source = "developer_dashboard" if developer else "admin_company"
                    changed_by = "developer" if developer else "admin"
                    for key, new_val in company_row.items():
                        # If audit_allowed_keys is set (admin path), only audit allowed fields
                        if audit_allowed_keys is not None and key not in audit_allowed_keys:
                            continue
                        old_val = prev_dict.get(key)
                        if old_val is None:
                            old_val = ""
                        if new_val is None:
                            new_val = ""
                        if str(old_val) != str(new_val):
                            try:
                                # Use existing connection for audit to avoid cross-connection locks
                                if hasattr(audit, 'log_company_audit_conn'):
                                    audit.log_company_audit_conn(conn, changed_by, source, key, str(old_val), str(new_val))
                                else:
                                    audit.log_company_audit(changed_by, source, key, str(old_val), str(new_val))
                            except Exception:
                                # Do not allow audit failures to break save
                                continue

                # Handle license rows only if this is a developer update or license info explicitly provided
                license_id = int(merged.get("license_id") or 0)
                license_key = str(merged.get("license_key") or "").strip().upper()
                install_key = str(merged.get("installation_key") or "").strip()
                if developer and (license_key or license_id):
                    license_row = {
                        "install_code": install_key,
                        "license_key": license_key,
                        "client_name": company_name,
                        "company_id": company_id,
                        "company_name": company_name,
                        "business_type": business_type,
                        "installation_key": install_key,
                        "activation_date": str(merged.get("activation_date") or date.today().isoformat()),
                        "expiry_date": str(merged.get("expiry_date") or ""),
                        "status": status,
                        "license_plan": plan,
                        "gstin": merged.get("gstin") or "",
                        "max_users": int(float(merged.get("max_users") or 1)),
                        "notes": merged.get("notes") or "",
                        "updated_at": now,
                    }
                    if license_id:
                        self._update(conn, "license", license_row, license_id)
                    else:
                        license_row["created_at"] = now
                        license_row["activated_at"] = now
                        license_row["last_checked_at"] = now
                        license_id = self._insert(conn, "license", license_row)

                dev_row = {
                    "company_name": company_name,
                    "owner_name": merged.get("owner_name") or "",
                    "mobile": merged.get("mobile") or merged.get("phone") or "",
                    "email": merged.get("email") or "",
                    "gst_number": merged.get("gstin") or "",
                    "business_type_code": business_type,
                    "subscription_plan_code": plan,
                    "invoice_template_code": invoice_template_code,
                    "status": status.title(),
                    "license_key": license_key,
                    "start_date": str(merged.get("activation_date") or date.today().isoformat())[:10],
                    "expiry_date": str(merged.get("expiry_date") or ""),
                    "grace_days": int(float(merged.get("grace_days") or 7)),
                    "license_status": status.title(),
                    "last_renewal_date": str(merged.get("activation_date") or date.today().isoformat())[:10],
                    "notes": merged.get("notes") or "",
                    "state": merged.get("state") or "",
                    "invoice_prefix": merged.get("invoice_prefix") or "",
                    "fssai_no": merged.get("fssai_no") or "",
                    "drug_license_no": merged.get("drug_license_no") or "",
                    "updated_at": now,
                }
                # Sync a limited dev_companies row so developer dashboard and admin remain compatible.
                # This creates/updates dev_companies with non-license fields; full license updates only when developer=True.
                dev_id = int(merged.get("dev_company_id") or 0)
                sync_dev_row = {
                    "company_name": company_name,
                    "owner_name": merged.get("owner_name") or "",
                    "mobile": merged.get("mobile") or merged.get("phone") or "",
                    "email": merged.get("email") or "",
                    "gst_number": merged.get("gstin") or "",
                    "pan": merged.get("pan") or "",
                    "business_type_code": business_type,
                    "invoice_template_code": invoice_template_code,
                    "fssai_no": merged.get("fssai_no") or "",
                    "updated_at": now,
                }
                existing_dev_cols = [r[1] for r in conn.execute("PRAGMA table_info(dev_companies)").fetchall()]
                sync_dev_row = {k: v for k, v in sync_dev_row.items() if k in existing_dev_cols}
                if not dev_id and license_key:
                    row = self._first(conn, "SELECT id FROM dev_companies WHERE license_key=? LIMIT 1", (license_key,))
                    dev_id = int(row["id"]) if row else 0
                if not dev_id:
                    row = self._first(conn, "SELECT id FROM dev_companies WHERE company_name=? LIMIT 1", (company_name,))
                    dev_id = int(row["id"]) if row else 0
                if dev_id:
                    self._update(conn, "dev_companies", sync_dev_row, dev_id)
                else:
                    sync_dev_row["created_at"] = now
                    self._insert(conn, "dev_companies", sync_dev_row)
        return company_id

    def developer_rows(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT dc.id,dc.company_name,dc.owner_name,dc.mobile,dc.email,dc.business_type_code,
                   dc.invoice_template_code,dc.license_key,dc.expiry_date,dc.license_status,dc.fssai_no,dc.pan
            FROM dev_companies dc
            ORDER BY dc.updated_at DESC, dc.id DESC
            LIMIT 200
            """
        )

    def _rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    @staticmethod
    def _first(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        return conn.execute(sql, params).fetchone()

    @staticmethod
    def _insert(conn: sqlite3.Connection, table: str, row: dict[str, Any]) -> int:
        columns = list(row)
        placeholders = ", ".join("?" for _ in columns)
        conn.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", tuple(row[column] for column in columns))
        return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    @staticmethod
    def _update(conn: sqlite3.Connection, table: str, row: dict[str, Any], row_id: int) -> None:
        assignments = ", ".join(f"{column}=?" for column in row)
        conn.execute(f"UPDATE {table} SET {assignments} WHERE id=?", tuple(row[column] for column in row) + (row_id,))

    def _add_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        if not self._has_column(conn, table, column):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    @staticmethod
    def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
        return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))
