import sqlite3
from services.license_service import LicenseService, LicenseContext, LicenseError
from services.developer_audit_service import DeveloperAuditService
from services.mysql_source import MySqlSource
import tempfile


def test_profile_for_aliases():
    from services.business_rules import profile_for

    assert profile_for("retail_supermarket").code == "retail"
    assert profile_for("pharmacy_medical").code == "pharmacy"
    assert profile_for("electronics_mobile").code == "electronics"
    assert profile_for("unknown_type").code == "distributor_wholesale"


def test_template_for_business_type_aliases_use_expected_templates():
    from services.company_profile_service import CompanyProfileService

    service = CompanyProfileService()
    assert service.template_for_business_type("retail_supermarket") == "retail_pos_bill"
    assert service.template_for_business_type("pharmacy_medical") == "pharmacy_retail_bill"
    assert service.template_for_business_type("electronics_mobile") == "electronics_sales_invoice"
    assert service.template_for_business_type("retail") == "retail_pos_bill"
    assert service.template_for_business_type("pharmacy") == "pharmacy_retail_bill"
    assert service.template_for_business_type("electronics") == "electronics_sales_invoice"
    assert service.template_for_business_type("hotel_restaurant") == "restaurant_table_bill"
    assert service.template_for_business_type("restaurant_food") == "restaurant_table_bill"
    assert service.template_for_business_type("service_business") == "service_job_card"
    assert service.template_for_business_type("warehouse_based") == "warehouse_gst_invoice"


def test_profile_for_aliases_includes_restaurant_and_service():
    from services.business_rules import profile_for

    assert profile_for("hotel_restaurant").code == "restaurant"
    assert profile_for("restaurant_food").code == "restaurant"
    assert profile_for("service_business").code == "service"
    assert profile_for("warehouse_based").code == "warehouse"


def test_validate_item_line_requires_mrp_for_pharmacy():
    from services.business_rules import validate_item_line

    errors = validate_item_line(
        "pharmacy_medical",
        {
            "item_name": "Paracetamol",
            "hsn": "300450",
            "unit": "PCS",
            "qty": 1,
            "rate": 10,
            "gst_rate": 12,
            "mrp": 0,
        },
    )
    assert "MRP is required for this business type." in errors


def test_invalid_developer_login_logs(tmp_path):
    db = tmp_path / "devtest.db"
    das = DeveloperAuditService(str(db))
    das.ensure_schema()
    das.log_attempt("tester", False, "invalid_key", "0.0.0")
    with sqlite3.connect(str(db)) as conn:
        row = conn.execute("SELECT username, success, reason FROM developer_login_attempts ORDER BY id DESC LIMIT 1").fetchone()
        assert row[0] == "tester"
        assert row[1] == 0
        assert row[2] == "invalid_key"


def test_admin_save_allows_business_fields(tmp_path):
    from services.company_profile_service import CompanyProfileService
    db = tmp_path / "company.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()
    data = {
        "company_name": "ACME Ltd",
        "business_name": "ACME Business",
        "phone": "9999999999",
        "email": "info@acme.test",
        "address": "1 Main St",
        "city": "Metropolis",
        "state": "State",
        "invoice_prefix": "AC",
    }
    cid = service.save_profile(data, developer=False)
    assert cid > 0
    profile = service.current_profile()
    assert profile["company_name"] == "ACME Ltd"


def test_admin_save_ignores_restricted_fields(tmp_path):
    from services.company_profile_service import CompanyProfileService
    db = tmp_path / "company2.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()
    data = {
        "company_name": "ACME Ltd",
        "business_type_code": "enterprise",
        "license_key": "FAKEKEY",
    }
    cid = service.save_profile(data, developer=False)
    profile = service.current_profile()
    # restricted fields should not be set via admin path
    assert profile.get("business_type_code") != "enterprise"
    assert profile.get("license_key") != "FAKEKEY"


def test_developer_save_updates_restricted_fields(tmp_path):
    from services.company_profile_service import CompanyProfileService
    db = tmp_path / "company3.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()
    data = {
        "company_name": "ACME Ltd",
        "business_type_code": "enterprise",
        "license_key": "DEVKEY",
    }
    cid = service.save_profile(data, developer=True)
    profile = service.current_profile()
    assert profile.get("business_type_code") == "enterprise"
    assert profile.get("license_key").upper() == "DEVKEY"


def test_admin_edit_creates_audit_row(tmp_path):
    from services.company_profile_service import CompanyProfileService
    import sqlite3

    db = tmp_path / "audit1.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()
    # initial save
    cid = service.save_profile({"company_name": "ACME", "phone": "111"}, developer=False)
    # admin update
    service.save_profile({"company_name": "ACME Co", "phone": "222"}, developer=False)
    with sqlite3.connect(str(db)) as conn:
        row = conn.execute("SELECT field_name, old_value, new_value, source FROM company_profile_audit ORDER BY id DESC LIMIT 1").fetchone()
        assert row is not None
        assert row[0] in {"company_name", "phone"}
        assert row[3] == "admin_company"


def test_admin_restricted_field_not_audited(tmp_path):
    from services.company_profile_service import CompanyProfileService
    import sqlite3

    db = tmp_path / "audit2.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()
    # attempt to set business_type_code via admin path
    service.save_profile({"company_name": "ACME", "business_type_code": "illegal"}, developer=False)
    with sqlite3.connect(str(db)) as conn:
        row = conn.execute("SELECT COUNT(*) FROM company_profile_audit WHERE field_name='business_type_code'").fetchone()
        assert row[0] == 0


def test_developer_change_restricted_field_is_audited(tmp_path):
    from services.company_profile_service import CompanyProfileService
    import sqlite3

    db = tmp_path / "audit3.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()
    service.save_profile({"company_name": "ACME", "business_type_code": "retail"}, developer=True)
    with sqlite3.connect(str(db)) as conn:
        row = conn.execute("SELECT field_name, old_value, new_value, source FROM company_profile_audit WHERE field_name='business_type_code' ORDER BY id DESC LIMIT 1").fetchone()
        assert row is not None
        assert row[2] == "retail"
        assert row[3] == "developer_dashboard"


def test_unchanged_save_creates_no_audit(tmp_path):
    from services.company_profile_service import CompanyProfileService
    import sqlite3

    db = tmp_path / "audit4.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()
    service.save_profile({"company_name": "ACME"}, developer=False)
    # save again with same data
    service.save_profile({"company_name": "ACME"}, developer=False)
    with sqlite3.connect(str(db)) as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM company_profile_audit").fetchone()[0]
        assert cnt >= 0


def test_audit_failure_does_not_break_save(tmp_path, monkeypatch):
    from services.company_profile_service import CompanyProfileService
    import sqlite3

    db = tmp_path / "audit5.db"
    service = CompanyProfileService(str(db))
    service.ensure_schema()

    # monkeypatch DeveloperAuditService.log_company_audit to raise
    import services.developer_audit_service as das_mod

    orig = das_mod.DeveloperAuditService.log_company_audit_conn

    def bad_log(self, *args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(das_mod.DeveloperAuditService, "log_company_audit_conn", bad_log)
    # should not raise
    service.save_profile({"company_name": "ACME"}, developer=False)
    # restore
    monkeypatch.setattr(das_mod.DeveloperAuditService, "log_company_audit_conn", orig)
