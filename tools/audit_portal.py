from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MatchRow:
    name: str
    line: int
    snippet: str


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def clean_snippet(value: str) -> str:
    return " ".join(value.strip().split())[:280]


def infer_module(route: str) -> str:
    route = route.lower()
    groups = {
        "Sales": ("sale", "quotation", "order", "pos", "kot"),
        "Purchase": ("purchase",),
        "Inventory": ("item", "stock", "warehouse", "batch", "dispatch", "route"),
        "Accounts": ("receipt", "payment", "ledger", "voucher", "journal", "expense", "bank", "cash"),
        "GST / Compliance": ("gst", "gstr", "einvoice", "eway", "itc"),
        "Administration": ("user", "role", "permission", "company", "license", "developer", "backup", "setting"),
        "Print / Documents": ("print", "archive", "document"),
        "Real Estate": ("real_estate", "property"),
        "Restaurant / Pharmacy": ("restaurant", "pharmacy", "prescription", "doctor", "patient"),
        "Manufacturing": ("manufacturing", "production", "bom"),
    }
    for module, keys in groups.items():
        if any(key in route for key in keys):
            return module
    return "Masters / Common"


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def collect_matches(text: str, pattern: str, group: int = 1) -> list[MatchRow]:
    rows: list[MatchRow] = []
    for match in re.finditer(pattern, text, re.M):
        rows.append(
            MatchRow(
                name=match.group(group),
                line=line_number(text, match.start()),
                snippet=clean_snippet(match.group(0)),
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PRM_GST portal routes and functions.")
    parser.add_argument("--source", default=r"D:\PRM_GST_DESKTOP")
    parser.add_argument("--out", default=r"D:\PRM_GST_DESKTOP\audit")
    args = parser.parse_args()

    source = Path(args.source)
    out = Path(args.out)
    index_path = source / "index.php"
    text = index_path.read_text(encoding="utf-8", errors="ignore")

    routes = collect_matches(text, r"case\s+['\"]([^'\"]+)['\"]\s*:")
    functions = collect_matches(text, r"^function\s+([a-zA-Z0-9_]+)\s*\(")
    layouts = collect_matches(text, r"layout\(\s*['\"]([^'\"]+)['\"]")
    menu_links = collect_matches(text, r"index\.php\?p=([a-zA-Z0-9_]+)")

    write_csv(
        out / "portal_routes.csv",
        ["route", "module", "line", "snippet"],
        [[row.name, infer_module(row.name), row.line, row.snippet] for row in routes],
    )
    write_csv(
        out / "portal_functions.csv",
        ["function", "module", "line", "snippet"],
        [[row.name, infer_module(row.name), row.line, row.snippet] for row in functions],
    )
    write_csv(
        out / "portal_layouts.csv",
        ["layout_title", "line", "snippet"],
        [[row.name, row.line, row.snippet] for row in layouts],
    )
    write_csv(
        out / "portal_menu_links.csv",
        ["route", "module", "line", "snippet"],
        [[row.name, infer_module(row.name), row.line, row.snippet] for row in menu_links],
    )

    source_files = sorted(
        p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in {".php", ".js", ".css", ".json", ".md", ".txt"}
    )
    write_csv(
        out / "portal_files.csv",
        ["relative_path", "extension", "size_bytes"],
        [[str(p.relative_to(source)), p.suffix.lower(), p.stat().st_size] for p in source_files],
    )

    summary = out / "portal_audit_summary.md"
    summary.write_text(
        "\n".join(
            [
                "# PRM_GST Portal Audit Summary",
                "",
                f"- Source folder: `{source}`",
                f"- Main portal file: `{index_path}`",
                f"- Main portal size bytes: `{index_path.stat().st_size}`",
                f"- Routes found: `{len(routes)}`",
                f"- PHP functions found: `{len(functions)}`",
                f"- Layout calls found: `{len(layouts)}`",
                f"- Menu/link route references found: `{len(menu_links)}`",
                f"- Source files indexed: `{len(source_files)}`",
                "",
                "## Next Action",
                "",
                "Use `portal_routes.csv` and `portal_functions.csv` to drive the desktop module migration backlog.",
            ]
        ),
        encoding="utf-8",
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
