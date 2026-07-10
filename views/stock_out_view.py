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


class StockOutView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
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
        header = TransactionHeader(
            "Stock Out / Load Challan",
            "Route stock loading with vehicle, driver, salesman and item rows | F4 add row | Ctrl+S draft",
            self,
        )
        self.source_status = header.status_label
        return header

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
        self.challan_no = QLineEdit()
        self.challan_date = QDateEdit()
        self.challan_date.setCalendarPopup(True)
        self.challan_date.setDate(QDate.currentDate())
        self.area = QLineEdit()
        self.warehouse = QComboBox()
        self.vehicle_no = QLineEdit()
        self.driver_name = QLineEdit()
        self.driver_phone = QLineEdit()
        self.salesman_name = QLineEdit()
        self.dispatch_status = QComboBox()
        self.dispatch_status.addItems(["Pending Dispatch", "Loaded", "Dispatched", "Completed", "Cancelled"])
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Route notes, loading instructions or dispatch remarks")

        grid.addWidget(self._field("Challan No", self.challan_no, 140), 0, 0)
        grid.addWidget(self._field("Date", self.challan_date, 120), 0, 1)
        grid.addWidget(self._field("Area / Route", self.area, 180), 0, 2)
        grid.addWidget(self._field("Warehouse", self.warehouse, 180), 0, 3)
        grid.addWidget(self._field("Vehicle No", self.vehicle_no, 140), 0, 4)
        grid.addWidget(self._field("Driver", self.driver_name, 160), 1, 0)
        grid.addWidget(self._field("Driver Phone", self.driver_phone, 130), 1, 1)
        grid.addWidget(self._field("Salesman", self.salesman_name, 160), 1, 2)
        grid.addWidget(self._field("Dispatch Status", self.dispatch_status, 160), 1, 3)
        grid.addWidget(self._field("Notes", self.notes, 250), 1, 4)
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
        self.mrp = QLineEdit("0.00")
        self.qty = QLineEdit("1")
        self.free_qty = QLineEdit("0")
        self.total_qty = QLineEdit("1")
        add_button = QPushButton("Add Row  F4")
        add_button.clicked.connect(self.add_line)

        grid.addWidget(self._field("Product Search", self.product, 340), 0, 0, 1, 3)
        grid.addWidget(self._field("HSN", self.hsn, 80), 0, 3)
        grid.addWidget(self._field("Unit", self.unit, 80), 0, 4)
        grid.addWidget(self._field("MRP", self.mrp, 90), 0, 5)
        grid.addWidget(self._field("Qty", self.qty, 90), 0, 6)
        grid.addWidget(self._field("SCH", self.free_qty, 90), 0, 7)
        grid.addWidget(self._field("Total", self.total_qty, 90), 0, 8)
        grid.addWidget(add_button, 0, 9)
        for control in (self.qty, self.free_qty):
            control.textChanged.connect(self._update_line_total)
        grid.setColumnStretch(0, 3)
        for column in range(1, 10):
            grid.setColumnStretch(column, 1)
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
        return ERPFieldBox(label, widget, self)

    def _table_card(self) -> QWidget:
        headers = ["#", "Item", "HSN", "Unit", "MRP", "Qty", "SCH", "Total"]
        self.table = ERPItemGrid(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for col, width in {0: 46, 1: 240, 2: 90, 3: 80, 4: 90, 5: 90, 6: 90, 7: 100}.items():
            self.table.setColumnWidth(col, width)
        # Allow editing of Qty and SCH
        self.table.set_editable_columns({5, 6})
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
        self.total_qty_label = QLabel("Loaded Qty: 0.000")
        self.total_free_label = QLabel("SCH Qty: 0.000")
        self.total_qty_label.setObjectName("metricValue")
        layout.addWidget(self.total_rows)
        layout.addWidget(self.total_qty_label)
        layout.addWidget(self.total_free_label)
        layout.addStretch(1)
        return frame

    def refresh(self) -> None:
        try:
            self.products = self.source.product_choices()
            warehouses = self.source.warehouses()
            self.recent_rows = self.source.operation_rows("load_challans", 100)
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            return
        self.warehouse.clear()
        self.warehouse.addItems([f"{row.get('id')} | {row.get('name')}" for row in warehouses] or ["Main Store"])
        labels = [self._product_label(row) for row in self.products]
        self.product_by_label = dict(zip(labels, self.products))
        self.product.clear()
        self.product.addItems(labels)
        self.source_status.setText(f"{len(self.products)} packs | {len(self.recent_rows)} load challans")

    def add_line(self) -> None:
        product = self.product_by_label.get(self.product.currentText())
        if not product:
            QMessageBox.warning(self, "Stock Out", "Select a product before adding.")
            return
        try:
            qty = float(self.qty.text().replace(",", "") or 0)
            free_qty = float(self.free_qty.text().replace(",", "") or 0)
            mrp = float(self.mrp.text().replace(",", "") or 0)
        except ValueError:
            QMessageBox.warning(self, "Stock Out", "MRP, Qty and SCH must be numeric.")
            return
        if qty < 0 or free_qty < 0:
            QMessageBox.warning(self, "Stock Out", "Quantity cannot be negative.")
            return
        self.rows.append(
            {
                "item_name": product.get("item_name") or "",
                "pack_name": product.get("pack_name") or "",
                "hsn": self.hsn.text().strip(),
                "unit": self.unit.text().strip() or "PCS",
                "mrp": mrp,
                "qty": qty,
                "free_qty": free_qty,
                "total_qty": qty + free_qty,
            }
        )
        self._redraw_rows()
        self.qty.setText("1")
        self.free_qty.setText("0")
        self.product.setFocus()

    def save_draft(self) -> None:
        if not self.challan_no.text().strip():
            QMessageBox.warning(self, "Stock Out", "Challan No is required.")
            self.challan_no.setFocus()
            return
        if not self.area.text().strip():
            QMessageBox.warning(self, "Stock Out", "Area / Route is required.")
            self.area.setFocus()
            return
        if not self.rows:
            QMessageBox.warning(self, "Stock Out", "Add at least one item row.")
            self.product.setFocus()
            return
        payload = {
            "source": "desktop_stock_out",
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "header": {
                "challan_no": self.challan_no.text().strip(),
                "challan_date": self.challan_date.date().toString("yyyy-MM-dd"),
                "area": self.area.text().strip(),
                "warehouse": self.warehouse.currentText(),
                "vehicle_no": self.vehicle_no.text().strip(),
                "driver_name": self.driver_name.text().strip(),
                "driver_phone": self.driver_phone.text().strip(),
                "salesman_name": self.salesman_name.text().strip(),
                "dispatch_status": self.dispatch_status.currentText(),
                "notes": self.notes.toPlainText().strip(),
            },
            "rows": self.rows,
        }
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        path = drafts_dir / f"stock_out_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Stock Out", f"Draft saved:\n{path}")

    def print_document_pdf(self) -> None:
        if not self._can_output_document("previewing"):
            return
        try:
            path, _, _ = self._create_document_pdf()
        except Exception as exc:
            QMessageBox.warning(self, "Stock Out", f"PDF could not be created:\n{exc}")
            return
        show_print_preview(self, path, "Stock Out Print Preview")

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
                QMessageBox.information(self, "Stock Out", f"{result.get('message')}\n\n{pdf_share_note(path)}")
                return
        except Exception as exc:
            QMessageBox.warning(self, "Stock Out", f"Share PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Stock Out", str(result.get("message") or pdf_share_note(path)))

    def email_document_pdf(self) -> None:
        if not self._can_output_document("emailing"):
            return
        try:
            path, caption, _ = self._create_document_pdf()
            message = self._communication_message("email", caption, path)
            result = prepare_email_document("", message["subject"], message["body"], path, db_path=self.source.sqlite_path)
            if not result.get("ok"):
                QMessageBox.warning(self, "Stock Out", str(result.get("message") or "Email could not be prepared."))
                return
        except Exception as exc:
            QMessageBox.warning(self, "Stock Out", f"Email PDF could not be prepared:\n{exc}")
            return
        QMessageBox.information(self, "Stock Out", str(result.get("message") or pdf_share_note(path)))

    def _can_output_document(self, action: str) -> bool:
        if not self.challan_no.text().strip():
            QMessageBox.warning(self, "Stock Out", f"Challan No is required before {action}.")
            self.challan_no.setFocus()
            return False
        if not self.area.text().strip():
            QMessageBox.warning(self, "Stock Out", f"Area / Route is required before {action}.")
            self.area.setFocus()
            return False
        if not self.rows:
            QMessageBox.information(self, "Stock Out", f"Add at least one item row before {action}.")
            self.product.setFocus()
            return False
        return True

    def _create_document_pdf(self) -> tuple[Any, str, str]:
        header = {
            "challan_no": self.challan_no.text().strip(),
            "challan_date": self.challan_date.date().toString("yyyy-MM-dd"),
            "area": self.area.text().strip(),
            "warehouse": self.warehouse.currentText(),
            "vehicle_no": self.vehicle_no.text().strip(),
            "driver_name": self.driver_name.text().strip(),
            "driver_phone": self.driver_phone.text().strip(),
            "salesman_name": self.salesman_name.text().strip(),
            "dispatch_status": self.dispatch_status.currentText(),
            "notes": self.notes.toPlainText().strip(),
        }
        rows = [
            {
                "#": index,
                "Item": f"{row.get('item_name', '')} / {row.get('pack_name', '')}",
                "HSN": row.get("hsn", ""),
                "Unit": row.get("unit", ""),
                "MRP": f"{float(row.get('mrp') or 0):.2f}",
                "Qty": f"{float(row.get('qty') or 0):.3f}",
                "SCH": f"{float(row.get('free_qty') or 0):.3f}",
                "Total": f"{float(row.get('total_qty') or 0):.3f}",
            }
            for index, row in enumerate(self.rows, start=1)
        ]
        qty = sum(float(row.get("qty") or 0) for row in self.rows)
        free_qty = sum(float(row.get("free_qty") or 0) for row in self.rows)
        filters = {
            "Challan No": header["challan_no"],
            "Date": header["challan_date"],
            "Area / Route": header["area"],
            "Warehouse": header["warehouse"],
            "Vehicle": header["vehicle_no"],
            "Driver": header["driver_name"],
            "Salesman": header["salesman_name"],
            "Status": header["dispatch_status"],
            "Loaded Qty": f"{qty:.3f}",
            "SCH Qty": f"{free_qty:.3f}",
            "Notes": header["notes"],
        }
        company = self._company()
        prints = self.config.project_root / "prints"
        safe_doc = header["challan_no"].replace("/", "_").replace(" ", "_")
        path = prints / f"stock_out_{safe_doc}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        write_report_pdf(path, "Stock Out / Load Challan", company, rows, filters, db_path=self.source.sqlite_path, document_type="report")
        caption = f"Stock Out / Load Challan: {header['challan_no']}\nRoute: {header['area']}\nLoaded Qty: {qty:.3f}\nSCH Qty: {free_qty:.3f}"
        return path, caption, header["driver_phone"]

    def _communication_message(self, channel: str, fallback_body: str, path: Any) -> dict[str, str]:
        qty = sum(float(row.get("qty") or 0) for row in self.rows)
        title = "Stock Out / Load Challan"
        context = document_message_context(
            title=title,
            document_no=self.challan_no.text(),
            party_name=self.area.text(),
            amount=qty,
            company=self._company(),
            pdf_path=path,
            extra={"route": self.area.text(), "total_qty": f"{qty:.3f}"},
        )
        return communication_message(
            channel=channel,
            document_type="stock_out",
            context=context,
            fallback_subject=f"{title} {self.challan_no.text()}",
            fallback_body=fallback_body,
            db_path=self.source.sqlite_path,
        )

    def _company(self) -> dict[str, Any]:
        try:
            return self.source.company()
        except Exception:
            return {}

    def clear_document(self) -> None:
        self.challan_no.clear()
        self.challan_date.setDate(QDate.currentDate())
        self.area.clear()
        self.vehicle_no.clear()
        self.driver_name.clear()
        self.driver_phone.clear()
        self.salesman_name.clear()
        self.notes.clear()
        self.rows.clear()
        self._redraw_rows()
        self.challan_no.setFocus()

    def _product_changed(self, label: str) -> None:
        row = self.product_by_label.get(label)
        if not row:
            return
        self.hsn.setText(str(row.get("hsn") or ""))
        self.unit.setText(str(row.get("unit") or "PCS"))
        self.mrp.setText(f"{float(row.get('mrp') or 0):.2f}")

    def _update_line_total(self) -> None:
        try:
            qty = float(self.qty.text().replace(",", "") or 0)
            free_qty = float(self.free_qty.text().replace(",", "") or 0)
            self.total_qty.setText(f"{qty + free_qty:.3f}")
        except ValueError:
            self.total_qty.setText("0.000")

    def _redraw_rows(self) -> None:
        self.table.setRowCount(len(self.rows))
        for index, row in enumerate(self.rows):
            values = [
                str(index + 1),
                f"{row['item_name']} / {row['pack_name']}",
                row["hsn"],
                row["unit"],
                f"{row['mrp']:.2f}",
                f"{row['qty']:.3f}",
                f"{row['free_qty']:.3f}",
                f"{row['total_qty']:.3f}",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in {0, 4, 5, 6, 7}:
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
        qty = sum(float(row["qty"]) for row in self.rows)
        free_qty = sum(float(row["free_qty"]) for row in self.rows)
        self.total_rows.setText(f"Rows: {len(self.rows)}")
        self.total_qty_label.setText(f"Loaded Qty: {qty:,.3f}")
        self.total_free_label.setText(f"SCH Qty: {free_qty:,.3f}")

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("F4"), self, activated=self.add_line)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_draft)
        QShortcut(QKeySequence("Delete"), self, activated=self.remove_selected_line)

    def _product_label(self, row: dict[str, Any]) -> str:
        stock = float(row.get("stock_qty") or 0)
        return f"{row.get('item_name','')} | {row.get('pack_name','')} | Stock {stock:.3f}"


def display_decimal(value: Any) -> str:
    if isinstance(value, Decimal):
        return f"{value:,.3f}"
    return str(value)
