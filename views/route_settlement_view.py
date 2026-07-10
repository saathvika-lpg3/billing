from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
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
from widgets.erp_components import (
    DocumentCard,
    ERPFieldBox,
    ERPTransactionGrid,
    TransactionHeader,
    TransactionPageLayout,
    TransactionSectionCard,
    TransactionToolbar,
)


class RouteSettlementView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.rows: list[dict[str, Any]] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        page = TransactionPageLayout(self)
        page.add_header(self._title_bar())
        page.add_toolbar(self._action_toolbar())
        page.add_section(self._form_card())
        page.add_grid(self._recent_card())

    def _title_bar(self) -> QWidget:
        header = TransactionHeader("Route Settlement", "Close route load with cash, credit, receipts, outstanding and short/excess")
        header.setMaximumHeight(58)
        header.status_label.setText("Source: loading")
        self.source_status = header.status_label
        return header

    def _action_toolbar(self) -> QWidget:
        return TransactionToolbar(
            [
                ("New", self.clear_form),
                ("Save", self.save_draft),
                ("Preview", self.print_settlement_pdf),
                ("Print", self.print_settlement_pdf),
                ("PDF", self.print_settlement_pdf),
                ("WhatsApp", self.share_settlement_whatsapp),
                ("Email", self.email_settlement_pdf),
                ("Close", self.close),
            ],
            self,
        )

    def _form_card(self) -> QWidget:
        frame = DocumentCard()
        frame.setMinimumHeight(165)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(4)
        self.settlement_no = QLineEdit()
        self.settlement_date = QDateEdit()
        self.settlement_date.setCalendarPopup(True)
        self.settlement_date.setDate(QDate.currentDate())
        self.area = QLineEdit()
        self.salesman = QLineEdit()
        self.total_bills = QLineEdit("0")
        self.cash_sales = QLineEdit("0.00")
        self.credit_sales = QLineEdit("0.00")
        self.receipts_total = QLineEdit("0.00")
        self.loaded_qty = QLineEdit("0.000")
        self.loaded_free = QLineEdit("0.000")
        self.outstanding_total = QLineEdit("0.00")
        self.collected_cash = QLineEdit("0.00")
        self.short_excess = QLineEdit("0.00")
        self.status = QComboBox()
        self.status.addItems(["Draft", "Submitted", "Closed", "Cancelled"])
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Settlement notes, shortage reason, pending follow-up")

        number_controls = [self.cash_sales, self.receipts_total, self.collected_cash]
        for control in number_controls:
            control.textChanged.connect(self._update_short_excess)

        grid.addWidget(self._field("Settlement No", self.settlement_no, 140), 0, 0)
        grid.addWidget(self._field("Date", self.settlement_date, 120), 0, 1)
        grid.addWidget(self._field("Area / Route", self.area, 180), 0, 2)
        grid.addWidget(self._field("Salesman", self.salesman, 180), 0, 3)
        grid.addWidget(self._field("Status", self.status, 120), 0, 4)
        grid.addWidget(self._field("Total Bills", self.total_bills, 100), 1, 0)
        grid.addWidget(self._field("Cash Sales", self.cash_sales, 110), 1, 1)
        grid.addWidget(self._field("Credit Sales", self.credit_sales, 110), 1, 2)
        grid.addWidget(self._field("Receipts", self.receipts_total, 110), 1, 3)
        grid.addWidget(self._field("Collected Cash", self.collected_cash, 120), 1, 4)
        grid.addWidget(self._field("Loaded Qty", self.loaded_qty, 110), 2, 0)
        grid.addWidget(self._field("Loaded SCH", self.loaded_free, 110), 2, 1)
        grid.addWidget(self._field("Outstanding", self.outstanding_total, 120), 2, 2)
        grid.addWidget(self._field("Short / Excess", self.short_excess, 120), 2, 3)
        grid.addWidget(self._field("Notes", self.notes, 240), 2, 4)
        for column in range(5):
            grid.setColumnStretch(column, 1)
        return frame

    def _field(self, label: str, widget: QWidget, width: int) -> QWidget:
        if isinstance(widget, QTextEdit):
            widget.setMinimumHeight(40)
            widget.setMaximumHeight(56)
        else:
            widget.setFixedHeight(28)
        widget.setMinimumWidth(min(width, 140))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return ERPFieldBox(label, widget, self)

    def _recent_card(self) -> QWidget:
        frame = TransactionSectionCard("recent")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        bar = QHBoxLayout()
        title = QLabel("Recent Settlements")
        title.setObjectName("cardTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search route settlements")
        self.search.textChanged.connect(self._redraw_table)
        bar.addWidget(title)
        bar.addStretch(1)
        bar.addWidget(self.search)
        layout.addLayout(bar)
        self.table = ERPTransactionGrid()
        self.table.set_editable_columns(set())
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.table, stretch=1)
        return frame

    def refresh(self) -> None:
        try:
            self.rows = self.source.operation_rows("route_settlement", 300)
            self.source_status.setText(f"Source: {len(self.rows)} settlements")
        except Exception as exc:
            self.rows = []
            self.source_status.setText(f"Source unavailable: {exc}")
        self._redraw_table()

    def save_draft(self) -> None:
        if not self.settlement_no.text().strip():
            QMessageBox.warning(self, "Route Settlement", "Settlement No is required.")
            self.settlement_no.setFocus()
            return
        if not self.area.text().strip():
            QMessageBox.warning(self, "Route Settlement", "Area / Route is required.")
            self.area.setFocus()
            return
        try:
            payload_values = {key: self._number(control) for key, control in self._number_controls().items()}
        except ValueError:
            QMessageBox.warning(self, "Route Settlement", "Amount and quantity fields must be numeric.")
            return
        payload = {
            "source": "desktop_route_settlement",
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "settlement": {
                "settlement_no": self.settlement_no.text().strip(),
                "settlement_date": self.settlement_date.date().toString("yyyy-MM-dd"),
                "area": self.area.text().strip(),
                "salesman_name": self.salesman.text().strip(),
                "status": self.status.currentText(),
                "notes": self.notes.toPlainText().strip(),
                **payload_values,
            },
        }
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        path = drafts_dir / f"route_settlement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Route Settlement", f"Draft saved:\n{path}")

    def print_settlement_pdf(self) -> None:
        if not self._can_output_settlement("previewing"):
            return
        try:
            path, _, _ = self._create_settlement_pdf()
        except Exception as exc:
            QMessageBox.warning(self, "Route Settlement", f"PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, "Route Settlement Print Preview")

    def share_settlement_whatsapp(self) -> None:
        if not self._can_output_settlement("sharing"):
            return
        try:
            path, caption, phone = self._create_settlement_pdf()
            message = self._communication_message("whatsapp", caption, path)
            caption = message["body"]
            QApplication.clipboard().setText(f"{caption}\nPDF: {path}")
            result = prepare_whatsapp_document(phone, caption, path)
            if not result.get("ok"):
                open_whatsapp_share(phone, caption)
                QMessageBox.information(self, "Route Settlement", f"{result.get('message')}\n\n{pdf_share_note(path)}")
                return
        except Exception as exc:
            QMessageBox.warning(self, "Route Settlement", f"Share PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Route Settlement", str(result.get("message") or pdf_share_note(path)))

    def email_settlement_pdf(self) -> None:
        if not self._can_output_settlement("emailing"):
            return
        try:
            path, caption, _ = self._create_settlement_pdf()
            message = self._communication_message("email", caption, path)
            result = prepare_email_document("", message["subject"], message["body"], path, db_path=self.source.sqlite_path)
            if not result.get("ok"):
                QMessageBox.warning(self, "Route Settlement", str(result.get("message") or "Email could not be prepared."))
                return
        except Exception as exc:
            QMessageBox.warning(self, "Route Settlement", f"Email PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Route Settlement", str(result.get("message") or pdf_share_note(path)))

    def _can_output_settlement(self, action: str) -> bool:
        if not self.settlement_no.text().strip():
            QMessageBox.warning(self, "Route Settlement", f"Settlement No is required before {action}.")
            self.settlement_no.setFocus()
            return False
        if not self.area.text().strip():
            QMessageBox.warning(self, "Route Settlement", f"Area / Route is required before {action}.")
            self.area.setFocus()
            return False
        try:
            self._settlement_values()
        except ValueError:
            QMessageBox.warning(self, "Route Settlement", "Amount and quantity fields must be numeric.")
            return False
        return True

    def _create_settlement_pdf(self) -> tuple[Any, str, str]:
        values = self._settlement_values()
        header = {
            "settlement_no": self.settlement_no.text().strip(),
            "settlement_date": self.settlement_date.date().toString("yyyy-MM-dd"),
            "area": self.area.text().strip(),
            "salesman_name": self.salesman.text().strip(),
            "status": self.status.currentText(),
            "notes": self.notes.toPlainText().strip(),
        }
        rows = [
            {"Metric": "Total Bills", "Value": f"{values['total_bills']:.0f}"},
            {"Metric": "Cash Sales", "Value": f"{values['cash_sales']:.2f}"},
            {"Metric": "Credit Sales", "Value": f"{values['credit_sales']:.2f}"},
            {"Metric": "Receipts", "Value": f"{values['receipts_total']:.2f}"},
            {"Metric": "Collected Cash", "Value": f"{values['collected_cash']:.2f}"},
            {"Metric": "Loaded Qty", "Value": f"{values['loaded_qty']:.3f}"},
            {"Metric": "Loaded SCH", "Value": f"{values['loaded_free']:.3f}"},
            {"Metric": "Outstanding", "Value": f"{values['outstanding_total']:.2f}"},
            {"Metric": "Short / Excess", "Value": f"{values['short_excess']:.2f}"},
        ]
        filters = {
            "Settlement No": header["settlement_no"],
            "Date": header["settlement_date"],
            "Area / Route": header["area"],
            "Salesman": header["salesman_name"],
            "Status": header["status"],
            "Notes": header["notes"],
        }
        company = self._company()
        prints = self.config.project_root / "prints"
        safe_doc = header["settlement_no"].replace("/", "_").replace(" ", "_")
        path = prints / f"route_settlement_{safe_doc}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        write_report_pdf(path, "Route Settlement", company, rows, filters, db_path=self.source.sqlite_path, document_type="report")
        caption = (
            f"Route Settlement: {header['settlement_no']}\n"
            f"Route: {header['area']}\n"
            f"Collected Cash: {values['collected_cash']:.2f}\n"
            f"Short / Excess: {values['short_excess']:.2f}"
        )
        return path, caption, ""

    def _communication_message(self, channel: str, fallback_body: str, path: Any) -> dict[str, str]:
        values = self._settlement_values()
        context = document_message_context(
            title="Route Settlement",
            document_no=self.settlement_no.text(),
            party_name=self.area.text(),
            amount=values["collected_cash"],
            company=self._company(),
            pdf_path=path,
            extra={
                "route": self.area.text(),
                "collected_cash": f"{values['collected_cash']:.2f}",
                "short_excess": f"{values['short_excess']:.2f}",
            },
        )
        return communication_message(
            channel=channel,
            document_type="route_settlement",
            context=context,
            fallback_subject=f"Route Settlement {self.settlement_no.text()}",
            fallback_body=fallback_body,
            db_path=self.source.sqlite_path,
        )

    def clear_form(self) -> None:
        self.settlement_no.clear()
        self.settlement_date.setDate(QDate.currentDate())
        self.area.clear()
        self.salesman.clear()
        self.total_bills.setText("0")
        self.cash_sales.setText("0.00")
        self.credit_sales.setText("0.00")
        self.receipts_total.setText("0.00")
        self.loaded_qty.setText("0.000")
        self.loaded_free.setText("0.000")
        self.outstanding_total.setText("0.00")
        self.collected_cash.setText("0.00")
        self.short_excess.setText("0.00")
        self.status.setCurrentIndex(0)
        self.notes.clear()

    def _update_short_excess(self) -> None:
        try:
            expected = self._number(self.cash_sales) + self._number(self.receipts_total)
            collected = self._number(self.collected_cash)
            self.short_excess.setText(f"{collected - expected:.2f}")
        except ValueError:
            self.short_excess.setText("0.00")

    def _number_controls(self) -> dict[str, QLineEdit]:
        return {
            "total_bills": self.total_bills,
            "cash_sales": self.cash_sales,
            "credit_sales": self.credit_sales,
            "receipts_total": self.receipts_total,
            "loaded_qty": self.loaded_qty,
            "loaded_free": self.loaded_free,
            "outstanding_total": self.outstanding_total,
            "collected_cash": self.collected_cash,
            "short_excess": self.short_excess,
        }

    def _settlement_values(self) -> dict[str, float]:
        return {key: self._number(control) for key, control in self._number_controls().items()}

    def _number(self, control: QLineEdit) -> float:
        return float(control.text().replace(",", "") or 0)

    def _company(self) -> dict[str, Any]:
        try:
            return self.source.company()
        except Exception:
            return {}

    def _redraw_table(self) -> None:
        query = self.search.text().strip().lower()
        rows = [row for row in self.rows if not query or query in " ".join(str(v) for v in row.values()).lower()]
        if not rows:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setItem(0, 0, QTableWidgetItem("No route settlements found."))
            return
        headers = list(rows[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([header.replace("_", " ").title() for header in headers])
        for row_index, row in enumerate(rows):
            for column_index, header in enumerate(headers):
                value = row.get(header)
                item = QTableWidgetItem(self._display(value))
                if isinstance(value, (int, float, Decimal)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column_index, item)
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        return "" if value is None else str(value)
