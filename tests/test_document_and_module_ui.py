from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFontDatabase, QKeyEvent, QShortcut
from PyQt6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
)
from reportlab.pdfgen import canvas

from config.app_config import AppConfig
from services.document_archive_service import DocumentArchiveService
from services.share_service import email_url
from views.dashboard_view import DashboardView
from views.account_entry_view import AccountEntryView
from views.developer_console_view import DeveloperConsoleView
from views.document_center_view import DOCUMENT_CATALOG, DocumentCenterView
from views.dispatch_return_view import DispatchReturnView
from views.financial_years_view import FinancialYearAdminView
from views.inventory_entry_view import InventoryEntryView
from views.module_hub_view import ACCOUNTS_OPERATIONS, ADMIN_OPERATIONS, INDUSTRY_OPERATIONS, ModuleHubView, ModuleOperation
from views.numbering_series_view import NumberingSeriesAdminView
from views.product_master_view import ProductMasterView
from views.purchase_entry_view import PurchaseEntryView
from views.purchase_document_view import PurchaseDocumentView
from services.master_repository import MasterRepository
from views.report_center_view import ReportCenterView
from views.route_settlement_view import RouteSettlementView
from views.sales_bill_view import SalesBillView
from views.main_window import MainWindow
from views.sales_document_view import SalesDocumentView
from views.scheme_master_view import SchemeMasterView
from views.simple_master_view import SimpleMasterView
from views.stock_out_view import StockOutView
from widgets.erp_components import (
    ERPBarChart,
    ERPDashboardCard,
    ERPToolbar,
    ERPFieldBox,
    ERPItemGrid,
    ERPLineChart,
    ERPPieChart,
    ERPTransactionGrid,
    GridActionBar,
    TransactionTaxSummaryPanel,
    TransactionHeader,
    TransactionGridPanel,
    TransactionTotalsPanel,
    TransactionToolbar,
)


_APP: QApplication | None = None
PROJECT_ROOT = Path(r"D:\PRM_GST_DESKTOP")


def app() -> QApplication:
    global _APP
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def config() -> AppConfig:
    return AppConfig(project_root=PROJECT_ROOT, source_root=Path(r"D:\PRM_GST_DESKTOP"))


def test_print_bills_id_column_stays_compact() -> None:
    app()
    view = DocumentCenterView(config())
    view.table.setColumnCount(3)
    view._apply_column_widths(["id", "bill_no", "customer_name"])

    assert view.table.columnWidth(0) <= 70
    assert view.table.columnWidth(2) >= 220
    view.close()


def test_document_center_filters_keep_readable_widths() -> None:
    app()
    view = DocumentCenterView(config())

    assert view.view_selector.minimumWidth() >= 200
    assert view.print_doc_type.minimumWidth() >= 200
    assert view.date_preset.minimumWidth() >= 140
    assert view.print_status.minimumWidth() >= 130
    assert view.from_date.minimumWidth() >= 140
    assert view.search.minimumWidth() <= 280
    assert view.show_button.text() == "Show Bills"
    assert "Show Bills" in view.filter_hint.text()
    view.close()


def test_document_center_print_rows_include_checkboxes() -> None:
    app()
    view = DocumentCenterView(config())
    view.open_view("print_bills")
    view.rows = [
        {"id": 1, "bill_no": "B1", "party_name": "Cash Customer"},
        {"id": 2, "bill_no": "B2", "party_name": "Credit Customer"},
    ]
    view._redraw_table()

    assert view.table.horizontalHeaderItem(0).text() == "Select"
    item = view.table.item(0, 0)
    assert item.checkState() == Qt.CheckState.Unchecked
    item.setCheckState(Qt.CheckState.Checked)
    assert view._selected_rows()[0]["id"] == 1
    view.select_all.setChecked(True)
    assert [view.table.item(row, 0).checkState() for row in range(view.table.rowCount())] == [
        Qt.CheckState.Checked,
        Qt.CheckState.Checked,
    ]
    assert [row["id"] for row in view._selected_rows()] == [1, 2]
    view.close()


def _headers(widget) -> list[str]:
    return [widget.horizontalHeaderItem(index).text() for index in range(widget.columnCount())]


def _labels(widget) -> set[str]:
    return {label.text() for label in widget.findChildren(QLabel)}


def _assert_field_labels_do_not_overlap_controls(widget) -> None:
    widget.resize(1440, 900)
    widget.show()
    app().processEvents()
    for box in widget.findChildren(QFrame):
        if box.objectName() != "fieldBox" or box.layout() is None or box.layout().count() < 2:
            continue
        label = box.layout().itemAt(0).widget()
        control = box.layout().itemAt(1).widget()
        if not isinstance(label, QLabel) or label.objectName() != "fieldLabel" or control is None:
            continue
        assert label.geometry().bottom() + 2 < control.geometry().top(), (
            f"{widget.__class__.__name__} label overlaps control: {label.text()}"
        )


def _select_combo_text(combo: QComboBox, text: str) -> None:
    index = combo.findText(text)
    if index >= 0:
        combo.setCurrentIndex(index)
    else:
        combo.setCurrentText(text)


def _first_combo_value(combo: QComboBox) -> str:
    placeholders = ("select ", "choose ")
    for index in range(combo.count()):
        text = combo.itemText(index).strip()
        if text and not text.lower().startswith(placeholders):
            return text
    return ""


def _prepare_item_transaction(view) -> None:
    for mapping_name, combo_name in (
        ("customer_by_label", "customer"),
        ("supplier_by_label", "supplier"),
    ):
        mapping = getattr(view, mapping_name, {})
        combo = getattr(view, combo_name, None)
        if mapping and isinstance(combo, QComboBox):
            _select_combo_text(combo, next(iter(mapping)))

    for combo_name in ("customer", "supplier"):
        combo = getattr(view, combo_name, None)
        if isinstance(combo, QComboBox) and not combo.currentData():
            text = _first_combo_value(combo)
            if text:
                _select_combo_text(combo, text)

    product_mapping = getattr(view, "product_by_label", {})
    product = getattr(view, "product", None)
    if product_mapping and isinstance(product, QComboBox):
        positive_stock = [
            (label, row)
            for label, row in product_mapping.items()
            if float(row.get("stock_qty") or 0) >= 1
        ]
        label = (positive_stock or list(product_mapping.items()))[0][0]
        _select_combo_text(product, label)

    for name, value in {
        "qty": "1",
        "free_qty": "0",
        "discount": "0",
        "scheme": "0",
        "mrp": "1.00",
        "rate": "1.00",
    }.items():
        widget = getattr(view, name, None)
        if hasattr(widget, "text") and hasattr(widget, "setText"):
            current = widget.text().strip()
            if name not in {"qty", "free_qty", "discount", "scheme"} and current not in {"", "0", "0.00"}:
                continue
            widget.setText(value)


