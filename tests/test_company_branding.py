from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QApplication
from pypdf import PdfReader

from config.app_config import AppConfig
from services.pdf_print import write_report_pdf
from widgets.company_branding import CompanyBrandingWidget, company_identity_lines


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _company() -> dict[str, str]:
    return {
        "company_name": "Lakshmi Sai Agencies",
        "business_type_code": "distributor_wholesale",
        "gstin": "36ABCDE1234F1Z5",
        "fssai_no": "FSSAI-1001",
        "drug_license_no": "DL-2026-01",
        "phone": "9000000000",
        "email": "accounts@example.test",
    }


def test_shared_company_branding_places_logo_above_identity_and_shows_all_details(tmp_path: Path) -> None:
    application = _app()
    assert application is not None
    widget = CompanyBrandingWidget(AppConfig(tmp_path, tmp_path), _company())
    try:
        layout = widget.layout()
        assert layout.itemAt(0).widget() is widget.logo
        assert layout.itemAt(1).widget() is widget.name_label
        assert widget.logo.text() == "LSA"
        text = " | ".join(label.text() for label in widget.detail_labels)
        assert "Distributor / Wholesale" in text
        assert "GSTIN" in text
        assert "FSSAI" in text
        assert "Drug Lic." in text
        assert "9000000000" in text
        assert "accounts@example.test" in text
    finally:
        widget.close()


def test_company_identity_lines_cover_business_registration_and_contact() -> None:
    text = " | ".join(company_identity_lines(_company()))
    for expected in ("Distributor / Wholesale", "GSTIN", "FSSAI", "Drug Lic.", "9000000000", "accounts@example.test"):
        assert expected in text


def test_report_pdf_repeats_complete_client_identity_with_placeholder_logo(tmp_path: Path) -> None:
    path = tmp_path / "branding-report.pdf"
    write_report_pdf(path, "Customer List", _company(), [{"name": "Buyer", "amount": 100}])
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    assert "LAKSHMI SAI AGENCIES" in text
    assert "Business: Distributor / Wholesale" in text
    assert "GSTIN: 36ABCDE1234F1Z5" in text
    assert "FSSAI: FSSAI-1001" in text
    assert "Drug Lic.: DL-2026-01" in text
