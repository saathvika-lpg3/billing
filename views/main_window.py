from __future__ import annotations

import traceback
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QSizePolicy,
    QApplication,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from config.qt_fonts import ensure_application_font
from services.audit_reader import read_csv_rows
from services.business_rules import normalize_business_type
from services.company_profile_service import CompanyProfileService
from services.license_service import LicenseContext, LicenseService
from services.mysql_source import MySqlSource
from views.account_entry_view import AccountEntryView
from views.dashboard_view import DashboardView
from views.document_center_view import DocumentCenterView
from views.dispatch_return_view import DispatchReturnView
from views.developer_console_view import DeveloperConsoleView
from views.excel_import_view import ExcelImportView
from views.financial_years_view import FinancialYearAdminView
from views.global_search_view import GlobalSearchView
from views.inventory_entry_view import InventoryEntryView
from views.label_print_view import LabelPrintView
from views.module_hub_view import (
    ACCOUNTS_OPERATIONS,
    ADMIN_OPERATIONS,
    DOCUMENT_OPERATIONS,
    INVENTORY_OPERATIONS,
    MASTERS_OPERATIONS,
    PURCHASE_OPERATIONS,
    REPORTS_OPERATIONS,
    SALES_OPERATIONS,
    ModuleHubView,
)
from views.numbering_series_view import NumberingSeriesAdminView
from views.party_master_view import PartyMasterView
from views.product_master_view import ProductMasterView
from views.purchase_entry_view import PurchaseEntryView
from views.purchase_document_view import PurchaseDocumentView
from views.report_center_view import ReportCenterView
from views.route_settlement_view import RouteSettlementView
from views.sales_bill_view import SalesBillView
from views.sales_document_view import SalesDocumentView
from views.scheme_master_view import SchemeMasterView
from views.simple_master_view import SimpleMasterView
from views.stock_dashboard_view import StockDashboardView
from views.stock_out_view import StockOutView
from widgets.enter_key_flow import EnterKeyFlowFilter
from widgets.erp_components import TransactionTotalsPanel, install_button_feedback_tree
from widgets.navigation import SidebarNavigationButton
from widgets.product_branding import ProductBrandHeader
from widgets.smart_combo import install_smart_combos


class FitToWidthStack(QStackedWidget):
    def hasHeightForWidth(self) -> bool:  # noqa: N802
        current = self.currentWidget()
        return bool(current and current.hasHeightForWidth())

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        current = self.currentWidget()
        if current and current.hasHeightForWidth():
            return current.heightForWidth(width)
        return self.sizeHint().height()

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        current = self.currentWidget()
        height = current.minimumSizeHint().height() if current else 0
        return QSize(0, height)

    def sizeHint(self) -> QSize:  # noqa: N802
        current = self.currentWidget()
        if current and current.property("transactionFramework") is True:
            # Transaction pages deliberately give the item grid the flexible
            # vertical region. Prefer the page's readable minimum so a normal
            # 1366x768 viewport compresses that grid before QScrollArea makes
            # the totals/footer start below the fold.
            height = current.minimumSizeHint().height()
        else:
            height = current.sizeHint().height() if current else 700
        return QSize(980, height)