def test_item_entry_uses_sch_before_discount() -> None:
    app()

    assert SalesDocumentView.headers == [
        "#",
        "Item",
        "HSN",
        "Qty",
        "Unit",
        "MRP",
        "Rate",
        "SCH",
        "Disc",
        "Taxable",
        "GST %",
        "Amount",
    ]

    views = [
        SalesBillView(config()),
        PurchaseEntryView(config()),
        StockOutView(config()),
        DispatchReturnView(config()),
        SchemeMasterView(config()),
        RouteSettlementView(config()),
    ]
    try:
        for view in views[:2]:
            headers = _headers(view.table)
            assert headers.index("Rate") < headers.index("SCH") < headers.index("Disc")
            assert "Free" not in headers

        assert "SCH" in _headers(views[2].table)
        assert "Free" not in _headers(views[2].table)
        assert "SCH Return" in _headers(views[3].table)
        assert "Free Return" not in _headers(views[3].table)
        assert "SCH Qty" in _labels(views[4])
        assert "Loaded SCH" in _labels(views[5])
    finally:
        for view in views:
            view.close()


def test_transaction_views_expose_shared_erp_components() -> None:
    app()
    views = [
        SalesBillView(config()),
        PurchaseEntryView(config()),
        SalesDocumentView(config(), "quotation"),
        InventoryEntryView(config(), "stock_entry"),
    ]
    try:
        for view in views:
            assert view.findChild(TransactionHeader) is not None
            assert view.findChild(TransactionToolbar) is not None
            assert view.findChild(ERPFieldBox) is not None
            assert view.property("transactionFramework") is True
    finally:
        for view in views:
            view.close()


def test_all_transaction_families_use_one_framework() -> None:
    app()
    views = [
        SalesBillView(config()),
        SalesDocumentView(config(), "sales_order"),
        SalesDocumentView(config(), "quotation"),
        SalesDocumentView(config(), "delivery_challan"),
        SalesDocumentView(config(), "sales_return"),
        PurchaseEntryView(config()),
        PurchaseDocumentView(config(), "purchase_order"),
        PurchaseDocumentView(config(), "purchase_return"),
        InventoryEntryView(config(), "stock_entry"),
        InventoryEntryView(config(), "transfer"),
        InventoryEntryView(config(), "adjustment"),
        StockOutView(config()),
        DispatchReturnView(config()),
        RouteSettlementView(config()),
        AccountEntryView(config(), "receipt"),
        AccountEntryView(config(), "payment"),
        AccountEntryView(config(), "journal"),
    ]
    try:
        for view in views:
            header = view.findChild(TransactionHeader)
            toolbar = view.findChild(TransactionToolbar)
            grid = view.findChild(ERPTransactionGrid)
            assert header is not None, view.__class__.__name__
            assert toolbar is not None, view.__class__.__name__
            assert grid is not None, view.__class__.__name__
            assert [toolbar.buttons[label].text() for label in TransactionToolbar.ACTION_ORDER] == list(
                TransactionToolbar.ACTION_ORDER
            )
    finally:
        for view in views:
            view.close()


def test_shared_transaction_buttons_feedback_and_unimplemented_message(monkeypatch) -> None:
    app()
    messages: list[str] = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: messages.append(str(args[2])) or None)
    called: list[str] = []
    toolbar = TransactionToolbar([("Save", lambda: called.append("save")), ("Preview", None)])
    try:
        toolbar.buttons["Preview"].click()
        app().processEvents()
        assert toolbar.buttons["Preview"].property("recentClick") is True
        assert messages and "Preview is not available" in messages[-1]

        toolbar.buttons["Save"].click()
        app().processEvents()
        assert called == ["save"]
        assert toolbar.buttons["Save"].property("recentClick") is True
        assert toolbar.buttons["Save"].property("_erpFeedbackInstalled") is True
    finally:
        toolbar.close()


def test_generic_erp_toolbar_unavailable_action_feedback(monkeypatch) -> None:
    app()
    messages: list[str] = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: messages.append(str(args[2])) or None)
    toolbar = ERPToolbar([("Export", None), ("Refresh", lambda: None)])
    try:
        buttons = {button.text(): button for button in toolbar.findChildren(QPushButton)}
        buttons["Export"].click()
        app().processEvents()
        assert buttons["Export"].property("_erpFeedbackInstalled") is True
        assert messages and "Export is not available" in messages[-1]
    finally:
        toolbar.close()


def test_transaction_layout_installs_feedback_for_local_buttons() -> None:
    app()
    view = SalesDocumentView(config(), "quotation")
    try:
        add_button = next(button for button in view.findChildren(QPushButton) if button.text().startswith("Add Row"))
        grid_button = view.findChild(GridActionBar).buttons["scan_barcode"]
        assert add_button.property("_erpFeedbackInstalled") is True
        assert grid_button.property("_erpFeedbackInstalled") is True
    finally:
        view.close()


def test_sales_document_preview_uses_pdf_print_path(monkeypatch) -> None:
    app()
    opened: list[tuple[Path, str]] = []
    monkeypatch.setattr("views.sales_document_view.show_print_preview", lambda parent, path, title: opened.append((Path(path), title)))
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    view = SalesDocumentView(config(), "quotation")
    try:
        _prepare_item_transaction(view)
        view.add_line()
        assert view.computed_lines
        toolbar = view.findChild(TransactionToolbar)
        assert toolbar is not None
        toolbar.buttons["Preview"].click()
        app().processEvents()
        assert opened
        assert opened[0][0].exists()
        assert opened[0][1] == "Quotation Print Preview"
    finally:
        view.close()


def test_email_url_encodes_subject_and_body() -> None:
    url = email_url("qa@example.com", "Invoice A/B", "PDF path: C:/PRM/prints/a b.pdf")

    assert url.startswith("mailto:qa%40example.com?")
    assert "Invoice%20A/B" in url
    assert "a%20b.pdf" in url


