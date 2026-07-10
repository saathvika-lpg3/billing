from __future__ import annotations

import csv
from pathlib import Path


AUDIT_DIR = Path(r"D:\PRM_GST_DESKTOP\audit")


PHASES = {
    "Foundation": ("developer", "company", "dashboard", "setting", "license", "user", "role", "backup", "financial"),
    "Masters": ("customer", "supplier", "brand", "manufacturer", "doctor", "agent", "project", "category", "unit", "tax", "item"),
    "Sales": ("sale", "quotation", "order", "pos", "kot", "receipt"),
    "Purchase": ("purchase", "payment"),
    "Inventory": ("stock", "warehouse", "batch", "dispatch", "route"),
    "Accounts": ("ledger", "voucher", "journal", "expense", "bank", "cash", "closing", "balance", "profit"),
    "GST / Compliance": ("gst", "gstr", "einvoice", "eway", "itc"),
    "Reports / Print": ("report", "print", "archive", "document", "export"),
    "Industry": ("restaurant", "pharmacy", "prescription", "real_estate", "manufacturing", "production", "bom"),
}


def phase_for(route: str, module: str) -> str:
    haystack = f"{route} {module}".lower()
    for phase, keys in PHASES.items():
        if any(key in haystack for key in keys):
            return phase
    return "Shared / Review"


def desktop_screen(route: str, phase: str) -> str:
    cleaned = route.replace("_", " ").title()
    if route.endswith("_new"):
        return f"{cleaned.replace(' New', '')} Entry"
    if route.endswith("_print"):
        return f"{cleaned.replace(' Print', '')} Print Preview"
    if route.endswith("_cancel"):
        return f"{cleaned.replace(' Cancel', '')} Cancel Action"
    if phase in {"Reports / Print", "GST / Compliance", "Accounts"}:
        return f"{cleaned} Workspace"
    return f"{cleaned} Screen"


def main() -> int:
    route_path = AUDIT_DIR / "portal_routes.csv"
    out_path = AUDIT_DIR / "migration_phase_map.csv"
    rows: list[dict[str, str]] = []
    with route_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            phase = phase_for(row["route"], row.get("module", ""))
            rows.append(
                {
                    "phase": phase,
                    "route": row["route"],
                    "source_module": row.get("module", ""),
                    "source_line": row.get("line", ""),
                    "desktop_screen": desktop_screen(row["route"], phase),
                    "status": "Not migrated",
                }
            )
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["phase", "route", "source_module", "source_line", "desktop_screen", "status"])
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["phase"]] = counts.get(row["phase"], 0) + 1
    summary = AUDIT_DIR / "migration_phase_summary.md"
    lines = ["# Migration Phase Summary", ""]
    for phase, count in sorted(counts.items()):
        lines.append(f"- {phase}: `{count}` routes")
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "A route is marked migrated only after its desktop screen, data access, validation, calculation, print/export behavior, and tests are complete.",
        ]
    )
    summary.write_text("\n".join(lines), encoding="utf-8")
    print(out_path)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
