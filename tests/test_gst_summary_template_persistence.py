import gc
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from services.company_profile_service import CompanyProfileService
from services import pdf_print


class GstSummaryTemplatePersistenceTests(unittest.TestCase):
    def _make_service(self, tmpdir):
        db_path = Path(tmpdir) / "company_profile_test.db"
        return CompanyProfileService(db_path), db_path

    def test_saved_template_persists_after_restart(self) -> None:
        tmpdir = tempfile.mkdtemp()
        try:
            service, db = self._make_service(tmpdir)
            service.save_profile({"company_name": "Acme", "invoice_template_code": "custom_gst_template"}, developer=True)
            # simulate restart by creating a new service instance
            service2 = CompanyProfileService(db)
            profile = service2.current_profile()
            self.assertEqual(profile.get("invoice_template_code"), "custom_gst_template")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_saved_template_not_overwritten_by_business_type_change(self) -> None:
        tmpdir = tempfile.mkdtemp()
        try:
            service, db = self._make_service(tmpdir)
            service.save_profile({"company_name": "Acme", "invoice_template_code": "custom_gst_template"}, developer=True)
            # change business type via admin save (developer=False)
            service.save_profile({"company_name": "Acme", "business_type_code": "pharmacy_medical"}, developer=False)
            profile = service.current_profile()
            self.assertEqual(profile.get("invoice_template_code"), "custom_gst_template")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_resolve_print_options_does_not_update_company_table(self) -> None:
        tmpdir = tempfile.mkdtemp()
        try:
            service, db = self._make_service(tmpdir)
            service.save_profile({"company_name": "Acme", "invoice_template_code": "custom_gst_template"}, developer=True)
            profile = service.current_profile()
            company = profile.copy()
            # call resolve_print_options (should not modify DB)
            opts = pdf_print.resolve_print_options(company, "sales_invoice", db_path=db)
            # reload from DB
            conn = sqlite3.connect(db)
            try:
                row = conn.execute("SELECT invoice_template_code FROM company LIMIT 1").fetchone()
                self.assertEqual(row[0], "custom_gst_template")
            finally:
                conn.close()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_write_transaction_pdf_does_not_update_company_table(self) -> None:
        tmpdir = tempfile.mkdtemp()
        outdir = Path(tmpdir) / "out"
        outdir.mkdir(parents=True, exist_ok=True)
        try:
            service, db = self._make_service(tmpdir)
            service.save_profile({"company_name": "Acme", "invoice_template_code": "custom_gst_template"}, developer=True)
            profile = service.current_profile()
            company = profile.copy()
            # minimal header/lines/totals
            header = {"no": "1", "date": "2026-07-06", "party_name": "Cust"}
            lines = [{"description": "Item", "qty": 1, "rate": 100.0, "taxable": 100.0}]
            totals = {"taxable": 100.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "gst_total": 0.0, "grand_total": 100.0}
            out_pdf = outdir / "inv.pdf"
            pdf_print.write_transaction_pdf(out_pdf, "Invoice", company, header, lines, totals, document_type="sales_invoice", db_path=db)
            # ensure DB unchanged
            conn = sqlite3.connect(db)
            try:
                row = conn.execute("SELECT invoice_template_code FROM company LIMIT 1").fetchone()
                self.assertEqual(row[0], "custom_gst_template")
            finally:
                conn.close()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
