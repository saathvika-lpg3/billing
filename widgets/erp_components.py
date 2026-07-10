from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QSize, Qt, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
)

from widgets.flow_layout import FlowLayout


def _refresh_widget_style(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def set_button_busy(button: QPushButton, busy: bool) -> None:
    try:
        button.setProperty("busy", busy)
        if button.isEnabled() != (not busy):
            button.setEnabled(not busy)
        _refresh_widget_style(button)
    except RuntimeError:
        return


def _set_button_recent_click(button: QPushButton, duration_ms: int = 700) -> None:
    button.setProperty("recentClick", True)
    _refresh_widget_style(button)

    def clear_recent() -> None:
        try:
            button.setProperty("recentClick", False)
            _refresh_widget_style(button)
        except RuntimeError:
            return

    QTimer.singleShot(duration_ms, clear_recent)


def install_button_feedback(button: QPushButton) -> QPushButton:
    """Install shared visual feedback on any ERP button once."""

    if button.property("_erpFeedbackInstalled") is True:
        return button
    button.setProperty("_erpFeedbackInstalled", True)
    button.setProperty("recentClick", False)
    button.setProperty("busy", False)
    button.pressed.connect(lambda checked=False, b=button: _set_button_recent_click(b, 500))
    button.clicked.connect(lambda checked=False, b=button: _set_button_recent_click(b))
    return button


def install_button_feedback_tree(root: QWidget) -> None:
    for button in root.findChildren(QPushButton):
        install_button_feedback(button)


def unavailable_action(parent: QWidget, action: str) -> None:
    QMessageBox.information(
        parent,
        "Action not available",
        f"{action} is not available on this screen yet. The click was received.",
    )


class ERPPageHeader(QFrame):
    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageHeader")
        self.setMinimumHeight(48)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        layout.addLayout(title_box, stretch=1)
        self.status_label = QLabel("Source: loading")
        self.status_label.setObjectName("caption")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)


