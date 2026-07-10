from __future__ import annotations

import argparse
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pysqlite


SQLITE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "prm_gst",
    "charset": "utf8mb4",
    "cursorclass": pysqlite.cursors.DictCursor,
}


def sqlite_type(sqlite_type: str) -> str:
    lower = sqlite_type.lower()
    if "int" in lower:
        return "INTEGER"
    if any(token in lower for token in ["decimal", "double", "float"]):
        return "REAL"
    if any(token in lower for token in ["date", "time", "year"]):
        return "TEXT"
    if any(token in lower for token in ["text", "char", "enum", "set", "json"]):
        return "TEXT"
    return "TEXT"


def clean_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def create_table(sqlite_conn: sqlite3.Connection, table: str, columns: list[dict[str, Any]]) -> None:
    parts = []
    for column in columns:
        name = column["Field"]
        col_type = sqlite_type(column["Type"])
        if column["Key"] == "PRI" and col_type == "INTEGER":
            parts.append(f"{quote(name)} INTEGER PRIMARY KEY")
        elif column["Key"] == "PRI":
            parts.append(f"{quote(name)} {col_type} PRIMARY KEY")
        else:
            parts.append(f"{quote(name)} {col_type}")
    sqlite_conn.execute(f"DROP TABLE IF EXISTS {quote(table)}")
    sqlite_conn.execute(f"CREATE TABLE {quote(table)} ({', '.join(parts)})")


def migrate_table(sqlite_conn, sqlite_conn: sqlite3.Connection, table: str) -> int:
    with sqlite_conn.cursor() as cur:
        cur.execute(f"DESCRIBE `{table}`")
        columns = list(cur.fetchall())
        create_table(sqlite_conn, table, columns)
        names = [column["Field"] for column in columns]
        cur.execute(f"SELECT * FROM `{table}`")
        rows = list(cur.fetchall())
    if not rows:
        return 0
    placeholders = ", ".join(["?"] * len(names))
    columns_sql = ", ".join(quote(name) for name in names)
    insert_sql = f"INSERT INTO {quote(table)} ({columns_sql}) VALUES ({placeholders})"
    values = [[clean_value(row.get(name)) for name in names] for row in rows]
    sqlite_conn.executemany(insert_sql, values)
    return len(rows)


def migrate(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pysqlite.connect(**SQLITE_CONFIG) as sqlite_conn, sqlite3.connect(output_path) as sqlite_conn:
        with sqlite_conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            table_key = f"Tables_in_{SQLITE_CONFIG['database']}"
            tables = [row[table_key] for row in cur.fetchall()]
        sqlite_conn.execute("PRAGMA journal_mode=WAL")
        sqlite_conn.execute("PRAGMA foreign_keys=OFF")
        total = 0
        for table in tables:
            count = migrate_table(sqlite_conn, sqlite_conn, table)
            total += count
            print(f"{table}: {count}")
        sqlite_conn.execute(
            "CREATE TABLE IF NOT EXISTS migration_meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        sqlite_conn.execute(
            "INSERT OR REPLACE INTO migration_meta (key, value) VALUES (?, ?)",
            ("migrated_at", datetime.now().isoformat(timespec="seconds")),
        )
        sqlite_conn.execute(
            "INSERT OR REPLACE INTO migration_meta (key, value) VALUES (?, ?)",
            ("source_database", SQLITE_CONFIG["database"]),
        )
        sqlite_conn.commit()
        print(f"migrated_tables={len(tables)} migrated_rows={total} output={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy PRM_GST SQLite data into local desktop SQLite database.")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / "database" / "prm_billing_inventory.db"),
    )
    args = parser.parse_args()
    migrate(Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
