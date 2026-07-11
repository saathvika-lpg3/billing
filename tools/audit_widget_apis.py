from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAN_FOLDERS = ("views", "widgets", "controllers")
WIDGET_TYPES = {
    "QLineEdit",
    "QTextEdit",
    "QPlainTextEdit",
    "QComboBox",
    "QSpinBox",
    "QDoubleSpinBox",
    "QDateEdit",
    "QDateTimeEdit",
    "QTimeEdit",
    "QCheckBox",
    "QRadioButton",
}
INVALID_METHODS = {
    "QComboBox": {
        "text",
        "setText",
        "toPlainText",
        "setPlainText",
        "value",
        "setValue",
        "isChecked",
        "setChecked",
    },
    "QLineEdit": {
        "currentText",
        "currentData",
        "setCurrentText",
        "setCurrentIndex",
        "toPlainText",
        "setPlainText",
        "value",
        "setValue",
        "isChecked",
        "setChecked",
    },
    "QTextEdit": {"currentText", "currentData", "value", "isChecked"},
    "QPlainTextEdit": {"currentText", "currentData", "setText", "value", "isChecked"},
    "QSpinBox": {"currentText", "currentData", "toPlainText", "isChecked"},
    "QDoubleSpinBox": {"currentText", "currentData", "toPlainText", "isChecked"},
    "QDateEdit": {"currentText", "currentData", "toPlainText", "isChecked"},
    "QDateTimeEdit": {"currentText", "currentData", "toPlainText", "isChecked"},
    "QTimeEdit": {"currentText", "currentData", "toPlainText", "isChecked"},
    "QCheckBox": {"currentText", "currentData", "toPlainText", "value", "setValue"},
    "QRadioButton": {"currentText", "currentData", "toPlainText", "value", "setValue"},
}


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    control: str
    widget_type: str
    method: str


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _self_control(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return node.attr
    return ""


def scan_file(path: Path) -> list[Finding]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    control_types: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        widget_type = _call_name(value.func)
        if widget_type not in WIDGET_TYPES:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            control = _self_control(target)
            if control:
                control_types.setdefault(control, set()).add(widget_type)

    findings: list[Finding] = []
    relative = path.relative_to(PROJECT_ROOT).as_posix()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        control = _self_control(node.func.value)
        if not control:
            continue
        method = node.func.attr
        for widget_type in sorted(control_types.get(control, ())):
            if method in INVALID_METHODS.get(widget_type, set()):
                findings.append(Finding(relative, node.lineno, f"self.{control}", widget_type, method))
    return findings


def audit() -> list[Finding]:
    findings: list[Finding] = []
    for folder in SCAN_FOLDERS:
        for path in sorted((PROJECT_ROOT / folder).rglob("*.py")):
            findings.extend(scan_file(path))
    return sorted(findings, key=lambda item: (item.file, item.line, item.control, item.method))


def write_outputs(findings: list[Finding]) -> tuple[Path, Path]:
    output_dir = PROJECT_ROOT / "audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "widget_api_audit.json"
    md_path = output_dir / "widget_api_audit.md"
    json_path.write_text(json.dumps([asdict(item) for item in findings], indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Widget API Audit",
        "",
        "Static AST audit of controls assigned to `self.*` in live view, widget and controller sources.",
        "",
        f"- Files scanned: {sum(1 for folder in SCAN_FOLDERS for _ in (PROJECT_ROOT / folder).rglob('*.py'))}",
        f"- Unsafe typed widget-method calls: {len(findings)}",
        "",
    ]
    if findings:
        lines.extend(["| File | Line | Control | Declared type | Invalid method |", "|---|---:|---|---|---|"])
        for item in findings:
            lines.append(f"| {item.file} | {item.line} | `{item.control}` | {item.widget_type} | `{item.method}()` |")
    else:
        lines.append("Result: **PASS** - no typed widget API mismatch was detected.")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    findings = audit()
    for path in write_outputs(findings):
        print(path)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
