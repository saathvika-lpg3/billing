from __future__ import annotations

from typing import Any, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from config.app_config import AppConfig
from services.dashboard_service import DashboardService
from widgets.company_branding import ClientCompanyIdentityCard
from widgets.erp_components import (
    ERPBarChart,
    ERPDashboardCard,
    ERPDashboardTable,
    ERPLineChart,
    ERPPageHeader,
    ERPPieChart,
)


class DashboardView(QWidget):
    def __init__(
        self,
        config: AppConfig,
        open_page: Callable[[str], None],
        route_allowed: Callable[[str], bool] | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.open_page = open_page
        self.route_allowed = route_allowed or (lambda _route: True)
        self.service = DashboardService()
        self.cards: dict[str, ERPDashboardCard] = {}
        self.card_order: list[str] = []
        self.metric_layouts: dict[str, QGridLayout] = {}
        self.tables: dict[str, ERPDashboardTable] = {}
        self.charts: dict[str, QWidget] = {}
        self.company_brand = ClientCompanyIdentityCard(self.config)
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        root.addWidget(self._title_bar())

        self.grid_host = QWidget()
        self.grid_host.setMinimumWidth(0)
        self.card_grid = QGridLayout(self.grid_host)
        self.card_grid.setContentsMargins(0, 0, 0, 0)
        self.card_grid.setHorizontalSpacing(6)
        self.card_grid.setVerticalSpacing(6)
        root.addWidget(self.grid_host)
        root.addStretch(1)

        self._create_cards()
        self._reflow_cards()

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Executive Dashboard", "Business intelligence, operations, accounts and system health")
        header.setMaximumHeight(56)
        self.header_status = header.status_label
        self.header_status.setText("Dashboard ready")
        refresh_button = QPushButton("Refresh All")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)
        if self.route_allowed("reports:daily_dispatch_summary"):
            dispatch_button = QPushButton("Dispatch Summary")
            dispatch_button.setObjectName("quickButton")
            dispatch_button.setAccessibleName("Open Dispatch Summary")
            dispatch_button.clicked.connect(lambda: self.open_page("reports:daily_dispatch_summary"))
            self.dispatch_summary_button = dispatch_button
            header.layout().addWidget(dispatch_button)
        header.layout().addWidget(refresh_button)
        return header

    def _create_cards(self) -> None:
        self._create_company_card()
        self._create_metric_card("business_summary", "Today's Business Summary", min_height=138)
        self._create_metric_card("sales_kpis", "Sales KPIs", ERPLineChart(), min_height=184)
        self._create_metric_card("purchase_kpis", "Purchase KPIs", ERPLineChart(), min_height=184)
        self._create_metric_card("cash_bank", "Cash & Bank Summary", ERPPieChart(), min_height=184)
        self._create_metric_table_card("receivables", "Receivables", ["name", "phone", "area", "balance"])
        self._create_metric_table_card("payables", "Payables", ["name", "phone", "area", "balance"])
        self._create_metric_card("stock_value", "Stock Value", ERPBarChart(), min_height=176)
        self._create_table_card("low_stock_alerts", "Low Stock Alerts", ["name", "unit", "stock", "min_stock", "reorder_qty"])
        self._create_table_card("expiry_alerts", "Expiry Alerts", ["item_name", "batch_no", "expiry_date", "stock"])
        self._create_table_card("pending_dispatch", "Pending Dispatch", ["challan_no", "challan_date", "area", "vehicle_no", "total_qty", "dispatch_status"])
        self._create_table_card("pending_purchase_orders", "Pending Purchase Orders", ["doc_no", "doc_date", "party_name", "grand_total", "status"])
        self._create_table_card("pending_sales_orders", "Pending Sales Orders", ["doc_no", "doc_date", "party_name", "grand_total", "status"])
        self._create_table_card("critical_alerts", "Critical Alerts", ["level", "title", "detail"], min_height=160)
        self._create_metric_table_card("communication_status", "Communication Status", ["channel", "recipient", "subject", "status", "result_code", "updated_at"])
        self._create_table_card("failed_communications", "Failed Communications", ["recipient", "subject", "result_code", "attempts", "next_retry_at"], min_height=160)
        self._create_chart_table_card("top_customers", "Top Customers", ["customer_name", "bills", "total"])
        self._create_chart_table_card("top_selling_products", "Top Selling Products", ["item_name", "qty", "total"])
        self._create_table_card("recent_sales", "Recent Sales", ["bill_no", "bill_date", "customer_name", "grand_total"], record_type="sales")
        self._create_table_card("recent_purchase", "Recent Purchase", ["bill_no", "bill_date", "supplier_name", "grand_total"], record_type="purchase")
        self._create_table_card("recent_receipts", "Recent Receipts", ["receipt_no", "receipt_date", "customer_name", "amount", "mode"], record_type="receipt")
        self._create_table_card("recent_payments", "Recent Payments", ["payment_no", "payment_date", "supplier_name", "amount", "mode"], record_type="payment")
        self._create_table_card("daily_tasks", "Daily Tasks", ["task", "detail", "priority"], min_height=158)
        self._create_table_card("backup_status", "Backup Status", ["action", "status", "message", "created_at"], min_height=148)
        self._create_table_card("database_health", "Database Health", ["status", "database", "size_mb"], min_height=148)
        self._create_table_card("application_version", "Application Version", ["component", "version", "notes", "updated_at"], min_height=148)

    def _add_card(self, key: str, title: str, min_height: int = 212) -> ERPDashboardCard:
        card = ERPDashboardCard(title, self.refresh, self)
        card.setMinimumHeight(min_height)
        self.cards[key] = card
        self.card_order.append(key)
        return card

    def _create_company_card(self) -> None:
        card = self._add_card("company", "Company Information", 310)
        card.setProperty("erpPreserveGeometry", True)
        card.content_layout.addWidget(self.company_brand)

    def _create_metric_card(self, key: str, title: str, chart: QWidget | None = None, min_height: int = 212) -> None:
        card = self._add_card(key, title, min_height)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        card.content_layout.addLayout(grid)
        self.metric_layouts[key] = grid
        if chart is not None:
            card.content_layout.addWidget(chart)
            self.charts[key] = chart

    def _create_metric_table_card(self, key: str, title: str, headers: list[str]) -> None:
        self._create_metric_card(key, title, min_height=178)
        table = ERPDashboardTable()
        table.setMaximumHeight(108)
        self.cards[key].content_layout.addWidget(table)
        self.tables[key] = table
        table.set_rows([], headers, self._pretty_headers())

    def _create_chart_table_card(self, key: str, title: str, headers: list[str]) -> None:
        card = self._add_card(key, title, 188)
        chart = ERPBarChart()
        table = ERPDashboardTable()
        table.setMaximumHeight(96)
        card.content_layout.addWidget(chart)
        card.content_layout.addWidget(table)
        self.charts[key] = chart
        self.tables[key] = table
        table.set_rows([], headers, self._pretty_headers())

    def _create_table_card(
        self,
        key: str,
        title: str,
        headers: list[str],
        record_type: str = "",
        min_height: int = 172,
    ) -> None:
        card = self._add_card(key, title, min_height)
        table = ERPDashboardTable()
        card.content_layout.addWidget(table)
        self.tables[key] = table
        table.set_rows([], headers, self._pretty_headers())
        if record_type:
            table.setToolTip("Double-click a row or press Enter to open the related document.")
            table.rowActivated.connect(lambda row, kind=record_type: self._open_record(kind, row))

    def refresh(self) -> None:
        for card in self.cards.values():
            card.set_loading()
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
        try:
            data = self.service.snapshot()
        except Exception as exc:
            for card in self.cards.values():
                card.set_error(str(exc))
            self.header_status.setText("Dashboard source unavailable")
            return

        self._render_company(data.get("company", {}))
        self._render_metric_section("business_summary", data.get("business_summary", []))
        self._render_metric_section("sales_kpis", data.get("sales_kpis", {}).get("items", []))
        self._set_line_chart("sales_kpis", data.get("sales_kpis", {}).get("trend", []))
        self._render_metric_section("purchase_kpis", data.get("purchase_kpis", {}).get("items", []))
        self._set_line_chart("purchase_kpis", data.get("purchase_kpis", {}).get("trend", []))
        self._render_metric_section("cash_bank", data.get("cash_bank", {}).get("items", []))
        self._set_pie_chart("cash_bank", data.get("cash_bank", {}).get("segments", []))
        self._render_metric_table("receivables", data.get("receivables", {}), ["name", "phone", "area", "balance"])
        self._render_metric_table("payables", data.get("payables", {}), ["name", "phone", "area", "balance"])
        self._render_metric_section("stock_value", data.get("stock_value", {}).get("items", []))
        self._set_bar_chart("stock_value", data.get("stock_value", {}).get("bars", []))
        self._render_table("low_stock_alerts", data.get("low_stock_alerts", []), ["name", "unit", "stock", "min_stock", "reorder_qty"])
        self._render_table("expiry_alerts", data.get("expiry_alerts", []), ["item_name", "batch_no", "expiry_date", "stock"])
        self._render_table("pending_dispatch", data.get("pending_dispatch", []), ["challan_no", "challan_date", "area", "vehicle_no", "total_qty", "dispatch_status"])
        self._render_table("pending_purchase_orders", data.get("pending_purchase_orders", []), ["doc_no", "doc_date", "party_name", "grand_total", "status"])
        self._render_table("pending_sales_orders", data.get("pending_sales_orders", []), ["doc_no", "doc_date", "party_name", "grand_total", "status"])
        self._render_table("critical_alerts", data.get("critical_alerts", []), ["level", "title", "detail"])
        self._render_metric_table("communication_status", data.get("communication_status", {}), ["channel", "recipient", "subject", "status", "result_code", "updated_at"])
        self._render_table("failed_communications", data.get("failed_communications", []), ["recipient", "subject", "result_code", "attempts", "next_retry_at"])
        self._render_chart_table("top_customers", data.get("top_customers", {}), ["customer_name", "bills", "total"])
        self._render_chart_table("top_selling_products", data.get("top_selling_products", {}), ["item_name", "qty", "total"])
        self._render_table("recent_sales", data.get("recent_sales", []), ["bill_no", "bill_date", "customer_name", "grand_total"])
        self._render_table("recent_purchase", data.get("recent_purchase", []), ["bill_no", "bill_date", "supplier_name", "grand_total"])
        self._render_table("recent_receipts", data.get("recent_receipts", []), ["receipt_no", "receipt_date", "customer_name", "amount", "mode"])
        self._render_table("recent_payments", data.get("recent_payments", []), ["payment_no", "payment_date", "supplier_name", "amount", "mode"])
        self._render_table("daily_tasks", data.get("daily_tasks", []), ["task", "detail", "priority"])
        self._render_table("backup_status", data.get("backup_status", []), ["action", "status", "message", "created_at"])
        self._render_table("database_health", data.get("database_health", []), ["status", "database", "size_mb"])
        self._render_table("application_version", data.get("application_version", []), ["component", "version", "notes", "updated_at"])
        self.header_status.setText("Dashboard refreshed")

    def _render_company(self, company: dict[str, Any]) -> None:
        card = self.cards["company"]
        if not company:
            card.set_empty()
            return
        self.company_brand.set_company(company)
        card.set_ready()

    def _render_metric_section(self, key: str, metrics: list[dict[str, Any]]) -> None:
        card = self.cards[key]
        layout = self.metric_layouts[key]
        self._clear_grid(layout)
        if not metrics:
            card.set_empty()
            return
        for index, metric in enumerate(metrics):
            layout.addWidget(self._metric_widget(metric), index // 2, index % 2)
        for column in range(2):
            layout.setColumnStretch(column, 1)
        card.set_ready(f"{len(metrics)} KPIs")

    def _render_metric_table(self, key: str, section: dict[str, Any], headers: list[str]) -> None:
        self._render_metric_section(key, section.get("items", []))
        self._render_table(key, section.get("rows", []), headers, allow_empty_ready=bool(section.get("items")))

    def _render_chart_table(self, key: str, section: dict[str, Any], headers: list[str]) -> None:
        self._set_bar_chart(key, section.get("bars", []))
        self._render_table(key, section.get("rows", []), headers)

    def _render_table(
        self,
        key: str,
        rows: list[dict[str, Any]],
        headers: list[str],
        allow_empty_ready: bool = False,
    ) -> None:
        card = self.cards[key]
        table = self.tables[key]
        table.set_rows(rows, headers, self._pretty_headers(), self._numeric_keys())
        if rows:
            card.set_ready(f"{len(rows)} rows")
        elif allow_empty_ready:
            card.set_ready("0 rows")
        else:
            card.set_empty()

    def _set_line_chart(self, key: str, points: list[dict[str, Any]]) -> None:
        chart = self.charts.get(key)
        if isinstance(chart, ERPLineChart):
            chart.set_points(points)

    def _set_pie_chart(self, key: str, segments: list[dict[str, Any]]) -> None:
        chart = self.charts.get(key)
        if isinstance(chart, ERPPieChart):
            chart.set_segments(segments)

    def _set_bar_chart(self, key: str, bars: list[dict[str, Any]]) -> None:
        chart = self.charts.get(key)
        if isinstance(chart, ERPBarChart):
            chart.set_bars(bars)

    def _metric_widget(self, metric: dict[str, Any]) -> QWidget:
        frame = QFrame()
        frame.setObjectName("innerCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(1)
        title = QLabel(str(metric.get("title") or "Metric"))
        title.setObjectName("dashboardMetricLabel")
        value = QLabel(str(metric.get("value") or "0"))
        value.setObjectName("dashboardMetricValue")
        note = QLabel(str(metric.get("note") or ""))
        note.setObjectName("dashboardMetricNote")
        note.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(value)
        layout.addWidget(note)
        return frame

    def _open_record(self, record_type: str, row: dict[str, Any]) -> None:
        record_id = int(row.get("id") or 0)
        if record_id <= 0:
            return
        route_map = {
            "sales": "document:sales",
            "purchase": "document:purchases",
            "receipt": "document:receipts",
            "payment": "document:payments",
        }
        route = route_map.get(record_type)
        if route:
            self.open_page(f"{route}:{record_id}")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reflow_cards()

    def _reflow_cards(self) -> None:
        if not hasattr(self, "card_grid"):
            return
        while self.card_grid.count():
            self.card_grid.takeAt(0)
        width = max(1, self.width())
        columns = 4 if width >= 1500 else 3 if width >= 1040 else 2 if width >= 720 else 1
        for index, key in enumerate(self.card_order):
            self.card_grid.addWidget(self.cards[key], index // columns, index % columns)
        for column in range(columns):
            self.card_grid.setColumnStretch(column, 1)

    def _clear_grid(self, layout: QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _pretty_headers(self) -> dict[str, str]:
        return {
            "bill_no": "Bill",
            "bill_date": "Date",
            "supplier_name": "Supplier",
            "customer_name": "Customer",
            "grand_total": "Amount",
            "receipt_no": "Receipt",
            "receipt_date": "Date",
            "payment_no": "Payment",
            "payment_date": "Date",
            "doc_no": "Document",
            "doc_date": "Date",
            "party_name": "Party",
            "item_name": "Item",
            "min_stock": "Min",
            "reorder_qty": "Reorder",
            "expiry_date": "Expiry",
            "batch_no": "Batch",
            "total_qty": "Qty",
            "dispatch_status": "Dispatch",
            "result_code": "Result",
            "next_retry_at": "Next Retry",
            "created_at": "Updated",
            "size_mb": "Size MB",
        }

    def _numeric_keys(self) -> set[str]:
        return {
            "amount",
            "attempts",
            "balance",
            "bills",
            "grand_total",
            "min_stock",
            "qty",
            "reorder_qty",
            "size_mb",
            "stock",
            "total",
            "total_qty",
        }