class ERPFieldBox(QFrame):
    def __init__(self, label: str, control: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fieldBox")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("fieldLabel")
        label_widget.setWordWrap(True)
        label_widget.setMinimumHeight(13)
        layout.addWidget(label_widget)
        layout.addWidget(control)


class ERPToolbar(QFrame):
    def __init__(self, buttons: list[tuple[str, object]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionToolbar")
        self.setProperty("role", "toolbar")
        layout = FlowLayout(self, margin=4, spacing=5)
        for label, callback in buttons:
            button = QPushButton(label)
            button.setObjectName("quickButton")
            if label in {"Save", "Print", "PDF"}:
                button.setObjectName("primaryButton")
            install_button_feedback(button)
            if callable(callback):
                button.clicked.connect(callback)
            else:
                button.clicked.connect(lambda checked=False, action=label: unavailable_action(self, action))
            layout.addWidget(button)


class TransactionHeader(ERPPageHeader):
    """Shared heading used by every transaction entry page."""

    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(title, subtitle, parent)
        self.setProperty("transactionFramework", True)
        self.setMinimumHeight(44)


class TransactionToolbar(QFrame):
    """Canonical transaction toolbar with a stable action order."""

    ACTION_ORDER = (
        "New",
        "Preview",
        "Print",
        "PDF",
        "WhatsApp",
        "Email",
        "Save",
        "Close",
        "Delete",
        "Export",
        "Import",
        "Refresh",
        "Search",
    )

    def __init__(self, buttons: list[tuple[str, object]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionToolbar")
        self.setProperty("role", "toolbar")
        self.setProperty("transactionFramework", True)
        callbacks = {label: callback for label, callback in buttons}
        layout = FlowLayout(self, margin=5, spacing=4)
        self.buttons: dict[str, QPushButton] = {}
        for label in self.ACTION_ORDER:
            callback = callbacks.get(label)
            button = QPushButton(label)
            button.setObjectName("primaryButton" if label == "Save" else "quickButton")
            button.setProperty("transactionAction", label.lower())
            button.setMinimumHeight(26)
            install_button_feedback(button)
            button.clicked.connect(self._callback_wrapper(button, label, callback))
            layout.addWidget(button)
            self.buttons[label] = button

    def _callback_wrapper(self, button: QPushButton, label: str, callback: object) -> Callable[[], None]:
        def run() -> None:
            if not callable(callback):
                unavailable_action(self, label)
                return
            set_button_busy(button, True)
            QApplication.processEvents()
            try:
                callback()
            finally:
                QTimer.singleShot(200, lambda: set_button_busy(button, False))

        return run


class TransactionCard(QFrame):
    """Base card marker for consistent transaction-page styling."""

    def __init__(self, role: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setProperty("transactionFramework", True)
        self.setProperty("transactionRole", role)


class CustomerCard(TransactionCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("customer", parent)


class DocumentCard(TransactionCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("document", parent)


class AdditionalInfoCard(TransactionCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("additional", parent)


class ProductSearchCard(TransactionCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("product-search", parent)


class RemarksCard(TransactionCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("remarks", parent)


class TaxSummaryCard(TransactionCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("tax-summary", parent)


class BottomTotalsCard(TransactionCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("bottom-totals", parent)


class TransactionSectionCard(TransactionCard):
    def __init__(self, role: str = "section", parent: QWidget | None = None) -> None:
        super().__init__(role, parent)


class PartyInfoCard(CustomerCard):
    pass


class DocumentDetailsCard(DocumentCard):
    pass


class RemarksTermsCard(RemarksCard):
    pass


class TotalsCard(BottomTotalsCard):
    pass


def _money(value: float | int | str | None) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"Rs {amount:,.2f}"


class TransactionTotalsPanel(BottomTotalsCard):
    """Shared transaction totals panel for item-entry documents."""

    FIELD_ORDER = (
        ("total_qty", "Total Quantity"),
        ("discount", "Discount"),
        ("taxable", "Taxable Amount"),
        ("cgst", "CGST"),
        ("sgst", "SGST"),
        ("igst", "IGST"),
        ("gst_total", "Total Tax"),
        ("round_off", "Round Off"),
        ("total_amount", "Total Amount"),
        ("grand_total", "Grand Total"),
    )

    def __init__(self, title: str = "Totals", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 5, 8, 6)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label, 0, 0, 1, 5)
        self.labels: dict[str, QLabel] = {}
        for index, (key, label) in enumerate(self.FIELD_ORDER):
            row = 1 + index // 5
            column = index % 5
            value_label = QLabel(f"{label}\n{self._zero_value(key)}")
            value_label.setObjectName("grandTotalValue" if key == "grand_total" else "summaryValue")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_label.setWordWrap(True)
            value_label.setMinimumHeight(42)
            layout.addWidget(value_label, row, column)
            self.labels[key] = value_label
        for column in range(5):
            layout.setColumnStretch(column, 1)

    def set_totals(self, lines: list[Any], totals: dict[str, float]) -> None:
        total_qty = sum(float(getattr(getattr(row, "source", row), "qty", 0) or 0) for row in lines)
        total_amount = float(totals.get("taxable", 0) or 0) + float(totals.get("gst_total", 0) or 0)
        values = {
            "total_qty": f"{total_qty:,.3f}",
            "discount": _money(totals.get("discount", 0)),
            "taxable": _money(totals.get("taxable", 0)),
            "cgst": _money(totals.get("cgst", 0)),
            "sgst": _money(totals.get("sgst", 0)),
            "igst": _money(totals.get("igst", 0)),
            "gst_total": _money(totals.get("gst_total", 0)),
            "round_off": _money(totals.get("round_off", 0)),
            "total_amount": _money(total_amount),
            "grand_total": _money(totals.get("grand_total", 0)),
        }
        for key, label in self.FIELD_ORDER:
            self.labels[key].setText(f"{label}\n{values[key]}")

    def _zero_value(self, key: str) -> str:
        if key == "total_qty":
            return "0.000"
        return _money(0)


class TransactionTaxSummaryPanel(TaxSummaryCard):
    """Shared tax summary table with a visible empty state."""

    def __init__(self, title: str = "Tax Summary", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 6)
        layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        self.table = QTableWidget(0, 3)
        self.table.setProperty("transactionFramework", True)
        self.table.setHorizontalHeaderLabels(["Tax Type", "Taxable", "Tax"])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(82)
        self.table.setMaximumHeight(96)
        layout.addWidget(title_label)
        layout.addWidget(self.table)
        self.set_lines([], {})

    def set_lines(self, lines: list[Any], totals: dict[str, float]) -> None:
        if not lines:
            self.table.setRowCount(1)
            for column, value in enumerate(["No data available", "", ""]):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(0, column, item)
            return
        buckets: dict[str, list[float]] = {}
        for line in lines:
            source = getattr(line, "source", line)
            gst_rate = float(getattr(source, "gst_rate", 0) or 0)
            taxable = float(getattr(line, "taxable", 0) or 0)
            for tax_key, label_rate, amount in (
                ("CGST", gst_rate / 2, float(getattr(line, "cgst", 0) or 0)),
                ("SGST", gst_rate / 2, float(getattr(line, "sgst", 0) or 0)),
                ("IGST", gst_rate, float(getattr(line, "igst", 0) or 0)),
            ):
                if not amount:
                    continue
                label = f"{tax_key} @ {self._rate_label(label_rate)}%"
                buckets.setdefault(label, [0.0, 0.0])
                buckets[label][0] += taxable
                buckets[label][1] += amount
        rows = [(label, round(values[0], 2), round(values[1], 2)) for label, values in sorted(buckets.items())]
        rows.append(("Total", float(totals.get("taxable", 0) or 0), float(totals.get("gst_total", 0) or 0)))
        self.table.setRowCount(len(rows))
        for row_index, (label, taxable, tax) in enumerate(rows):
            for column, value in enumerate([label, _money(taxable), _money(tax)]):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column > 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column, item)

    def _rate_label(self, rate: float) -> str:
        return f"{rate:.2f}".rstrip("0").rstrip(".")


class GridActionBar(QFrame):
    """Compact item-grid action strip shared by transaction entry screens."""

    ACTIONS = (
        ("Add Row", "add_row"),
        ("Delete Row", "delete_row"),
        ("Import", "import"),
        ("Scan Barcode", "scan_barcode"),
    )

    def __init__(
        self,
        handlers: dict[str, Callable[[], None] | None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("actionToolbar")
        self.setProperty("transactionFramework", True)
        self.setProperty("gridActionBar", True)
        self.setProperty("transactionRole", "grid-actions")
        handlers = handlers or {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)
        self.buttons: dict[str, QPushButton] = {}
        for label, key in self.ACTIONS:
            button_text = "Add Row / F4" if key == "add_row" else label
            button = QPushButton(button_text)
            button.setObjectName("quickButton")
            button.setMinimumHeight(26)
            button.setProperty("gridCommand", key)
            callback = handlers.get(key)
            install_button_feedback(button)
            button.clicked.connect(self._callback_wrapper(button, label, key, callback))
            button.setToolTip(self._tooltip(key))
            layout.addWidget(button)
            self.buttons[key] = button
        layout.addStretch(1)

    def _callback_wrapper(
        self,
        button: QPushButton,
        label: str,
        key: str,
        callback: Callable[[], None] | None,
    ) -> Callable[[], None]:
        def run() -> None:
            if not callable(callback):
                unavailable_action(self, label)
                return
            set_button_busy(button, True)
            QApplication.processEvents()
            try:
                callback()
            finally:
                QTimer.singleShot(200, lambda: set_button_busy(button, False))

        return run

    def _tooltip(self, key: str) -> str:
        labels = {
            "add_row": "Add the current product line or press F4.",
            "delete_row": "Delete the selected item row safely.",
            "import": "Import item rows where this page supports it.",
            "scan_barcode": "Focus barcode or product scan input where available.",
        }
        return labels.get(key, "")


class TransactionGridPanel(TransactionSectionCard):
    def __init__(
        self,
        grid: QWidget,
        handlers: dict[str, Callable[[], None] | None] | None = None,
        role: str = "items",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(role, parent)
        self.grid = grid
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(3)
        self.action_bar = GridActionBar(self._wrapped_handlers(handlers or {}), self)
        layout.addWidget(self.action_bar)
        layout.addWidget(grid, stretch=1)

    def _wrapped_handlers(
        self,
        handlers: dict[str, Callable[[], None] | None],
    ) -> dict[str, Callable[[], None] | None]:
        callback = handlers.get("add_row")
        if not callable(callback):
            return handlers

        def add_row_and_focus() -> None:
            before_rows = self._row_count()
            callback()
            self._focus_grid_row(before_rows)

        wrapped = dict(handlers)
        wrapped["add_row"] = add_row_and_focus
        return wrapped

    def _row_count(self) -> int:
        row_count = getattr(self.grid, "rowCount", None)
        if callable(row_count):
            return int(row_count())
        return 0

    def _focus_grid_row(self, previous_rows: int) -> None:
        if self._row_count() <= 0:
            return
        focus_row = self._row_count() - 1 if self._row_count() > previous_rows else max(
            0,
            getattr(self.grid, "currentRow", lambda: 0)(),
        )
        editable_columns = getattr(self.grid, "_editable_column_list", None)
        columns = editable_columns() if callable(editable_columns) else []
        focus_column = columns[0] if columns else 0
        set_focus = getattr(self.grid, "setFocus", None)
        set_current_cell = getattr(self.grid, "setCurrentCell", None)
        if callable(set_focus):
            set_focus()
        if callable(set_current_cell):
            set_current_cell(focus_row, focus_column)
        ensure_item = getattr(self.grid, "_ensure_item", None)
        item = ensure_item(focus_row, focus_column) if callable(ensure_item) else None
        edit_item = getattr(self.grid, "editItem", None)
        if item is not None and callable(edit_item):
            edit_item(item)


class TransactionPageLayout:
    """Small scaffold that keeps transaction screen regions in one order."""

    def __init__(self, page: QWidget, margin: int = 0, spacing: int = 4) -> None:
        self.layout = QVBoxLayout(page)
        self.layout.setContentsMargins(margin, margin, margin, margin)
        self.layout.setSpacing(spacing)
        page.setProperty("transactionFramework", True)

    def add_header(self, widget: QWidget) -> None:
        install_button_feedback_tree(widget)
        self.layout.addWidget(widget)

    def add_toolbar(self, widget: QWidget) -> None:
        install_button_feedback_tree(widget)
        self.layout.addWidget(widget)

    def add_section(self, widget: QWidget, stretch: int = 0) -> None:
        install_button_feedback_tree(widget)
        self.layout.addWidget(widget, stretch=stretch)

    def add_grid(self, widget: QWidget, stretch: int = 1) -> None:
        widget.setProperty("transactionGridRegion", True)
        install_button_feedback_tree(widget)
        self.layout.addWidget(widget, stretch=stretch)

    def add_summary(self, widget: QWidget) -> None:
        widget.setProperty("transactionSummaryRegion", True)
        install_button_feedback_tree(widget)
        self.layout.addWidget(widget)


class ERPSectionCard(QFrame):
    def __init__(self, title: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            layout.addWidget(title_label)


class ERPToolbarButton(QPushButton):
    def __init__(self, label: str, primary: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.setObjectName("primaryButton" if primary else "quickButton")
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        install_button_feedback(self)


class ERPStatusBadge(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("alertChip")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(24)


class ERPDashboardCard(QFrame):
    """Reusable executive-dashboard card with refresh and common UI states."""

    def __init__(
        self,
        title: str,
        refresh_callback: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setProperty("dashboardCard", True)
        self.setMinimumHeight(112)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(5)

        header = QHBoxLayout()
        header.setSpacing(5)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(True)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("caption")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setMinimumWidth(48)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("quickButton")
        self.refresh_button.setToolTip(f"Refresh {title}")
        self.refresh_button.setMinimumHeight(24)
        self.refresh_button.setMaximumHeight(28)
        self.refresh_button.setMaximumWidth(74)
        install_button_feedback(self.refresh_button)
        if callable(refresh_callback):
            self.refresh_button.clicked.connect(refresh_callback)
        header.addWidget(self.title_label, stretch=1)
        header.addWidget(self.status_label)
        header.addWidget(self.refresh_button)
        root.addLayout(header)

        self.state_label = QLabel("")
        self.state_label.setObjectName("dashboardState")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setWordWrap(True)
        self.state_label.setMinimumHeight(38)
        self.state_label.hide()
        root.addWidget(self.state_label)

        self.content = QWidget()
        self.content.setObjectName("dashboardCardContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)
        root.addWidget(self.content, stretch=1)

    def set_loading(self, message: str = "Loading...") -> None:
        self.status_label.setText("Loading")
        self.state_label.setText(message)
        self.state_label.show()
        self.content.hide()
        set_button_busy(self.refresh_button, True)

    def set_empty(self, message: str = "No data available") -> None:
        self.status_label.setText("No data")
        self.state_label.setText(message)
        self.state_label.show()
        self.content.hide()
        set_button_busy(self.refresh_button, False)

    def set_error(self, message: str = "Unable to load data") -> None:
        self.status_label.setText("Error")
        self.state_label.setText(message)
        self.state_label.show()
        self.content.hide()
        set_button_busy(self.refresh_button, False)

    def set_ready(self, message: str = "Ready") -> None:
        self.status_label.setText(message)
        self.state_label.hide()
        self.content.show()
        set_button_busy(self.refresh_button, False)


class ERPDashboardTable(QTableWidget):
    """Read-only dashboard table with keyboard and double-click activation."""

    rowActivated = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 0, parent)
        self.setProperty("dashboardTable", True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(28)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setMinimumSectionSize(42)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._rows: list[dict[str, Any]] = []
        self._headers: list[str] = []
        self.cellDoubleClicked.connect(self._emit_row_activated)

    def set_rows(
        self,
        rows: list[dict[str, Any]],
        headers: list[str],
        pretty_headers: dict[str, str] | None = None,
        numeric_keys: set[str] | None = None,
    ) -> None:
        self._rows = list(rows)
        self._headers = list(headers)
        labels = pretty_headers or {}
        numeric = numeric_keys or set()
        self.clear()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels([labels.get(header, header.replace("_", " ").title()) for header in headers])
        if not rows:
            self.setRowCount(1)
            if headers:
                self.setItem(0, 0, QTableWidgetItem("No data available"))
                for column in range(1, len(headers)):
                    self.setItem(0, column, QTableWidgetItem(""))
            return
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(self._display(value))
                if header in numeric or isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.setItem(row_index, column, item)
        self.resizeRowsToContents()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._emit_row_activated(max(0, self.currentRow()), max(0, self.currentColumn()))
            return
        super().keyPressEvent(event)

    def _emit_row_activated(self, row: int, _column: int) -> None:
        if 0 <= row < len(self._rows):
            self.rowActivated.emit(self._rows[row])

    def _display(self, value: Any) -> str:
        if isinstance(value, float):
            return f"{value:,.2f}"
        return "" if value is None else str(value)


class ERPLineChart(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.points: list[dict[str, Any]] = []
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_points(self, points: list[dict[str, Any]]) -> None:
        self.points = list(points)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart = self.rect().adjusted(18, 12, -18, -28)
        values = [float(point.get("value") or 0) for point in self.points]
        if not self.points or not any(values):
            painter.setPen(QColor("#475569"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data available")
            return
        max_value = max(max(values), 1.0)
        painter.setPen(QPen(QColor("#D8E2F0"), 1))
        for index in range(4):
            y = chart.bottom() - (chart.height() * index / 3)
            painter.drawLine(chart.left(), int(y), chart.right(), int(y))
        points: list[tuple[int, int]] = []
        for index, point in enumerate(self.points):
            x = chart.left() + int(chart.width() * index / max(1, len(self.points) - 1))
            y = chart.bottom() - int(chart.height() * float(point.get("value") or 0) / max_value)
            points.append((x, y))
        painter.setPen(QPen(QColor("#2563EB"), 2))
        for current, nxt in zip(points, points[1:]):
            painter.drawLine(current[0], current[1], nxt[0], nxt[1])
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(QColor("#2563EB"), 2))
        for x, y in points:
            painter.drawEllipse(x - 3, y - 3, 6, 6)
        painter.setPen(QColor("#475569"))
        painter.setFont(QFont("Segoe UI", 7))
        for index, point in enumerate(self.points):
            x = chart.left() + int(chart.width() * index / max(1, len(self.points) - 1))
            painter.drawText(x - 26, chart.bottom() + 6, 52, 18, Qt.AlignmentFlag.AlignCenter, str(point.get("label", "")))


class ERPPieChart(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.segments: list[dict[str, Any]] = []
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_segments(self, segments: list[dict[str, Any]]) -> None:
        self.segments = list(segments)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        total = sum(max(0.0, float(segment.get("value") or 0)) for segment in self.segments)
        if total <= 0:
            painter.setPen(QColor("#475569"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data available")
            return
        size = min(max(74, self.height() - 36), max(74, int(self.width() * 0.32)))
        pie_rect = self.rect().adjusted(14, 14, 0, 0)
        pie_rect.setWidth(size)
        pie_rect.setHeight(size)
        start_angle = 90 * 16
        for segment in self.segments:
            value = max(0.0, float(segment.get("value") or 0))
            if value <= 0:
                continue
            span = int(-360 * 16 * value / total)
            color = QColor(str(segment.get("color") or "#2563EB"))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            painter.drawPie(pie_rect, start_angle, span)
            start_angle += span
        legend_x = pie_rect.right() + 16
        painter.setFont(QFont("Segoe UI", 8))
        for index, segment in enumerate(self.segments[:5]):
            value = max(0.0, float(segment.get("value") or 0))
            if value <= 0:
                continue
            y = pie_rect.top() + index * 24
            color = QColor(str(segment.get("color") or "#2563EB"))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            painter.drawRoundedRect(legend_x, y + 4, 10, 10, 3, 3)
            painter.setPen(QColor("#475569"))
            label = str(segment.get("label") or "Value")
            painter.drawText(legend_x + 16, y, max(80, self.width() - legend_x - 20), 18, Qt.AlignmentFlag.AlignLeft, label)


class ERPBarChart(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.bars: list[dict[str, Any]] = []
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_bars(self, bars: list[dict[str, Any]]) -> None:
        self.bars = list(bars)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        values = [float(row.get("value") or 0) for row in self.bars]
        if not self.bars or not any(values):
            painter.setPen(QColor("#475569"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data available")
            return
        chart = self.rect().adjusted(16, 12, -16, -24)
        max_value = max(max(values), 1.0)
        bar_gap = 8
        bar_width = max(12, int((chart.width() - bar_gap * (len(self.bars) - 1)) / max(1, len(self.bars))))
        painter.setFont(QFont("Segoe UI", 7))
        for index, row in enumerate(self.bars):
            value = float(row.get("value") or 0)
            x = chart.left() + index * (bar_width + bar_gap)
            height = int(chart.height() * value / max_value)
            y = chart.bottom() - height
            color = QColor(str(row.get("color") or "#2563EB"))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            painter.drawRoundedRect(x, y, bar_width, height, 4, 4)
            painter.setPen(QColor("#475569"))
            painter.drawText(x - 6, chart.bottom() + 5, bar_width + 12, 16, Qt.AlignmentFlag.AlignCenter, str(row.get("label") or ""))


class ERPGrid(QTableWidget):
    """Standardized editable grid for transaction pages.

    Features:
    - Single-click cell editing for configured editable columns
    - Enter moves to next editable cell; Shift+Enter moves to previous
    - Tab/Shift+Tab native behavior preserved
    - Alternating rows, sticky header and consistent row height
    """

    def __init__(self, rows: int = 0, cols: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(rows, cols, parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._editable_columns: set[int] = set()
        self._editable_columns_configured = False
        self.verticalHeader().setDefaultSectionSize(26)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setTabKeyNavigation(False)

    def set_editable_columns(self, cols: set[int]) -> None:
        self._editable_columns = set(cols)
        self._editable_columns_configured = True

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(0, 96)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(760, 132)

    def _editable_column_list(self) -> list[int]:
        cols = sorted(self._editable_columns) if self._editable_columns_configured else list(range(self.columnCount()))
        return [col for col in cols if 0 <= col < self.columnCount() and not self.isColumnHidden(col)]

    def _ensure_item(self, row: int, col: int) -> QTableWidgetItem:
        item = self.item(row, col)
        if item is None:
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, col, item)
        return item

    def _focus_first_editable_cell(self) -> None:
        cols = self._editable_column_list()
        if not cols or self.rowCount() <= 0:
            return
        row = self.currentRow()
        if row < 0:
            row = 0
        self.setCurrentCell(min(row, self.rowCount() - 1), cols[0])

    def _move_to_editable_cell(self, shift: bool = False) -> None:
        cols = self._editable_column_list()
        if not cols:
            return
        row = self.currentRow()
        col = self.currentColumn()
        if row < 0:
            row = 0
        if col < 0:
            col = cols[0]
        try:
            idx = cols.index(col)
        except ValueError:
            idx = 0
        if shift:
            if idx <= 0:
                next_row = max(0, row - 1)
                next_col = cols[-1]
            else:
                next_row = row
                next_col = cols[idx - 1]
        else:
            if idx + 1 < len(cols):
                next_row = row
                next_col = cols[idx + 1]
            else:
                next_row = min(self.rowCount() - 1, row + 1)
                next_col = cols[0]
        if next_row < 0:
            next_row = 0
        self.setCurrentCell(next_row, next_col)
        item = self._ensure_item(next_row, next_col)
        self.editItem(item)

    def focusInEvent(self, event: QEvent) -> None:
        super().focusInEvent(event)
        if self.rowCount() > 0 and self.currentRow() < 0:
            self._focus_first_editable_cell()

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        idx = self.indexAt(event.pos())
        if not idx.isValid():
            return
        col = idx.column()
        row = idx.row()
        if col in self._editable_columns:
            item = self._ensure_item(row, col)
            self.editItem(item)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        modifiers = event.modifiers()
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._move_to_editable_cell(shift)
            return
        if key == Qt.Key.Key_Tab:
            self._move_to_editable_cell(shift)
            return
        if key == Qt.Key.Key_Escape:
            if self.state() == QAbstractItemView.State.EditingState and self.currentItem() is not None:
                self.closePersistentEditor(self.currentItem())
                return
            self.clearSelection()
            return
        blocked = modifiers & (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        )
        if self.currentColumn() >= 0 and self.currentColumn() in self._editable_columns and event.text() and not blocked:
            item = self._ensure_item(self.currentRow(), self.currentColumn())
            self.editItem(item)
        return super().keyPressEvent(event)


class ERPTransactionGrid(ERPGrid):
    """Keyboard-first transaction grid with centralized command hooks."""

    commandRequested = pyqtSignal(str)
    lastEditableCellReached = pyqtSignal()

    def __init__(self, rows: int = 0, cols: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(rows, cols, parent)
        self.setProperty("transactionFramework", True)
        self._command_handlers: dict[str, Callable[[], None]] = {}

    def set_command_handlers(self, handlers: dict[str, Callable[[], None] | None]) -> None:
        self._command_handlers = {key: value for key, value in handlers.items() if callable(value)}

    def _invoke_command(self, command: str) -> bool:
        callback = self._command_handlers.get(command)
        self.commandRequested.emit(command)
        if callback is None:
            return False
        before_rows = self.rowCount()
        callback()
        if command == "add_row":
            self._focus_added_or_current_row(before_rows)
        return True

    def _focus_added_or_current_row(self, previous_rows: int) -> None:
        if self.rowCount() <= 0:
            return
        columns = self._editable_column_list()
        if not columns:
            return
        row = self.rowCount() - 1 if self.rowCount() > previous_rows else max(0, self.currentRow())
        row = min(row, self.rowCount() - 1)
        column = columns[0]
        self.setFocus()
        self.setCurrentCell(row, column)
        self.editItem(self._ensure_item(row, column))

    def _move_to_editable_cell(self, shift: bool = False) -> None:
        cols = self._editable_column_list()
        if not cols or self.rowCount() <= 0:
            return
        row = max(self.currentRow(), 0)
        col = self.currentColumn()
        if col not in cols:
            col = cols[-1] if shift else cols[0]
        index = cols.index(col)
        if shift:
            if index > 0:
                target_row, target_col = row, cols[index - 1]
            elif row > 0:
                target_row, target_col = row - 1, cols[-1]
            else:
                target_row, target_col = 0, cols[0]
        else:
            if index + 1 < len(cols):
                target_row, target_col = row, cols[index + 1]
            elif row + 1 < self.rowCount():
                target_row, target_col = row + 1, cols[0]
            else:
                self.lastEditableCellReached.emit()
                target_row, target_col = row, cols[-1]
        self.setCurrentCell(target_row, target_col)
        self.editItem(self._ensure_item(target_row, target_col))

    def _move_home_end(self, end: bool, document: bool) -> None:
        cols = self._editable_column_list()
        if not cols or self.rowCount() <= 0:
            return
        row = self.rowCount() - 1 if document and end else 0 if document else max(self.currentRow(), 0)
        col = cols[-1] if end else cols[0]
        self.setCurrentCell(row, col)

    def _copy_selection(self, clear: bool = False) -> None:
        indexes = sorted(self.selectedIndexes(), key=lambda index: (index.row(), index.column()))
        if not indexes and self.currentIndex().isValid():
            indexes = [self.currentIndex()]
        if not indexes:
            return
        rows: dict[int, dict[int, str]] = {}
        for index in indexes:
            item = self.item(index.row(), index.column())
            rows.setdefault(index.row(), {})[index.column()] = item.text() if item else ""
        min_col = min(index.column() for index in indexes)
        max_col = max(index.column() for index in indexes)
        text = "\n".join(
            "\t".join(columns.get(col, "") for col in range(min_col, max_col + 1))
            for _, columns in sorted(rows.items())
        )
        QApplication.clipboard().setText(text)
        if clear:
            for index in indexes:
                if index.column() in self._editable_column_list():
                    self._ensure_item(index.row(), index.column()).setText("")

    def _paste_clipboard(self) -> None:
        start_row = max(self.currentRow(), 0)
        start_col = max(self.currentColumn(), 0)
        editable = self._editable_column_list()
        if not editable or start_col not in editable:
            start_col = editable[0]
        start_index = editable.index(start_col)
        for row_offset, line in enumerate(QApplication.clipboard().text().splitlines()):
            target_row = start_row + row_offset
            if target_row >= self.rowCount():
                break
            for col_offset, value in enumerate(line.split("\t")):
                editable_index = start_index + col_offset
                if editable_index >= len(editable):
                    break
                self._ensure_item(target_row, editable[editable_index]).setText(value)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        modifiers = event.modifiers()
        control = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        if key == Qt.Key.Key_F2:
            if self.currentRow() >= 0 and self.currentColumn() in self._editable_column_list():
                self.editItem(self._ensure_item(self.currentRow(), self.currentColumn()))
            return
        command_keys = {
            Qt.Key.Key_F3: "duplicate_row",
            Qt.Key.Key_F4: "add_row",
            Qt.Key.Key_F5: "product_search",
            Qt.Key.Key_F6: "batch",
            Qt.Key.Key_F7: "stock",
            Qt.Key.Key_F8: "save",
            Qt.Key.Key_F9: "preview",
            Qt.Key.Key_F10: "print",
            Qt.Key.Key_Delete: "remove_row",
        }
        if key in command_keys and self._invoke_command(command_keys[key]):
            return
        if control and key == Qt.Key.Key_P and self._invoke_command("product_search"):
            return
        if control and key == Qt.Key.Key_C:
            self._copy_selection()
            return
        if control and key == Qt.Key.Key_X:
            self._copy_selection(clear=True)
            return
        if control and key == Qt.Key.Key_V:
            self._paste_clipboard()
            return
        if control and key == Qt.Key.Key_Z and self._invoke_command("undo"):
            return
        if control and key == Qt.Key.Key_Y and self._invoke_command("redo"):
            return
        if key == Qt.Key.Key_Home:
            self._move_home_end(end=False, document=control)
            return
        if key == Qt.Key.Key_End:
            self._move_home_end(end=True, document=control)
            return
        super().keyPressEvent(event)


class ERPItemGrid(ERPTransactionGrid):
    pass


class BottomShortcutBar(QFrame):
    def __init__(self, text: str = "F4 Add Row | Del Delete Row | Ctrl+S Save | Esc Back", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionToolbar")
        self.setProperty("transactionFramework", True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        label = QLabel(text)
        label.setObjectName("caption")
        layout.addWidget(label)
        layout.addStretch(1)
