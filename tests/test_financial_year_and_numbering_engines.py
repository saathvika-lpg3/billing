from __future__ import annotations

import sqlite3
from datetime import date

from services.financial_year_service import FinancialYearService
from services.numbering_series_service import NumberingSeriesService


def test_financial_year_create_and_current_switch(tmp_path):
    db_path = tmp_path / "erp.db"
    service = FinancialYearService(db_path)

    year1_id = service.create_year("2025-26", date(2025, 4, 1), date(2026, 3, 31))
    year2_id = service.create_year("2026-27", date(2026, 4, 1), date(2027, 3, 31))

    current = service.get_current_year()
    assert current is not None
    assert current["id"] == year1_id

    switched = service.set_current_year(year2_id)
    assert switched["is_current"] == 1
    assert switched["label"] == "2026-27"
    current_after = service.get_current_year()
    assert current_after["id"] == year2_id


def test_financial_year_close_lock_and_delete(tmp_path):
    db_path = tmp_path / "erp.db"
    service = FinancialYearService(db_path)

    year_id = service.create_year("2025-26", date(2025, 4, 1), date(2026, 3, 31))
    service.lock_year(year_id)
    locked = service.get_year(year_id)
    assert locked is not None
    assert locked["is_locked"] == 1

    try:
        service.close_year(year_id)
    except ValueError as exc:
        assert "Locked financial years cannot be closed" in str(exc)

    try:
        service.open_year(year_id)
    except ValueError as exc:
        assert "Locked financial years cannot be opened" in str(exc)

    # Create a second year whose end date is in the past, then close and reopen it
    second_year_id = service.create_year("2023-24", date(2023, 4, 1), date(2024, 3, 31))
    service.close_year(second_year_id)
    reopened = service.open_year(second_year_id)
    assert reopened["status"] == "Open"
    service.close_year(second_year_id)
    assert service.get_year(second_year_id)["status"] == "Closed"


def test_financial_year_period_overlap_validation(tmp_path):
    db_path = tmp_path / "erp.db"
    service = FinancialYearService(db_path)

    service.create_year("2025-26", date(2025, 4, 1), date(2026, 3, 31))
    try:
        service.create_year("2025-26-dup", date(2026, 1, 1), date(2026, 12, 31))
        assert False, "Expected overlap validation"
    except ValueError as exc:
        assert "overlap" in str(exc).lower()


def test_numbering_series_create_generate_and_preview(tmp_path):
    db_path = tmp_path / "erp.db"
    service = NumberingSeriesService(db_path)

    series_id = service.create_series(
        document_type="Sales Invoice",
        prefix="SI",
        financial_year_label="2026-27",
        padding_length=6,
        start_number=1,
        reset_rule=NumberingSeriesService.RESET_YEARLY,
    )
    series = service.get_series(series_id)
    assert series is not None
    assert series["prefix"] == "SI"

    next_number = service.generate_next("Sales Invoice", {"financial_year_label": "2026-27"})
    assert next_number == "SI-2026-27-000001"

    preview = service.generate_next("Sales Invoice", {"financial_year_label": "2026-27"}, preview=True)
    assert preview == "SI-2026-27-000002"


def test_numbering_series_duplicate_prevention(tmp_path):
    db_path = tmp_path / "erp.db"
    service = NumberingSeriesService(db_path)

    service.create_series(document_type="Purchase Invoice", prefix="PI", financial_year_label="2026-27")
    try:
        service.create_series(document_type="Purchase Invoice", prefix="PI", financial_year_label="2026-27")
        assert False, "Expected duplicate series prevention"
    except ValueError as exc:
        assert "already exists" in str(exc).lower()


def test_numbering_series_reservation_and_cancellation(tmp_path):
    db_path = tmp_path / "erp.db"
    service = NumberingSeriesService(db_path)

    series_id = service.create_series(document_type="Receipt", prefix="RC", financial_year_label="2026-27")
    next_number = service.generate_next("Receipt", {"financial_year_label": "2026-27"})
    assert next_number == "RC-2026-27-000001"

    reservation = service.reserve_number(series_id, "RC-2026-27-000002", reserved_by="tester")
    assert reservation > 0

    service.cancel_reserved_number(reservation)
    cancelled = service.get_reservation(reservation)
    assert cancelled is not None
    assert cancelled["status"] == "cancelled"