def test_remaining_transaction_output_actions_create_report_pdfs(monkeypatch) -> None:
    app()
    opened: list[tuple[Path, str]] = []
    monkeypatch.setattr("views.inventory_entry_view.show_print_preview", lambda parent, path, title: opened.append((Path(path), title)))
    monkeypatch.setattr("views.stock_out_view.show_print_preview", lambda parent, path, title: opened.append((Path(path), title)))
    monkeypatch.setattr("views.dispatch_return_view.show_print_preview", lambda parent, path, title: opened.append((Path(path), title)))
    monkeypatch.setattr("views.route_settlement_view.show_print_preview", lambda parent, path, title: opened.append((Path(path), title)))
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

    inventory = InventoryEntryView(config(), "stock_entry")
    stock_out = StockOutView(config())
    dispatch_return = DispatchReturnView(config())
    route = RouteSettlementView(config())
    views = [inventory, stock_out, dispatch_return, route]
    try:
        inventory.doc_no.setText("INV-QA-001")
        inventory.rows = [
            {
                "item_name": "QA Item",
                "pack_name": "Pack",
                "hsn": "9987",
                "unit": "PCS",
                "current": 2.0,
                "qty": 5.0,
                "difference": 5.0,
                "reason": "QA",
            }
        ]
        inventory._redraw_rows()

        stock_out.challan_no.setText("LOAD-QA-001")
        stock_out.area.setText("QA Route")
        stock_out.rows = [
            {
                "item_name": "QA Item",
                "pack_name": "Pack",
                "hsn": "9987",
                "unit": "PCS",
                "mrp": 10.0,
                "qty": 3.0,
                "free_qty": 1.0,
                "total_qty": 4.0,
            }
        ]
        stock_out._redraw_rows()

        source_label = "SO-QA-001 | 2026-07-10 | QA Customer | QA Route | Loaded"
        dispatch_return.source_doc.clear()
        dispatch_return.source_doc.addItem(source_label)
        dispatch_return.source_doc.setCurrentText(source_label)
        dispatch_return.source_by_label = {
            source_label: {
                "source_table": "stock_outs",
                "id": 1,
                "source_ref": "SO-QA-001",
                "customer_name": "QA Customer",
                "route": "QA Route",
                "dispatch_status": "Loaded",
            }
        }
        dispatch_return.return_no.setText("DRTN-QA-001")
        dispatch_return.lines = [
            {
                "item_name": "QA Item",
                "pack_name": "Pack",
                "unit": "PCS",
                "dispatched_qty": 4.0,
                "returned_qty": 0.0,
                "available_qty": 4.0,
                "available_free_qty": 1.0,
            }
        ]
        dispatch_return._redraw_lines()
        dispatch_return._set_cell(0, 5, "2.000")
        dispatch_return._set_cell(0, 7, "2.000")

        route.settlement_no.setText("RST-QA-001")
        route.area.setText("QA Route")
        route.cash_sales.setText("100.00")
        route.receipts_total.setText("50.00")
        route.collected_cash.setText("150.00")

        for view in views:
            toolbar = view.findChild(TransactionToolbar)
            assert toolbar is not None
            toolbar.buttons["Preview"].click()
            app().processEvents()

        assert len(opened) == 4
        assert all(path.exists() for path, _ in opened)
        assert [title for _, title in opened] == [
            "Stock Entry Print Preview",
            "Stock Out Print Preview",
            "Dispatch Return Print Preview",
            "Route Settlement Print Preview",
        ]
    finally:
        for view in views:
            view.close()


def test_transaction_toolbars_do_not_leave_silent_disabled_actions() -> None:
    app()
    view = SalesDocumentView(config(), "quotation")
    try:
        toolbar = view.findChild(TransactionToolbar)
        assert toolbar is not None
        for label in TransactionToolbar.ACTION_ORDER:
            button = toolbar.buttons[label]
            assert button.isEnabled(), label
            assert button.property("_erpFeedbackInstalled") is True
    finally:
        view.close()


def test_item_entry_add_row_f4_and_delete_are_shared_and_safe(monkeypatch) -> None:
    app()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    views = [
        ("sales_bill", SalesBillView(config()), True),
        ("purchase_entry", PurchaseEntryView(config()), True),
        ("quotation", SalesDocumentView(config(), "quotation"), True),
        ("sales_order", SalesDocumentView(config(), "sales_order"), True),
        ("delivery_challan", SalesDocumentView(config(), "delivery_challan"), True),
        ("sales_return", SalesDocumentView(config(), "sales_return"), False),
        ("purchase_order", PurchaseDocumentView(config(), "purchase_order"), True),
        ("purchase_return", PurchaseDocumentView(config(), "purchase_return"), False),
        ("stock_entry", InventoryEntryView(config(), "stock_entry"), True),
        ("stock_transfer", InventoryEntryView(config(), "transfer"), True),
        ("stock_adjustment", InventoryEntryView(config(), "adjustment"), True),
        ("stock_out", StockOutView(config()), True),
        ("dispatch_return", DispatchReturnView(config()), False),
    ]

    try:
        for name, view, row_add_expected in views:
            _prepare_item_transaction(view)
            view.show()
            app().processEvents()

            assert isinstance(view.table, ERPItemGrid), name
            assert view.findChild(GridActionBar) is not None, name
            if name != "dispatch_return":
                assert view.findChild(TransactionGridPanel) is not None, name

            before_rows = view.table.rowCount()
            add_button = view.findChild(GridActionBar).buttons["add_row"]
            if add_button.isEnabled():
                add_button.click()
                app().processEvents()
            after_button_rows = view.table.rowCount()

            view.table.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F4, Qt.KeyboardModifier.NoModifier))
            app().processEvents()
            after_f4_rows = view.table.rowCount()

            if row_add_expected:
                assert after_button_rows >= before_rows + 1, name
                assert after_f4_rows >= after_button_rows + 1, name
                assert view.table.currentRow() == after_f4_rows - 1, name
                assert view.table.currentColumn() == view.table._editable_column_list()[0], name
            else:
                assert after_button_rows >= before_rows, name
                assert after_f4_rows >= after_button_rows, name

            view.table.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier))
            app().processEvents()
            assert view.table.rowCount() >= 0, name
    finally:
        for _, view, _ in views:
            view.close()


def test_item_entry_totals_panel_updates_grand_total_and_tax_summary(monkeypatch) -> None:
    app()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    views = [
        ("sales_bill", SalesBillView(config())),
        ("purchase_entry", PurchaseEntryView(config())),
        ("quotation", SalesDocumentView(config(), "quotation")),
        ("sales_order", SalesDocumentView(config(), "sales_order")),
        ("delivery_challan", SalesDocumentView(config(), "delivery_challan")),
        ("purchase_order", PurchaseDocumentView(config(), "purchase_order")),
    ]
    try:
        for name, view in views:
            _prepare_item_transaction(view)
            view.add_line()
            app().processEvents()
            totals_panel = view.findChild(TransactionTotalsPanel)
            tax_panel = view.findChild(TransactionTaxSummaryPanel)
            assert totals_panel is not None, name
            assert tax_panel is not None, name
            assert "Grand Total" in totals_panel.labels["grand_total"].text(), name
            assert "Rs 0.00" not in totals_panel.labels["grand_total"].text(), name
            assert "Total Quantity" in totals_panel.labels["total_qty"].text(), name
            assert "Discount" in totals_panel.labels["discount"].text(), name
            assert "CGST" in totals_panel.labels["cgst"].text(), name
            assert "SGST" in totals_panel.labels["sgst"].text(), name
            assert "IGST" in totals_panel.labels["igst"].text(), name
            assert "Total Amount" in totals_panel.labels["total_amount"].text(), name
            assert tax_panel.table.rowCount() >= 1, name
    finally:
        for _, view in views:
            view.close()


