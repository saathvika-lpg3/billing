import sqlite3
import tempfile
import shutil
import unittest
from pathlib import Path

from services.company_profile_service import CompanyProfileService
from services.license_service import LicenseContext, LicenseService


class LicenseUpsertPreserveTemplateTest(unittest.TestCase):
    def test_license_upsert_preserves_explicit_company_template(self):
        tmp = tempfile.mkdtemp()
        try:
            db = Path(tmp) / "license_test.db"
            svc = CompanyProfileService(db)
            svc.ensure_schema()
            # insert a company row with explicit invoice_template_code
            with sqlite3.connect(db) as conn:
                conn.execute("INSERT INTO company(name,invoice_template_code) VALUES(?,?)", ("Acme", "explicit_template"))
                conn.commit()
                # build a minimal LicenseContext
                ctx = LicenseContext(
                    source_path=Path("/tmp/ic"),
                    company_name="Acme Co",
                    phone_number="111",
                    area="City",
                    license_key="PRM-TEST-2026-ABCD",
                    installation_key="INST",
                    super_admin_username="admin",
                    super_admin_password="pw",
                    developer_login_key="devkey",
                    plan="basic",
                    expiry_date="2099-12-31",
                    status="active",
                    business_type_code="retail_supermarket",
                    payload={},
                    raw_text="{}",
                )
                # Call static method to upsert
                LicenseService._upsert_company(conn, ctx)
                row = conn.execute("SELECT invoice_template_code FROM company ORDER BY id LIMIT 1").fetchone()
                self.assertEqual(row[0], "explicit_template")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
