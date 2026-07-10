from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "database" / "prm_billing_inventory.db"


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def resolve_database(value: str) -> Path:
    candidate = Path(value)
    if candidate.exists():
        return candidate
    project_candidate = ROOT / value
    if project_candidate.exists():
        return project_candidate
    if value == "prm_gst" and DEFAULT_DATABASE.exists():
        return DEFAULT_DATABASE
    raise FileNotFoundError(
        f"SQLite database not found: {value}. Pass --database with a valid .db path."
    )


def audit_tables(conn: sqlite3.Connection, *, include_row_counts: bool = False) -> list[list[str]]:
    rows: list[list[str]] = []
    tables = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    for (table,) in tables:
        count = "not_collected"
        if include_row_counts:
            count = str(conn.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}").fetchone()[0])
        rows.append([table, count])
    return rows


def audit_columns(conn: sqlite3.Connection, tables: list[list[str]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for table, _count in tables:
        for column in conn.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall():
            _cid, name, col_type, not_null, default, pk = column
            rows.append(
                [
                    table,
                    name,
                    col_type or "",
                    "NO" if not_null else "YES",
                    "" if default is None else str(default),
                    "PRI" if pk else "",
                    "",
                ]
            )
    return rows


def audit_indexes(conn: sqlite3.Connection, tables: list[list[str]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for table, _count in tables:
        for index in conn.execute(f"PRAGMA index_list({quote_identifier(table)})").fetchall():
            _seq, index_name, unique, _origin, _partial = index
            non_unique = "0" if unique else "1"
            for index_col in conn.execute(f"PRAGMA index_info({quote_identifier(index_name)})").fetchall():
                _col_seq, seq_in_index, column_name = index_col
                rows.append([table, index_name, non_unique, str(seq_in_index + 1), column_name])
    return rows


def write_tsv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PRM_GST SQLite schema.")
    parser.add_argument("--database", default=str(DEFAULT_DATABASE))
    parser.add_argument("--out", default=r"D:\PRM_GST_DESKTOP\audit")
    parser.add_argument(
        "--include-row-counts",
        action="store_true",
        help="Include live table row counts. Keep disabled for shareable repository artifacts.",
    )
    args = parser.parse_args()
    out = Path(args.out)
    db = resolve_database(args.database)

    with sqlite3.connect(db) as conn:
        tables = audit_tables(conn, include_row_counts=args.include_row_counts)
        columns = audit_columns(conn, tables)
        indexes = audit_indexes(conn, tables)

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
