from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sqlite_schema_audit_uses_stdlib_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "audit.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        conn.execute("CREATE INDEX idx_customers_name ON customers(name)")
        conn.execute("INSERT INTO customers (name) VALUES ('ACME')")

    out_dir = tmp_path / "audit"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "audit_mysql_schema.py"),
            "--database",
            str(db_path),
            "--out",
            str(out_dir),
        ],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert (out_dir / "sqlite_schema_summary.md").exists()
    assert "customers\tnot_collected" in (out_dir / "sqlite_tables.tsv").read_text(encoding="utf-8")
    columns = (out_dir / "sqlite_columns.tsv").read_text(encoding="utf-8")
    assert "customers\tid\tINTEGER\tYES\t\tPRI" in columns
    assert "customers\tname\tTEXT\tNO" in columns
    assert "idx_customers_name" in (out_dir / "sqlite_indexes.tsv").read_text(encoding="utf-8")


def test_operation_parity_accepts_profit_loss_alias() -> None:
    from tools.audit_operation_parity import CURRENT, EXPECTED, LABEL_ALIASES

    current_labels = [operation.label for operation in CURRENT["Accounts"]]
    aliases = LABEL_ALIASES["Accounts"]
    missing = [
        label
        for label in EXPECTED["Accounts"]
        if label not in current_labels and aliases.get(label) not in current_labels
    ]

    assert "ERP Profit & Loss" not in missing
    assert "Profit & Loss" in current_labels


def test_live_ui_audit_inventory_has_release_gate_fields() -> None:
    import tools.audit_live_ui as live_ui_audit

    expected = {
        "menu_route",
        "view_class",
        "view_file",
        "shared_framework",
        "header_implementation",
        "toolbar_implementation",
        "layout_type",
        "action_buttons",
        "signal_slot_wiring",
        "keyboard_shortcuts",
        "save_handler",
        "error_handling",
        "test_coverage",
        "screen_fit",
        "known_issue",
    }

    assert live_ui_audit.TARGET_SIZES == ((1366, 768), (1440, 900), (1920, 1080))
    assert set(live_ui_audit.INVENTORY_FIELDS) == expected
    source = (ROOT / "tools" / "audit_live_ui.py").read_text(encoding="utf-8")
    for field in expected:
        assert f'"{field}"' in source
    assert "_vertical_toolbar_stacks" in source
    assert "_grand_total_visible" in source


def test_legacy_mysql_migration_utility_imports_and_keeps_connection_roles_distinct() -> None:
    import inspect

    from tools.migrate_mysql_to_sqlite import migrate_table, sqlite_type

    assert list(inspect.signature(migrate_table).parameters) == ["mysql_conn", "sqlite_conn", "table"]
    assert sqlite_type("bigint unsigned") == "INTEGER"
    assert sqlite_type("decimal(12,2)") == "REAL"
    assert sqlite_type("varchar(80)") == "TEXT"


def test_widget_api_audit_has_no_typed_control_method_mismatches() -> None:
    from tools.audit_widget_apis import audit

    assert audit() == []
