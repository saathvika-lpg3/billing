from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtGui import QKeySequence, QShortcut, QKeyEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
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
    QHeaderView,
    QStyledItemDelegate,
)

from config.app_config import AppConfig
from services.master_repository import MasterRepository
from services.mysql_source import MySqlSource
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPToolbar
from widgets.form_layout_helpers import build_field_section


class ProductMasterView(QWidget):
    pack_headers = [
        "Pack Size", "Unit", "Display Name", "Barcode", "HSN", "Supplier Code",
        "MRP", "PTR", "PTS", "Purchase", "Sale", "Dealer", "Distributor",
        "Wholesale", "Retail", "Scheme", "Box Qty", "Opening", "Current",
        "Low", "Reorder", "Default", "Active",
    ]

    list_headers = [
        "Product", "Category", "Brand", "Supplier", "Type / Tax",
        "Packs", "Default Pack", "Stock / Status",
    ]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.repository = MasterRepository(self.source.sqlite_path)
        self.products: list[dict[str, Any]] = []
        self.product_by_id: dict[int, dict[str, Any]] = {}
        self.supplier_labels: dict[str, int] = {}
        self.category_labels: dict[str, int] = {}
        self.brand_labels: dict[str, int] = {}
        self.form_controls: list[QWidget] = []
        self._build()
        self._load_source_data()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(3)
        root.addWidget(self._title_bar())
        root.addWidget(self._form_card())
        root.addWidget(self._pack_card())
        root.addWidget(self._list_card(), stretch=1)
        self._register_hotkeys()
        self._register_form_navigation()

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader(
            "Product Master",
            "FMCG-ready product entry | packs, prices, barcode, stock controls",
            self,
        )
        self.source_status = header.status_label
        toolbar = ERPToolbar(
            [
                ("New", self.clear_form),
                ("Advanced", self.open_notes),
                ("Save Product", self.save_draft),
            ]
        )
        header.layout().addWidget(toolbar)
        return header

    def _prepare_control(self, widget: QWidget, minimum_width: int = 96, fixed_height: int = 28) -> QWidget:
        widget.setMinimumWidth(min(minimum_width, 120))
        if not isinstance(widget, QTextEdit):
            widget.setFixedHeight(fixed_height)
        else:
            widget.setMinimumHeight(40)
            widget.setMaximumHeight(70)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if isinstance(widget, QComboBox):
            widget.setMaxVisibleItems(18)
            widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 8))
            widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        return widget

    def _field(self, label: str, widget: QWidget, minimum_width: int = 100) -> QWidget:
        self._prepare_control(widget, minimum_width=minimum_width)
        return ERPFieldBox(label, widget, self)

    def _form_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        self.product_id = 0
        self.code = QLineEdit()
        self.code.setPlaceholderText("Required")
        self.supplier = QComboBox()
        self.category = QComboBox()
        self.brand = QComboBox()
        self.name = QLineEdit()
        self.name.setPlaceholderText("Required")
        self.item_type = QComboBox()
        self.item_type.addItems(["Stock Item", "Service Item", "Consumable", "Asset", "Raw Material", "Finished Goods"])
        self.status = QComboBox()
        self.status.addItems(["Active", "Inactive", "Hold", "Discontinued"])
        self.hsn = QLineEdit()
        self.gst = QComboBox()
        self.sale_unit = QComboBox()
        self.sale_unit.setEditable(True)
        self.sale_unit.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.sale_unit.setToolTip("Select sale unit or type to add/search")
        self.purchase_unit = QComboBox()
        self.purchase_unit.setEditable(True)
        self.purchase_unit.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.purchase_unit.setToolTip("Select purchase unit or type to add/search")
        self.valuation = QComboBox()
        self.valuation.addItems(["weighted_average", "fifo", "standard_cost"])
        self.sku_alias = QLineEdit()
        self.lead_time = QLineEdit("0")
        self.shelf_life = QLineEdit("0")
        self.near_expiry = QLineEdit("0")
        self.multi_uom = QCheckBox("Multi-UOM")
        self.pack_conversion = QCheckBox("Pack Conversion")
        self.batch_required = QCheckBox("Batch Required")
        self.expiry_required = QCheckBox("Expiry Required")
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Internal item notes")

        fields = [
            ("Product Code *", self.code, 140),
            ("Product Name *", self.name, 280),
            ("Supplier / Brand", self.supplier, 180),
            ("Category *", self.category, 160),
            ("Brand", self.brand, 160),
            ("HSN", self.hsn, 90),
            ("GST %", self.gst, 90),
            ("Sale UoM *", self.sale_unit, 90),
            ("Purchase UoM *", self.purchase_unit, 90),
            ("Valuation", self.valuation, 120),
            ("SKU Alias", self.sku_alias, 140),
            ("Lead Time", self.lead_time, 120),
            ("Shelf Life Days", self.shelf_life, 120),
            ("Near Expiry Alert Days", self.near_expiry, 150),
            ("Notes", self.notes, 360),
            ("Batch Required", self.batch_required, 160),
            ("Expiry Required", self.expiry_required, 160),
            ("Multi-UOM", self.multi_uom, 140),
            ("Pack Conversion", self.pack_conversion, 160),
        ]
        layout.addWidget(build_field_section(fields, spacing=6, margin=0))
        for _, widget, _ in fields:
            self.form_controls.append(widget)

        return frame

    def _pack_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMinimumHeight(92)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        head = QHBoxLayout()
        title = QLabel("Package / Variant Details")
        title.setObjectName("cardTitle")
        self.add_pack_btn = QPushButton("Add Pack")
        self.add_pack_btn.clicked.connect(self.add_pack_row)
        self.remove_pack_btn = QPushButton("Remove Selected")
        self.remove_pack_btn.clicked.connect(self.remove_selected_pack)
        head.addWidget(title)
        head.addStretch(1)
        head.addWidget(self.add_pack_btn)
        head.addWidget(self.remove_pack_btn)
        layout.addLayout(head)
        # Use a custom table that advances focus on Enter/Return
        class PackTable(QTableWidget):
            def __init__(self, owner: "ProductMasterView", *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.owner = owner

            def _advance_cell(self, forward: bool = True) -> None:
                row = self.currentRow()
                col = self.currentColumn()
                if row < 0 or col < 0:
                    return
                if forward:
                    col += 1
                    if col >= self.columnCount():
                        col = 0
                        row += 1
                else:
                    col -= 1
                    if col < 0:
                        row = max(0, row - 1)
                        col = self.columnCount() - 1
                if row >= self.rowCount():
                    try:
                        self.owner.add_pack_row()
                    except Exception:
                        self.insertRow(row)
                self.setCurrentCell(row, col)
                widget = self.cellWidget(row, col)
                if widget is not None:
                    try:
                        widget.setFocus()
                    except Exception:
                        pass
                else:
                    item = self.item(row, col)
                    if item is not None:
                        self.editItem(item)

            def eventFilter(self, obj: QObject, event: QEvent) -> bool:
                if event.type() == QEvent.Type.KeyPress and isinstance(obj, (QComboBox, QLineEdit)):
                    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        self._advance_cell(forward=not bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
                        return True
                return super().eventFilter(obj, event)

            def keyPressEvent(self, event: QKeyEvent) -> None:
                key = event.key()
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self._advance_cell(forward=not bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
                    return
                super().keyPressEvent(event)

        self.pack_table = PackTable(self, 0, len(self.pack_headers))
        self.pack_table.setHorizontalHeaderLabels(self.pack_headers)
        self.pack_table.setAlternatingRowColors(True)
        self.pack_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.pack_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.pack_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.pack_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.pack_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.pack_table.setMinimumHeight(54)
        self.pack_table.setToolTip("Double-click to edit. Press Enter to move to next cell. Select a row and click Remove Selected to delete.")
        self.pack_table.installEventFilter(self.pack_table)
        layout.addWidget(self.pack_table, stretch=1)
        hint = QLabel("Tip: Double-click a pack cell to edit; press Enter to move. Use Remove Selected to delete rows.")
        hint.setObjectName("caption")
        layout.addWidget(hint)
        return frame

    def _list_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMinimumHeight(148)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        bar = QHBoxLayout()
        title = QLabel("Product List")
        title.setObjectName("cardTitle")
        self.search = QLineEdit()
        self.search.setProperty("enterSubmits", True)
        self.search.setPlaceholderText("Search product, code, barcode, supplier, HSN")
        self.search.textChanged.connect(self._redraw_product_list)
        self.search.returnPressed.connect(self._redraw_product_list)
        bar.addWidget(title)
        bar.addStretch(1)
        bar.addWidget(self.search)
        layout.addLayout(bar)
        self.product_table = QTableWidget(0, len(self.list_headers))
        self.product_table.setHorizontalHeaderLabels(self.list_headers)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_table.setMinimumHeight(92)
        self.product_table.verticalHeader().setDefaultSectionSize(24)
        self.product_table.cellDoubleClicked.connect(self._load_product_from_table)
        layout.addWidget(self.product_table, stretch=1)
        return frame

    def _load_source_data(self) -> None:
        try:
            self.repository.ensure_schema()
            suppliers = self.source.suppliers()
            categories = self.source.item_categories()
            brands = self.source.brands()
            units = self.source.units()
            slabs = self.source.tax_slabs()
            self.products = self.source.product_master_rows()
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            return
        self.product_by_id = {int(row["id"]): row for row in self.products}
        self._fill_id_combo(self.supplier, {"No Company": 0} | {s["name"]: int(s["id"]) for s in suppliers}, self.supplier_labels)
        self._fill_id_combo(self.category, {"Choose Category": 0} | {c["name"]: int(c["id"]) for c in categories}, self.category_labels)
        self._fill_id_combo(self.brand, {"No Brand": 0} | {b["name"]: int(b["id"]) for b in brands}, self.brand_labels)
        # make supplier/category/brand editable and provide MatchContains completers
        for combo in (self.supplier, self.category, self.brand):
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            completer = QCompleter([combo.itemText(i) for i in range(combo.count())], self)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            combo.setCompleter(completer)
            combo.setToolTip("Type to filter; press Enter to select")
        self.units = [u["name"] for u in units] or ["PCS"]
        # populate sale/purchase unit combos
        try:
            self.sale_unit.clear()
            self.sale_unit.addItems(self.units)
            self.purchase_unit.clear()
            self.purchase_unit.addItems(self.units)
        except Exception:
            pass
        self.gst.clear()
        self.gst.addItems([f"{float(s['rate']):.2f}" for s in slabs] or ["0.00", "5.00", "12.00", "18.00", "28.00"])
        # Check for UOM/price foundation availability in DB and show small indicator
        try:
            import sqlite3
            with sqlite3.connect(self.repository.db_path) as conn:
                row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uoms'").fetchone()
                uom_flag = "UOMs:Yes" if row else "UOMs:No"
        except Exception:
            uom_flag = "UOMs:Unknown"
        self.source_status.setText(f"{len(self.products)} products | {len(suppliers)} suppliers | {uom_flag}")
        self._redraw_product_list()
        self.clear_form()

    def _fill_id_combo(self, combo: QComboBox, values: dict[str, int], target: dict[str, int]) -> None:
        combo.clear()
        target.clear()
        for label, row_id in values.items():
            combo.addItem(label)
            target[label] = row_id

    def _set_combo_id(self, combo: QComboBox, labels: dict[str, int], row_id: int) -> None:
        for label, candidate_id in labels.items():
            if candidate_id == row_id:
                combo.setCurrentText(label)
                return
        combo.setCurrentIndex(0)

    def _redraw_product_list(self) -> None:
        query = self.search.text().strip().lower() if hasattr(self, "search") else ""
        rows = []
        for row in self.products:
            haystack = " ".join(str(row.get(key, "")) for key in (
                "name", "code", "sku_alias", "supplier_item_code", "hsn",
                "barcode", "supplier_name", "category_name", "brand_name",
                "default_pack_name", "default_pack_barcode", "item_type",
                "status", "gst", "batch_required", "expiry_required",
                "multi_uom", "pack_conversion", "shelf_life_days", "near_expiry_days",
            )).lower()
            if query and query not in haystack:
                continue
            rows.append(row)
        self.product_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.product_table.setVerticalHeaderItem(row_index, QTableWidgetItem(str(row.get("id", ""))))
            values = [
                f"{row.get('name','')}\n{row.get('code','')}",
                row.get("category_name", ""),
                row.get("brand_name", ""),
                row.get("supplier_name", ""),
                f"{row.get('item_type','')}\nHSN {row.get('hsn','')} | GST {float(row.get('gst') or 0):.2f}%",
                str(int(row.get("pack_count") or 0)),
                f"{row.get('default_pack_name','')}\nMRP {float(row.get('default_mrp') or 0):.2f} | Sale {float(row.get('default_sale_rate') or 0):.2f}",
                f"{float(row.get('pack_stock_total') or 0):.3f}\n{row.get('status','')} | {row.get('default_pack_barcode','')}",
            ]
            for col, value in enumerate(values):
                self.product_table.setItem(row_index, col, QTableWidgetItem(str(value)))
        self.product_table.resizeRowsToContents()
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _load_product_from_table(self, row: int, _col: int) -> None:
        item = self.product_table.verticalHeaderItem(row)
        if not item:
            return
        product = self.product_by_id.get(int(item.text()))
        if product:
            self.load_product(product)

    def load_product(self, product: dict[str, Any]) -> None:
        self.product_id = int(product.get("id") or 0)
        self.code.setText(str(product.get("code") or ""))
        self.name.setText(str(product.get("name") or ""))
        self.hsn.setText(str(product.get("hsn") or ""))
        self.item_type.setCurrentText(str(product.get("item_type") or "Stock Item"))
        self.status.setCurrentText(str(product.get("status") or "Active"))
        self.gst.setCurrentText(f"{float(product.get('gst') or 0):.2f}")
        self.sale_unit.setText(str(product.get("sale_unit") or ""))
        self.purchase_unit.setText(str(product.get("purchase_unit") or ""))
        self.valuation.setCurrentText(str(product.get("valuation_method") or "weighted_average"))
        self.sku_alias.setText(str(product.get("sku_alias") or ""))
        self.lead_time.setText(str(int(product.get("lead_time_days") or 0)))
        self.shelf_life.setText(str(int(product.get("shelf_life_days") or 0)))
        self.near_expiry.setText(str(int(product.get("near_expiry_days") or 0)))
        self.multi_uom.setChecked(int(product.get("multi_uom") or 0) == 1)
        self.pack_conversion.setChecked(int(product.get("pack_conversion") or 0) == 1)
        self.batch_required.setChecked(int(product.get("batch_required") or 0) == 1)
        self.expiry_required.setChecked(int(product.get("expiry_required") or 0) == 1)
        self.notes.setPlainText(str(product.get("item_notes") or ""))
        self._set_combo_id(self.supplier, self.supplier_labels, int(product.get("supplier_id") or 0))
        self._set_combo_id(self.category, self.category_labels, int(product.get("category_id") or 0))
        self._set_combo_id(self.brand, self.brand_labels, int(product.get("brand_id") or 0))
        packs = self.source.product_pack_rows(self.product_id)
        self._load_packs(packs or [self._default_pack(product)])

    def clear_form(self) -> None:
        self.product_id = 0
        for widget in [self.code, self.name, self.hsn, self.sku_alias]:
            widget.clear()
        self.lead_time.setText("0")
        self.sale_unit.clear()
        self.purchase_unit.clear()
        self.shelf_life.setText("0")
        self.near_expiry.setText("0")
        self.multi_uom.setChecked(False)
        self.pack_conversion.setChecked(False)
        self.item_type.setCurrentText("Stock Item")
        self.status.setCurrentText("Active")
        self.valuation.setCurrentText("weighted_average")
        self.batch_required.setChecked(False)
        self.expiry_required.setChecked(False)
        self.notes.clear()
        for combo in [self.supplier, self.category, self.brand]:
            combo.setCurrentIndex(0)
        if self.gst.count():
            self.gst.setCurrentText("18.00" if self.gst.findText("18.00") >= 0 else self.gst.itemText(0))
        self.pack_table.setRowCount(0)
        self.add_pack_row()
        self.code.setFocus()

    def _default_pack(self, product: dict[str, Any] | None = None) -> dict[str, Any]:
        product = product or {}
        unit = str(product.get("unit") or product.get("sale_unit") or (self.units[0] if hasattr(self, "units") else "PCS"))
        pack_size = float(product.get("pack_size") or 1)
        return {
            "pack_size": pack_size,
            "pack_unit": unit,
            "display_name": f"{pack_size:g} {unit}",
            "barcode": product.get("barcode", ""),
            "hsn": product.get("hsn", ""),
            "supplier_item_code": product.get("supplier_item_code", ""),
            "mrp": product.get("mrp", 0),
            "ptr": product.get("ptr", 0),
            "pts": product.get("pts", 0),
            "purchase_rate": product.get("buy_rate", 0),
            "sale_rate": product.get("sale_rate", 0),
            "dealer_rate": product.get("sale_rate", 0),
            "distributor_rate": product.get("sale_rate", 0),
            "wholesale_rate": product.get("sale_rate", 0),
            "retail_rate": product.get("sale_rate", 0),
            "scheme": "",
            "box_qty": product.get("box_qty", 0),
            "opening_stock_qty": product.get("stock", 0),
            "current_stock_qty": product.get("stock", 0),
            "low_stock_alert": product.get("min_stock", 0),
            "reorder_qty": product.get("reorder_qty", 0),
            "is_default": 1,
            "is_active": 1,
        }

    def _load_packs(self, packs: list[dict[str, Any]]) -> None:
        self.pack_table.setRowCount(0)
        for pack in packs:
            self.add_pack_row(pack)

    def add_pack_row(self, pack: dict[str, Any] | None = None) -> None:
        pack = pack or self._default_pack()
        row = self.pack_table.rowCount()
        self.pack_table.insertRow(row)
        keys = [
            "pack_size", "pack_unit", "display_name", "barcode", "hsn", "supplier_item_code",
            "mrp", "ptr", "pts", "purchase_rate", "sale_rate", "dealer_rate",
            "distributor_rate", "wholesale_rate", "retail_rate", "scheme", "box_qty",
            "opening_stock_qty", "current_stock_qty", "low_stock_alert", "reorder_qty",
        ]
        for col, key in enumerate(keys):
            value = pack.get(key, "")
            if isinstance(value, float):
                value = f"{value:.3f}" if key.endswith("qty") or key in {"pack_size", "box_qty"} else f"{value:.2f}"
            if col == 1:
                combo = self._create_unit_combo_cell(str(value))
                self.pack_table.setCellWidget(row, col, combo)
            else:
                item = QTableWidgetItem(str(value))
                self.pack_table.setItem(row, col, item)
        for col, key in [(21, "is_default"), (22, "is_active")]:
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if int(pack.get(key) or 0) == 1 else Qt.CheckState.Unchecked)
            self.pack_table.setItem(row, col, item)
        # ensure a default current cell for easier editing
        self.pack_table.setCurrentCell(row, 0)

    def _create_unit_combo_cell(self, current: str) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.addItems(self.units)
        combo.setCurrentText(current)
        combo.setToolTip("Type unit name to filter or select from list")
        completer = QCompleter(self.units, combo)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)
        combo.installEventFilter(self.pack_table)
        return combo

    def remove_selected_pack(self) -> None:
        rows = sorted({index.row() for index in self.pack_table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.pack_table.removeRow(row)
        if self.pack_table.rowCount() == 0:
            self.add_pack_row()

    def open_notes(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Advanced Product Details")
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        item_type = QComboBox(dialog)
        item_type.addItems(["Stock Item", "Service Item", "Consumable", "Asset", "Raw Material", "Finished Goods"])
        item_type.setCurrentText(self.item_type.currentText())
        status = QComboBox(dialog)
        status.addItems(["Active", "Inactive", "Hold", "Discontinued"])
        status.setCurrentText(self.status.currentText())
        sku_alias = QLineEdit(self.sku_alias.text(), dialog)
        valuation = QComboBox(dialog)
        valuation.addItems(["weighted_average", "fifo", "standard_cost"])
        valuation.setCurrentText(self.valuation.currentText())
        lead_time = QLineEdit(self.lead_time.text(), dialog)
        editor = QTextEdit(dialog)
        editor.setMinimumHeight(84)
        editor.setMaximumHeight(120)
        editor.setPlainText(self.notes.toPlainText())
        form.addRow("Item Type", item_type)
        form.addRow("Status", status)
        form.addRow("SKU / Alias", sku_alias)
        form.addRow("Valuation Method", valuation)
        form.addRow("Lead Time Days", lead_time)
        form.addRow("Item Notes", editor)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.item_type.setCurrentText(item_type.currentText())
            self.status.setCurrentText(status.currentText())
            self.sku_alias.setText(sku_alias.text().strip())
            self.valuation.setCurrentText(valuation.currentText())
            self.lead_time.setText(lead_time.text().strip() or "0")
            self.notes.setPlainText(editor.toPlainText())

    def _pack_payload(self) -> tuple[list[dict[str, Any]], list[str]]:
        rows: list[dict[str, Any]] = []
        errors: list[str] = []
        barcodes: set[str] = set()
        active_count = 0
        for row in range(self.pack_table.rowCount()):
            def text(col: int) -> str:
                # Prefer cell widget value if present (e.g., unit combo), else table item
                widget = self.pack_table.cellWidget(row, col)
                if widget is not None:
                    # common widget types
                    try:
                        # QComboBox
                        if hasattr(widget, "currentText"):
                            return str(widget.currentText() or "").strip()
                        # QLineEdit or similar
                        if hasattr(widget, "text"):
                            return str(widget.text() or "").strip()
                    except Exception:
                        pass
                item = self.pack_table.item(row, col)
                return item.text().strip() if item else ""

            def number(col: int, label: str) -> float:
                raw = text(col)
                try:
                    value = float(raw or 0)
                except ValueError:
                    errors.append(f"Row {row + 1}: {label} must be numeric.")
                    return 0.0
                if value < 0:
                    errors.append(f"Row {row + 1}: {label} cannot be negative.")
                return value

            default_item = self.pack_table.item(row, 21)
            active_item = self.pack_table.item(row, 22)
            is_default = default_item and default_item.checkState() == Qt.CheckState.Checked
            is_active = not active_item or active_item.checkState() == Qt.CheckState.Checked
            if is_active:
                active_count += 1
            barcode = text(3)
            if barcode:
                barcode_key = barcode.upper()
                if barcode_key in barcodes:
                    errors.append(f"Duplicate barcode in pack rows: {barcode}")
                barcodes.add(barcode_key)
            pack = {
                "pack_size": number(0, "Pack Size"),
                "pack_unit": text(1) or "PCS",
                "display_name": text(2) or f"{number(0, 'Pack Size'):g} {text(1) or 'PCS'}",
                "barcode": barcode,
                "hsn": text(4),
                "supplier_item_code": text(5),
                "mrp": number(6, "MRP"),
                "ptr": number(7, "PTR"),
                "pts": number(8, "PTS"),
                "purchase_rate": number(9, "Purchase"),
                "sale_rate": number(10, "Sale"),
                "dealer_rate": number(11, "Dealer"),
                "distributor_rate": number(12, "Distributor"),
                "wholesale_rate": number(13, "Wholesale"),
                "retail_rate": number(14, "Retail"),
                "scheme": text(15),
                "box_qty": number(16, "Box Qty"),
                "opening_stock_qty": number(17, "Opening"),
                "current_stock_qty": number(18, "Current"),
                "low_stock_alert": number(19, "Low"),
                "reorder_qty": number(20, "Reorder"),
                "is_default": 1 if is_default else 0,
                "is_active": 1 if is_active else 0,
            }
            if pack["pack_size"] <= 0:
                errors.append(f"Row {row + 1}: Pack Size is required.")
            rows.append(pack)
        if active_count == 0:
            errors.append("Product must have at least one active package row.")
        if rows and not any(row["is_default"] for row in rows if row["is_active"]):
            rows[0]["is_default"] = 1
        return rows, errors

    def _product_payload(self) -> tuple[dict[str, Any], list[str]]:
        packs, errors = self._pack_payload()
        if not self.code.text().strip():
            errors.append("Product Code is required.")
        if not self.name.text().strip():
            errors.append("Product Name is required.")
        if self.category_labels.get(self.category.currentText(), 0) <= 0:
            errors.append("Category is required.")
        hsn = self.hsn.text().strip()
        if hsn and (not hsn.isdigit() or len(hsn) not in {4, 6, 8}):
            errors.append("HSN must be 4, 6, or 8 digits.")
        try:
            lead_time_days = int(float(self.lead_time.text() or 0))
            if lead_time_days < 0:
                errors.append("Lead Time cannot be negative.")
        except ValueError:
            lead_time_days = 0
            errors.append("Lead Time must be numeric.")
        sale_unit = self.sale_unit.text().strip() or "PCS"
        purchase_unit = self.purchase_unit.text().strip() or sale_unit
        try:
            shelf_life_days = int(float(self.shelf_life.text() or 0))
            if shelf_life_days < 0:
                errors.append("Shelf Life Days cannot be negative.")
        except ValueError:
            shelf_life_days = 0
            errors.append("Shelf Life Days must be numeric.")
        try:
            near_expiry_days = int(float(self.near_expiry.text() or 0))
            if near_expiry_days < 0:
                errors.append("Near Expiry Alert Days cannot be negative.")
        except ValueError:
            near_expiry_days = 0
            errors.append("Near Expiry Alert Days must be numeric.")
        payload = {
            "product_id": self.product_id,
            "code": self.code.text().strip(),
            "supplier_id": self.supplier_labels.get(self.supplier.currentText(), 0),
            "category_id": self.category_labels.get(self.category.currentText(), 0),
            "brand_id": self.brand_labels.get(self.brand.currentText(), 0),
            "name": self.name.text().strip(),
            "item_type": self.item_type.currentText(),
            "status": self.status.currentText(),
            "hsn": hsn,
            "gst": float(self.gst.currentText() or 0),
            "sale_unit": sale_unit,
            "purchase_unit": purchase_unit,
            "valuation_method": self.valuation.currentText(),
            "sku_alias": self.sku_alias.text().strip(),
            "lead_time_days": lead_time_days,
            "batch_required": self.batch_required.isChecked(),
            "expiry_required": self.expiry_required.isChecked(),
            "multi_uom": self.multi_uom.isChecked(),
            "pack_conversion": self.pack_conversion.isChecked(),
            "shelf_life_days": shelf_life_days,
            "near_expiry_days": near_expiry_days,
            "item_notes": self.notes.toPlainText().strip(),
            "packs": packs,
        }
        return payload, errors

    def save_draft(self) -> None:
        payload, errors = self._product_payload()
        if errors:
            QMessageBox.warning(self, "Product Master", "\n".join(dict.fromkeys(errors)))
            return
        try:
            saved_id = self.repository.save_product(payload)
        except Exception as exc:
            QMessageBox.warning(self, "Product Master", f"Product could not be saved:\n{exc}")
            return
        self.product_id = saved_id
        self._load_source_data()
        QMessageBox.information(self, "Product Master", f"Product saved to local database.\nProduct ID: {saved_id}")

    def _register_hotkeys(self) -> None:
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_draft)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.clear_form)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search.setFocus())
        QShortcut(QKeySequence("F4"), self, activated=self.add_pack_row)
        QShortcut(QKeySequence("Delete"), self, activated=self.remove_selected_pack)
        QShortcut(QKeySequence("Esc"), self, activated=self.clear_form)

    def _register_form_navigation(self) -> None:
        for control in self.form_controls:
            control.installEventFilter(self)
        # also handle pack table enter navigation
        self.pack_table.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if isinstance(obj, (QLineEdit, QComboBox)):
                if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
                    if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                        self.focusPreviousChild()
                    else:
                        self.focusNextChild()
                    return True
            # when editing the pack table, move to next cell on Enter
            if obj is self.pack_table and event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
                # move forward unless shift is held
                forward = not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                row = self.pack_table.currentRow()
                col = self.pack_table.currentColumn()
                if row < 0 or col < 0:
                    return False
                if forward:
                    col += 1
                    if col >= self.pack_table.columnCount():
                        col = 0
                        row += 1
                else:
                    col -= 1
                    if col < 0:
                        row = max(0, row - 1)
                        col = self.pack_table.columnCount() - 1
                if row >= self.pack_table.rowCount():
                    self.add_pack_row()
                self.pack_table.setCurrentCell(row, col)
                item = self.pack_table.item(row, col)
                if item:
                    self.pack_table.editItem(item)
                return True
        return super().eventFilter(obj, event)