def test_return_documents_keep_visible_zero_totals_without_source_items() -> None:
    app()
    views = [
        ("sales_return", SalesDocumentView(config(), "sales_return")),
        ("purchase_return", PurchaseDocumentView(config(), "purchase_return")),
    ]
    try:
        for name, view in views:
            totals_panel = view.findChild(TransactionTotalsPanel)
            tax_panel = view.findChild(TransactionTaxSummaryPanel)
            assert totals_panel is not None, name
            assert tax_panel is not None, name
            assert "Grand Total" in totals_panel.labels["grand_total"].text(), name
            assert "Rs 0.00" in totals_panel.labels["grand_total"].text(), name
            assert tax_panel.table.item(0, 0).text() == "No data available", name
    finally:
        for _, view in views:
            view.close()


def test_transaction_grid_keyboard_navigation_and_commands() -> None:
    app()
    grid = ERPTransactionGrid(2, 5)
    grid.set_editable_columns({1, 2, 4})
    grid.setColumnHidden(2, True)
    called: list[str] = []
    grid.set_command_handlers({"add_row": lambda: called.append("add"), "save": lambda: called.append("save")})
    grid.setCurrentCell(0, 1)

    grid.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_End, Qt.KeyboardModifier.NoModifier))
    assert (grid.currentRow(), grid.currentColumn()) == (0, 4)
    grid.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Home, Qt.KeyboardModifier.NoModifier))
    assert (grid.currentRow(), grid.currentColumn()) == (0, 1)
    grid.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_End, Qt.KeyboardModifier.ControlModifier))
    assert (grid.currentRow(), grid.currentColumn()) == (1, 4)
    grid.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Home, Qt.KeyboardModifier.ControlModifier))
    assert (grid.currentRow(), grid.currentColumn()) == (0, 1)

    grid.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F4, Qt.KeyboardModifier.NoModifier))
    grid.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F8, Qt.KeyboardModifier.NoModifier))
    assert called == ["add", "save"]
    grid.close()


def test_sales_bill_advanced_controls_stay_in_more_details_dialog() -> None:
    app()
    view = SalesBillView(config())
    try:
        view.resize(1440, 900)
        view.show()
        app().processEvents()
        assert all(control.isHidden() for control in (view.employee, view.warehouse, view.branch, view.cost_center))
        assert view.table.columnWidth(1) >= 120
    finally:
        view.close()


def test_secondary_detail_dialogs_fit_compact_desktop(monkeypatch) -> None:
    app()
    checked_titles: list[str] = []

    def inspect_dialog(dialog: QDialog) -> QDialog.DialogCode:
        dialog.adjustSize()
        dialog.show()
        app().processEvents()
        assert dialog.width() <= 1200, dialog.windowTitle()
        assert dialog.height() <= 700, dialog.windowTitle()
        assert not _horizontally_clipped_control_names(dialog), dialog.windowTitle()
        checked_titles.append(dialog.windowTitle())
        dialog.hide()
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", inspect_dialog)
    sales = SalesBillView(config())
    product = ProductMasterView(config())
    try:
        sales.open_more_details()
        product.open_notes()
        assert checked_titles == ["Sales Bill - More Details", "Advanced Product Details"]
    finally:
        sales.close()
        product.close()


def test_entry_page_labels_do_not_overlap_controls() -> None:
    app()
    views = [
        SalesBillView(config()),
        PurchaseEntryView(config()),
        SalesDocumentView(config(), "quotation"),
        SalesDocumentView(config(), "sales_return"),
        PurchaseDocumentView(config(), "purchase_order"),
        PurchaseDocumentView(config(), "purchase_return"),
        StockOutView(config()),
        DispatchReturnView(config()),
        InventoryEntryView(config(), "stock_entry"),
        InventoryEntryView(config(), "transfer"),
        InventoryEntryView(config(), "adjustment"),
        ProductMasterView(config()),
        SchemeMasterView(config()),
        RouteSettlementView(config()),
        FinancialYearAdminView(config()),
        NumberingSeriesAdminView(config()),
    ]
    try:
        for view in views:
            _assert_field_labels_do_not_overlap_controls(view)
    finally:
        for view in views:
            view.close()


def test_product_master_view_has_search_and_hotkeys() -> None:
    app()
    view = ProductMasterView(config())
    try:
        assert view.search.placeholderText() == "Search product, code, barcode, supplier, HSN"
        shortcut_keys = {shortcut.key().toString() for shortcut in view.findChildren(QShortcut)}
        assert {"Ctrl+S", "Ctrl+N", "Ctrl+F", "F4", "Del", "Esc"}.issubset(shortcut_keys)
        assert view.pack_table.columnCount() == len(view.pack_headers)
        assert view.product_table.columnCount() == len(view.list_headers)
        called = {"value": False}
        view.search.returnPressed.connect(lambda: called.__setitem__("value", True))
        view.search.returnPressed.emit()
        assert called["value"] is True
        labels = [label.text() for label in view.findChildren(QLabel) if label.objectName() == "fieldLabel"]
        assert any("Product Code" in label for label in labels)
        assert any("Product Name" in label for label in labels)
        assert any("Category" in label for label in labels)

        # Ensure Enter and Shift+Enter move focus through form controls.
        first_control = view.code
        second_control = view.name
        first_control.setFocus()
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        app().sendEvent(first_control, event)
        assert view.focusWidget() is not first_control
        prev_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
        app().sendEvent(second_control, prev_event)
        assert view.focusWidget() is not second_control
    finally:
        view.close()


