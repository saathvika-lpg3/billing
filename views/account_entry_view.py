from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
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
from services.pdf_print import document_share_caption, write_voucher_pdf
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
    DocumentCard,
    ERPFieldBox,
    ERPTransactionGrid,
    TransactionHeader,
    TransactionPageLayout,
    TransactionSectionCard,
    TransactionToolbar,
)


ACCOUNT_MODES = {
    "receipt": {
        "title": "Receipt Entry",
        "subtitle": "Customer collection | cash/bank mode | branch and cost center",
        "doc_label": "Receipt No",
        "date_label": "Receipt Date",
        "party_label": "Customer",
        "party_source": "customers",
        "list_key": "receipts",
    },
    "payment": {
        "title": "Payment Entry",
        "subtitle": "Supplier payment | cash/bank mode | branch and cost center",
        "doc_label": "Payment No",
        "date_label": "Payment Date",
        "party_label": "Supplier",
        "party_source": "suppliers",
        "list_key": "payments",
    },
    "expense": {
        "title": "Expense Entry",
        "subtitle": "Expense ledger, paid-to details and payment mode",
        "doc_label": "Expense No",
        "date_label": "Expense Date",
        "party_label": "Expense Ledger",
        "party_source": "ledgers",
        "list_key": "expenses",
    },
    "journal": {
        "title": "Journal Entry",
        "subtitle": "Debit and credit ledger posting with narration",
        "doc_label": "Entry No",
        "date_label": "Entry Date",
        "party_label": "Debit Ledger",
        "party_source": "ledgers",
        "list_key": "journal",
    },
}


