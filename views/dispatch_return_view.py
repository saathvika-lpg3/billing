from __future__ import annotations

from datetime import datetime
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QCompleter,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.mysql_source import MySqlSource
from services.pdf_print import write_report_pdf
from services.print_preview import show_print_preview
from services.share_service import (
    communication_message,
    document_message_context,
    open_whatsapp_share,
    pdf_share_note,
    prepare_email_document,
    prepare_whatsapp_document,
)
from services.transaction_repository import TransactionRepository
from widgets.erp_components import (
    BottomTotalsCard,
    DocumentCard,
    ERPFieldBox,
    ERPItemGrid,
    ERPTransactionGrid,
    GridActionBar,
    TransactionHeader,
    TransactionPageLayout,
    TransactionSectionCard,
    TransactionToolbar,
)


class DispatchReturnView(QWidget):
    editable_columns = {5, 6, 8, 9}

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.repository = TransactionRepository()
        self.source_rows: list[dict[str, Any]] = []
        self.source_by_label: dict[str, dict[str, Any]] = {}
        self.lines: list[dict[str, Any]] = []
        self._updating = False
        self._build()
        self.refresh_sources()
        self._register_hotkeys()

    def _build(self) -> None:
        page = TransactionPageLayout(self)
        page.add_header(self._title_bar())
        page.add_toolbar(self._action_toolbar())
        page.add_section(self._source_card())
        page.add_grid(self._table_card())
        page.add_summary(self._summary_card())

    def _title_bar(self) -> QWidget:
        header = TransactionHeader(
            "Dispatch Return",
            "Record returned route stock with accepted/damaged quantity and linked credit note where applicable",
            self,
        )
        self.source_status = header.status_label
        return header

    def _action_toolbar(self) -> QWidget:
        return TransactionToolbar(
            [
                ("New", self.clear_form),
                ("Save", self.save_return),
                ("Preview", self.print_return_pdf),
                ("Print", self.print_return_pdf),
                ("PDF", self.print_return_pdf),
                ("WhatsApp", self.share_return_whatsapp),
                ("Email", self.email_return_pdf),
                ("Close", self.close),
            ],
            self,
        )

    def _source_card(self) -> QWidget:
        frame = DocumentCard()
        frame.setMinimumHeight(112)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(6)

        self.source_type = QComboBox()
        self.source_type.addItems(["Sales Bills", "Load Challans"])
        self.source_type.currentIndexChanged.connect(self.refresh_sources)
        self.source_doc = QComboBox()
        self.source_doc.setEditable(True)
        self.source_doc.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.return_no = QLineEdit()
        self.return_date = QDateEdit()
        self.return_date.setCalendarPopup(True)
        self.return_date.setDate(QDate.currentDate())
        self.reason = QLineEdit("Returned from dispatch")
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Optional remarks")
        load_button = QPushButton("Show Items")
        load_button.clicked.connect(self.load_items)

        grid.addWidget(self._field("Source", self.source_type, 140), 0, 0)
        grid.addWidget(self._field("Document", self.source_doc, 360), 0, 1, 1, 3)
        grid.addWidget(self._field("Return No", self.return_no, 150), 0, 4)
        grid.addWidget(self._field("Return Date", self.return_date, 130), 0, 5)
        grid.addWidget(load_button, 0, 6)
        grid.addWidget(self._field("Reason", self.reason, 300), 1, 0, 1, 3)
        grid.addWidget(self._field("Remarks", self.notes, 420), 1, 3, 1, 4)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 2)
        return frame

    def _field(self, label: str, widget: QWidget, width: int) -> QWidget:
        if isinstance(widget, QTextEdit):
            widget.setMinimumHeight(40)
            widget.setMaximumHeight(56)
        else:
            widget.setFixedHeight(28)
        widget.setMinimumWidth(min(width, 120))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if isinstance(widget, QComboBox):
            widget.setMaxVisibleItems(18)
            widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 8))
            completer = widget.completer()
            if completer:
                completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
        return ERPFieldBox(label, widget, self)

    def _table_card(self) -> QWidget:
        frame = TransactionSectionCard("items")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(
            GridActionBar(
                {
                    "add_row": self.load_items,
                    "delete_row": None,
                    "import": None,
                    "scan_barcode": lambda: self.source_doc.setFocus(),
                },
                self,
            )
        )
        hint = QLabel("Enter Return Qty and Damaged Qty. Accepted Qty is calculated as Return Qty minus Damaged Qty.")
        hint.setObjectName("caption")
        layout.addWidget(hint)
        headers = ["#", "Item", "Dispatched", "Returned", "Balance", "Return Qty", "Damaged", "Accepted", "SCH Return", "Remarks"]
        self.table = ERPItemGrid(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 360)
        # editable: Return Qty, Damaged, SCH Return, Remarks
        self.table.set_editable_columns({5, 6, 8, 9})
        self.table.itemChanged.connect(self._line_changed)
        self.table.set_command_handlers(
            {
                "product_search": lambda: self.source_doc.setFocus(),
                "save": self.save_return,
            }
        )
        layout.addWidget(self.table)
        return frame

    def _summary_card(self) -> QWidget:
        frame = BottomTotalsCard()
        frame.setMaximumHeight(52)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 5, 8, 5)
        self.row_count = QLabel("Rows: 0")
        self.total_returned = QLabel("Returned: 0.000")
        self.total_accepted = QLabel("Accepted: 0.000")
        self.total_damaged = QLabel("Damaged: 0.000")
        self.total_accepted.setObjectName("metricValue")
        for widget in [self.row_count, self.total_returned, self.total_accepted, self.total_damaged]:
            layout.addWidget(widget)
        layout.addStretch(1)
        return frame

    def refresh_sources(self) -> None:
        source_table = self._source_table()
        try:
            self.source_rows = self.source.dispatch_return_sources(source_table, 300)
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            return
        labels = [self._source_label(row) for row in self.source_rows]
        self.source_by_label = dict(zip(labels, self.source_rows))
        self.source_doc.clear()
        self.source_doc.addItems(["Choose dispatch document", *labels])
        self.source_status.setText(f"{len(self.source_rows)} dispatch source document(s)")
        if not self.return_no.text().strip():
            self.return_no.setText(f"DRTN-{datetime.now():%y%m%d-%H%M%S}")

    def load_items(self) -> None:
        selected = self.source_by_label.get(self.source_doc.currentText())
        if not selected:
            QMessageBox.information(self, "Dispatch Return", "Choose a dispatch document first.")
            self.source_doc.setFocus()
            return
        try:
            self.lines = self.source.dispatch_return_source_lines(str(selected["source_table"]), int(selected["id"]))
        except Exception as exc:
            QMessageBox.warning(self, "Dispatch Return", f"Items could not be loaded:\n{exc}")
            return
        self._redraw_lines()
        self.source_status.setText(f"Loaded {len(self.lines)} returnable item row(s)")

    def _redraw_lines(self) -> None:
        self._updating = True
        self.table.setRowCount(len(self.lines))
        for row_index, row in enumerate(self.lines):
            balance = float(row.get("available_qty") or 0)
            values = [
                str(row_index + 1),
                f"{row.get('item_name','')} / {row.get('pack_name','')} / {row.get('unit','')}",
                f"{float(row.get('dispatched_qty') or 0):.3f}",
                f"{float(row.get('returned_qty') or 0):.3f}",
                f"{balance:.3f}",
                "0.000",
                "0.000",
                "0.000",
                "0.000",
                "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in self.editable_columns:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column not in {1, 9}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column, item)
        self._updating = False
        self._update_summary()

    def _line_changed(self, item: QTableWidgetItem) -> None:
        if self._updating or item.column() not in self.editable_columns:
            return
        row = item.row()
        if row < 0 or row >= len(self.lines):
            return
        if item.column() in {5, 6, 8}:
            value = self._cell_float(row, item.column())
            if item.column() == 5:
                value = min(value, float(self.lines[row].get("available_qty") or value))
            elif item.column() == 8:
                value = min(value, float(self.lines[row].get("available_free_qty") or value))
            elif item.column() == 6:
                value = min(value, self._cell_float(row, 5))
            self._set_cell(row, item.column(), f"{max(value, 0):.3f}")
        accepted = max(self._cell_float(row, 5) - self._cell_float(row, 6), 0.0)
        self._set_cell(row, 7, f"{accepted:.3f}")
        self._update_summary()

    def save_return(self) -> None:
        selected = self.source_by_label.get(self.source_doc.currentText())
        if not selected:
            QMessageBox.warning(self, "Dispatch Return", "Choose a dispatch document before saving.")
            self.source_doc.setFocus()
            return
        if not self.lines:
            QMessageBox.warning(self, "Dispatch Return", "Show source items before saving.")
            return
        rows: list[dict[str, Any]] = []
        for row_index, line in enumerate(self.lines):
            rows.append(
                {
                    "source_item_id": line.get("source_item_id"),
                    "return_qty": self._cell_float(row_index, 5),
                    "damaged_qty": self._cell_float(row_index, 6),
                    "return_free_qty": self._cell_float(row_index, 8),
                    "remarks": self._cell_text(row_index, 9),
                    "reason": self.reason.text().strip(),
                }
            )
        header = {
            "return_no": self.return_no.text().strip(),
            "return_date": self.return_date.date().toString("yyyy-MM-dd"),
            "source_table": selected["source_table"],
            "source_id": selected["id"],
            "reason": self.reason.text().strip(),
            "notes": self.notes.toPlainText().strip(),
        }
        try:
            return_id = self.repository.save_dispatch_return(header, rows)
        except Exception as exc:
            QMessageBox.warning(self, "Dispatch Return", f"Dispatch return could not be saved:\n{exc}")
            return
        QMessageBox.information(self, "Dispatch Return", f"Dispatch return saved.\nID: {return_id}")
        self.clear_form()
        self.refresh_sources()

    def print_return_pdf(self) -> None:
        if not self._can_output_return("previewing"):
            return
        try:
            path, _, _ = self._create_return_pdf()
        except Exception as exc:
            QMessageBox.warning(self, "Dispatch Return", f"PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, "Dispatch Return Print Preview")

    def share_return_whatsapp(self) -> None:
        if not self._can_output_return("sharing"):
            return
        try:
            path, caption, phone = self._create_return_pdf()
            message = self._communication_message("whatsapp", caption, path)
            caption = message["body"]
            QApplication.clipboard().setText(f"{caption}\nPDF: {path}")
            result = prepare_whatsapp_document(phone, caption, path)
            if not result.get("ok"):
                open_whatsapp_share(phone, caption)
                QMessageBox.information(self, "Dispatch Return", f"{result.get('message')}\n\n{pdf_share_note(path)}")
                return
        except Exception as exc:
            QMessageBox.warning(self, "Dispatch Return", f"Share PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Dispatch Return", str(result.get("message") or pdf_share_note(path)))

    def email_return_pdf(self) -> None:
        if not self._can_output_return("emailing"):
            return
        try:
            path, caption, _ = self._create_return_pdf()
            selected = self.source_by_label.get(self.source_doc.currentText(), {})
            message = self._communication_message("email", caption, path)
            result = prepare_email_document(
                selected.get("email") or selected.get("customer_email") or "",
                message["subject"],
                message["body"],
                path,
                db_path=self.source.sqlite_path,
            )
            if not result.get("ok"):
                QMessageBox.warning(self, "Dispatch Return", str(result.get("message") or "Email could not be prepared."))
                return
        except Exception as exc:
            QMessageBox.warning(self, "Dispatch Return", f"Email PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Dispatch Return", str(result.get("message") or pdf_share_note(path)))

    def _can_output_return(self, action: str) -> bool:
        if not self.source_by_label.get(self.source_doc.currentText()):
            QMessageBox.warning(self, "Dispatch Return", f"Choose a dispatch document before {action}.")
            self.source_doc.setFocus()
            return False
        if not self.return_no.text().strip():
            QMessageBox.warning(self, "Dispatch Return", f"Return No is required before {action}.")
            self.return_no.setFocus()
            return False
        if not self.lines:
            QMessageBox.information(self, "Dispatch Return", f"Show source items before {action}.")
            return False
        return True

    def _create_return_pdf(self) -> tuple[Any, str, str]:
        selected = self.source_by_label.get(self.source_doc.currentText(), {})
        rows = []
        for row_index, line in enumerate(self.lines):
            rows.append(
                {
                    "#": row_index + 1,
                    "Item": f"{line.get('item_name', '')} / {line.get('pack_name', '')} / {line.get('unit', '')}",
                    "Dispatched": f"{float(line.get('dispatched_qty') or 0):.3f}",
                    "Returned": f"{float(line.get('returned_qty') or 0):.3f}",
                    "Balance": f"{float(line.get('available_qty') or 0):.3f}",
                    "Return Qty": f"{self._cell_float(row_index, 5):.3f}",
                    "Damaged": f"{self._cell_float(row_index, 6):.3f}",
                    "Accepted": f"{self._cell_float(row_index, 7):.3f}",
                    "SCH Return": f"{self._cell_float(row_index, 8):.3f}",
                    "Remarks": self._cell_text(row_index, 9),
                }
            )
        returned = sum(self._cell_float(row, 5) for row in range(self.table.rowCount()))
        damaged = sum(self._cell_float(row, 6) for row in range(self.table.rowCount()))
        accepted = sum(self._cell_float(row, 7) for row in range(self.table.rowCount()))
        filters = {
            "Return No": self.return_no.text().strip(),
            "Return Date": self.return_date.date().toString("yyyy-MM-dd"),
            "Source": selected.get("source_ref") or self.source_doc.currentText(),
            "Customer": selected.get("customer_name", ""),
            "Route": selected.get("route", ""),
            "Reason": self.reason.text().strip(),
            "Returned": f"{returned:.3f}",
            "Accepted": f"{accepted:.3f}",
            "Damaged": f"{damaged:.3f}",
            "Notes": self.notes.toPlainText().strip(),
        }
        company = self._company()
        prints = self.config.project_root / "prints"
        safe_doc = self.return_no.text().replace("/", "_").replace(" ", "_")
        path = prints / f"dispatch_return_{safe_doc}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        write_report_pdf(path, "Dispatch Return", company, rows, filters, db_path=self.source.sqlite_path, document_type="report")
        caption = f"Dispatch Return: {self.return_no.text()}\nSource: {selected.get('source_ref') or '-'}\nReturned: {returned:.3f}\nAccepted: {accepted:.3f}"
        phone = selected.get("phone") or selected.get("customer_phone") or ""
        return path, caption, str(phone)

    def _communication_message(self, channel: str, fallback_body: str, path: Any) -> dict[str, str]:
        selected = self.source_by_label.get(self.source_doc.currentText(), {})
        returned = sum(self._cell_float(row, 5) for row in range(self.table.rowCount()))
        accepted = sum(self._cell_float(row, 7) for row in range(self.table.rowCount()))
        context = document_message_context(
            title="Dispatch Return",
            document_no=self.return_no.text(),
            party_name=selected.get("customer_name") or selected.get("source_ref") or self.source_doc.currentText(),
            amount=accepted,
            company=self._company(),
            pdf_path=path,
            extra={"returned_qty": f"{returned:.3f}", "accepted_qty": f"{accepted:.3f}"},
        )
        return communication_message(
            channel=channel,
            document_type="dispatch_return",
            context=context,
            fallback_subject=f"Dispatch Return {self.return_no.text()}",
            fallback_body=fallback_body,
            db_path=self.source.sqlite_path,
        )

    def _company(self) -> dict[str, Any]:
        try:
            return self.source.company()
        except Exception:
            return {}

    def clear_form(self) -> None:
        self.return_no.setText(f"DRTN-{datetime.now():%y%m%d-%H%M%S}")
        self.return_date.setDate(QDate.currentDate())
        self.reason.setText("Returned from dispatch")
        self.notes.clear()
        self.lines.clear()
        self._redraw_lines()
        if self.source_doc.count():
            self.source_doc.setCurrentIndex(0)
        self.source_doc.setFocus()

    def _source_table(self) -> str:
        return "stock_outs" if self.source_type.currentText() == "Load Challans" else "sales"

    def _source_label(self, row: dict[str, Any]) -> str:
        return (
            f"{row.get('source_ref','')} | {row.get('source_date','')} | "
            f"{row.get('customer_name','')} | {row.get('route','')} | {row.get('dispatch_status','')}"
        )

    def _cell_float(self, row: int, column: int) -> float:
        try:
            return max(float(self._cell_text(row, column).replace(",", "") or 0), 0.0)
        except ValueError:
            return 0.0

    def _cell_text(self, row: int, column: int) -> str:
        item = self.table.item(row, column)
        return item.text().strip() if item else ""

    def _set_cell(self, row: int, column: int, value: str) -> None:
        self._updating = True
        item = self.table.item(row, column)
        if item:
            item.setText(value)
        self._updating = False

    def _update_summary(self) -> None:
        returned = sum(self._cell_float(row, 5) for row in range(self.table.rowCount()))
        damaged = sum(self._cell_float(row, 6) for row in range(self.table.rowCount()))
        accepted = sum(self._cell_float(row, 7) for row in range(self.table.rowCount()))
        self.row_count.setText(f"Rows: {self.table.rowCount()}")
        self.total_returned.setText(f"Returned: {returned:,.3f}")
        self.total_accepted.setText(f"Accepted: {accepted:,.3f}")
        self.total_damaged.setText(f"Damaged: {damaged:,.3f}")

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_return)
