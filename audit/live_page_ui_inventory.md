# Live Page UI Inventory

Generated from the page factories used by `MainWindow`; fallback pages, visible button wiring, shared UI markers, and three target desktop sizes are checked at runtime.

- Live routes: 59
- Routes with no detected issue: 59
- Routes requiring review: 0

| Route | View | Framework | Toolbar | Wiring | Screen fit | Known issue |
|---|---|---|---|---|---|---|
| accounts | ModuleHubView | Shared ERP UI Framework | CompactActionToolbar | 39/39 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| administration | ModuleHubView | Shared ERP UI Framework | CompactActionToolbar | 17/17 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| audit | QWidget | Qt page framework | none | 0/0 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| bank_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| branch_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| brand_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| category_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| company_settings | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| cost_center_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| customer_master | PartyMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| dashboard | DashboardView | Shared ERP UI Framework | none | 27/27 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| delivery_challan_entry | SalesDocumentView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| developer_console | DeveloperConsoleView | Shared ERP UI Framework | none | 1/1 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| dispatch_return_entry | DispatchReturnView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| document_center | DocumentCenterView | Shared ERP UI Framework | CompactActionToolbar | 6/6 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| document_hub | ModuleHubView | Shared ERP UI Framework | CompactActionToolbar | 12/12 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| employee_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| erp_search | GlobalSearchView | Shared ERP UI Framework | CompactActionToolbar | 5/5 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| excel_import | ExcelImportView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| expense_entry | AccountEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | TransactionToolbar | 13/13 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| financial_years | FinancialYearAdminView | Shared ERP UI Framework | CompactActionToolbar | 8/8 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| gst_rate_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| inventory | ModuleHubView | Shared ERP UI Framework | CompactActionToolbar | 21/21 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| journal_entry | AccountEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | TransactionToolbar | 13/13 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| ledger_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| masters | ModuleHubView | Shared ERP UI Framework | CompactActionToolbar | 21/21 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| migration_backlog | QWidget | Qt page framework | none | 0/0 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| numbering_series | NumberingSeriesAdminView | Shared ERP UI Framework | CompactActionToolbar | 4/4 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| payment_entry | AccountEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | TransactionToolbar | 13/13 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| payment_term_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| product_labels | LabelPrintView | Shared ERP UI Framework | CompactActionToolbar | 5/5 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| product_master | ProductMasterView | Shared ERP UI Framework | CompactActionToolbar | 11/11 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| purchase | ModuleHubView | Shared ERP UI Framework | CompactActionToolbar | 14/14 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| purchase_entry | PurchaseEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| purchase_order_entry | PurchaseDocumentView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| purchase_return_entry | PurchaseDocumentView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 19/19 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| quotation_entry | SalesDocumentView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| receipt_entry | AccountEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | TransactionToolbar | 13/13 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| reports | ReportCenterView | Shared ERP UI Framework | CompactActionToolbar | 9/9 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| route_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| route_settlement | RouteSettlementView | Shared Transaction Entry Framework + Shared ERP UI Framework | TransactionToolbar | 13/13 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| sales | ModuleHubView | Shared ERP UI Framework | CompactActionToolbar | 17/17 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| sales_bill | SalesBillView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 19/19 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| sales_order_entry | SalesDocumentView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| sales_return_entry | SalesDocumentView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 19/19 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| salesman_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| scheme_master | SchemeMasterView | Shared ERP UI Framework | CompactActionToolbar | 2/2 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| stock_adjustment_entry | InventoryEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| stock_dashboard | StockDashboardView | Qt page framework | none | 1/1 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| stock_entry_entry | InventoryEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| stock_out_entry | StockOutView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| stock_transfer_entry | InventoryEntryView | Shared Transaction Entry Framework + Shared ERP UI Framework | GridActionBar, TransactionToolbar | 18/18 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| supplier_master | PartyMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| tax_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| transporter_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| ui_rules | QWidget | Qt page framework | none | 0/0 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| unit_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| vehicle_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |
| warehouse_master | SimpleMasterView | Shared ERP UI Framework | CompactActionToolbar | 3/3 visible buttons wired | 1366x768:PASS / 1440x900:PASS / 1920x1080:PASS | none found |

The CSV companion contains the complete action, shortcut, save-handler, error-handling, source-file, and test-coverage fields.