class MainWindow(QMainWindow):
    def _startup_trace(self, step: str, status: str, message: str = "") -> None:
        log_dir = Path(__file__).resolve().parents[1] / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "prm_startup.log"
        timestamp = datetime.now().isoformat(timespec="seconds")
        entry = f"{timestamp} | {step} | {status} | {message}\n"
        try:
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(entry)
        except Exception:
            pass

    def _startup_trace_exception(self, step: str, exc: Exception) -> None:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self._startup_trace(step, "FAILED", f"exception_type={type(exc).__name__} message={exc}")
        frame = traceback.extract_tb(exc.__traceback__)[-1] if exc.__traceback__ else None
        if frame is not None:
            self._startup_trace(
                step,
                "TRACEBACK",
                f"filename={frame.filename} method={frame.name} line={frame.lineno}",
            )
        self._startup_trace(step, "TRACEBACK", tb.rstrip())

    def __init__(
        self,
        config: AppConfig,
        start_page: str = "dashboard",
        license_context: LicenseContext | None = None,
        license_service: LicenseService | None = None,
        session: dict[str, str] | None = None,
    ) -> None:
        self._startup_trace("main_window_constructor", "START", "Initializing MainWindow")
        super().__init__()
        ensure_application_font()
        self.config = config
        self.license_context = license_context
        self.license_service = license_service
        self.session = session or {"name": "Developer", "email": "", "role": "admin"}
        self.developer_unlocked = False
        self.source = MySqlSource()
        self.history: list[str] = []
        self.current_page = "dashboard"
        self.current_route = "dashboard"
        self.dark_mode = False
        self.company_profile: dict[str, object] = {}
        self._startup_trace("company_profile_loading", "START", "Loading company profile")
        try:
            self.company_profile = CompanyProfileService(self.source.sqlite_path).current_profile()
            self._startup_trace(
                "company_profile_loading",
                "SUCCESS",
                "company_id={company_id} name={name} business_type={business_type} logo_configured={logo}".format(
                    company_id=int(self.company_profile.get("company_id") or 0),
                    name=str(self.company_profile.get("company_name") or ""),
                    business_type=str(self.company_profile.get("business_type_code") or ""),
                    logo=bool(self.company_profile.get("logo_path")),
                ),
            )
        except Exception as exc:
            self._startup_trace_exception("company_profile_loading", exc)
        self._startup_trace("business_type_loading", "START", "Loading business type")
        try:
            business_type = normalize_business_type(
                str(self.company_profile.get("business_type_code") or self.company_profile.get("business_type") or "").strip()
            )
            self._startup_trace("business_type_loading", "SUCCESS", f"business_type={business_type}")
        except Exception as exc:
            self._startup_trace_exception("business_type_loading", exc)
        self.setWindowTitle("PRM BILLING INVENTORY")
        self.resize(1220, 700)
        self.setMinimumSize(900, 500)
        self.stack = FitToWidthStack()
        self.stack.setMinimumWidth(0)
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_scroll: QScrollArea | None = None
        self.pages: dict[str, QWidget] = {}
        self.page_factories: dict[str, Callable[[], QWidget]] = {}
        self.sidebar_buttons: dict[str, QPushButton] = {}
        self.ribbon_buttons: dict[str, QPushButton] = {}
        self.top_info_blocks: list[QWidget] = []
        self._startup_trace("setup_ui", "START", "Building main window shell")
        try:
            self.setCentralWidget(self._build_shell())
            install_button_feedback_tree(self)
            install_smart_combos(self)
            self._startup_trace("setup_ui", "SUCCESS", "Main window shell built")
        except Exception as exc:
            self._startup_trace_exception("setup_ui", exc)
            raise
        # Eagerly create commonly used master pages so tests and callers
        # that expect these pages to exist can find them immediately.
        for key in (
            "route_master",
            "salesman_master",
            "vehicle_master",
            "transporter_master",
            "bank_master",
            "tax_master",
            "payment_term_master",
        ):
            try:
                self._ensure_page(key)
            except Exception:
                # Failure to pre-create a page should not stop startup.
                continue
        self.setStatusBar(QStatusBar())
        self.statusBar().setObjectName("footerBar")
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().showMessage("Ready")
        self._startup_trace("signal_connections", "START", "Installing event filter and shortcuts")
        try:
            self.enter_key_filter = EnterKeyFlowFilter(self)
            QApplication.instance().installEventFilter(self.enter_key_filter)
            self._register_shortcuts()
            self._startup_trace("signal_connections", "SUCCESS", "Event filter and shortcuts installed")
        except Exception as exc:
            self._startup_trace_exception("signal_connections", exc)
            raise
        self._startup_trace("theme_loading", "START", "Applying initial theme")
        try:
            self.apply_theme("light")
            self._startup_trace("theme_loading", "SUCCESS", "Initial theme applied")
        except Exception as exc:
            self._startup_trace_exception("theme_loading", exc)
            raise
        self._startup_trace("dashboard_loading", "START", f"Opening start page={start_page}")
        try:
            self.open_page(start_page if start_page in self.pages else "dashboard", remember=False)
            self._startup_trace("dashboard_loading", "SUCCESS", "Start page opened")
        except Exception as exc:
            self._startup_trace_exception("dashboard_loading", exc)
            raise
        self._startup_trace("main_window_constructor", "SUCCESS", "MainWindow initialization completed")

    def closeEvent(self, event):
        app = QApplication.instance()
        if app and getattr(self, "enter_key_filter", None):
            app.removeEventFilter(self.enter_key_filter)
        try:
            self.source.close_database_resources()
        except Exception:
            pass
        super().closeEvent(event)

    def _build_shell(self) -> QWidget:
        shell = QWidget()
        shell.setObjectName("shellHost")
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(5)
        self._startup_trace("menu_creation", "START", "Building top menu bar")
        try:
            layout.addWidget(self._top_bar())
            self._startup_trace("menu_creation", "SUCCESS", "Top menu bar built")
        except Exception as exc:
            self._startup_trace_exception("menu_creation", exc)
            raise
        self._startup_trace("toolbar_creation", "START", "Building module ribbon")
        try:
            self.ribbon_layout = self._module_ribbon()
            self._startup_trace("toolbar_creation", "SUCCESS", "Module ribbon built")
        except Exception as exc:
            self._startup_trace_exception("toolbar_creation", exc)
            raise
        layout.addWidget(self.ribbon_layout)
        self.page_factories["dashboard"] = lambda: DashboardView(self.config, self.open_page, self.can_open_route)
        self.page_factories["erp_search"] = lambda: GlobalSearchView(
            self.config, self.open_page, self.can_open_route
        )
        self.page_factories["audit"] = self._audit_page
        self.page_factories["ui_rules"] = self._ui_rules_page
        self.page_factories["migration_backlog"] = self._backlog_page
        self.page_factories["sales_bill"] = lambda: SalesBillView(self.config)
        self.page_factories["quotation_entry"] = lambda: SalesDocumentView(self.config, "quotation")
        self.page_factories["sales_order_entry"] = lambda: SalesDocumentView(self.config, "sales_order")
        self.page_factories["delivery_challan_entry"] = lambda: SalesDocumentView(self.config, "delivery_challan")
        self.page_factories["sales_return_entry"] = lambda: SalesDocumentView(self.config, "sales_return")
        self.page_factories["category_master"] = lambda: SimpleMasterView(self.config, "category")
        self.page_factories["product_master"] = lambda: ProductMasterView(self.config)
        self.page_factories["customer_master"] = lambda: PartyMasterView(self.config, "customer")
        self.page_factories["supplier_master"] = lambda: PartyMasterView(self.config, "supplier")
        self.page_factories["brand_master"] = lambda: SimpleMasterView(self.config, "brand")
        self.page_factories["unit_master"] = lambda: SimpleMasterView(self.config, "unit")
        self.page_factories["gst_rate_master"] = lambda: SimpleMasterView(self.config, "gst_rate")
        self.page_factories["bank_master"] = lambda: SimpleMasterView(self.config, "bank")
        self.page_factories["tax_master"] = lambda: SimpleMasterView(self.config, "tax_master")
        self.page_factories["payment_term_master"] = lambda: SimpleMasterView(self.config, "payment_term")
        self.page_factories["scheme_master"] = lambda: SchemeMasterView(self.config)
        self.page_factories["product_labels"] = lambda: LabelPrintView(self.config)
        self.page_factories["excel_import"] = lambda: ExcelImportView(self.config)
        self.page_factories["employee_master"] = lambda: SimpleMasterView(self.config, "employee")
        self.page_factories["purchase_entry"] = lambda: PurchaseEntryView(self.config)
        self.page_factories["purchase_order_entry"] = lambda: PurchaseDocumentView(self.config, "purchase_order")
        self.page_factories["purchase_return_entry"] = lambda: PurchaseDocumentView(self.config, "purchase_return")
        self.page_factories["stock_dashboard"] = lambda: StockDashboardView(self.config)
        self.page_factories["stock_entry_entry"] = lambda: InventoryEntryView(self.config, "stock_entry")
        self.page_factories["stock_transfer_entry"] = lambda: InventoryEntryView(self.config, "transfer")
        self.page_factories["stock_adjustment_entry"] = lambda: InventoryEntryView(self.config, "adjustment")
        self.page_factories["stock_out_entry"] = lambda: StockOutView(self.config)
        self.page_factories["dispatch_return_entry"] = lambda: DispatchReturnView(self.config)
        self.page_factories["route_settlement"] = lambda: RouteSettlementView(self.config)
        self.page_factories["warehouse_master"] = lambda: SimpleMasterView(self.config, "warehouse")
        self.page_factories["branch_master"] = lambda: SimpleMasterView(self.config, "branch")
        self.page_factories["cost_center_master"] = lambda: SimpleMasterView(self.config, "cost_center")
        self.page_factories["route_master"] = lambda: SimpleMasterView(self.config, "route")
        self.page_factories["salesman_master"] = lambda: SimpleMasterView(self.config, "salesman")
        self.page_factories["vehicle_master"] = lambda: SimpleMasterView(self.config, "vehicle")
        self.page_factories["transporter_master"] = lambda: SimpleMasterView(self.config, "transporter")
        self.page_factories["ledger_master"] = lambda: SimpleMasterView(self.config, "ledger")
        self.page_factories["company_settings"] = lambda: SimpleMasterView(self.config, "company")
        self.page_factories["financial_years"] = lambda: FinancialYearAdminView(self.config)
        self.page_factories["numbering_series"] = lambda: NumberingSeriesAdminView(self.config)
        self.page_factories["receipt_entry"] = lambda: AccountEntryView(self.config, "receipt")
        self.page_factories["payment_entry"] = lambda: AccountEntryView(self.config, "payment")
        self.page_factories["expense_entry"] = lambda: AccountEntryView(self.config, "expense")
        self.page_factories["journal_entry"] = lambda: AccountEntryView(self.config, "journal")
        self.page_factories["masters"] = lambda: ModuleHubView(
            self.config,
            "Masters",
            "Categories, products, customers, suppliers, GST rates",
            self._filter_operations("masters", MASTERS_OPERATIONS),
            self.open_page,
        )
        self.page_factories["sales"] = lambda: ModuleHubView(
            self.config,
            "Sales",
            "Quotations, orders, billing, returns, delivery challans",
            self._filter_operations("sales", SALES_OPERATIONS),
            self.open_page,
            self.open_transaction_for_edit,
        )
        self.page_factories["document_hub"] = lambda: ModuleHubView(
            self.config,
            "Document Center",
            "Print bills, labels, templates and document audit",
            self._filter_operations("document_center", DOCUMENT_OPERATIONS),
            self.open_page,
        )
        self.page_factories["document_center"] = lambda: DocumentCenterView(self.config)
        self.page_factories["developer_console"] = lambda: DeveloperConsoleView(self.config)
        self.page_factories["purchase"] = lambda: ModuleHubView(
            self.config,
            "Purchase",
            "Purchase orders, stock buying, supplier returns",
            self._filter_operations("purchase", PURCHASE_OPERATIONS),
            self.open_page,
            self.open_transaction_for_edit,
        )
        self.page_factories["inventory"] = lambda: ModuleHubView(
            self.config,
            "Inventory",
            "Stock, transfers, alerts, warehouse movement",
            self._filter_operations("inventory", INVENTORY_OPERATIONS),
            self.open_page,
            self.open_transaction_for_edit,
        )
        self.page_factories["accounts"] = lambda: ModuleHubView(
            self.config,
            "Accounts",
            "Receipts, payments, ledgers, vouchers, statements",
            self._filter_operations("accounts", ACCOUNTS_OPERATIONS),
            self.open_page,
            self.open_transaction_for_edit,
        )
        self.page_factories["reports"] = lambda: ReportCenterView(
            self.config, allowed_report_keys=self._allowed_report_keys()
        )
        self.page_factories["administration"] = lambda: ModuleHubView(
            self.config,
            "Administration",
            "Users, roles, company, print settings and backup",
            self._filter_operations("administration", ADMIN_OPERATIONS),
            self.open_page,
        )
        self._startup_trace("menu_creation", "START", "Populating module ribbon actions")
        try:
            self._populate_module_ribbon()
            self._startup_trace("menu_creation", "SUCCESS", "Module ribbon populated")
        except Exception as exc:
            self._startup_trace_exception("menu_creation", exc)
            raise
        body = QWidget()
        body.setObjectName("shellBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(6)
        self.sidebar = self._build_sidebar()
        body_layout.addWidget(self.sidebar)
        self.content_host = QWidget()
        self.content_host.setObjectName("contentHost")
        content_layout = QVBoxLayout(self.content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.content_scroll = QScrollArea()
        self.content_scroll.setObjectName("contentScroll")
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_scroll.setWidget(self.stack)
        content_layout.addWidget(self.content_scroll, stretch=1)
        body_layout.addWidget(self.content_host, stretch=1)
        layout.addWidget(body, stretch=1)
        return shell

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(148)
        sidebar.setMaximumWidth(160)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        title = QLabel("PRM SOFTWARE")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)
        subtitle = QLabel("ERP workspace")
        subtitle.setObjectName("sidebarSubtitle")
        layout.addWidget(subtitle)
        entries = [
            ("dashboard", "Dashboard"),
            ("sales", "Sales"),
            ("sales_order_entry", "Sales Order"),
            ("quotation_entry", "Quotation"),
            ("delivery_challan_entry", "Delivery Challan"),
        ]
        if self.can_open_route("reports:daily_dispatch_summary"):
            entries.append(("reports:daily_dispatch_summary", "Dispatch Summary"))
        entries.extend([
            ("sales_return_entry", "Sales Return"),
            ("purchase", "Purchase"),
            ("purchase_order_entry", "Purchase Order"),
            ("purchase_entry", "Goods Receipt"),
            ("purchase_return_entry", "Purchase Return"),
            ("inventory", "Inventory"),
            ("accounts", "Accounts"),
        ])
        if self._module_visible("reports"):
            entries.append(("reports", "Reports"))
        if self._module_visible("administration"):
            entries.append(("administration", "Settings"))
        for page_key, label in entries:
            button = SidebarNavigationButton(label)
            button.setObjectName("sidebarButton")
            button.setCheckable(True)
            button.setAutoExclusive(False)
            button.setAccessibleName(f"Open {label}")
            button.setAccessibleDescription("ERP Navigator item. Use Up or Down, Enter, Tab, mouse, or Escape.")
            button.setToolTip(f"Open {label} | Up/Down navigate | Enter open | Esc back")
            button.clicked.connect(lambda checked=False, key=page_key: self.open_page(key))
            button.moveRequested.connect(lambda offset, current=button: self._move_sidebar_focus(current, offset))
            button.escapeRequested.connect(self.go_back)
            self.sidebar_buttons[page_key] = button
            layout.addWidget(button)
        layout.addStretch(1)
        return sidebar

    def _move_sidebar_focus(self, current: QPushButton, offset: int) -> None:
        buttons = [button for button in self.sidebar_buttons.values() if button.isVisible() and button.isEnabled()]
        if not buttons or current not in buttons:
            return
        target = buttons[(buttons.index(current) + int(offset)) % len(buttons)]
        target.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if not hasattr(self, "sidebar"):
            return
        if self.width() < 1000:
            minimum, maximum = 132, 148
        elif self.width() < 1200:
            minimum, maximum = 140, 152
        else:
            minimum, maximum = 148, 160
        self.sidebar.setMinimumWidth(minimum)
        self.sidebar.setMaximumWidth(maximum)
        if hasattr(self, "top_info_blocks"):
            show_top_info = self.width() >= 1220
            for block in self.top_info_blocks:
                block.setVisible(show_top_info)
            if hasattr(self, "user_label"):
                self.user_label.setVisible(not show_top_info)
        if hasattr(self, "command_search"):
            if self.width() < 1000:
                self.command_search.setMinimumWidth(120)
                self.command_search.setMaximumWidth(180)
            elif self.width() < 1220:
                self.command_search.setMinimumWidth(160)
                self.command_search.setMaximumWidth(240)
            else:
                self.command_search.setMinimumWidth(220)
                self.command_search.setMaximumWidth(340)
        if self.content_scroll is not None and self.stack.currentWidget() is not None:
            page = self.stack.currentWidget()
            QTimer.singleShot(0, lambda: self._sync_active_page_height(page))

    def _refresh_sidebar_state(self) -> None:
        for page_key, button in self.sidebar_buttons.items():
            active = page_key == self.current_route
            button.setChecked(active)
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
        self._refresh_ribbon_state()

    def _refresh_ribbon_state(self) -> None:
        active_group = self._page_group(self.current_route)
        for group, button in self.ribbon_buttons.items():
            active = group == active_group
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _page_group(self, page_key: str) -> str:
        if page_key in {"dashboard"}:
            return "dashboard"
        if page_key in {
            "sales",
            "sales_bill",
            "quotation_entry",
            "sales_order_entry",
            "delivery_challan_entry",
            "sales_return_entry",
        }:
            return "sales"
        if page_key in {"purchase", "purchase_entry", "purchase_order_entry", "purchase_return_entry"}:
            return "purchase"
        if page_key in {
            "inventory",
            "stock_dashboard",
            "stock_entry_entry",
            "stock_transfer_entry",
            "stock_adjustment_entry",
            "stock_out_entry",
            "dispatch_return_entry",
            "route_settlement",
        }:
            return "inventory"
        if page_key in {"accounts", "receipt_entry", "payment_entry", "expense_entry", "journal_entry"}:
            return "accounts"
        if page_key in {"reports"} or page_key.startswith("reports:"):
            return "reports"
        if page_key in {"document_hub", "document_center", "product_labels"}:
            return "document_center"
        if page_key in {"administration", "financial_years", "numbering_series", "company_settings"}:
            return "administration"
        if page_key.endswith("_master") or page_key in {"masters", "scheme_master", "excel_import"}:
            return "masters"
        if page_key == "developer_console":
            return "developer"
        return page_key

    def _top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setMaximumHeight(74)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(8)
        self.product_brand = ProductBrandHeader(self.config, compact=True)
        layout.addWidget(self.product_brand, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.command_search = QLineEdit()
        self.command_search.setPlaceholderText("Search menu, customer, product...        Ctrl+K")
        self.command_search.setProperty("enterSubmits", True)
        self.command_search.setMinimumWidth(220)
        self.command_search.setMaximumWidth(340)
        self.command_search.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.command_search.returnPressed.connect(self._run_command_search)
        self._startup_trace("signal_connections", "SUCCESS", "Command search connected")
        layout.addWidget(self.command_search)
        self.top_info_blocks = [
            self._top_info_block("FINANCIAL YEAR", self._financial_year_label()),
            self._top_info_block("BRANCH", "Head Office"),
            self._top_info_block(self.session.get("name", "Super Admin"), self.session.get("role", "Administrator")),
        ]
        for block in self.top_info_blocks:
            layout.addWidget(block)
        self.theme_button = QPushButton("Dark")
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)
        self.user_label = QLabel(self._session_caption())
        self.user_label.setObjectName("caption")
        self.user_label.setVisible(False)
        layout.addWidget(self.user_label)
        self.developer_button = QPushButton("Developer Login")
        # Developer dashboard button should be gated; open secure login when clicked
        self.developer_button.clicked.connect(self._developer_button_clicked)
        layout.addWidget(self.developer_button)
        logout = QPushButton("Logout")
        logout.clicked.connect(self.close)
        layout.addWidget(logout)
        return bar

    def _financial_year_label(self) -> str:
        today = datetime.now()
        start_year = today.year if today.month >= 4 else today.year - 1
        return f"{start_year}-{str(start_year + 1)[-2:]}"

    def _top_info_block(self, title: str, value: str) -> QWidget:
        frame = QFrame()
        frame.setObjectName("topInfoBlock")
        frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(0)
        label = QLabel(title)
        label.setObjectName("topInfoLabel")
        content = QLabel(value or "-")
        content.setObjectName("topInfoValue")
        layout.addWidget(label)
        layout.addWidget(content)
        return frame

    def _module_ribbon(self) -> QWidget:
        ribbon = QFrame()
        ribbon.setObjectName("ribbon")
        ribbon.setMaximumHeight(42)
        layout = QHBoxLayout(ribbon)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)
        return ribbon

    def _populate_module_ribbon(self) -> None:
        layout = self.ribbon_layout.layout()
        if not isinstance(layout, QHBoxLayout):
            return
        self.ribbon_buttons.clear()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._add_ribbon_button(layout, "Home", "dashboard")
        self._add_ribbon_menu(layout, "Masters", "masters", MASTERS_OPERATIONS)
        self._add_ribbon_menu(layout, "Sales", "sales", SALES_OPERATIONS)
        self._add_ribbon_menu(layout, "Purchase", "purchase", PURCHASE_OPERATIONS)
        self._add_ribbon_menu(layout, "Inventory", "inventory", INVENTORY_OPERATIONS)
        self._add_ribbon_menu(layout, "Accounts", "accounts", ACCOUNTS_OPERATIONS)
        if self._module_visible("reports"):
            self._add_ribbon_menu(layout, "Reports", "reports", REPORTS_OPERATIONS)
        if self._module_visible("document_center"):
            self._add_ribbon_menu(layout, "Document Center", "document_center", DOCUMENT_OPERATIONS)
        if self._module_visible("administration"):
            self._add_ribbon_menu(layout, "Administration", "administration", ADMIN_OPERATIONS)
        self._add_ribbon_action_button(layout, "Developer", self._developer_button_clicked)
        layout.addStretch(1)

    def _add_ribbon_button(self, layout: QHBoxLayout, label: str, page: str) -> None:
        button = QPushButton(label)
        button.setObjectName("ribbonButton")
        button.setMinimumWidth(0)
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        button.clicked.connect(lambda checked=False, key=page: self.open_page(key))
        self.ribbon_buttons[self._page_group(page)] = button
        layout.addWidget(button)

    def _add_ribbon_action_button(self, layout: QHBoxLayout, label: str, callback: Callable[[], None]) -> None:
        button = QPushButton(label)
        button.setObjectName("ribbonButton")
        button.setMinimumWidth(0)
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        button.clicked.connect(callback)
        self.ribbon_buttons["developer"] = button
        layout.addWidget(button)

    def _add_ribbon_menu(self, layout: QHBoxLayout, label: str, hub_page: str, operations: list) -> None:
        button = QPushButton(label)
        button.setObjectName("ribbonMenuButton")
        button.setMinimumWidth(0)
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        menu = QMenu(button)
        menu.setObjectName("moduleMenu")
        visible_operations = self._filter_operations(hub_page, operations)
        has_categories = any(str(getattr(operation, "category", "") or "") for operation in visible_operations)
        if has_categories:
            submenus: dict[str, QMenu] = {}
            for operation in visible_operations:
                category = str(getattr(operation, "category", "") or "General")
                submenu = submenus.get(category)
                if submenu is None:
                    submenu = QMenu(category, menu)
                    submenu.setObjectName("moduleSubMenu")
                    menu.addMenu(submenu)
                    submenus[category] = submenu
                action = QAction(operation.label, self)
                action.triggered.connect(
                    lambda checked=False, op=operation, page=hub_page: self._activate_module_operation(page, op)
                )
                submenu.addAction(action)
        else:
            for operation in visible_operations:
                action = QAction(operation.label, self)
                action.triggered.connect(
                    lambda checked=False, op=operation, page=hub_page: self._activate_module_operation(page, op)
                )
                menu.addAction(action)
        button.clicked.connect(lambda checked=False, b=button, m=menu: m.popup(b.mapToGlobal(b.rect().bottomLeft())))
        self.ribbon_buttons[hub_page] = button
        layout.addWidget(button)

    def _activate_module_operation(self, hub_page: str, operation) -> None:
        if operation.target_page:
            self.open_page(operation.target_page)
            if operation.target_page == hub_page:
                page = self.pages.get(hub_page)
                if hasattr(page, "open_report"):
                    page.open_report(operation.key)
                elif hasattr(page, "open_view"):
                    page.open_view(operation.key)
            return
        self.open_page(hub_page)
        page = self.pages.get(hub_page)
        if isinstance(page, ModuleHubView):
            page.open_operation(operation)
            return
        if hub_page == "reports" and hasattr(page, "open_report"):
            page.open_report(operation.key)
        elif hub_page == "document_center" and hasattr(page, "open_view"):
            page.open_view(operation.key)

    def _dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._page_title("Executive Dashboard", "Fast access to billing, inventory, accounts and compliance"))
        grid = QGridLayout()
        cards = [
            ("Business Audit", "Source menu and database coverage used to verify desktop parity.", "audit"),
            ("Data Center", "Local desktop data, backups, reports, GST files and print templates.", "document_center"),
            ("Operator Rules", "Keyboard flow, focused entry screens, validations and fast shortcuts.", "ui_rules"),
            ("Daily Work", "Open billing, purchases, stock, accounts and reports from the top ribbon.", "sales_bill"),
        ]
        for index, (title, text, page_key) in enumerate(cards):
            grid.addWidget(self._card(title, text, page_key), index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch(1)
        return page

    def _audit_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._page_title("Business Audit", "Menu and database facts used for desktop parity verification"))
        self.audit_selector = QComboBox()
        self.audit_selector.addItems(["portal_routes.csv", "portal_functions.csv", "sqlite_tables.tsv", "sqlite_columns.tsv"])
        self.audit_selector.currentTextChanged.connect(self._load_audit_table)
        layout.addWidget(self.audit_selector)
        self.audit_table = QTableWidget()
        self.audit_table.setAlternatingRowColors(True)
        layout.addWidget(self.audit_table, stretch=1)
        self._load_audit_table(self.audit_selector.currentText())
        return page

    def _ui_rules_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._page_title("Desktop UI Rules", "The app will not copy the old web look"))
        rules = [
            "Top ribbon navigation with command search, not long web-style pages.",
            "Compact proportional form groups with focused popup editors.",
            "Esc closes popup or returns to the previous screen.",
            "Ctrl+S saves, Ctrl+P previews print, F4 adds a transaction row.",
            "Inline validation near fields; service layer owns business rules.",
            "Fast screens: cached masters, lazy tables, background long jobs.",
        ]
        for rule in rules:
            label = QLabel(rule)
            label.setObjectName("ruleLine")
            layout.addWidget(label)
        layout.addStretch(1)
        return page

    def _backlog_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._page_title("Completion Roadmap", "Workflow verification order for the desktop ERP"))
        rows = [
            ("1", "Audit Reports", "Complete", "Route/schema inventory and risk map"),
            ("2", "Desktop Data", "Complete", "Local SQLite data with validation and backup support"),
            ("3", "Sales Bill", "Complete", "Header, rows, packs, GST, stock, ledger, print"),
            ("4", "Product Master", "Complete", "FMCG packs, barcode, batch/expiry, prices"),
            ("5", "Purchase", "Complete", "Purchase bill/order/return and stock input"),
            ("6", "Inventory", "Complete", "Warehouse, transfer, stock out, route settlement"),
            ("7", "Accounts", "Complete", "Vouchers, ledger posting, trial balance, P&L"),
            ("8", "GST / Compliance", "Complete", "GST return, ITC, e-invoice, e-way bill JSON"),
            ("9", "Reports / Prints", "Complete", "PDF, CSV, archive and print templates"),
        ]
        table = QTableWidget(len(rows), 4)
        table.setHorizontalHeaderLabels(["#", "Area", "Stage", "Definition of Done"])
        table.setAlternatingRowColors(True)
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        layout.addWidget(table, stretch=1)
        return page

    def _page_title(self, title: str, subtitle: str) -> QWidget:
        frame = QFrame()
        frame.setObjectName("pageHeader")
        layout = QVBoxLayout(frame)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        sub = QLabel(subtitle)
        sub.setObjectName("pageSubtitle")
        layout.addWidget(heading)
        layout.addWidget(sub)
        return frame

    def _card(self, title: str, text: str, page_key: str) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        heading = QLabel(title)
        heading.setObjectName("cardTitle")
        body = QLabel(text)
        body.setWordWrap(True)
        body.setObjectName("cardBody")
        button = QPushButton("Open")
        button.clicked.connect(lambda checked=False, key=page_key: self.open_page(key))
        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addStretch(1)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignRight)
        return card

    def _load_audit_table(self, file_name: str) -> None:
        path = self.config.audit_dir / file_name
        rows = read_csv_rows(path)
        self.audit_table.clear()
        if not rows:
            self.audit_table.setRowCount(1)
            self.audit_table.setColumnCount(1)
            self.audit_table.setHorizontalHeaderLabels(["Status"])
            self.audit_table.setItem(0, 0, QTableWidgetItem(f"Run audit tools first: {path.name}"))
            return
        headers = list(rows[0].keys())
        self.audit_table.setColumnCount(len(headers))
        self.audit_table.setRowCount(len(rows))
        self.audit_table.setHorizontalHeaderLabels(headers)
        for row_index, row in enumerate(rows):
            for column_index, header in enumerate(headers):
                self.audit_table.setItem(row_index, column_index, QTableWidgetItem(row.get(header, "")))
        self.audit_table.resizeColumnsToContents()

    def _run_command_search(self) -> None:
        text = self.command_search.text().strip()
        if not text:
            return
        self.open_page("erp_search")
        page = self.pages.get("erp_search")
        if hasattr(page, "open_search"):
            page.open_search(text)
        self.command_search.clear()

    def _ensure_page(self, key: str) -> QWidget | None:
        if key in self.pages:
            return self.pages[key]
        factory = self.page_factories.get(key)
        if not factory:
            return None
        try:
            page = factory()
        except Exception as exc:
            page = self._page_fallback(key, exc)
        self.pages[key] = page
        install_button_feedback_tree(page)
        self._fit_page_to_width(page)
        self.stack.addWidget(page)
        return page

    def _page_fallback(self, key: str, exc: Exception) -> QWidget:
        page = QWidget()
        page.setProperty("factoryFallback", True)
        page.setProperty("failedRoute", key)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        heading = QLabel(f"{key.replace('_', ' ').title()}")
        heading.setObjectName("pageTitle")
        message = QLabel(
            "This page could not be initialized automatically. Please reopen it after the issue is resolved."
        )
        message.setWordWrap(True)
        detail = QLabel(str(exc))
        detail.setObjectName("pageSubtitle")
        detail.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(message)
        layout.addWidget(detail)
        layout.addStretch(1)
        return page

    def open_page(self, key: str, remember: bool = True) -> None:
        if key == "dashboard":
            self._startup_trace("home_page_creation", "START", "Creating dashboard page")
        if key.startswith("document:"):
            self._open_document_route(key, remember=remember)
            return
        if key.startswith("reports:"):
            report_key = key.split(":", 1)[1]
            if not self.can_open_route(key):
                QMessageBox.information(self, "Access", "This report is not enabled for the current plan/user.")
                return
            previous_route = self.current_route
            self.open_page("reports", remember=False)
            page = self.pages.get("reports")
            if hasattr(page, "open_report"):
                page.open_report(report_key)
                if report_key == "account_closing":
                    page.ca_export_panel.setVisible(True)
                    if hasattr(page, "_sync_ca_export_panel_height"):
                        page._sync_ca_export_panel_height(True)
                    page.status_label.setText("Account Closing | Select one row and use Export CA File")
                    if hasattr(page, "table") and page.table.rowCount() > 0:
                        page.table.clearSelection()
                        page.table.selectRow(0)
                        page.table.setFocus()
            if remember and previous_route != key:
                self.history.append(previous_route)
            self.current_route = key
            self._refresh_sidebar_state()
            self.statusBar().showMessage(f"Open report: {report_key}")
            return
        if key == "reports" and not self._module_visible("reports"):
            QMessageBox.information(self, "Access", "Reports are not enabled for the current plan/user.")
            return
        page = self._ensure_page(key)
        if page is None:
            return
        if key == "dashboard":
            self._startup_trace("home_page_creation", "SUCCESS", "Dashboard page created")
        if key == "developer_console" and not self._ensure_developer_access():
            return
        if key == "administration" and not self._module_visible("administration"):
            QMessageBox.information(self, "Access", "This menu is not enabled for the current plan/user.")
            return
        if remember and self.current_route != key:
            self.history.append(self.current_route)
        self.current_page = key
        self.current_route = key
        self._fit_page_to_width(self.pages[key])
        self.stack.setCurrentWidget(self.pages[key])
        self.stack.updateGeometry()
        page = self.pages[key]
        if self.content_scroll is not None:
            self.content_scroll.verticalScrollBar().setValue(0)
        QTimer.singleShot(0, lambda: self._finalize_page_fit(page))
        self._refresh_sidebar_state()
        self.statusBar().showMessage(f"Open: {key}")

    def _finalize_page_fit(self, page: QWidget) -> None:
        if self.stack.currentWidget() is not page:
            return
        self._fit_page_to_width(page)
        install_smart_combos(page)
        self._refresh_page_layouts(page)
        self.stack.updateGeometry()
        self._sync_active_page_height(page)
        if self.content_scroll is not None:
            self.content_scroll.verticalScrollBar().setValue(0)
        # Height fitting can add or remove the vertical scrollbar, changing a
        # list table's viewport by a few pixels. Refill non-transaction columns
        # after that geometry transition so no blank strip remains at the edge.
        QTimer.singleShot(
            0,
            lambda: self._finalize_responsive_page(page),
        )

    def _finalize_responsive_page(self, page: QWidget) -> None:
        if self.stack.currentWidget() is not page:
            return
        self._fit_page_to_width(page)
        sync_page = getattr(page, "sync_responsive_layout", None)
        if callable(sync_page):
            sync_page()
        install_smart_combos(page)
        self._refresh_page_layouts(page)
        for totals_panel in page.findChildren(TransactionTotalsPanel):
            totals_panel.sync_responsive_layout()
        self._sync_active_page_height(page)

    def _refresh_page_layouts(self, page: QWidget) -> None:
        for widget in [page, *page.findChildren(QWidget)]:
            layout = widget.layout()
            if layout is not None:
                layout.invalidate()
                layout.activate()
        page.updateGeometry()

    def _sync_active_page_height(self, page: QWidget) -> None:
        if self.content_scroll is None or self.stack.currentWidget() is not page:
            return
        if page.property("transactionFramework") is True:
            # QScrollArea can retain the page's earlier preferred height after
            # responsive cards lower their true minimum. Fit the shared stack
            # to the viewport, but keep genuine overflow scrollable.
            viewport_height = self.content_scroll.viewport().height()
            target_height = max(viewport_height, page.minimumSizeHint().height())
            self.stack.setMinimumHeight(target_height)
            self.stack.setMaximumHeight(target_height)
        else:
            self.stack.setMinimumHeight(0)
            self.stack.setMaximumHeight(16777215)
            self.stack.adjustSize()
        self.stack.updateGeometry()

    def _open_document_route(self, key: str, remember: bool = True) -> None:
        parts = key.split(":")
        if len(parts) != 3:
            return
        source_type = parts[1]
        try:
            record_id = int(parts[2])
        except ValueError:
            return
        if record_id <= 0:
            return
        if source_type in {"sales", "purchases"}:
            self.open_page("document_center", remember=remember)
            page = self.pages.get("document_center")
            if hasattr(page, "open_document_record"):
                page.open_document_record(source_type, record_id)
            self.statusBar().showMessage(f"Open document: {source_type} #{record_id}")
            return
        voucher_targets = {"receipts": "receipt_entry", "payments": "payment_entry"}
        target = voucher_targets.get(source_type)
        if target:
            self.open_page(target, remember=remember)
            page = self.pages.get(target)
            if hasattr(page, "select_recent_record"):
                page.select_recent_record(record_id)
            self.statusBar().showMessage(f"Open voucher: {source_type} #{record_id}")

    def open_transaction_for_edit(self, source_table: str, record_id: int) -> None:
        target_by_source = {"sales": "sales_bill", "purchases": "purchase_entry"}
        target = target_by_source.get(str(source_table or "").strip().lower())
        if not target:
            raise ValueError(f"Editing is not supported for {source_table}.")
        self.open_page(target)
        page = self.pages.get(target)
        if page is None or not hasattr(page, "load_for_edit"):
            raise ValueError("The transaction editor is not available.")
        page.load_for_edit(int(record_id))
        self.statusBar().showMessage(f"Editing {source_table} #{record_id}")

    def _business_type_code(self) -> str:
        company = self.source.company()
        return normalize_business_type(str(company.get("business_type_code") or company.get("business_type") or "").strip())



    def go_back(self) -> None:
        if self.history:
            self.open_page(self.history.pop(), remember=False)
        else:
            self.open_page("dashboard", remember=False)

    def _register_shortcuts(self) -> None:
        QShortcut(QKeySequence("Esc"), self, activated=self.go_back)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.command_search_focus)
        QAction("Back", self, shortcut=QKeySequence("Alt+Left"), triggered=self.go_back)

    def command_search_focus(self) -> None:
        self.command_search.setFocus()
        self.command_search.selectAll()

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        self.apply_theme("dark" if self.dark_mode else "light")

    def apply_theme(self, name: str) -> None:
        self._startup_trace("style_loading", "START", f"Loading {name} stylesheet")
        try:
            path = self.config.theme_dir / f"{name}.qss"
            if path.exists():
                self.setStyleSheet(path.read_text(encoding="utf-8"))
                self._startup_trace("style_loading", "SUCCESS", f"Loaded {path}")
            else:
                self._startup_trace("style_loading", "FAILED", f"Stylesheet missing: {path}")
            self.theme_button.setText("Light" if name == "dark" else "Dark")
        except Exception as exc:
            self._startup_trace_exception("style_loading", exc)
            raise

    def _session_caption(self) -> str:
        name = self.session.get("name") or self.session.get("email") or "User"
        role = self.session.get("role") or "viewer"
        return f"{name} ({role})"

    def _module_visible(self, module: str) -> bool:
        role = (self.session.get("role") or "").lower()
        plan = (self.license_context.plan_code if self.license_context else "premium").lower()
        if module == "reports":
            return self._permission_allowed("reports")
        if module in {"dashboard", "masters", "sales", "purchase", "inventory", "accounts"}:
            return True
        if module == "document_center":
            return plan in {"standard", "premium", "enterprise", "professional"}
        if module == "administration":
            return role in {"admin", "administrator", "developer", "super admin"} and plan in {
                "standard",
                "premium",
                "enterprise",
                "professional",
            }
        return True

    def _permission_allowed(self, permission_key: str) -> bool:
        role = str(self.session.get("role") or "").strip().lower()
        if role in {"admin", "administrator", "developer", "super admin", "super_admin", "superadmin"}:
            return True
        try:
            rows = self.source.rows(
                "SELECT allowed FROM role_permissions WHERE LOWER(role_name)=LOWER(%s) AND permission_key=%s",
                (role, permission_key),
            )
        except Exception:
            return False
        return bool(rows and int(rows[0].get("allowed") or 0))

    def _allowed_report_keys(self) -> set[str]:
        if not self._module_visible("reports"):
            return set()
        return {str(operation.key) for operation in self._filter_operations("reports", REPORTS_OPERATIONS)}

    def can_open_route(self, route: str) -> bool:
        target = str(route or "").strip()
        if target == "reports":
            return self._module_visible("reports")
        if target.startswith("reports:"):
            return target.split(":", 1)[1] in self._allowed_report_keys()
        if target == "administration":
            return self._module_visible("administration")
        return True

    def _filter_operations(self, module: str, operations: list) -> list:
        if module == "reports" and not self._module_visible("reports"):
            return []
        plan = (self.license_context.plan_code if self.license_context else "premium").lower()
        if plan in {"premium", "enterprise", "professional"}:
            return list(operations)
        if module == "administration":
            allowed = {"company", "users"}
            return [operation for operation in operations if operation.key in allowed]
        if plan == "basic" and module == "reports":
            allowed_categories = {"Sales / Purchase", "Inventory", "Accounts"}
            return [operation for operation in operations if getattr(operation, "category", "") in allowed_categories]
        if plan == "basic" and module == "document_center":
            return []
        return list(operations)

    def _filter_industry_operations(self, operations: list) -> list:
        """Filter industry-specific operations based on current company business type.

        This narrows the INDUSTRY_OPERATIONS shown to the user so that only
        operations relevant to the company's business type appear.
        """
        bt = self._business_type_code()
        if not bt:
            return list(operations)
        # Map normalized business types to allowed operation keys
        allowed_map = {
            "pharmacy": {
                "pharmacy_retail_billing",
                "pharmacy_wholesale_billing",
                "prescription_entry",
                "prescription_billing",
            },
            "restaurant": {
                "pos_dine_in",
                "pos_take_away",
                "pos_delivery",
                "kot_new",
                "ready_orders",
                "restaurant_categories",
                "restaurant_tables",
            },
            "electronics": {"electronics_pos_billing"},
            "retail": {"pos_billing"},
        }
        allowed = allowed_map.get(bt)
        if allowed is None:
            return list(operations)
        return [op for op in operations if op.key in allowed]

    def _ensure_developer_access(self) -> bool:
        if self.developer_unlocked:
            return True
        if not self.license_context or not self.license_service:
            self.developer_unlocked = True
            return True
        from services.developer_audit_service import DeveloperAuditService

        key, ok = QInputDialog.getText(
            self,
            "Developer Login",
            "Enter Developer Login Key",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            DeveloperAuditService(self.license_service.db_path).log_attempt("", False, "cancelled")
            return False
        try:
            valid = self.license_service.validate_developer_key(key, self.license_context)
        except Exception as exc:
            DeveloperAuditService(self.license_service.db_path).log_attempt("", False, f"error:{exc}")
            QMessageBox.warning(self, "Developer Login", "Developer login failed due to license error.")
            return False
        if valid:
            DeveloperAuditService(self.license_service.db_path).log_attempt("developer", True, "ok")
            self.developer_unlocked = True
            self.statusBar().showMessage("Developer Console unlocked for this session.")
            return True
        DeveloperAuditService(self.license_service.db_path).log_attempt("developer", False, "invalid_key")
        QMessageBox.warning(self, "Developer Login", "Invalid developer key.")
        return False

    def _developer_button_clicked(self) -> None:
        # Show secure login before opening developer console
        if self._ensure_developer_access():
            self.open_page("developer_console")

    def _fit_page_to_width(self, page: QWidget) -> None:
        max_size = 16777215
        page.setMinimumWidth(0)
        page.setMaximumWidth(max_size)
        page.setSizePolicy(QSizePolicy.Policy.Expanding, page.sizePolicy().verticalPolicy())
        controls = (QLineEdit, QComboBox, QDateEdit, QPushButton)
        for widget in page.findChildren(QWidget):
            if widget.property("erpPreserveGeometry") is True:
                continue
            requested_width = int(widget.property("erpMinimumWidth") or 0)
            widget.setMinimumWidth(min(requested_width, 200) if requested_width else 0)
            if widget.maximumWidth() < max_size and not isinstance(widget, QTableWidget):
                widget.setMaximumWidth(max_size)
            name = widget.objectName()
            if isinstance(widget, QFrame):
                widget.setMinimumWidth(min(requested_width, 200) if requested_width else 0)
                role = str(widget.property("transactionRole") or "")
                if name == "pageHeader":
                    widget.setMinimumHeight(0)
                    widget.setMaximumHeight(max(widget.maximumHeight(), 56))
                elif name == "actionToolbar":
                    widget.setMinimumHeight(0)
                    widget.setMaximumHeight(max(widget.maximumHeight(), 44))
                elif name == "fieldBox":
                    widget.setMinimumHeight(46)
                    widget.setMaximumHeight(max(widget.maximumHeight(), 96))
                elif name == "card" or widget.property("transactionFramework") is True:
                    widget.setMinimumHeight(0)
                    if role in {"customer", "document"}:
                        widget.setMaximumHeight(max(widget.maximumHeight(), 154))
                    elif role in {"product-search", "grid-actions"}:
                        widget.setMaximumHeight(max(widget.maximumHeight(), 124))
            if isinstance(widget, controls):
                widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                widget.setMinimumHeight(24)
                widget.setMaximumHeight(30)
                if isinstance(widget, QComboBox):
                    widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 10))
                    widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            elif isinstance(widget, QTextEdit):
                widget.setMinimumHeight(min(widget.minimumHeight(), 40))
                if widget.maximumHeight() < max_size:
                    widget.setMaximumHeight(max(widget.maximumHeight(), 70))
                widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            elif isinstance(widget, QTableWidget):
                widget.setMinimumWidth(0)
                widget.setMaximumWidth(max_size)
                widget.setMinimumHeight(min(widget.minimumHeight(), 96))
                widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                widget.horizontalHeader().setMinimumSectionSize(32)
                header = widget.horizontalHeader()
                metrics = header.fontMetrics()
                visible_columns: list[int] = []
                for column in range(widget.columnCount()):
                    item = widget.horizontalHeaderItem(column)
                    if item is None or widget.isColumnHidden(column):
                        continue
                    visible_columns.append(column)
                    required_width = min(220, metrics.horizontalAdvance(item.text()) + 24)
                    if widget.columnWidth(column) < required_width:
                        header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
                        widget.setColumnWidth(column, required_width)
                if widget.property("transactionFramework") is not True and visible_columns:
                    compact_headers = {"id", "#", "select", "active", "status"}
                    flexible_columns = [
                        column
                        for column in visible_columns
                        if str(widget.horizontalHeaderItem(column).text()).strip().lower() not in compact_headers
                    ] or visible_columns
                    available_width = widget.viewport().width()
                    used_width = header.length()
                    if used_width < available_width:
                        extra_width = available_width - used_width
                        share, remainder = divmod(extra_width, len(flexible_columns))
                        for index, column in enumerate(flexible_columns):
                            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
                            widget.setColumnWidth(
                                column,
                                widget.columnWidth(column) + share + (1 if index < remainder else 0),
                            )
                widget.updateGeometries()
                if widget.property("transactionFramework") is not True and visible_columns:
                    available_width = widget.viewport().width()
                    used_width = header.length()
                    if used_width < available_width:
                        extra_width = available_width - used_width
                        share, remainder = divmod(extra_width, len(flexible_columns))
                        for index, column in enumerate(flexible_columns):
                            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
                            widget.setColumnWidth(
                                column,
                                widget.columnWidth(column) + share + (1 if index < remainder else 0),
                            )
                        widget.updateGeometries()
                needs_horizontal_scroll = header.length() > widget.viewport().width()
                widget.setHorizontalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOn
                    if needs_horizontal_scroll
                    else Qt.ScrollBarPolicy.ScrollBarAsNeeded
                )
                widget.verticalHeader().setDefaultSectionSize(min(widget.verticalHeader().defaultSectionSize(), 26))
            elif isinstance(widget, QAbstractScrollArea):
                widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
