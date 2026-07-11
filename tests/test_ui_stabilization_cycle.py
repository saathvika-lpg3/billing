from __future__ import annotations

import os
import sqlite3
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QDate, QDateTime, QTime
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDoubleSpinBox,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QRadioButton,
    QSpinBox,
    QTableWidgetItem,
    QTextEdit,
    QTimeEdit,
)

from config.app_config import AppConfig
from services.master_repository import MasterRepository
from views.product_master_view import ProductMasterView
from views.main_window import MainWindow
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.erp_components import ERPFieldBox, TransactionTotalsPanel
from widgets.widget_values import set_widget_value, widget_text, widget_value


ROOT = Path(__file__).resolve().parents[1]
_APP: QApplication | None = None


def app() -> QApplication:
    global _APP
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def test_safe_widget_value_matrix_and_combo_setter_preserves_items() -> None:
    app()
    line = QLineEdit("  line  ")
    text = QTextEdit("  text  ")
    plain = QPlainTextEdit("  plain  ")
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItem("Each", 11)
    combo.addItem("Box", 12)
    spin = QSpinBox()
    spin.setValue(7)
    decimal = QDoubleSpinBox()
    decimal.setValue(2.5)
    date_edit = QDateEdit(QDate(2026, 7, 11))
    time_edit = QTimeEdit(QTime(12, 34, 56))
    datetime_edit = QDateTimeEdit(QDateTime(QDate(2026, 7, 11), QTime(12, 34, 56)))
    check = QCheckBox()
    check.setChecked(True)
    radio = QRadioButton()
    radio.setChecked(True)

    assert widget_value(line) == "line"
    assert widget_value(text) == "text"
    assert widget_value(plain) == "plain"
    assert widget_value(combo) == "Each"
    assert widget_value(combo, prefer_combo_data=True) == 11
    assert widget_value(spin) == 7
    assert widget_value(decimal) == 2.5
    assert widget_value(date_edit) == QDate(2026, 7, 11)
    assert widget_value(time_edit) == QTime(12, 34, 56)
    assert widget_value(datetime_edit) == QDateTime(QDate(2026, 7, 11), QTime(12, 34, 56))
    assert widget_value(check) is True
    assert widget_value(radio) is True
    assert widget_value(QTableWidgetItem("  cell  ")) == "cell"

    original_items = [combo.itemText(index) for index in range(combo.count())]
    set_widget_value(combo, "Case")
    assert widget_text(combo) == "Case"
    assert [combo.itemText(index) for index in range(combo.count())] == original_items


def test_compact_toolbar_is_horizontal_wired_and_supports_all_feedback_states() -> None:
    app()
    called: list[str] = []
    toolbar = CompactActionToolbar(
        [
            ActionSpec("New", lambda: called.append("new"), role="positive"),
            ActionSpec("Save", lambda: called.append("save"), role="primary"),
            ActionSpec("Delete", lambda: called.append("delete"), role="destructive"),
            ActionSpec("Refresh", lambda: called.append("refresh")),
        ]
    )
    try:
        assert toolbar.property("actionLayout") == "horizontal-wrap"
        assert toolbar.flow_layout.rowCountForWidth(1200) == 1
        assert toolbar.flow_layout.rowCountForWidth(80) > 1
        assert all(button.receivers(button.clicked) > 0 for button in toolbar.buttons.values())
        toolbar.button("Save").click()
        assert called == ["save"]
        toolbar.set_busy("Save")
        assert toolbar.button("Save").property("actionState") == "busy"
        assert not toolbar.button("Save").isEnabled()
        toolbar.mark_success("Save", reset_after_ms=0)
        assert toolbar.button("Save").property("success") is True
        assert toolbar.button("Save").isEnabled()
        toolbar.mark_error("Save", reset_after_ms=0)
        assert toolbar.button("Save").property("error") is True
    finally:
        toolbar.close()


def test_grand_total_has_numeric_binding_accessibility_and_strong_fallback_style() -> None:
    application = app()
    panel = TransactionTotalsPanel()
    try:
        panel.set_totals(
            [{"qty": 2}, {"qty": 3.5}],
            {
                "discount": 5,
                "taxable": 100,
                "cgst": 9,
                "sgst": 9,
                "igst": 0,
                "gst_total": 18,
                "round_off": 0.25,
                "grand_total": 118.25,
            },
        )
        grand = panel.labels["grand_total"]
        assert panel.values["total_qty"] == 5.5
        assert panel.values["grand_total"] == 118.25
        assert grand.text() == "Grand Total\nRs 118.25"
        assert grand.accessibleName() == "Grand Total"
        assert grand.accessibleDescription() == "Rs 118.25"
        assert grand.font().bold()
        assert grand.font().pointSizeF() >= application.font().pointSizeF() + 2
        assert "background-color: #0B1F4D" in grand.styleSheet()
        assert "color: #FFFFFF" in grand.styleSheet()
    finally:
        panel.close()


