from __future__ import annotations

import csv
from pathlib import Path


def read_csv_rows(path: Path, limit: int = 200) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({key: value for key, value in row.items()})
            if len(rows) >= limit:
                break
        return rows