def test_simple_master_branch_warehouse_cost_center_views_load_and_branch_id_saves(tmp_path: Path, monkeypatch) -> None:
    app()
    db_path = tmp_path / "prm_billing_inventory.db"
    repo = MasterRepository(db_path)
    repo.ensure_schema()
    monkeypatch.setenv("PRM_SQLITE_DB", str(db_path))
    monkeypatch.setenv("PRM_USE_SQLITE", "0")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    branch_id = repo.save_simple(
        "branch",
        0,
        {
            "code": "BRQA",
            "name": "QA Branch",
            "state": "Telangana",
            "is_active": True,
        },
    )

    branch_view = SimpleMasterView(config(), "branch")
    warehouse_view = SimpleMasterView(config(), "warehouse")
    cost_center_view = SimpleMasterView(config(), "cost_center")
    try:
        assert branch_view.spec.mode == "branch"
        assert warehouse_view.spec.mode == "warehouse"
        assert cost_center_view.spec.mode == "cost_center"

        branch_combo = warehouse_view.controls["branch_id"]
        assert branch_combo.count() >= 1
        assert any(isinstance(branch_combo.itemData(idx), int) for idx in range(branch_combo.count()))

        selected_index = next(
            (idx for idx in range(branch_combo.count()) if branch_combo.itemData(idx) == branch_id),
            0,
        )
        branch_combo.setCurrentIndex(selected_index)
        assert branch_combo.currentData() == branch_id
        assert branch_combo.currentData() != branch_combo.currentText()

        warehouse_view.controls["code"].setText("WHQA")
        warehouse_view.controls["name"].setText("QA Warehouse")
        warehouse_view.controls["address"].setText("Warehouse Road")
        warehouse_view.controls["contact_person"].setText("Mr X")
        warehouse_view.controls["phone"].setText("9000000000")
        warehouse_view.save_draft()

        with sqlite3.connect(db_path) as conn:
            row = conn.execute("SELECT branch_id FROM warehouses WHERE code=?", ("WHQA",)).fetchone()
        assert row is not None
        assert row[0] == branch_id
    finally:
        branch_view.close()
        warehouse_view.close()
        cost_center_view.close()


def test_simple_master_route_salesman_vehicle_views_load_and_route_ids_save(tmp_path: Path, monkeypatch) -> None:
    app()
    db_path = tmp_path / "prm_billing_inventory.db"
    repo = MasterRepository(db_path)
    repo.ensure_schema()
    monkeypatch.setenv("PRM_SQLITE_DB", str(db_path))
    monkeypatch.setenv("PRM_USE_SQLITE", "0")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    salesman_id = repo.save_simple(
        "salesman",
        0,
        {
            "code": "SMQA",
            "name": "QA Salesman",
            "mobile": "9000000000",
            "email": "salesman@example.com",
            "address": "Beat 1",
            "is_active": True,
        },
    )
    vehicle_id = repo.save_simple(
        "vehicle",
        0,
        {
            "code": "VHQA",
            "vehicle_no": "TS09AB1234",
            "vehicle_type": "Van",
            "driver_name": "Ramesh",
            "driver_mobile": "9000000001",
            "capacity": 1500,
            "is_active": True,
        },
    )

    route_view = SimpleMasterView(config(), "route")
    try:
        assert route_view.spec.mode == "route"

        sales_combo = route_view.controls["salesman_id"]
        vehicle_combo = route_view.controls["vehicle_id"]
        assert any(isinstance(sales_combo.itemData(idx), int) for idx in range(sales_combo.count()))
        assert any(isinstance(vehicle_combo.itemData(idx), int) for idx in range(vehicle_combo.count()))

        selected_sales_index = next(
            (idx for idx in range(sales_combo.count()) if sales_combo.itemData(idx) == salesman_id),
            0,
        )
        selected_vehicle_index = next(
            (idx for idx in range(vehicle_combo.count()) if vehicle_combo.itemData(idx) == vehicle_id),
            0,
        )
        sales_combo.setCurrentIndex(selected_sales_index)
        vehicle_combo.setCurrentIndex(selected_vehicle_index)
        assert sales_combo.currentData() == salesman_id
        assert vehicle_combo.currentData() == vehicle_id

        route_view.controls["code"].setText("RTQA")
        route_view.controls["name"].setText("QA Route")
        route_view.controls["area"].setText("North Zone")
        route_view.save_draft()

        with sqlite3.connect(db_path) as conn:
            row = conn.execute("SELECT salesman_id,vehicle_id FROM routes WHERE code=?", ("RTQA",)).fetchone()

        assert row is not None
        assert row[0] == salesman_id
        assert row[1] == vehicle_id
    finally:
        route_view.close()


def test_sales_document_view_has_consistent_toolbar_and_header() -> None:
    app()
    view = SalesDocumentView(config(), "quotation")
    try:
        toolbar = view.findChild(QFrame, "actionToolbar")
        assert toolbar is not None
        assert toolbar.layout().count() >= 6
        assert view.findChild(QFrame, "pageHeader") is not None
    finally:
        view.close()


def test_main_window_has_operational_master_pages() -> None:
    app()
    window = MainWindow(config())
    try:
        assert "route_master" in window.pages
        assert "salesman_master" in window.pages
        assert "vehicle_master" in window.pages
        assert "transporter_master" in window.pages
        assert "bank_master" in window.pages
        assert "tax_master" in window.pages
        assert "payment_term_master" in window.pages
        assert window.pages["route_master"].__class__.__name__ == "SimpleMasterView"
        assert window.pages["salesman_master"].__class__.__name__ == "SimpleMasterView"
        assert window.pages["vehicle_master"].__class__.__name__ == "SimpleMasterView"
        assert window.pages["transporter_master"].__class__.__name__ == "SimpleMasterView"
        assert window.pages["bank_master"].__class__.__name__ == "SimpleMasterView"
        assert window.pages["tax_master"].__class__.__name__ == "SimpleMasterView"
        assert window.pages["payment_term_master"].__class__.__name__ == "SimpleMasterView"
    finally:
        window.close()


def test_main_window_shell_matches_locked_navigation_surface() -> None:
    app()
    window = MainWindow(config())
    try:
        assert "Segoe UI" in QFontDatabase.families()
        assert 160 <= window.command_search.minimumWidth() <= 220
        assert 280 <= window.command_search.maximumWidth() <= 340
        sidebar = window.findChild(QFrame, "sidebar")
        assert sidebar.minimumWidth() <= 168
        assert sidebar.maximumWidth() <= 188

        sidebar_labels = [button.text() for button in window.sidebar_buttons.values()]
        assert sidebar_labels == [
            "Dashboard",
            "Sales",
            "Sales Order",
            "Quotation",
            "Delivery Challan",
            "Sales Return",
            "Purchase",
            "Purchase Order",
            "Goods Receipt",
            "Purchase Return",
            "Inventory",
            "Accounts",
            "Reports",
            "Settings",
        ]

        ribbon_labels = [button.text() for button in window.ribbon_layout.findChildren(QPushButton)]
        assert ribbon_labels[:3] == ["Home", "Masters", "Sales"]
        assert ribbon_labels[-2:] == ["Administration", "Developer"]
        assert ribbon_labels.index("Document Center") > ribbon_labels.index("Reports")

        window.open_page("quotation_entry", remember=False)
        assert window.sidebar_buttons["quotation_entry"].property("active") is True
    finally:
        window.close()