def test_product_master_combo_save_multi_pack_reload_and_edit_without_duplicate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app()
    db_path = tmp_path / "product-master-regression.db"
    repository = MasterRepository(db_path)
    repository.ensure_schema()
    repository.save_simple(
        "category",
        0,
        {"code": "QA", "name": "QA Category", "default_gst": 18, "is_active": True},
    )
    repository.save_simple("unit", 0, {"name": "EA", "is_active": True})
    repository.save_simple("unit", 0, {"name": "BOX", "is_active": True})
    repository.save_simple("gst_rate", 0, {"rate": 18, "name": "GST 18", "is_active": True})
    monkeypatch.setenv("PRM_SQLITE_DB", str(db_path))
    monkeypatch.setenv("PRM_USE_SQLITE", "0")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    view = ProductMasterView(AppConfig(ROOT, ROOT))
    try:
        assert view.sale_unit.count() == 2
        assert view.purchase_unit.count() == 2
        view.clear_form()
        assert view.sale_unit.count() == 2
        assert view.purchase_unit.count() == 2

        view.code.setText("QA-P-001")
        view.name.setText("Combo Safe Product")
        view.category.setCurrentText("QA Category")
        view.hsn.setText("1234")
        view.gst.setCurrentText("18.00")
        view.sale_unit.setCurrentText("EA")
        view.purchase_unit.setCurrentText("EA")
        view.supplier.setCurrentIndex(0)
        view.brand.setCurrentIndex(0)
        view.pack_table.cellWidget(0, 1).setCurrentText("EA")
        view.pack_table.item(0, 2).setText("1 Each")
        view.pack_table.item(0, 3).setText("QA-UNIT-1")
        view.pack_table.item(0, 6).setText("100")
        view.pack_table.item(0, 9).setText("70")
        view.pack_table.item(0, 10).setText("90")
        view.add_pack_row(
            {
                "pack_size": 10,
                "pack_unit": "EA",
                "display_name": "Box of 10",
                "barcode": "QA-UNIT-10",
                "mrp": 950,
                "purchase_rate": 650,
                "sale_rate": 850,
                "current_stock_qty": 3,
                "is_default": 0,
                "is_active": 1,
            }
        )

        payload, errors = view._product_payload()
        assert not errors
        assert payload["sale_unit"] == "EA"
        assert payload["purchase_unit"] == "EA"
        assert len(payload["packs"]) == 2

        view.save_draft()
        saved_id = view.product_id
        assert saved_id > 0
        assert view.sale_unit.currentText() == "EA"
        assert view.purchase_unit.currentText() == "EA"
        assert view.pack_table.rowCount() == 2

        view.name.setText("Combo Safe Product Updated")
        view.save_draft()
        assert view.product_id == saved_id
        with sqlite3.connect(db_path) as conn:
            assert conn.execute("SELECT COUNT(*) FROM items WHERE code='QA-P-001'").fetchone()[0] == 1
            assert conn.execute("SELECT COUNT(*) FROM product_packs WHERE product_id=?", (saved_id,)).fetchone()[0] == 2
            row = conn.execute(
                "SELECT name,sale_unit,purchase_unit FROM items WHERE id=?",
                (saved_id,),
            ).fetchone()
        assert row == ("Combo Safe Product Updated", "EA", "EA")
    finally:
        view.close()


def test_product_master_source_has_no_qcombobox_line_edit_api_regression() -> None:
    source = (ROOT / "views" / "product_master_view.py").read_text(encoding="utf-8")
    assert "self.sale_unit.text(" not in source
    assert "self.purchase_unit.text(" not in source
    assert "self.sale_unit.setText(" not in source
    assert "self.purchase_unit.setText(" not in source


def test_button_theme_has_specific_pressed_focus_disabled_busy_success_error_states() -> None:
    for theme_name in ("light.qss", "dark.qss"):
        theme = (ROOT / "themes" / theme_name).read_text(encoding="utf-8")
        for selector in (
            "QPushButton#primaryButton:pressed",
            "QPushButton#quickButton:pressed",
            "QPushButton#primaryButton:focus",
            "QPushButton#primaryButton:disabled",
            'QPushButton[actionState="busy"]',
            'QPushButton[actionState="success"]',
            'QPushButton[actionState="error"]',
            "QPushButton:checked",
        ):
            assert selector in theme, (theme_name, selector)


def test_grand_total_is_inside_1366x768_viewport_for_primary_transactions() -> None:
    application = app()
    window = MainWindow(AppConfig(ROOT, ROOT))
    try:
        window.resize(1366, 768)
        window.show()
        application.processEvents()
        for route in ("sales_bill", "purchase_entry", "quotation_entry", "sales_order_entry", "purchase_order_entry"):
            window.open_page(route, remember=False)
            application.processEvents()
            application.processEvents()
            page = window.pages[route]
            panel = page.findChild(TransactionTotalsPanel)
            assert panel is not None, route
            grand = panel.labels["grand_total"]
            viewport = window.content_scroll.viewport()
            top = grand.mapTo(viewport, grand.rect().topLeft()).y()
            bottom = grand.mapTo(viewport, grand.rect().bottomLeft()).y()
            assert 0 <= top < bottom <= viewport.height(), (route, top, bottom, viewport.height())
    finally:
        window.close()


def test_product_master_wide_cards_have_no_vertical_field_overlap_at_1366() -> None:
    application = app()
    window = MainWindow(AppConfig(ROOT, ROOT))
    try:
        window.resize(1366, 768)
        window.show()
        application.processEvents()
        window.open_page("product_master", remember=False)
        application.processEvents()
        application.processEvents()
        view = window.pages["product_master"]
        assert view._form_layout_compact is False
        assert view.basic_card.geometry().right() < view.inventory_card.geometry().left()
        assert view.identification_card.geometry().top() > max(
            view.basic_card.geometry().bottom(),
            view.inventory_card.geometry().bottom(),
        )
        for card in (view.basic_card, view.inventory_card, view.identification_card):
            assert card.height() >= card.minimumSizeHint().height()
            fields = card.findChildren(ERPFieldBox)
            for index, field in enumerate(fields):
                assert all(not field.geometry().intersects(other.geometry()) for other in fields[index + 1 :])
    finally:
        window.close()
