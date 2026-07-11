from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QDateEdit,
    QFrame,
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
from services.financial_year_service import FinancialYearService
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.form_layout_helpers import build_field_section, prepare_form_control
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPGrid


class FinancialYearAdminView(QWidget):
    def __init__(self, config: AppConfig, db_path: Path | None = None) -> None:
        super().__init__()
        self.config = config
        self.service = FinancialYearService(db_path)
        self.current_id = 0
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._form_card())
        root.addWidget(self._table_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Financial Years", "Create, select and manage the fiscal year lifecycle.")
        header.status_label.setText("Ready")
        self.status_label = header.status_label
        return header

    def _form_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.label_input = QLineEdit()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")

        prepare_form_control(self.label_input, minimum_width=240)
        prepare_form_control(self.start_date, minimum_width=140)
        prepare_form_control(self.end_date, minimum_width=140)

        fields = [
            ("Year Label", self.label_input, 240),
            ("Start Date", self.start_date, 140),
            ("End Date", self.end_date, 140),
        ]
        layout.addWidget(build_field_section(fields, spacing=6, margin=0))

        self.action_toolbar = CompactActionToolbar(
            [
                ActionSpec("New", self.clear_form, "Start a new financial year record.", role="positive"),
                ActionSpec("Save Year", self.save_year, "Save the financial year.", role="primary"),
                ActionSpec("Set Current", self.set_current_year, "Make the selected year current."),
                ActionSpec("Open Year", self.open_year, "Reopen the selected closed year."),
                ActionSpec("Close Year", self.close_year, "Close the selected financial year.", role="destructive"),
                ActionSpec("Lock Year", self.lock_year, "Permanently lock the selected year.", role="destructive"),
                ActionSpec("Delete", self.delete_year, "Delete the selected unused year.", role="destructive"),
                ActionSpec("Refresh", self.refresh, "Reload financial years."),
            ]
        )
        self.new_button = self.action_toolbar.button("New")
        self.save_button = self.action_toolbar.button("Save Year")
        self.current_button = self.action_toolbar.button("Set Current")
        self.open_button = self.action_toolbar.button("Open Year")
        self.close_button = self.action_toolbar.button("Close Year")
        self.lock_button = self.action_toolbar.button("Lock Year")
        self.delete_button = self.action_toolbar.button("Delete")
        self.refresh_button = self.action_toolbar.button("Refresh")
        layout.addWidget(self.action_toolbar)
        return frame

    def _field(self, label: str, widget: QWidget) -> QWidget:
        box = QFrame()
        box.setObjectName("fieldBox")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("fieldLabel")
        layout.addWidget(label_widget)
        layout.addWidget(widget)
        return box

    def _table_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.itemSelectionChanged.connect(self._row_selected)
        layout.addWidget(self.table, stretch=1)
        return frame

    def clear_form(self) -> None:
        self.current_id = 0
        self.label_input.clear()
        today = QDate.currentDate()
        self.start_date.setDate(today)
        self.end_date.setDate(today)
        self.status_label.setText("Ready")
        self._update_action_buttons(None)

    def refresh(self) -> None:
        years = self.service.list_years()
        self._populate_table(years)
        self.status_label.setText(f"{len(years)} financial year(s) loaded")
        if years:
            self._select_table_row(0)
        else:
            self.clear_form()

    def _populate_table(self, rows: list[dict[str, object]]) -> None:
        headers = [
            "id",
            "label",
            "start_date",
            "end_date",
            "status",
            "is_current",
            "is_locked",
            "locked_at",
            "created_at",
            "updated_at",
        ]
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([self._pretty(column) for column in headers])
        for row_index, row in enumerate(rows):
            for col_index, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(str(value or ""))
                if header in {"id", "is_current", "is_locked"}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeRowsToContents()

    def _select_table_row(self, row_index: int) -> None:
        if 0 <= row_index < self.table.rowCount():
            self.table.selectRow(row_index)

    def _row_selected(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.clear_form()
            return
        row = selected[0].row()
        item = self.table.item(row, 0)
        if item is None:
            self.clear_form()
            return
        self._load_year(int(item.text()))

    def _load_year(self, year_id: int) -> None:
        year = self.service.get_year(year_id)
        if not year:
            self.clear_form()
            return
        self.current_id = int(year.get("id") or 0)
        self.label_input.setText(str(year.get("label") or ""))
        self.start_date.setDate(QDate.fromString(str(year.get("start_date") or ""), "yyyy-MM-dd"))
        self.end_date.setDate(QDate.fromString(str(year.get("end_date") or ""), "yyyy-MM-dd"))
        self._update_action_buttons(year)
        current_status = "Current" if int(year.get("is_current", 0)) else "Open"
        status_value = str(year.get("status") or "Open")
        if status_value == "Closed":
            current_status = "Closed"
        if int(year.get("is_locked", 0)):
            current_status = "Locked"
        self.status_label.setText(f"Selected: {year.get('label') or ''} ({current_status})")

    def _update_action_buttons(self, year: dict[str, object] | None) -> None:
        has_year = year is not None
        self.save_button.setEnabled(True)
        self.current_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.lock_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        if not has_year:
            return
        locked = int(year.get("is_locked", 0) or 0)
        status = str(year.get("status") or "").lower()
        self.current_button.setEnabled(status == "open" and not locked)
        self.close_button.setEnabled(status == "open" and not locked)
        self.open_button.setEnabled(status == "closed" and not locked)
        self.lock_button.setEnabled(not locked)
        self.delete_button.setEnabled(not locked)
        self.save_button.setEnabled(status != "closed" and not locked)

    def save_year(self) -> None:
        label = self.label_input.text().strip()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        try:
            if self.current_id:
                self.service.update_year(self.current_id, label=label, start_date=start_date, end_date=end_date)
                self.status_label.setText(f"Year updated: {label}")
            else:
                self.service.create_year(label, start_date, end_date)
                self.status_label.setText(f"Year created: {label}")
        except Exception as exc:
            QMessageBox.warning(self, "Financial Years", str(exc))
            return
        self.refresh()

    def set_current_year(self) -> None:
        self._perform_action(self.service.set_current_year, "Set current year")

    def close_year(self) -> None:
        self._perform_action(self.service.close_year, "Close financial year")

    def open_year(self) -> None:
        self._perform_action(self.service.open_year, "Open financial year")

    def lock_year(self) -> None:
        self._perform_action(self.service.lock_year, "Lock financial year")

    def delete_year(self) -> None:
        if QMessageBox.question(self, "Delete Financial Year", "Delete the selected financial year?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self._perform_action(self.service.delete_year, "Delete financial year")

    def _perform_action(self, action: callable, label: str) -> None:
        if not self.current_id:
            QMessageBox.warning(self, "Financial Years", "Select a financial year first.")
            return
        try:
            action(self.current_id)
            self.status_label.setText(f"{label} succeeded.")
        except Exception as exc:
            QMessageBox.warning(self, "Financial Years", str(exc))
            return
        self.refresh()

    @staticmethod
    def _pretty(value: str) -> str:
        return value.replace("_", " ").strip().title()
