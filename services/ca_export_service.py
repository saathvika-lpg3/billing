from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook


def _safe_name(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "ca_export")).strip("_")
    return text[:80] or "ca_export"


def _iso_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class CaExportService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def prepare_export(
        self,
        closing_period: dict[str, Any],
        output_dir: Path,
        export_format: str,
        ca_email: str = "",
        itr_form: str = "",
        assessment_year: str = "",
        schema_version: str = "inventory",
    ) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        identifier = _safe_name(closing_period.get("period_label") or closing_period.get("id") or "period")
        file_name = f"ca_export_{identifier}_{_iso_timestamp()}"
        if export_format.lower() == "json":
            output_path = output_dir / f"{file_name}.json"
            self._write_json(output_path, closing_period, ca_email, itr_form, assessment_year, schema_version)
        else:
            output_path = output_dir / f"{file_name}.xlsx"
            self._write_excel(output_path, closing_period, ca_email, itr_form, assessment_year, schema_version)
        self._record_export(closing_period, output_path, export_format, ca_email, itr_form, assessment_year, schema_version)
        return {
            "file_path": str(output_path),
            "export_format": export_format,
            "ca_email": ca_email,
            "assessment_year": assessment_year,
            "itr_form": itr_form,
            "schema_version": schema_version,
        }

    def _write_json(
        self,
        path: Path,
        closing_period: dict[str, Any],
        ca_email: str,
        itr_form: str,
        assessment_year: str,
        schema_version: str,
    ) -> None:
        payload = {
            "schema_version": schema_version,
            "prepared_at": datetime.now().isoformat(timespec="seconds"),
            "assessment_year": assessment_year,
            "itr_form": itr_form,
            "ca_email": ca_email,
            "closing_period": {key: closing_period.get(key) for key in sorted(closing_period.keys())},
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _write_excel(
        self,
        path: Path,
        closing_period: dict[str, Any],
        ca_email: str,
        itr_form: str,
        assessment_year: str,
        schema_version: str,
    ) -> None:
        workbook = Workbook()
        summary = workbook.active
        summary.title = "Summary"
        summary.append(["Field", "Value"])
        summary.append(["Schema Version", schema_version])
        summary.append(["Prepared At", datetime.now().isoformat(timespec="seconds")])
        summary.append(["Assessment Year", assessment_year])
        summary.append(["ITR/Schema", itr_form])
        summary.append(["CA Email", ca_email])
        summary.append([])
        summary.append(["Closing Period Field", "Value"])
        for key in sorted(closing_period.keys()):
            summary.append([key, closing_period.get(key)])
        workbook.save(path)

    def _record_export(
        self,
        closing_period: dict[str, Any],
        output_path: Path,
        export_format: str,
        ca_email: str,
        itr_form: str,
        assessment_year: str,
        schema_version: str,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO ca_export_logs(company_id,company_name,financial_year_id,financial_year_label,closing_period_id,closing_type,from_date,to_date,ca_email,export_format,file_path,email_status,email_message,created_by,created_by_name,created_at,itr_form,assessment_year,schema_version,close_decision) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        closing_period.get("company_id"),
                        closing_period.get("company_name"),
                        closing_period.get("financial_year_id"),
                        closing_period.get("financial_year_label"),
                        closing_period.get("id"),
                        closing_period.get("closing_type"),
                        closing_period.get("from_date"),
                        closing_period.get("to_date"),
                        ca_email,
                        export_format,
                        str(output_path),
                        "Prepared",
                        "Export created by desktop CA Export",
                        None,
                        None,
                        now,
                        itr_form,
                        assessment_year,
                        schema_version,
                        None,
                    ),
                )
                conn.commit()
            except sqlite3.OperationalError:
                # If the table does not exist, skip logging but preserve export file.
                pass
