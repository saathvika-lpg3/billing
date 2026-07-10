from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


SQLITE_EXE = Path(r"C:\xampp\sqlite\bin\sqlite.exe")


def run_sqlite(sql: str) -> list[list[str]]:
    if not SQLITE_EXE.exists():
        raise FileNotFoundError(f"SQLite client not found: {SQLITE_EXE}")
    result = subprocess.run(
        [str(SQLITE_EXE), "-uroot", "-N", "-B", "-e", sql],
        text=True,
        capture_output=True,
        check=True,
    )
    rows: list[list[str]] = []
    for line in result.stdout.splitlines():
        rows.append(line.split("\t"))
    return rows


def write_tsv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PRM_GST SQLite schema.")
    parser.add_argument("--database", default="prm_gst")
    parser.add_argument("--out", default=r"D:\PRM_GST_DESKTOP\audit")
    args = parser.parse_args()
    out = Path(args.out)
    db = args.database

    tables = run_sqlite(
        f"""
        SELECT TABLE_NAME, COALESCE(TABLE_ROWS,0)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA='{db}'
        ORDER BY TABLE_NAME
        """
    )
    columns = run_sqlite(
        f"""
        SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COALESCE(COLUMN_DEFAULT,''), COLUMN_KEY, EXTRA
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA='{db}'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
    )
    indexes = run_sqlite(
        f"""
        SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA='{db}'
        ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
        """
    )

    write_tsv(out / "sqlite_tables.tsv", ["table", "estimated_rows"], tables)
    write_tsv(
        out / "sqlite_columns.tsv",
        ["table", "column", "type", "nullable", "default", "key", "extra"],
        columns,
    )
    write_tsv(
        out / "sqlite_indexes.tsv",
        ["table", "index", "non_unique", "seq", "column"],
        indexes,
    )

    summary = out / "sqlite_schema_summary.md"
    summary.write_text(
        "\n".join(
            [
                "# PRM_GST SQLite Schema Summary",
                "",
                f"- Database: `{db}`",
                f"- Tables: `{len(tables)}`",
                f"- Columns: `{len(columns)}`",
                f"- Index column entries: `{len(indexes)}`",
                "",
                "## Largest / Most Important Table Groups",
                "",
                "- Sales: `sales`, `sales_items`, `sales_returns`, `sales_return_items`",
                "- Purchase: `purchases`, `purchase_items`, `purchase_returns`, `purchase_return_items`",
                "- Inventory: `items`, `product_packs`, `warehouse_stock`, `stock_log`, `stock_transfers`, `stock_outs`",
                "- Accounts: `voucher_headers`, `voucher_lines`, `ledger_postings`, `account_ledgers`, `ledger_groups`",
                "- GST: `gst_postings`, `gst_return_filings`, `gst_adjustments`, `einvoices`, `eway_bills`",
                "- Printing: `print_templates`, `print_logs`, `print_batches`, `document_archive_logs`",
            ]
        ),
        encoding="utf-8",
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