def test_developer_console_exposes_communication_admin_tab() -> None:
    app()
    view = DeveloperConsoleView(config())
    try:
        labels = [view.tabs.tabText(index) for index in range(view.tabs.count())]
        assert "Communication" in labels
        assert view.email_delivery_mode.currentText() in {"handoff", "smtp"}
        assert view.email_smtp_port.value() >= 1
        assert view.communication_retry_table is not None
        assert view.communication_log_table is not None
        view.email_delivery_mode.setCurrentText("handoff")
        view.test_email_delivery_settings()
        assert "smtp_not_enabled" in view.comm_delivery_diagnostics.text()
        view.comm_test_whatsapp.setText("9000000000")
        view.check_whatsapp_delivery_link()
        assert "link_ready" in view.comm_delivery_diagnostics.text()
        subtab_labels = [view.communication_tabs.tabText(index) for index in range(view.communication_tabs.count())]
        assert subtab_labels == ["Delivery", "Message Templates"]
        assert view.communication_template_table.rowCount() >= 1
        assert view.template_code is not view.comm_template_code
        assert view.comm_contact_field.findData("billing_email") >= 0
        view.comm_template_channel.setCurrentText("email")
        view.comm_template_document_type.setCurrentText("sales_invoice")
        view.comm_contact_field.setCurrentIndex(view.comm_contact_field.findData("billing_email"))
        view.comm_template_subject.setText("Invoice {document_no}")
        view.comm_template_body.setPlainText("Dear {party_name}, amount {amount}.")
        view.preview_communication_template()
        assert "Invoice DEMO-001" in view.comm_template_preview.toPlainText()
        assert "billing_email" in view.comm_contact_result.text()
    finally:
        view.close()


def test_executive_dashboard_uses_shared_cards_and_real_charts() -> None:
    app()
    opened: list[str] = []
    view = DashboardView(config(), opened.append)
    try:
        card_titles = [card.title_label.text() for card in view.findChildren(ERPDashboardCard)]
        required = {
            "Company Information",
            "Today's Business Summary",
            "Sales KPIs",
            "Purchase KPIs",
            "Cash & Bank Summary",
            "Receivables",
            "Payables",
            "Stock Value",
            "Low Stock Alerts",
            "Expiry Alerts",
            "Pending Dispatch",
            "Pending Purchase Orders",
            "Pending Sales Orders",
            "Critical Alerts",
            "Communication Status",
            "Failed Communications",
            "Top Customers",
            "Top Selling Products",
            "Recent Sales",
            "Recent Purchase",
            "Recent Receipts",
            "Recent Payments",
            "Daily Tasks",
            "Backup Status",
            "Database Health",
            "Application Version",
        }
        assert required.issubset(set(card_titles))
        assert "Work Center - Frequently Used Operations" not in {label.text() for label in view.findChildren(QLabel)}
        assert len(view.findChildren(ERPDashboardCard)) >= len(required)
        assert all(card.refresh_button.isEnabled() for card in view.findChildren(ERPDashboardCard))
        assert view.findChild(ERPLineChart) is not None
        assert view.findChild(ERPPieChart) is not None
        assert view.findChild(ERPBarChart) is not None
    finally:
        view.close()


def test_executive_dashboard_recent_rows_route_to_documents() -> None:
    app()
    opened: list[str] = []
    view = DashboardView(config(), opened.append)
    try:
        view.tables["recent_sales"].rowActivated.emit({"id": 11})
        view.tables["recent_purchase"].rowActivated.emit({"id": 12})
        view.tables["recent_receipts"].rowActivated.emit({"id": 13})
        view.tables["recent_payments"].rowActivated.emit({"id": 14})
        assert opened == [
            "document:sales:11",
            "document:purchases:12",
            "document:receipts:13",
            "document:payments:14",
        ]
    finally:
        view.close()


def test_document_center_all_subviews_fit_and_keep_buttons_wired() -> None:
    app()
    window = MainWindow(config())
    try:
        window.resize(1366, 768)
        window.show()
        window.open_page("document_center", remember=False)
        app().processEvents()
        page = window.pages["document_center"]

        for _label, key in DOCUMENT_CATALOG:
            page.open_view(key)
            window._fit_page_to_width(page)
            app().processEvents()
            app().processEvents()

            assert page.view_selector.currentData() == key
            assert window.content_scroll.horizontalScrollBar().maximum() == 0, key
            assert not _field_label_overlap_names(page), key
            assert not _horizontally_clipped_control_names(page), key
            assert not _clipped_table_header_names(page), key
            assert not _hidden_table_scrollbar_names(page), key
            dead_buttons = [
                button.text().strip() or button.objectName() or button.__class__.__name__
                for button in page.findChildren(QPushButton)
                if button.isVisibleTo(page) and button.isEnabled() and button.receivers(button.clicked) == 0
            ]
            assert not dead_buttons, (key, dead_buttons)
    finally:
        window.close()


def test_module_hub_operation_states_fit_and_keep_buttons_wired() -> None:
    app()
    window = MainWindow(config())
    hub_pages = ["masters", "sales", "purchase", "inventory", "accounts", "document_hub", "administration"]
    try:
        window.resize(1366, 768)
        window.show()
        for page_key in hub_pages:
            window.open_page(page_key, remember=False)
            app().processEvents()
            page = window.pages[page_key]
            assert isinstance(page, ModuleHubView), page_key
            for operation in page.operations:
                page.open_operation(operation)
                page.show_options()
                window._fit_page_to_width(page)
                app().processEvents()
                app().processEvents()

                assert window.content_scroll.horizontalScrollBar().maximum() == 0, (page_key, operation.key)
                assert not _horizontally_clipped_control_names(page), (page_key, operation.key)
                assert not _clipped_table_header_names(page), (page_key, operation.key)
                assert not _hidden_table_scrollbar_names(page), (page_key, operation.key)
                dead_buttons = [
                    button.text().strip() or button.objectName() or button.__class__.__name__
                    for button in page.findChildren(QPushButton)
                    if button.isVisibleTo(page) and button.isEnabled() and button.receivers(button.clicked) == 0
                ]
                assert not dead_buttons, (page_key, operation.key, dead_buttons)
    finally:
        window.close()


