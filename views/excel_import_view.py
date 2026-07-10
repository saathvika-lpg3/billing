from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.import_service import ImportService
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPToolbar, ERPGrid

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover - guarded for packaged environments
    load_workbook = None


class ExcelImportView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.import_service = ImportService()
        self.selected_path: Path | None = None
        self.all_rows: list[dict[str, str]] = []
        self.preview_rows: list[dict[str, str]] = []
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._control_card())
        root.addWidget(self._table_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Excel Import", "Stage product, customer, supplier and stock imports before posting")
        header.setMaximumHeight(58)
        header.status_label.setText("No file selected")
        self.status_label = header.status_label
        return header

    def _control_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMaximumHeight(68)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(6)
        self.import_type = QComboBox()
        self.import_type.addItems(["Products", "Product Packs", "Customers", "Suppliers", "Opening Stock", "Schemes"])
        self.path_box = QLineEdit()
        self.path_box.setPlaceholderText("Choose CSV / Excel file")
        toolbar = ERPToolbar(
            [
                ("Choose File", self.choose_file),
                ("Save Import Draft", self.save_import_draft),
                ("Post Import", self.post_import),
            ]
        )
        layout.addWidget(ERPFieldBox("Import Type", self.import_type))
        layout.addWidget(ERPFieldBox("Import File", self.path_box), stretch=1)
        layout.addWidget(toolbar)
        return frame

    def _table_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self._show_status("Choose a CSV file to preview the first rows. Excel files are staged for import validation.")
        return frame

    def choose_file(self) -> None:
        path_text, _ = QFileDialog.getOpenFileName(self, "Choose Import File", str(self.config.project_root), "Import Files (*.csv *.xlsx *.xls)")
        if not path_text:
            return
        self.selected_path = Path(path_text)
        self.path_box.setText(path_text)
        if self.selected_path.suffix.lower() == ".csv":
            self._preview_csv(self.selected_path)
        else:
            self._preview_excel(self.selected_path)
        self.status_label.setText(self.selected_path.name)

    def save_import_draft(self) -> None:
        if not self.selected_path:
            QMessageBox.warning(self, "Excel Import", "Choose an import file first.")
            return
        payload = {
            "source": "desktop_excel_import",
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "import_type": self.import_type.currentText(),
            "file_path": str(self.selected_path),
            "preview_rows": self.preview_rows[:25],
            "row_count": len(self.all_rows),
        }
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        path = drafts_dir / f"excel_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Excel Import", f"Import draft saved:\n{path}")

    def post_import(self) -> None:
        if not self.selected_path:
            QMessageBox.warning(self, "Excel Import", "Choose an import file first.")
            return
        if not self.all_rows:
            QMessageBox.warning(self, "Excel Import", "No import rows are available to post.")
            return
        try:
            result = self.import_service.post_rows(self.import_type.currentText(), self.all_rows)
        except Exception as exc:
            QMessageBox.warning(self, "Excel Import", f"Import could not be posted:\n{exc}")
            return
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        audit_path = drafts_dir / f"excel_import_posted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        audit_path.write_text(
            json.dumps(
                {
                    "source": "desktop_excel_import_post",
                    "saved_at": datetime.now().isoformat(timespec="seconds"),
                    "import_type": self.import_type.currentText(),
                    "file_path": str(self.selected_path),
                    "row_count": len(self.all_rows),
                    "result": result,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        QMessageBox.information(
            self,
            "Excel Import",
            f"Import posted.\nInserted: {result['inserted']}\nUpdated: {result['updated']}\nSkipped: {result['skipped']}\nAudit copy:\n{audit_path}",
        )

    def _preview_csv(self, path: Path) -> None:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            self.all_rows = [dict(row) for row in reader]
            self.preview_rows = self.all_rows[:50]
        self._render_preview()

    def _preview_excel(self, path: Path) -> None:
        if load_workbook is None:
            self.all_rows = []
            self.preview_rows = []
            self._show_status("Excel support is not installed in this Python environment.")
            return
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet = workbook.active
        values = list(sheet.iter_rows(values_only=True))
        if not values:
            self.all_rows = []
            self.preview_rows = []
            self._show_status("Excel file is empty.")
            return
        headers = [str(value or "").strip() for value in values[0]]
        rows: list[dict[str, str]] = []
        for raw in values[1:]:
            row = {headers[index]: "" if value is None else str(value) for index, value in enumerate(raw) if index < len(headers) and headers[index]}
            if any(str(value).strip() for value in row.values()):
                rows.append(row)
        self.all_rows = rows
        self.preview_rows = rows[:50]
        self._render_preview()

    def _render_preview(self) -> None:
        if not self.preview_rows:
            self._show_status("CSV file is empty or has no headers.")
            return
        headers = list(self.preview_rows[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(self.preview_rows))
        self.table.setHorizontalHeaderLabels(headers)
        for row_index, row in enumerate(self.preview_rows):
            for column_index, header in enumerate(headers):
                self.table.setItem(row_index, column_index, QTableWidgetItem(row.get(header, "")))
        self.table.resizeRowsToContents()

    def _show_status(self, message: str) -> None:
        self.table.setColumnCount(1)
        self.table.setRowCount(1)
        self.table.setHorizontalHeaderLabels(["Status"])
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 0, item)
