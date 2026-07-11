from __future__ import annotations

from decimal import Decimal

from views.report_center_view import ReportCenterView


def test_dispatch_totals_never_sum_record_ids() -> None:
    headers = ["id", "challan_no", "total_qty", "total_value"]
    rows = [
        {"id": 1001, "challan_no": "DC-1", "total_qty": 5.0, "total_value": Decimal("250.00")},
        {"id": 1002, "challan_no": "DC-2", "total_qty": 7.0, "total_value": Decimal("350.00")},
    ]

    numeric = ReportCenterView._numeric_total_headers(rows, headers)
    assert numeric == ["total_qty", "total_value"]
    assert "id" not in numeric