class AccountEntryView(QWidget):
    def __init__(self, config: AppConfig, mode: str) -> None:
        super().__init__()
        if mode not in ACCOUNT_MODES:
            raise ValueError(f"Unknown account mode: {mode}")
        self.config = config
        self.mode = mode
        self.meta = ACCOUNT_MODES[mode]
        self.source = MySqlSource()
        self.repository = TransactionRepository()
        self.company: dict[str, Any] = {}
        self.option_maps: dict[str, dict[str, dict[str, Any]]] = {}
        self.recent_rows: list[dict[str, Any]] = []
        self.visible_rows: list[dict[str, Any]] = []
        self.last_saved_id = 0
        self._build()
        self.refresh()
        self._register_hotkeys()

    def _build(self) -> None:
        page = TransactionPageLayout(self)
        page.add_header(self._title_bar())
        page.add_toolbar(self._action_toolbar())
        page.add_section(self._entry_card())
        page.add_grid(self._recent_card())

    def _title_bar(self) -> QWidget:
        header = TransactionHeader(str(self.meta["title"]), str(self.meta["subtitle"]), self)
        self.source_status = header.status_label
        return header

    def _action_toolbar(self) -> QWidget:
        return TransactionToolbar(
            [
                ("New", self.clear_form),
                ("Save", self.save_draft),
                ("Preview", self.print_voucher_pdf),
                ("Print", self.print_voucher_pdf),
                ("PDF", self.print_voucher_pdf),
                ("WhatsApp", self.share_voucher_whatsapp),
                ("Email", self.email_voucher_pdf),
                ("Close", self.close),
            ],
            self,
        )

    def _entry_card(self) -> QWidget:
        frame = DocumentCard()
        frame.setMinimumHeight(124)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(4)

        self.doc_no = QLineEdit()
        self.entry_date = QDateEdit()
        self.entry_date.setCalendarPopup(True)
        self.entry_date.setDate(QDate.currentDate())
        self.party = QComboBox()
        self.amount = QLineEdit("0.00")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Cash", "Bank", "UPI", "Card", "Cheque", "Adjustment"])
        self.branch = QComboBox()
        self.cost_center = QComboBox()
        self.status = QComboBox()
        self.status.addItems(["Active", "Draft", "Hold", "Cancelled"])
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Narration / notes")

        grid.addWidget(self._field(str(self.meta["doc_label"]), self.doc_no, 140), 0, 0)
        grid.addWidget(self._field(str(self.meta["date_label"]), self.entry_date, 120), 0, 1)
        grid.addWidget(self._field(str(self.meta["party_label"]), self.party, 240), 0, 2, 1, 2)
        grid.addWidget(self._field("Amount", self.amount, 120), 0, 4)
        if self.mode == "journal":
            self.credit_ledger = QComboBox()
            self.voucher_type = QComboBox()
            self.voucher_type.addItems(["Journal", "Contra", "Adjustment", "Opening"])
            grid.addWidget(self._field("Voucher Type", self.voucher_type, 120), 1, 0)
            grid.addWidget(self._field("Credit Ledger", self.credit_ledger, 240), 1, 1, 1, 2)
        elif self.mode == "expense":
            self.paid_to = QLineEdit()
            grid.addWidget(self._field("Paid To", self.paid_to, 220), 1, 0, 1, 2)
            grid.addWidget(self._field("Mode", self.mode_combo, 120), 1, 2)
        else:
            grid.addWidget(self._field("Mode", self.mode_combo, 120), 1, 0)
        grid.addWidget(self._field("Branch", self.branch, 150), 1, 3)
        grid.addWidget(self._field("Cost Center", self.cost_center, 150), 1, 4)
        grid.addWidget(self._field("Status", self.status, 120), 2, 0)
        grid.addWidget(self._field("Notes", self.notes, 320), 2, 1, 1, 4)
        for column in range(5):
            grid.setColumnStretch(column, 1)
        return frame

    def _field(self, label: str, widget: QWidget, width: int) -> QWidget:
        if isinstance(widget, QTextEdit):
            widget.setMinimumHeight(40)
            widget.setMaximumHeight(56)
        else:
            widget.setFixedHeight(28)
        widget.setMinimumWidth(min(width, 160))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if isinstance(widget, QComboBox):
            widget.setMaxVisibleItems(18)
            widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 8))
        return ERPFieldBox(label, widget, self)

    def _recent_card(self) -> QWidget:
        frame = TransactionSectionCard("recent")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        bar = QHBoxLayout()
        title = QLabel("Recent Entries")
        title.setObjectName("cardTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search recent entries")
        self.search.textChanged.connect(self._redraw_table)
        bar.addWidget(title)
        bar.addStretch(1)
        bar.addWidget(self.search)
        layout.addLayout(bar)
        self.table = ERPTransactionGrid()
        self.table.set_editable_columns(set())
        self.table.set_command_handlers(
            {
                "save": self.save_draft,
                "preview": self.print_voucher_pdf,
                "print": self.print_voucher_pdf,
                "product_search": lambda: self.search.setFocus(),
            }
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.table, stretch=1)
        return frame

    def refresh(self) -> None:
        try:
            self.company = self.source.company()
            self._load_options()
            self.recent_rows = self.source.operation_rows(str(self.meta["list_key"]), 300)
            self.source_status.setText(f"Source: {len(self.recent_rows)} recent rows")
        except Exception as exc:
            self.recent_rows = []
            self.source_status.setText(f"Source unavailable: {exc}")
        self._redraw_table()

    def _load_options(self) -> None:
        self.option_maps.clear()
        self._fill_combo(self.party, str(self.meta["party_source"]))
        if self.mode == "journal":
            self._fill_combo(self.credit_ledger, "ledgers")
        self._fill_combo(self.branch, "branches", optional_label="Main")
        self._fill_combo(self.cost_center, "cost_centers", optional_label="No Cost Center")

    def _fill_combo(self, combo: QComboBox, source_key: str, optional_label: str = "") -> None:
        combo.clear()
        if optional_label:
            combo.addItem(optional_label)
        rows = self._option_rows(source_key)
        option_map = {}
        for row in rows:
            label = self._option_label(source_key, row)
            combo.addItem(label)
            option_map[label] = row
        self.option_maps[source_key] = option_map

    def _option_rows(self, source_key: str) -> list[dict[str, Any]]:
        if source_key == "customers":
            return self.source.operation_rows("customers", 500)
        if source_key == "suppliers":
            return self.source.operation_rows("suppliers", 500)
        if source_key == "ledgers":
            return self.source.operation_rows("ledgers", 500)
        if source_key == "branches":
            return self.source.operation_rows("branches", 500)
        if source_key == "cost_centers":
            return self.source.operation_rows("cost_centers", 500)
        return []

    def _option_label(self, source_key: str, row: dict[str, Any]) -> str:
        if source_key in {"customers", "suppliers"}:
            phone = row.get("phone") or ""
            return f"{row.get('id')} | {row.get('name')} | {phone}"
        if source_key == "ledgers":
            return f"{row.get('id')} | {row.get('name')} | {row.get('group_name')}"
        return f"{row.get('id')} | {row.get('name')}"

    def _redraw_table(self) -> None:
        query = self.search.text().strip().lower()
        rows = []
        for row in self.recent_rows:
            haystack = " ".join(str(value) for value in row.values()).lower()
            if not query or query in haystack:
                rows.append(row)
        self.visible_rows = rows
        if not rows:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setItem(0, 0, QTableWidgetItem("No recent entries."))
            return
        headers = list(rows[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([self._pretty(header) for header in headers])
        for row_index, row in enumerate(rows):
            for column_index, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(self._display(value))
                if isinstance(value, (int, float, Decimal)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column_index, item)
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()

    def select_recent_record(self, record_id: int) -> None:
        self.search.clear()
        self.refresh()
        for row_index, row in enumerate(self.visible_rows):
            if int(row.get("id") or 0) != record_id:
                continue
            self.table.clearSelection()
            self.table.selectRow(row_index)
            self.table.setFocus()
            item = self.table.item(row_index, 0)
            if item is not None:
                self.table.scrollToItem(item)
            self.source_status.setText(f"Selected {self.meta['title']} #{record_id}")
            return

    def clear_form(self) -> None:
        self.doc_no.clear()
        self.entry_date.setDate(QDate.currentDate())
        self.amount.setText("0.00")
        self.notes.clear()
        self.status.setCurrentIndex(0)
        self.mode_combo.setCurrentIndex(0)
        if self.party.count():
            self.party.setCurrentIndex(0)
        if self.branch.count():
            self.branch.setCurrentIndex(0)
        if self.cost_center.count():
            self.cost_center.setCurrentIndex(0)
        if self.mode == "journal":
            self.voucher_type.setCurrentIndex(0)
            if self.credit_ledger.count():
                self.credit_ledger.setCurrentIndex(0)
        if self.mode == "expense":
            self.paid_to.clear()
        self.doc_no.setFocus()

    def save_draft(self) -> None:
        if not self.doc_no.text().strip():
            QMessageBox.warning(self, str(self.meta["title"]), f"{self.meta['doc_label']} is required.")
            self.doc_no.setFocus()
            return
        try:
            amount = float(self.amount.text().replace(",", "") or 0)
        except ValueError:
            QMessageBox.warning(self, str(self.meta["title"]), "Amount must be numeric.")
            self.amount.setFocus()
            return
        if amount <= 0:
            QMessageBox.warning(self, str(self.meta["title"]), "Amount must be greater than zero.")
            self.amount.setFocus()
            return
        payload = self._entry_payload(amount)
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.mode}_entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = drafts_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            saved_id = self.repository.save_account_entry(self.mode, payload["entry"])
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Entry could not be saved:\n{exc}")
            return
        self.last_saved_id = saved_id
        QMessageBox.information(self, str(self.meta["title"]), f"Saved to local database.\nID: {saved_id}\nAudit copy:\n{path}")
        self.refresh()

    def print_voucher_pdf(self) -> None:
        try:
            path, _, _ = self._create_voucher_pdf()
        except ValueError as exc:
            QMessageBox.warning(self, str(self.meta["title"]), str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Voucher PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, f"{self.meta['title']} Print Preview")

    def share_voucher_whatsapp(self) -> None:
        try:
            path, caption, phone = self._create_voucher_pdf()
            message = self._communication_message("whatsapp", caption, path)
            caption = message["body"]
            QApplication.clipboard().setText(f"{caption}\nPDF: {path}")
            result = prepare_whatsapp_document(phone, caption, path)
            if not result.get("ok"):
                if result.get("code") != "missing_phone":
                    open_whatsapp_share(phone, caption)
                QMessageBox.information(self, str(self.meta["title"]), f"{result.get('message')}\n\n{pdf_share_note(path)}")
                return
        except ValueError as exc:
            QMessageBox.warning(self, str(self.meta["title"]), str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Voucher share could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, str(self.meta["title"]), str(result.get("message") or pdf_share_note(path)))

    def email_voucher_pdf(self) -> None:
        try:
            path, caption, _ = self._create_voucher_pdf()
            party = self._current_party_row()
            message = self._communication_message("email", caption, path)
            result = prepare_email_document(
                party.get("email") or "",
                message["subject"],
                message["body"],
                path,
                db_path=self.source.sqlite_path,
            )
            if not result.get("ok"):
                QMessageBox.warning(self, str(self.meta["title"]), str(result.get("message") or "Email could not be prepared."))
                return
        except ValueError as exc:
            QMessageBox.warning(self, str(self.meta["title"]), str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Voucher email could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, str(self.meta["title"]), str(result.get("message") or pdf_share_note(path)))

    def _create_voucher_pdf(self) -> tuple[Any, str, str]:
        if not self.doc_no.text().strip():
            self.doc_no.setFocus()
            raise ValueError(f"{self.meta['doc_label']} is required.")
        try:
            amount = float(self.amount.text().replace(",", "") or 0)
        except ValueError as exc:
            self.amount.setFocus()
            raise ValueError("Amount must be numeric.") from exc
        if amount <= 0:
            self.amount.setFocus()
            raise ValueError("Amount must be greater than zero.")
        payload = self._entry_payload(amount)
        entry = payload["entry"]
        prints = self.config.project_root / "prints"
        safe_doc = self.doc_no.text().replace("/", "_").replace(" ", "_")
        path = prints / f"{self.mode}_{safe_doc}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        title, voucher_type, party_label = self._voucher_print_meta()
        write_voucher_pdf(
            path,
            title,
            self.company,
            entry,
            voucher_type=voucher_type,
            party_label=party_label,
            prepared_by="Administrator",
        )
        party = self._current_party_row()
        caption = document_share_caption(title, entry["doc_no"], entry["party_name"], entry["amount"], self.company, path)
        return path, caption, str(party.get("phone") or "")

    def _communication_message(self, channel: str, fallback_body: str, path: Any) -> dict[str, str]:
        try:
            amount = float(self.amount.text().replace(",", "") or 0)
        except ValueError:
            amount = 0
        title, _, _ = self._voucher_print_meta()
        party_name = self.party.currentText()
        context = document_message_context(
            title=title,
            document_no=self.doc_no.text(),
            party_name=party_name,
            amount=amount,
            company=self.company,
            pdf_path=path,
        )
        return communication_message(
            channel=channel,
            document_type=self.mode,
            context=context,
            fallback_subject=f"{self.meta['title']} {self.doc_no.text()}",
            fallback_body=fallback_body,
            db_path=self.source.sqlite_path,
        )

    def _voucher_print_meta(self) -> tuple[str, str, str]:
        if self.mode == "receipt":
            return "Receipt Voucher", "receipt", "Received From"
        if self.mode == "payment":
            return "Payment Voucher", "payment_voucher", "Paid To"
        if self.mode == "expense":
            return "Expense Voucher", "expense_voucher", "Paid To"
        return "Journal Voucher", "journal", "Debit Ledger"

    def _current_party_row(self) -> dict[str, Any]:
        return self.option_maps.get(str(self.meta["party_source"]), {}).get(self.party.currentText(), {})

    def _entry_payload(self, amount: float) -> dict[str, Any]:
        party_source = str(self.meta["party_source"])
        party = self.option_maps.get(party_source, {}).get(self.party.currentText(), {})
        party_type = {"customers": "customer", "suppliers": "supplier"}.get(party_source, "")
        entry = {
            "doc_no": self.doc_no.text().strip(),
            "entry_date": self.entry_date.date().toString("yyyy-MM-dd"),
            "party": self.party.currentText(),
            "party_id": party.get("id") or 0,
            "party_name": str(party.get("name") or self.party.currentText()),
            "party_type": party_type,
            "amount": amount,
            "branch": self.branch.currentText(),
            "cost_center": self.cost_center.currentText(),
            "status": self.status.currentText(),
            "notes": self.notes.toPlainText().strip(),
        }
        if self.mode == "journal":
            credit_row = self.option_maps.get("ledgers", {}).get(self.credit_ledger.currentText(), {})
            entry["voucher_type"] = self.voucher_type.currentText()
            entry["credit_ledger"] = str(credit_row.get("name") or self.credit_ledger.currentText())
        elif self.mode == "expense":
            entry["mode"] = self.mode_combo.currentText()
            entry["paid_to"] = self.paid_to.text().strip()
        else:
            entry["mode"] = self.mode_combo.currentText()
        return {
            "source": "desktop_account_entry",
            "mode": self.mode,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "entry": entry,
        }

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_draft)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.print_voucher_pdf)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.share_voucher_whatsapp)

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        return "" if value is None else str(value)

    def _pretty(self, value: str) -> str:
        return value.replace("_", " ").strip().title()
