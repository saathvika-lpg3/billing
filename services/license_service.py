from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import platform
import re
import secrets
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from config.app_config import AppConfig
from services.company_profile_service import CompanyProfileService
from services.mysql_source import MySqlSource


class LicenseError(RuntimeError):
    pass


@dataclass(frozen=True)
class LicenseContext:
    source_path: Path
    company_name: str
    phone_number: str
    area: str
    license_key: str
    installation_key: str
    super_admin_username: str
    super_admin_password: str
    developer_login_key: str
    plan: str
    expiry_date: str
    status: str
    business_type_code: str
    payload: dict[str, Any]
    raw_text: str
    signed: bool = False
    signature_verified: bool = False

    @property
    def plan_code(self) -> str:
        return self.plan.strip().lower() or "basic"

    @property
    def is_premium(self) -> bool:
        return self.plan_code in {"premium", "enterprise", "professional"}


class LicenseService:
    _LICENSE_RE = re.compile(r"^PRM-[A-Z0-9]{2,20}-20[0-9]{2}-[A-Z0-9]{4,32}$")

    def __init__(self, config: AppConfig, db_path: Path | None = None) -> None:
        self.config = config
        self.db_path = Path(db_path) if db_path else MySqlSource().sqlite_path

    def require_license(self) -> LicenseContext:
        path = self.find_license_file()
        if not path:
            raise LicenseError(
                "Client license file is missing. Installation must be completed with a valid .prmlic file."
            )
        context = self.read_license_file(path)
        self.validate(context)
        return context

    def find_license_file(self) -> Path | None:
        candidates: list[Path] = []
        env_path = os.environ.get("PRM_CLIENT_LICENSE_FILE", "").strip()
        if env_path:
            candidates.append(Path(env_path))
        candidates.extend(
            [
                self.config.project_root / "license" / "client.prmlic",
                self.config.resource_root / "license" / "client.prmlic",
                self.config.project_root / "client.prmlic",
                self.config.resource_root / "client.prmlic",
            ]
        )
        for path in candidates:
            if path.exists() and path.is_file():
                return path
        return None

    def read_license_file(self, path: Path) -> LicenseContext:
        raw = path.read_text(encoding="utf-8-sig").strip()
        if not raw:
            raise LicenseError("Selected .prmlic file is empty.")
        if raw.startswith("PRMLIC1."):
            payload, verified = self._read_signed_payload(raw)
            return self._context_from_payload(path, payload, raw, signed=True, verified=verified)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LicenseError(f"Selected .prmlic file is not valid JSON or PRMLIC1 text: {exc}") from exc
        row = self._single_row(parsed)
        return self._context_from_payload(path, row, raw, signed=False, verified=False)

    def validate(self, context: LicenseContext) -> None:
        required = {
            "Client Company Name": context.company_name,
            "Phone Number": context.phone_number,
            "Area": context.area,
            "License Key": context.license_key,
            "Installation Key": context.installation_key,
            "Super Admin Username": context.super_admin_username,
            "Super Admin Password": context.super_admin_password,
            "Developer Login Key": context.developer_login_key,
            "Plan": context.plan,
            "Expiry Date": context.expiry_date,
            "Status": context.status,
            "Business Type Code": context.business_type_code,
        }
        missing = [label for label, value in required.items() if not str(value or "").strip()]
        if missing:
            raise LicenseError("Client license is incomplete. Missing: " + ", ".join(missing))
        if context.status.strip().lower() != "active":
            raise LicenseError("Client license is not Active.")
        license_key = context.license_key.strip().upper()
        if not self._LICENSE_RE.match(license_key):
            raise LicenseError("Client license key format is invalid.")
        try:
            expiry = datetime.strptime(context.expiry_date.strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise LicenseError("Client license expiry date must be YYYY-MM-DD.") from exc
        if expiry < date.today():
            raise LicenseError(f"Client license expired on {context.expiry_date}.")

    def apply_to_database(self, context: LicenseContext) -> None:
        machine_hash = self.machine_hash()
        license_hash = hashlib.sha256(context.raw_text.encode("utf-8")).hexdigest()
        now = datetime.now().isoformat(timespec="seconds")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            self._ensure_schema(conn)
            activation = conn.execute(
                "SELECT license_key,machine_hash FROM license_activation ORDER BY id LIMIT 1"
            ).fetchone()
            if activation and activation["license_key"] == context.license_key:
                if activation["machine_hash"] != machine_hash:
                    raise LicenseError(
                        "This installation is already activated on another machine. Reinstall with the client's .prmlic file."
                    )
                conn.execute(
                    """
                    UPDATE license_activation
                    SET license_hash=?, last_checked_at=?, expiry_date=?, status=?
                    WHERE id=1
                    """,
                    (license_hash, now, context.expiry_date, context.status),
                )
            elif activation:
                conn.execute("DELETE FROM license_activation")
                self._insert_activation(conn, context, machine_hash, license_hash, now)
            else:
                self._insert_activation(conn, context, machine_hash, license_hash, now)

            company_id = self._upsert_company(conn, context)
            self._upsert_license_row(conn, context, company_id, machine_hash, license_hash, now)
            self.upsert_user(
                conn,
                name="Super Admin",
                email=context.super_admin_username,
                password=context.super_admin_password,
                role="admin",
            )

    def authenticate_user(self, username: str, password: str, context: LicenseContext) -> dict[str, str] | None:
        user_text = username.strip()
        if not user_text or not password:
            return None
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            self._ensure_schema(conn)
            self.upsert_user(
                conn,
                name="Super Admin",
                email=context.super_admin_username,
                password=context.super_admin_password,
                role="admin",
            )
            row = conn.execute(
                """
                SELECT id,name,email,pass,role,COALESCE(locked,0) locked
                FROM users
                WHERE lower(COALESCE(email,''))=lower(?)
                   OR lower(COALESCE(name,''))=lower(?)
                ORDER BY id
                LIMIT 1
                """,
                (user_text, user_text),
            ).fetchone()
            if not row or int(row["locked"] or 0):
                return None
            if not self.verify_password(password, row["pass"] or ""):
                return None
            conn.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(timespec="seconds"), row["id"]))
            return {
                "id": str(row["id"]),
                "name": str(row["name"] or row["email"] or user_text),
                "email": str(row["email"] or user_text),
                "role": str(row["role"] or "viewer"),
            }

    def validate_developer_key(self, key: str, context: LicenseContext) -> bool:
        return hmac.compare_digest(key.strip().upper(), context.developer_login_key.strip().upper())

    def upsert_user(
        self,
        conn: sqlite3.Connection,
        *,
        name: str,
        email: str,
        password: str,
        role: str,
        locked: int = 0,
    ) -> int:
        existing = conn.execute(
            "SELECT id,pass FROM users WHERE lower(COALESCE(email,''))=lower(?) LIMIT 1",
            (email.strip(),),
        ).fetchone()
        password_hash = self.hash_password(password)
        if existing:
            conn.execute(
                "UPDATE users SET name=?, pass=?, role=?, locked=? WHERE id=?",
                (name, password_hash, role, locked, existing["id"]),
            )
            return int(existing["id"])
        conn.execute(
            "INSERT INTO users(name,email,pass,role,locked) VALUES(?,?,?,?,?)",
            (name, email.strip(), password_hash, role, locked),
        )
        return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        iterations = 200_000
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), iterations)
        return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, stored: str) -> bool:
        if not stored:
            return False
        if stored.startswith("pbkdf2_sha256$"):
            try:
                _name, iterations, salt, expected = stored.split("$", 3)
                digest = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt.encode("ascii"),
                    int(iterations),
                ).hex()
            except Exception:
                return False
            return hmac.compare_digest(digest, expected)
        return hmac.compare_digest(password, stored)

    @staticmethod
    def machine_hash() -> str:
        machine_guid = ""
        if os.name == "nt":
            try:
                import winreg

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                    machine_guid = str(winreg.QueryValueEx(key, "MachineGuid")[0])
            except Exception:
                machine_guid = ""
        raw = "|".join(
            [
                machine_guid,
                platform.node(),
                platform.machine(),
                str(uuid.getnode()),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _read_signed_payload(self, raw: str) -> tuple[dict[str, Any], bool]:
        parts = raw.split(".")
        if len(parts) != 3 or parts[0] != "PRMLIC1":
            raise LicenseError("Signed .prmlic format is invalid.")
        payload_bytes = self._b64url_decode(parts[1])
        signature = self._b64url_decode(parts[2])
        public_key_path = self.config.assets_dir / "license_public_key.txt"
        if not public_key_path.exists():
            raise LicenseError("License public key is missing from the application.")
        public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
        try:
            public_key.verify(signature, payload_bytes, padding.PKCS1v15(), hashes.SHA256())
        except InvalidSignature as exc:
            raise LicenseError("Signed .prmlic verification failed.") from exc
        payload = json.loads(payload_bytes.decode("utf-8"))
        return payload, True

    @staticmethod
    def _b64url_decode(value: str) -> bytes:
        padded = value + "=" * ((4 - len(value) % 4) % 4)
        return base64.urlsafe_b64decode(padded.encode("ascii"))

    @staticmethod
    def _single_row(parsed: Any) -> dict[str, Any]:
        if isinstance(parsed, list):
            rows = parsed
        elif isinstance(parsed, dict):
            if isinstance(parsed.get("clients"), list):
                rows = parsed["clients"]
            elif isinstance(parsed.get("licenses"), list):
                rows = parsed["licenses"]
            elif isinstance(parsed.get("client"), dict):
                rows = [parsed["client"]]
            else:
                rows = [parsed]
        else:
            rows = []
        if len(rows) != 1 or not isinstance(rows[0], dict):
            raise LicenseError("Client .prmlic must contain exactly one client row.")
        return dict(rows[0])

    def _context_from_payload(
        self,
        path: Path,
        payload: dict[str, Any],
        raw: str,
        *,
        signed: bool,
        verified: bool,
    ) -> LicenseContext:
        return LicenseContext(
            source_path=path,
            company_name=self._field(payload, "client_company_name", "company_name", "company", "Client Company Name"),
            phone_number=self._field(payload, "phone_number", "phone", "mobile", "Phone Number"),
            area=self._field(payload, "area", "city", "location", "Area"),
            license_key=self._field(payload, "license_key", "License Key").upper(),
            installation_key=self._field(payload, "installation_key", "Installation Key"),
            super_admin_username=self._field(payload, "super_admin_username", "admin_email", "Super Admin Username"),
            super_admin_password=self._field(payload, "super_admin_password", "admin_password", "Super Admin Password"),
            developer_login_key=self._field(payload, "developer_login_key", "developer_key", "Developer Login Key"),
            plan=self._field(payload, "plan", "subscription_plan", "License Plan") or "Basic",
            expiry_date=self._field(payload, "expiry_date", "expiry", "Valid Till"),
            status=self._field(payload, "status") or "Active",
            business_type_code=self._field(payload, "business_type_code", "business_type", "Business Type Code")
            or "distributor_wholesale",
            payload=payload,
            raw_text=raw,
            signed=signed,
            signature_verified=verified,
        )

    @staticmethod
    def _field(payload: dict[str, Any], *names: str) -> str:
        normalized = {re.sub(r"[^a-z0-9]", "", str(key).lower()): value for key, value in payload.items()}
        for name in names:
            key = re.sub(r"[^a-z0-9]", "", name.lower())
            if key in normalized:
                return str(normalized[key] or "").strip()
        return ""

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS license_activation (
                id INTEGER PRIMARY KEY CHECK(id=1),
                license_key TEXT NOT NULL,
                installation_key TEXT NOT NULL,
                company_name TEXT NOT NULL,
                plan TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                status TEXT NOT NULL,
                business_type_code TEXT NOT NULL,
                machine_hash TEXT NOT NULL,
                license_hash TEXT NOT NULL,
                activated_at TEXT NOT NULL,
                last_checked_at TEXT NOT NULL
            )
            """
        )

    @staticmethod
    def _insert_activation(
        conn: sqlite3.Connection,
        context: LicenseContext,
        machine_hash: str,
        license_hash: str,
        now: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO license_activation(
                id,license_key,installation_key,company_name,plan,expiry_date,status,
                business_type_code,machine_hash,license_hash,activated_at,last_checked_at
            ) VALUES(1,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                context.license_key,
                context.installation_key,
                context.company_name,
                context.plan,
                context.expiry_date,
                context.status,
                context.business_type_code,
                machine_hash,
                license_hash,
                now,
                now,
            ),
        )

    @staticmethod
    def _upsert_company(conn: sqlite3.Connection, context: LicenseContext) -> int:
        # Preserve any explicitly saved company invoice_template_code. Only apply
        # license-provided defaults when company row has no template set.
        row = conn.execute("SELECT id,invoice_template_code FROM company ORDER BY id LIMIT 1").fetchone()
        # Use CompanyProfileService with default DB path to resolve business-type default.
        default_template = CompanyProfileService().template_for_business_type(context.business_type_code)
        if row:
            try:
                existing_template = str(row["invoice_template_code"] or "").strip()
            except Exception:
                # sqlite may return a tuple if row_factory not set; invoice_template_code is second column
                existing_template = str(row[1] or "").strip()
            # If an explicit template exists, retain it; otherwise use license/default.
            invoice_template_code = existing_template if existing_template else default_template
            values = (
                context.company_name,
                context.company_name,
                context.phone_number,
                context.area,
                context.business_type_code,
                invoice_template_code,
                context.plan_code,
            )
            # row may be sqlite3.Row (mapping) or a tuple; handle both
            try:
                row_id = int(row["id"])
            except Exception:
                row_id = int(row[0])
            conn.execute(
                """
                UPDATE company
                SET name=?, business_name=?, phone=?, city=?, business_type_code=?,
                    invoice_template_code=?, subscription_plan_code=?
                WHERE id=?
                """,
                values + (row_id,),
            )
            return row_id
        conn.execute(
            """
            INSERT INTO company(name,business_name,phone,city,business_type_code,invoice_template_code,subscription_plan_code)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                context.company_name,
                context.company_name,
                context.phone_number,
                context.area,
                context.business_type_code,
                default_template,
                context.plan_code,
            ),
        )
        return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    @staticmethod
    def _upsert_license_row(
        conn: sqlite3.Connection,
        context: LicenseContext,
        company_id: int,
        machine_hash: str,
        license_hash: str,
        now: str,
    ) -> None:
        row = conn.execute("SELECT id FROM license WHERE license_key=? LIMIT 1", (context.license_key,)).fetchone()
        payload_json = json.dumps(context.payload, ensure_ascii=False, sort_keys=True)
        values = (
            context.installation_key,
            context.license_key,
            context.company_name,
            company_id,
            context.company_name,
            context.business_type_code,
            context.installation_key,
            context.expiry_date,
            context.status.lower(),
            context.plan_code,
            machine_hash,
            context.raw_text if context.signed else "",
            payload_json,
            license_hash,
            now,
        )
        if row:
            conn.execute(
                """
                UPDATE license
                SET install_code=?, license_key=?, client_name=?, company_id=?, company_name=?,
                    business_type=?, installation_key=?, expiry_date=?, status=?, license_plan=?,
                    machine_hash=?, signed_license_token=?, license_payload=?, license_signature_hash=?,
                    updated_at=?
                WHERE id=?
                """,
                values + (row["id"],),
            )
            return
        conn.execute(
            """
            INSERT INTO license(
                install_code,license_key,client_name,company_id,company_name,business_type,
                installation_key,expiry_date,status,license_plan,machine_hash,signed_license_token,
                license_payload,license_signature_hash,created_at,updated_at,activation_date,
                activated_at,last_checked_at,max_users,installation_count
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            values + (now, now, now, now, 3, 1),
        )
