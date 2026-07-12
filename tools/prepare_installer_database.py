from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


# Product-owned reference/configuration rows that are safe and useful on a new
# client installation. All customer, transaction, credential, activation,
# communication-log, and runtime-setting tables intentionally remain empty.
REFERENCE_TABLES = (
    "account_ledgers",
    "app_release_versions",
    "ca_json_templates",
    "communication_templates",
    "dev_business_types",
    "dev_invoice_templates",
    "dev_modules",
    "dev_subscription_plans",
    "ledger_groups",
    "migration_meta",
    "print_template_families",
    "print_templates",
    "role_permissions",
    "schema_migrations",
    "tax_codes",
    "tax_slabs",
    "units",
    "uoms",
    "voucher_approval_rules",
    "voucher_types",
)


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _schema_objects(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT type,name,tbl_name,sql
        FROM sqlite_master
        WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'
        ORDER BY CASE type
            WHEN 'table' THEN 0
            WHEN 'view' THEN 1
            WHEN 'index' THEN 2
            WHEN 'trigger' THEN 3
            ELSE 4 END,
            name
        """
    ).fetchall()


def _copy_table(source: sqlite3.Connection, target: sqlite3.Connection, table: str) -> int:
    columns = [str(row[1]) for row in source.execute(f"PRAGMA table_info({_quote(table)})")]
    if not columns:
        return 0
    rows = source.execute(f"SELECT * FROM {_quote(table)}").fetchall()
    if not rows:
        return 0
    column_sql = ",".join(_quote(column) for column in columns)
    placeholders = ",".join("?" for _ in columns)
    target.executemany(
        f"INSERT INTO {_quote(table)} ({column_sql}) VALUES ({placeholders})",
        [tuple(row) for row in rows],
    )
    return len(rows)


def build_installer_database(source_path: Path, output_path: Path) -> dict[str, Any]:
    source_path = Path(source_path).resolve()
    output_path = Path(output_path).resolve()
    if source_path == output_path:
        raise ValueError("Installer seed output must be different from the source database.")
    if not source_path.is_file():
        raise FileNotFoundError(f"Source database was not found: {source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    source_uri = f"file:{source_path.as_posix()}?mode=ro"
    copied: dict[str, int] = {}
    with sqlite3.connect(source_uri, uri=True) as source, sqlite3.connect(output_path) as target:
        source.row_factory = sqlite3.Row
        objects = _schema_objects(source)
        target.execute("PRAGMA foreign_keys=OFF")

        for row in objects:
            if row["type"] == "table":
                target.execute(str(row["sql"]))

        available_tables = {str(row["name"]) for row in objects if row["type"] == "table"}
        for table in REFERENCE_TABLES:
            if table in available_tables:
                copied[table] = _copy_table(source, target, table)

        for object_type in ("view", "index", "trigger"):
            for row in objects:
                if row["type"] == object_type:
                    target.execute(str(row["sql"]))

        user_version = int(source.execute("PRAGMA user_version").fetchone()[0])
        target.execute(f"PRAGMA user_version={user_version}")
        target.commit()

        integrity = str(target.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity.lower() != "ok":
            raise RuntimeError(f"Installer seed integrity check failed: {integrity}")

        non_reference_rows: dict[str, int] = {}
        for table in sorted(available_tables - set(REFERENCE_TABLES)):
            count = int(target.execute(f"SELECT COUNT(*) FROM {_quote(table)}").fetchone()[0])
            if count:
                non_reference_rows[table] = count
        if non_reference_rows:
            raise RuntimeError(
                "Installer seed unexpectedly contains runtime/client rows: "
                + json.dumps(non_reference_rows, sort_keys=True)
            )

        activation_count = int(target.execute("SELECT COUNT(*) FROM license_activation").fetchone()[0])
        client_license_count = int(target.execute("SELECT COUNT(*) FROM license").fetchone()[0])
        user_count = int(target.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        transaction_count = sum(
            int(target.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("sales", "purchases", "receipts", "payments", "ledger_postings", "gst_postings")
        )

    return {
        "output": str(output_path),
        "integrity": integrity,
        "reference_rows": copied,
        "license_activation_rows": activation_count,
        "license_rows": client_license_count,
        "user_rows": user_count,
        "transaction_rows": transaction_count,
    }


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Create a client-safe SQLite seed for the desktop installer.")
    parser.add_argument(
        "--source",
        type=Path,
        default=project_root / "database" / "prm_billing_inventory_seed.db",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "build" / "installer_payload" / "database" / "prm_billing_inventory.db",
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    result = build_installer_database(args.source, args.output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