def test_transaction_page_height_tracks_active_viewport() -> None:
    app()
    window = MainWindow(config())
    try:
        window.resize(1536, 920)
        window.show()
        window.open_page("sales_order_entry", remember=False)
        app().processEvents()

        page = window.pages["sales_order_entry"]
        summaries = [
            frame for frame in page.findChildren(QFrame) if frame.property("transactionSummaryRegion") is True
        ]
        assert window.stack.height() == window.content_scroll.viewport().height()
        assert page.height() == window.content_scroll.viewport().height()
        assert summaries
        assert summaries[0].geometry().bottom() <= page.height()
    finally:
        window.close()


def test_all_registered_pages_fit_target_resolutions_without_horizontal_overflow() -> None:
    app()
    window = MainWindow(config())
    pages = sorted(window.page_factories)
    desktop_sizes = [
        (1366, 768),
        (1440, 900),
        (1920, 1080),
        (1093, 614),  # 1366x768 at 125% Windows scaling
        (911, 512),  # 1366x768 at 150% Windows scaling
    ]
    try:
        for width, height in desktop_sizes:
            window.resize(width, height)
            window.show()
            app().processEvents()
            assert (window.width(), window.height()) == (width, height)
            if width < 1000:
                assert window.sidebar.maximumWidth() <= 148
            for page_key in pages:
                window.open_page(page_key, remember=False)
                app().processEvents()
                app().processEvents()
                page = window.pages[page_key]
                assert window.content_scroll.horizontalScrollBar().maximum() == 0, (width, height, page_key)
                assert window.stack.width() <= window.content_scroll.viewport().width() + 2, (
                    width,
                    height,
                    page_key,
                )
                assert not _field_label_overlap_names(page), (width, height, page_key)
                assert not _horizontally_clipped_control_names(page), (width, height, page_key)
                assert not _clipped_table_header_names(page), (width, height, page_key)
                assert not _underfilled_table_names(page), (width, height, page_key)
                assert not _hidden_table_scrollbar_names(page), (width, height, page_key)
                assert not _horizontally_clipped_control_names(window), (width, height, page_key, "shell")
    finally:
        window.close()


def test_report_center_account_closing_ca_export_panel_fits_target_width() -> None:
    app()
    window = MainWindow(config())
    try:
        window.resize(1366, 768)
        window.show()
        window.open_page("reports:account_closing", remember=False)
        app().processEvents()
        app().processEvents()
        page = window.pages["reports"]

        assert page.ca_export_panel.isVisible()
        assert window.content_scroll.horizontalScrollBar().maximum() == 0
        assert not _field_label_overlap_names(page)
        assert not _horizontally_clipped_control_names(page)
        assert not _clipped_table_header_names(page)
        assert not _hidden_table_scrollbar_names(page)
    finally:
        window.close()


def test_all_registered_pages_visible_buttons_have_click_receivers() -> None:
    app()
    window = MainWindow(config())
    try:
        window.resize(1366, 768)
        window.show()
        app().processEvents()
        for page_key in sorted(window.page_factories):
            window.open_page(page_key, remember=False)
            app().processEvents()
            page = window.pages[page_key]
            dead_buttons = [
                button.text().strip() or button.objectName() or button.__class__.__name__
                for button in page.findChildren(QPushButton)
                if button.isVisibleTo(page) and button.isEnabled() and button.receivers(button.clicked) == 0
            ]
            assert not dead_buttons, (page_key, dead_buttons)
    finally:
        window.close()


def test_core_page_open_performance_smoke() -> None:
    app()
    window = MainWindow(config())
    pages = [
        "dashboard",
        "sales_bill",
        "purchase_entry",
        "quotation_entry",
        "document_center",
        "reports",
        "receipt_entry",
        "payment_entry",
    ]
    try:
        window.resize(1366, 768)
        window.show()
        app().processEvents()
        started = time.perf_counter()
        for page_key in pages:
            window.open_page(page_key, remember=False)
            app().processEvents()
        elapsed = time.perf_counter() - started
        assert elapsed < 30.0
    finally:
        window.close()


def _field_label_overlap_names(widget) -> list[str]:
    overlaps: list[str] = []
    for box in widget.findChildren(QFrame):
        if box.objectName() != "fieldBox" or box.layout() is None or box.layout().count() < 2:
            continue
        label_holder = box.layout().itemAt(0).widget()
        control = box.layout().itemAt(1).widget()
        label = label_holder if isinstance(label_holder, QLabel) else None
        if label is None and label_holder is not None:
            labels = [child for child in label_holder.findChildren(QLabel) if child.objectName() == "fieldLabel"]
            label = labels[0] if labels else None
        if label is None or control is None or not label.isVisible() or not control.isVisible():
            continue
        if label.mapTo(box, label.rect().bottomLeft()).y() + 2 >= control.mapTo(box, control.rect().topLeft()).y():
            overlaps.append(label.text())
    return overlaps


def _horizontally_clipped_control_names(widget) -> list[str]:
    clipped: list[str] = []
    controls = [*widget.findChildren(QLabel), *widget.findChildren(QAbstractButton)]
    for control in controls:
        if not control.isVisibleTo(widget) or control.width() <= 0:
            continue
        left = control.mapTo(widget, control.rect().topLeft()).x()
        right = control.mapTo(widget, control.rect().topRight()).x()
        text = control.text().strip()
        name = text or control.objectName() or control.__class__.__name__
        if left < -2 or right > widget.width() + 2:
            clipped.append(name)
            continue
        if not text or (isinstance(control, QLabel) and control.wordWrap()):
            continue
        if control.sizeHint().width() > control.width() + 2:
            clipped.append(name)
    return clipped


def _clipped_table_header_names(widget) -> list[str]:
    clipped: list[str] = []
    for table in widget.findChildren(QTableWidget):
        metrics = table.horizontalHeader().fontMetrics()
        for column in range(table.columnCount()):
            item = table.horizontalHeaderItem(column)
            if item is None or table.isColumnHidden(column):
                continue
            required_width = metrics.horizontalAdvance(item.text()) + 18
            if table.columnWidth(column) + 2 < required_width:
                clipped.append(f"{item.text()} ({table.columnWidth(column)}<{required_width})")
    return clipped


def _underfilled_table_names(widget) -> list[str]:
    underfilled: list[str] = []
    for table in widget.findChildren(QTableWidget):
        if table.property("transactionFramework") is True or not table.isVisibleTo(widget) or table.columnCount() == 0:
            continue
        header = table.horizontalHeader()
        if header.length() + 2 < table.viewport().width():
            underfilled.append(f"{table.objectName() or table.__class__.__name__} ({header.length()}<{table.viewport().width()})")
    return underfilled


