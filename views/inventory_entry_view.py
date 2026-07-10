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
    ProductSearchCard,
    TransactionHeader,
    TransactionGridPanel,
    TransactionPageLayout,
    TransactionSectionCard,
    TransactionToolbar,
)


INVENTORY_MODES = {
    "stock_entry": {
        "title": "Stock Entry",
        "subtitle": "Opening, receipt or issue stock entry with warehouse and item quantities",
        "doc_label": "Entry No",
        "list_key": "stock_entry",
    },
    "transfer": {
        "title": "Stock Transfer",
        "subtitle": "Move stock between warehouses with item-wise quantities",
        "doc_label": "Transfer No",
        "list_key": "transfer_list",
    },
    "adjustment": {
        "title": "Stock Adjustment",
        "subtitle": "Physical count correction with current and counted stock",
        "doc_label": "Adjustment No",
        "list_key": "stock_adjustment",
    },
}


class InventoryEntryView(QWidget):
    def __init__(self, config: AppConfig, mode: str) -> None:
        super().__init__()
        if mode not in INVENTORY_MODES:
            raise ValueError(f"Unknown inventory mode: {mode}")
        self.config = config
        self.mode = mode
        self.meta = INVENTORY_MODES[mode]
        self.source = MySqlSource()
        self.repository = TransactionRepository()
        self.products: list[dict[str, Any]] = []
        self.product_by_label: dict[str, dict[str, Any]] = {}
        self.rows: list[dict[str, Any]] = []
        self.recent_rows: list[dict[str, Any]] = []
        self._build()
        self.refresh()
        self._register_hotkeys()

    def _build(self) -> None:
        page = TransactionPageLayout(self)
        page.add_header(self._title_bar())
        page.add_toolbar(self._action_toolbar())
        page.add_section(self._header_card())
        page.add_section(self._line_card())
        page.add_grid(self._table_card())
        page.add_summary(self._summary_card())

    def _title_bar(self) -> QWidget:
        header = TransactionHeader(str(self.meta["title"]), f"{self.meta['subtitle']} | F4 add row | Ctrl+S draft", self)
        self.source_status = header.status_label
        return header

    def _field(self, label: str, widget: QWidget, width: int = 100) -> QWidget:
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
        return ERPFieldBox(label, widget, self)

    def _action_toolbar(self) -> QWidget:
        return TransactionToolbar(
            [
                ("New", self.clear_document),
                ("Save", self.save_draft),
                ("Preview", self.print_document_pdf),
                ("Print", self.print_document_pdf),
                ("PDF", self.print_document_pdf),
                ("WhatsApp", self.share_document_whatsapp),
                ("Email", self.email_document_pdf),
                ("Close", self.close),
                ("Delete", self.remove_selected_line),
            ],
            self,
        )

    def _header_card(self) -> QWidget:
        frame = DocumentCard()
        frame.setMinimumHeight(112)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(6)
        self.doc_no = QLineEdit()
        self.doc_date = QDateEdit()
        self.doc_date.setCalendarPopup(True)
        self.doc_date.setDate(QDate.currentDate())
        self.from_warehouse = QComboBox()
        self.to_warehouse = QComboBox()
        self.status = QComboBox()
        self.status.addItems(["Active", "Draft", "Posted", "Cancelled"])
        self.notes = QTextEdit()
        grid.addWidget(self._field(str(self.meta["doc_label"]), self.doc_no, 140), 0, 0)
        grid.addWidget(self._field("Date", self.doc_date, 120), 0, 1)
        if self.mode == "transfer":
            grid.addWidget(self._field("From Warehouse", self.from_warehouse, 170), 0, 2)
            grid.addWidget(self._field("To Warehouse", self.to_warehouse, 170), 0, 3)
        else:
            grid.addWidget(self._field("Warehouse", self.from_warehouse, 170), 0, 2)
        grid.addWidget(self._field("Status", self.status, 110), 0, 4)
        grid.addWidget(self._field("Notes", self.notes, 260), 1, 0, 1, 5)
        for column in range(5):
            grid.setColumnStretch(column, 1)
        return frame

    def _line_card(self) -> QWidget:
        frame = ProductSearchCard()
        frame.setMinimumHeight(58)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        self.product = QComboBox()
        self.product.currentTextChanged.connect(self._product_changed)
        self.hsn = QLineEdit()
        self.unit = QLineEdit()
        self.current_stock = QLineEdit("0.000")
        self.qty = QLineEdit("1")
        self.reason = QLineEdit()
        add_button = QPushButton("Add Row  F4")
        add_button.clicked.connect(self.add_line)

        grid.addWidget(self._field("Product Search", self.product, 300), 0, 0, 1, 3)
        grid.addWidget(self._field("HSN", self.hsn, 80), 0, 3)
        grid.addWidget(self._field("Unit", self.unit, 80), 0, 4)
        grid.addWidget(self._field("Current", self.current_stock, 90), 0, 5)
        grid.addWidget(self._field("Qty / Counted", self.qty, 100), 0, 6)
        grid.addWidget(self._field("Reason", self.reason, 180), 0, 7, 1, 2)
        grid.addWidget(add_button, 0, 9)
        grid.setColumnStretch(0, 3)
        for column in range(1, 10):
            grid.setColumnStretch(column, 1)
        return frame

    def _table_card(self) -> QWidget:
        headers = ["#", "Item", "HSN", "Unit", "Current", "Qty / Counted", "Difference", "Reason"]
        self.table = ERPItemGrid(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for col, width in {0: 46, 1: 240, 2: 90, 3: 80, 4: 90, 5: 120, 6: 110, 7: 180}.items():
            self.table.setColumnWidth(col, width)
        # For inventory counted grids, allow editing of qty and reason columns if required
        self.table.set_editable_columns({5, 7})
        self.table.set_command_handlers(
            {
                "add_row": self.add_line,
                "product_search": lambda: self.product.setFocus(),
                "save": self.save_draft,
                "remove_row": self.remove_selected_line,
            }
        )
        return TransactionGridPanel(
            self.table,
            {
                "add_row": self.add_line,
                "delete_row": self.remove_selected_line,
                "import": None,
                "scan_barcode": lambda: self.product.setFocus(),
            },
            parent=self,
        )

    def _summary_card(self) -> QWidget:
        frame = BottomTotalsCard()
        frame.setMaximumHeight(54)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 5, 8, 5)
        self.total_rows = QLabel("Rows: 0")
        self.total_qty = QLabel("Total Qty: 0.000")
        self.total_diff = QLabel("Difference: 0.000")
        self.total_diff.setObjectName("metricValue")
        layout.addWidget(self.total_rows)
        layout.addWidget(self.total_qty)
        layout.addWidget(self.total_diff)
        layout.addStretch(1)
        return frame

    def refresh(self) -> None:
        try:
            self.products = self.source.product_choices()
            warehouses = self.source.warehouses()
            self.recent_rows = self.source.operation_rows(str(self.meta["list_key"]), 100)
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            return
        warehouse_labels = [f"{row.get('id')} | {row.get('name')}" for row in warehouses]
        self.from_warehouse.clear()
        self.from_warehouse.addItems(warehouse_labels or ["Main Store"])
        self.to_warehouse.clear()
        self.to_warehouse.addItems(warehouse_labels or ["Main Store"])
        labels = [self._product_label(row) for row in self.products]
        self.product_by_label = dict(zip(labels, self.products))
        self.product.clear()
        self.product.addItems(labels)
        self.source_status.setText(f"{len(self.products)} packs | {len(warehouses)} warehouses | {len(self.recent_rows)} recent")

    def _product_label(self, row: dict[str, Any]) -> str:
        return f"{row.get('item_name','')} | {row.get('pack_name','')} | Stock {float(row.get('stock_qty') or 0):.3f}"

    def _product_changed(self, label: str) -> None:
        row = self.product_by_label.get(label)
        if not row:
            return
        self.hsn.setText(str(row.get("hsn") or ""))
        self.unit.setText(str(row.get("unit") or "PCS"))
        self.current_stock.setText(f"{float(row.get('stock_qty') or 0):.3f}")

    def add_line(self) -> None:
        product = self.product_by_label.get(self.product.currentText())
        if not product:
            QMessageBox.warning(self, str(self.meta["title"]), "Select a product before adding a row.")
            return
        try:
            current = float(self.current_stock.text().replace(",", "") or 0)
            qty = float(self.qty.text().replace(",", "") or 0)
        except ValueError:
            QMessageBox.warning(self, str(self.meta["title"]), "Qty/current stock must be numeric.")
            return
        if qty < 0:
            QMessageBox.warning(self, str(self.meta["title"]), "Quantity cannot be negative.")
            return
        diff = qty - current if self.mode == "adjustment" else qty
        self.rows.append(
            {
                "item_name": product.get("item_name") or "",
                "item_id": int(float(product.get("item_id") or 0)),
                "pack_id": int(float(product.get("pack_id") or 0)),
                "pack_name": product.get("pack_name") or "",
                "pack_size": float(product.get("pack_size") or 1),
                "hsn": self.hsn.text().strip(),
                "unit": self.unit.text().strip() or "PCS",
                "mrp": float(product.get("mrp") or 0),
                "current": current,
                "qty": qty,
                "difference": diff,
                "reason": self.reason.text().strip(),
            }
        )
        self._redraw_rows()
        self.qty.setText("1")
        self.reason.clear()
        self.product.setFocus()

    def _redraw_rows(self) -> None:
        self.table.setRowCount(len(self.rows))
        for index, row in enumerate(self.rows):
            values = [
                str(index + 1),
                f"{row['item_name']} / {row['pack_name']}",
                row["hsn"],
                row["unit"],
                f"{row['current']:.3f}",
                f"{row['qty']:.3f}",
                f"{row['difference']:.3f}",
                row["reason"],
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in {0, 4, 5, 6}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(index, column, item)
        self.table.resizeRowsToContents()
        self._update_summary()

    def remove_selected_line(self) -> None:
        selected = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)
        if not selected and self.table.currentRow() >= 0:
            selected = [self.table.currentRow()]
        for row_index in selected:
            if 0 <= row_index < len(self.rows):
                self.rows.pop(row_index)
        self._redraw_rows()

    def _update_summary(self) -> None:
        total_qty = sum(float(row["qty"]) for row in self.rows)
        total_diff = sum(float(row["difference"]) for row in self.rows)
        self.total_rows.setText(f"Rows: {len(self.rows)}")
        self.total_qty.setText(f"Total Qty: {total_qty:,.3f}")
        self.total_diff.setText(f"Difference: {total_diff:,.3f}")

    def clear_document(self) -> None:
        self.doc_no.clear()
        self.doc_date.setDate(QDate.currentDate())
        self.notes.clear()
        self.rows.clear()
        self._redraw_rows()
        self.doc_no.setFocus()

    def save_draft(self) -> None:
        if not self.doc_no.text().strip():
            QMessageBox.warning(self, str(self.meta["title"]), f"{self.meta['doc_label']} is required.")
            self.doc_no.setFocus()
            return
        if self.mode == "transfer" and self.from_warehouse.currentText() == self.to_warehouse.currentText():
            QMessageBox.warning(self, str(self.meta["title"]), "From and To warehouse cannot be same.")
            self.to_warehouse.setFocus()
            return
        if not self.rows:
            QMessageBox.warning(self, str(self.meta["title"]), "Add at least one item row.")
            self.product.setFocus()
            return
        payload = self._inventory_payload()
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = drafts_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            saved_id = self.repository.save_inventory_entry(self.mode, payload["header"], self.rows)
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Inventory entry could not be saved:\n{exc}")
            return
        QMessageBox.information(self, str(self.meta["title"]), f"Saved to local database.\nID: {saved_id}\nAudit copy:\n{path}")
        self.refresh()

    def print_document_pdf(self) -> None:
        if not self._can_output_document("previewing"):
            return
        try:
            path, _, _ = self._create_document_pdf()
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, f"{self.meta['title']} Print Preview")

    def share_document_whatsapp(self) -> None:
        if not self._can_output_document("sharing"):
            return
        try:
            path, caption, phone = self._create_document_pdf()
            message = self._communication_message("whatsapp", caption, path)
            caption = message["body"]
            QApplication.clipboard().setText(f"{caption}\nPDF: {path}")
            result = prepare_whatsapp_document(phone, caption, path)
            if not result.get("ok"):
                open_whatsapp_share(phone, caption)
                QMessageBox.information(self, str(self.meta["title"]), f"{result.get('message')}\n\n{pdf_share_note(path)}")
                return
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Share PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, str(self.meta["title"]), str(result.get("message") or pdf_share_note(path)))

    def email_document_pdf(self) -> None:
        if not self._can_output_document("emailing"):
            return
        try:
            path, caption, _ = self._create_document_pdf()
            message = self._communication_message("email", caption, path)
            result = prepare_email_document("", message["subject"], message["body"], path, db_path=self.source.sqlite_path)
            if not result.get("ok"):
                QMessageBox.warning(self, str(self.meta["title"]), str(result.get("message") or "Email could not be prepared."))
                return
        except Exception as exc:
            QMessageBox.warning(self, str(self.meta["title"]), f"Email PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, str(self.meta["title"]), str(result.get("message") or pdf_share_note(path)))

    def _can_output_document(self, action: str) -> bool:
        if not self.doc_no.text().strip():
            QMessageBox.warning(self, str(self.meta["title"]), f"{self.meta['doc_label']} is required before {action}.")
            self.doc_no.setFocus()
            return False
        if self.mode == "transfer" and self.from_warehouse.currentText() == self.to_warehouse.currentText():
            QMessageBox.warning(self, str(self.meta["title"]), "From and To warehouse cannot be same.")
            self.to_warehouse.setFocus()
            return False
        if not self.rows:
            QMessageBox.information(self, str(self.meta["title"]), f"Add at least one item row before {action}.")
            self.product.setFocus()
            return False
        return True

    def _create_document_pdf(self) -> tuple[Any, str, str]:
        payload = self._inventory_payload()
        header = payload["header"]
        title = str(self.meta["title"])
        rows = [
            {
                "#": index,
                "Item": f"{row.get('item_name', '')} / {row.get('pack_name', '')}",
                "HSN": row.get("hsn", ""),
                "Unit": row.get("unit", ""),
                "Current": f"{float(row.get('current') or 0):.3f}",
                "Qty / Counted": f"{float(row.get('qty') or 0):.3f}",
                "Difference": f"{float(row.get('difference') or 0):.3f}",
                "Reason": row.get("reason", ""),
            }
            for index, row in enumerate(self.rows, start=1)
        ]
        total_qty = sum(float(row.get("qty") or 0) for row in self.rows)
        total_diff = sum(float(row.get("difference") or 0) for row in self.rows)
        filters = {
            "Document No": header["doc_no"],
            "Date": header["doc_date"],
            "From Warehouse": header["from_warehouse"],
            "To Warehouse": header.get("to_warehouse", ""),
            "Status": header["status"],
            "Rows": len(self.rows),
            "Total Qty": f"{total_qty:.3f}",
            "Difference": f"{total_diff:.3f}",
            "Notes": header.get("notes", ""),
        }
        company = self._company()
        prints = self.config.project_root / "prints"
        safe_doc = self.doc_no.text().replace("/", "_").replace(" ", "_")
        path = prints / f"{self.mode}_{safe_doc}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        write_report_pdf(path, title, company, rows, filters, db_path=self.source.sqlite_path, document_type="report")
        caption = f"{title}: {header['doc_no']}\nDate: {header['doc_date']}\nRows: {len(self.rows)}\nTotal Qty: {total_qty:.3f}"
        return path, caption, ""

    def _communication_message(self, channel: str, fallback_body: str, path: Any) -> dict[str, str]:
        total_qty = sum(float(row.get("qty") or 0) for row in self.rows)
        title = str(self.meta["title"])
        context = document_message_context(
            title=title,
            document_no=self.doc_no.text(),
            party_name=self.warehouse.currentText(),
            amount=total_qty,
            company=self._company(),
            pdf_path=path,
            extra={"rows": len(self.rows), "total_qty": f"{total_qty:.3f}"},
        )
        return communication_message(
            channel=channel,
            document_type=self.mode,
            context=context,
            fallback_subject=f"{title} {self.doc_no.text()}",
            fallback_body=fallback_body,
            db_path=self.source.sqlite_path,
        )

    def _company(self) -> dict[str, Any]:
        try:
            return self.source.company()
        except Exception:
            return {}

    def _inventory_payload(self) -> dict[str, Any]:
        header = {
            "doc_no": self.doc_no.text().strip(),
            "doc_date": self.doc_date.date().toString("yyyy-MM-dd"),
            "from_warehouse": self.from_warehouse.currentText(),
            "from_warehouse_id": self._combo_id(self.from_warehouse.currentText()),
            "to_warehouse": self.to_warehouse.currentText() if self.mode == "transfer" else "",
            "to_warehouse_id": self._combo_id(self.to_warehouse.currentText()) if self.mode == "transfer" else 0,
            "status": self.status.currentText(),
            "notes": self.notes.toPlainText().strip(),
        }
        return {
            "source": "desktop_inventory_entry",
            "mode": self.mode,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "header": header,
            "rows": self.rows,
        }

    def _combo_id(self, text: str) -> int:
        try:
            return int(str(text).split("|", 1)[0].strip())
        except (ValueError, IndexError):
            return 0

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("F4"), self, activated=self.add_line)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_draft)
        QShortcut(QKeySequence("Delete"), self, activated=self.remove_selected_line)


def display_decimal(value: Any) -> str:
    if isinstance(value, Decimal):
        return f"{value:,.3f}"
    return str(value)
