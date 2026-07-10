import gc
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from services.company_profile_service import CompanyProfileService


class CompanyProfileServicePanTests(unittest.TestCase):
    def test_pan_round_trip(self) -> None:
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "company_profile_test.db"
            service = CompanyProfileService(db_path)

            service.save_profile({"company_name": "Acme Trading", "pan": "ABCDE1234F"}, developer=True)
            profile = service.current_profile()

            self.assertEqual(profile.get("pan"), "ABCDE1234F")

            conn = sqlite3.connect(db_path)
            try:
                self.assertEqual(conn.execute("SELECT pan FROM company LIMIT 1").fetchone()[0], "ABCDE1234F")
            finally:
                conn.close()

            profile = None
            service = None
            gc.collect()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_invoice_template_code_persists_when_explicitly_set(self) -> None:
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "company_profile_test.db"
            service = CompanyProfileService(db_path)

            service.save_profile(
                {
                    "company_name": "Acme Trading",
                    "pan": "ABCDE1234F",
                    "invoice_template_code": "custom_invoice_template",
                },
                developer=True,
            )
            profile = service.current_profile()

            self.assertEqual(profile.get("invoice_template_code"), "custom_invoice_template")
            self.assertEqual(profile.get("invoice_template_code_source"), "company")

            conn = sqlite3.connect(db_path)
            try:
                row = conn.execute("SELECT invoice_template_code FROM company LIMIT 1").fetchone()
                self.assertEqual(row[0], "custom_invoice_template")
            finally:
                conn.close()

            profile = None
            service = None
            gc.collect()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