def _hidden_table_scrollbar_names(widget) -> list[str]:
    hidden: list[str] = []
    for table in widget.findChildren(QTableWidget):
        scrollbar = table.horizontalScrollBar()
        if table.isVisibleTo(widget) and scrollbar.maximum() > 0 and not scrollbar.isVisible():
            hidden.append(table.objectName() or table.__class__.__name__)
    return hidden


def test_main_window_falls_back_when_dashboard_page_factory_raises(monkeypatch) -> None:
    app()
    import views.main_window as main_window_module

    def boom(*args, **kwargs):
        raise RuntimeError("dashboard failed")

    monkeypatch.setattr(main_window_module, "DashboardView", boom)
    window = MainWindow(config())
    try:
        assert window.current_page == "dashboard"
        fallback_page = window.pages["dashboard"]
        assert fallback_page is not None
        assert any(isinstance(widget, QLabel) for widget in fallback_page.findChildren(QLabel))
    finally:
        window.close()


def test_main_window_master_navigation_opens_new_master_pages() -> None:
    app()
    window = MainWindow(config())
    try:
        from views.module_hub_view import MASTERS_OPERATIONS

        operations = {operation.key: operation for operation in MASTERS_OPERATIONS}
        targets = {
            "gst_rates": "gst_rate_master",
            "banks": "bank_master",
            "tax_codes": "tax_master",
            "payment_terms": "payment_term_master",
        }
        for operation_key, expected_page in targets.items():
            operation = operations[operation_key]
            assert operation.target_page == expected_page
            window._activate_module_operation("masters", operation)
            assert window.current_page == expected_page
    finally:
        window.close()


def test_main_window_account_setup_navigation_opens_operational_master_pages() -> None:
    app()
    window = MainWindow(config())
    try:
        operations = {operation.key: operation for operation in ACCOUNTS_OPERATIONS}
        targets = {
            "routes": "route_master",
            "salesmen": "salesman_master",
            "vehicles": "vehicle_master",
            "transporters": "transporter_master",
        }
        for operation_key, expected_page in targets.items():
            operation = operations[operation_key]
            assert operation.target_page == expected_page
            window._activate_module_operation("accounts", operation)
            assert window.current_page == expected_page
    finally:
        window.close()


def test_simple_master_operational_master_views_load() -> None:
    app()
    views = [
        SimpleMasterView(config(), "route"),
        SimpleMasterView(config(), "salesman"),
        SimpleMasterView(config(), "vehicle"),
        SimpleMasterView(config(), "transporter"),
    ]
    try:
        for view in views:
            assert view.spec.mode in {"route", "salesman", "vehicle", "transporter"}
            assert view.table.rowCount() >= 0
            assert view.search.placeholderText() == "Search current master rows"
    finally:
        for view in views:
            view.close()


def test_module_list_operation_hides_shortcut_grid() -> None:
    app()
    view = ModuleHubView(
        config(),
        "Sales",
        "Sales list test",
        [ModuleOperation("Sales List", "sales_list")],
    )

    assert view.operation_panel.isHidden()
    view.close()


def test_industry_menu_filters_for_pharmacy_business_type() -> None:
    app()
    window = MainWindow(config())
    try:
        window.source = type("StubSource", (), {"company": lambda self: {"business_type_code": "pharmacy_medical"}})()
        filtered = window._filter_industry_operations(INDUSTRY_OPERATIONS)
        keys = {op.key for op in filtered}
        assert "pharmacy_retail_billing" in keys
        assert "pharmacy_wholesale_billing" in keys
        assert "electronics_pos_billing" not in keys
        assert "pos_billing" not in keys
    finally:
        window.close()


def test_industry_menu_filters_for_restaurant_alias_business_type() -> None:
    app()
    window = MainWindow(config())
    try:
        window.source = type("StubSource", (), {"company": lambda self: {"business_type_code": "hotel_restaurant"}})()
        filtered = window._filter_industry_operations(INDUSTRY_OPERATIONS)
        keys = {op.key for op in filtered}
        assert "pos_dine_in" in keys
        assert "kot_new" in keys
        assert "restaurant_tables" in keys
        assert "pos_billing" not in keys
    finally:
        window.close()


def test_admin_operations_include_financial_years_and_numbering_series() -> None:
    keys = [operation.key for operation in ADMIN_OPERATIONS]
    assert "financial_years" in keys
    assert "numbering_series" in keys
    operation_map = {operation.key: operation for operation in ADMIN_OPERATIONS}
    assert operation_map["financial_years"].target_page == "financial_years"
    assert operation_map["numbering_series"].target_page == "numbering_series"


def test_accounting_reports_use_statement_tree() -> None:
    app()
    view = ReportCenterView(config())

    view.open_report("erp_profit_loss")
    assert view.table.isHidden()
    assert not view.statement_panel.isHidden()
    assert view.statement_left.topLevelItemCount() > 0
    assert view.statement_right.topLevelItemCount() > 0
    assert view.statement_control.minimumHeight() >= 220

    view.open_report("balance_sheet")
    assert view.table.isHidden()
    assert not view.statement_panel.isHidden()
    assert view.statement_left.headerItem().text(0) == "Liabilities"
    assert view.statement_right.headerItem().text(0) == "Assets"
    assert view.statement_control.minimumHeight() >= 220
    view.close()


def test_accounting_statement_reports_open_print_preview(monkeypatch) -> None:
    app()
    opened: list[tuple[Path, str]] = []
    monkeypatch.setattr(
        "views.report_center_view.show_print_preview",
        lambda parent, path, title: opened.append((Path(path), title)),
    )
    view = ReportCenterView(config())
    try:
        for report_key, preview_title in [
            ("erp_profit_loss", "Profit & Loss Print Preview"),
            ("balance_sheet", "Balance Sheet Print Preview"),
        ]:
            opened.clear()
            view.open_report(report_key)
            view.print_report()

            assert opened, report_key
            pdf_path, title = opened[-1]
            assert title == preview_title
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0
    finally:
        view.close()


def test_archive_service_merges_selected_prints(tmp_path: Path) -> None:
    db_path = tmp_path / "archive.sqlite3"
    service = DocumentArchiveService(AppConfig(project_root=tmp_path, source_root=tmp_path), db_path)
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    for path, label in [(first, "First"), (second, "Second")]:
        pdf = canvas.Canvas(str(path))
        pdf.drawString(72, 720, label)
        pdf.save()

    target = service.archive_path({"document_type": "sales_bulk", "doc_no": "selected", "category": "Print Batches"}, "pdf")
    merged = service.merge_pdfs([first, second], target)

    assert merged.exists()
    assert "PRM Billing and Inventory" in str(merged)
    assert "Archive" in str(merged)
