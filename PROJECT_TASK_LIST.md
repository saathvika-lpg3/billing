# PRM Billing Inventory Desktop Project Task List

## 1. Execution strategy
This task list is based on the current codebase structure and the audit findings in PROJECT_AUDIT.md. The highest-value work is to stabilize the runtime database strategy and bootstrap flow first, then complete the core transaction and master-data modules.

## 2. Priority legend
- Priority P0: blocking / startup / data integrity / packaging
- Priority P1: high-value workflow completion
- Priority P2: refinement / reporting / polish

## 3. Module-by-module implementation plan

### 1) App bootstrap and runtime configuration
- Module: app.py, config/app_config.py
- Current state: startup flow exists and is structured, but database path resolution and packaging assumptions are inconsistent.
- Completion: 70%
- Missing / risky items:
  - Single canonical SQLite path strategy
  - First-run bootstrap for database and folders
  - Reliable behavior for packaged builds and local runs
- Database changes:
  - Add a deterministic DB path resolver with fallback logic
  - Ensure the same path is used across app.py, services, and installer packaging
- UI changes:
  - None required at the core level; startup diagnostics may be helpful
- Reports / outputs:
  - Startup log and environment diagnostics
- Priority: P0
- Effort: Medium

### 2) License and authentication flow
- Module: services/license_service.py, views/login_dialog.py
- Current state: license gating exists and login flow is present.
- Completion: 75%
- Missing / risky items:
  - License activation and fallback behavior should be more explicit for first-time installs
  - Better handling of missing/invalid license files and database activation edge cases
- Database changes:
  - Ensure license activation writes only to the canonical DB path
- UI changes:
  - Improve license error dialogs and first-run guidance
- Reports / outputs:
  - License validation summary
- Priority: P0
- Effort: Medium

### 3) Database access layer and SQLite path strategy
- Module: services/sqlite_source.py, database/connection.py
- Current state: central DB path logic exists but is ambiguous and appears to drift across environments.
- Completion: 55%
- Missing / risky items:
  - One authoritative DB location
  - Clear distinction between development DB and packaged runtime DB
  - Consistent use of the same path in views/services/tests/installer scripts
- Database changes:
  - Introduce a single resolver that checks explicit env/config values, then app root, then packaged locations
  - Make DB creation and schema initialization automatic on first run
- UI changes:
  - Optional developer console diagnostics for current DB path
- Reports / outputs:
  - DB path audit report in logs or developer console
- Priority: P0
- Effort: Medium

### 4) Master repository and schema bootstrap
- Module: services/master_repository.py
- Current state: core persistence layer for masters exists and is fairly broad.
- Completion: 72%
- Missing / risky items:
  - Full schema migration and idempotent bootstrap
  - Stronger validation around master references
  - Better handling of default packs, tax slabs, and opening stock initialization
- Database changes:
  - Add migration-safe table creation and column updates
  - Normalise product/party/master relations
- UI changes:
  - Improve validation messages and duplicate prevention
- Reports / outputs:
  - Master data summary report
- Priority: P1
- Effort: Medium

### 5) Product master
- Module: views/product_master_view.py
- Current state: substantial UI and save path exist; packs, stock, and tax fields are present.
- Completion: 80%
- Missing / risky items:
  - Better error handling for invalid pack rows
  - More robust duplicate detection for code/barcode
  - Better import/export compatibility and search quality
- Database changes:
  - Ensure pack and stock values are stored consistently
  - Validate default pack and active pack rules
- UI changes:
  - Add inline validation and clearer pack row editing
- Reports / outputs:
  - Product list export / stock summary
- Priority: P1
- Effort: Medium

### 6) Party master (customer / supplier)
- Module: views/party_master_view.py
- Current state: likely present and wired to master persistence.
- Completion: 70%
- Missing / risky items:
  - Consistent party type handling and validation
  - GST / address / contact data quality rules
- Database changes:
  - Ensure party references are compatible with sales/purchase/account entries
- UI changes:
  - Add better address, GST, and balance display
- Reports / outputs:
  - Party ledger summary
- Priority: P1
- Effort: Medium

### 7) Simple masters and reference data
- Module: views/simple_master_view.py
- Current state: central reference screens exist for categories, brands, units, GST rates, warehouses, branches, cost centers, ledgers, company settings, employees.
- Completion: 76%
- Missing / risky items:
  - Consistent save semantics across all master types
  - Better validation and duplicate prevention
- Database changes:
  - Add schema consistency checks for each master table
- UI changes:
  - Improve field mapping and default selections
- Reports / outputs:
  - Reference data quality report
- Priority: P1
- Effort: Medium

### 8) Sales billing workflow
- Module: views/sales_bill_view.py, services/transaction_repository.py, services/sales_calculator.py
- Current state: substantial billing workflow exists with line items, calculations, and save path.
- Completion: 78%
- Missing / risky items:
  - Complete end-to-end validation with stock, GST, and voucher posting
  - Confirm invoice number generation and rounding behavior
  - Verify print/share and save consistency
- Database changes:
  - Validate sales, sales_items, stock_log, vouchers, and ledger tables
- UI changes:
  - Tighten line-item validation and totals feedback
- Reports / outputs:
  - Invoice print, sales register, stock impact report
- Priority: P0
- Effort: High

### 9) Sales document flow
- Module: views/sales_document_view.py, services/order_conversion_service.py
- Current state: quotation, sales order, delivery challan, sales return workflows are present.
- Completion: 74%
- Missing / risky items:
  - Ensure document conversion between quotation / order / challan / bill is reliable
  - Validate stock impact and return logic for each document type
- Database changes:
  - Ensure the document tables and related item tables are consistently populated
- UI changes:
  - Make document state transitions clearer
- Reports / outputs:
  - Order-to-bill conversion report
- Priority: P1
- Effort: High

### 10) Purchase entry and purchase documents
- Module: views/purchase_entry_view.py, views/purchase_document_view.py
- Current state: entry and document views exist.
- Completion: 72%
- Missing / risky items:
  - Purchase stock impact and purchase return validation
  - Consistent numbering and tax/posting behavior
- Database changes:
  - Validate purchase, purchase_items, purchase_returns, stock_log, and vouchers
- UI changes:
  - Improve purchase-specific validations and status handling
- Reports / outputs:
  - Purchase register and stock movement ledger
- Priority: P1
- Effort: High

### 11) Inventory and stock movement
- Module: views/inventory_entry_view.py, views/stock_out_view.py, views/stock_dashboard_view.py
- Current state: inventory entry and stock movement flows are present.
- Completion: 70%
- Missing / risky items:
  - Ensure stock entry/transfer/adjustment semantics are accurate and auditable
  - Make stock dashboards reflect real-time movement after transactions
- Database changes:
  - Validate stock_log, product_packs, items, and warehouse-level stock calculations
- UI changes:
  - Add better stock alerts and movement history views
- Reports / outputs:
  - Stock ledger, stock age, movement summary
- Priority: P0
- Effort: High

### 12) Dispatch return workflow
- Module: views/dispatch_return_view.py, services/transaction_repository.py
- Current state: return flow exists and includes accepted/damaged quantities.
- Completion: 68%
- Missing / risky items:
  - Validate against stock and accounting impact more strictly
  - Confirm source document handling for sales vs load challan
- Database changes:
  - Ensure dispatch_returns and dispatch_return_items are saved consistently
- UI changes:
  - Add clearer validation for return quantities and balance limits
- Reports / outputs:
  - Dispatch return register
- Priority: P1
- Effort: Medium

### 13) Account entry and voucher posting
- Module: views/account_entry_view.py, services/transaction_repository.py
- Current state: receipt/payment/expense/journal views exist and some posting logic is implemented.
- Completion: 71%
- Missing / risky items:
  - Confirm ledger posting behavior across all modes
  - Improve voucher numbering and posting consistency
- Database changes:
  - Validate account_vouchers, ledger entries, and receipt/payment tables
- UI changes:
  - Better validation for branch/cost center and ledger selection
- Reports / outputs:
  - Ledger statement, day book, receipt/payment summary
- Priority: P1
- Effort: High

### 14) Reporting and document center
- Module: views/report_center_view.py, views/document_center_view.py
- Current state: reporting and document modules are present.
- Completion: 65%
- Missing / risky items:
  - Report queries should be aligned with the current schema and transaction flows
  - Document audit and archive integration should be completed end to end
- Database changes:
  - Ensure report-friendly views or summary tables are available
- UI changes:
  - Improve filters and export actions
- Reports / outputs:
  - Sales report, purchase report, stock report, party ledger, GST summary
- Priority: P2
- Effort: Medium

### 15) Printing, sharing, and PDF output
- Module: services/pdf_print.py, services/print_preview.py, services/share_service.py
- Current state: print and share flows are present.
- Completion: 73%
- Missing / risky items:
  - Ensure print templates match saved transaction data
  - Validate PDF preview and WhatsApp share flows on packaged installations
- Database changes:
  - None directly; ensure saved transaction payloads are complete
- UI changes:
  - Add preview and print status feedback
- Reports / outputs:
  - Printable invoices, vouchers, labels, and delivery notes
- Priority: P1
- Effort: Medium

### 16) Backup, restore, and maintenance
- Module: services/backup_service.py, services/data_maintenance_service.py
- Current state: backup and restore support exists but should be hardened.
- Completion: 66%
- Missing / risky items:
  - Safer restore workflows with confirmation and validation
  - Better backup integrity checks and encryption handling
- Database changes:
  - Snapshot and restore should target the canonical DB path only
- UI changes:
  - Add restore preview and explicit warnings
- Reports / outputs:
  - Backup/restore audit log
- Priority: P1
- Effort: Medium

### 17) Developer console and admin tools
- Module: views/developer_console_view.py
- Current state: broad feature set exists and is useful for operations.
- Completion: 69%
- Missing / risky items:
  - Better validation of maintenance actions
  - Safer path operations and admin-only safeguards
- Database changes:
  - Ensure admin actions are scoped to the active DB and not an unintended copy
- UI changes:
  - Add confirmation dialogs and environment summary
- Reports / outputs:
  - System health summary
- Priority: P2
- Effort: Medium

### 18) Packaging and installer workflow
- Module: PRM_Billing_Inventory.spec, installer/, build/
- Current state: packaging assets exist, but the spec appears to rely on machine-specific paths.
- Completion: 60%
- Missing / risky items:
  - Portable spec that correctly packages assets, themes, templates, and DB files
  - Deterministic installation location and runtime path resolution
- Database changes:
  - Ensure packaged builds use the same DB path resolver as local runs
- UI changes:
  - None directly; installer-facing diagnostics may be helpful
- Reports / outputs:
  - Build/install validation checklist
- Priority: P0
- Effort: High

### 19) Tests and regression coverage
- Module: tests/
- Current state: test folders exist, but the core startup and DB path regression cases should be expanded.
- Completion: 58%
- Missing / risky items:
  - Tests for DB path resolution, license flow, transaction save, inventory movement, and installer packaging behavior
- Database changes:
  - Seed test DBs and verify migration behavior
- UI changes:
  - Add smoke tests for critical forms
- Reports / outputs:
  - CI-friendly regression suite
- Priority: P1
- Effort: Medium

## 4. Recommended implementation order
1. Stabilize database path resolution and first-run bootstrap
2. Harden license/auth startup flow
3. Validate and complete sales/purchase/inventory transaction save paths
4. Finish master-data screens and reference data integrity
5. Improve reporting, printing, backup, and packaging
6. Expand regression tests

## 5. Suggested first milestones
- Milestone 1: One canonical DB path and reliable first-run creation
- Milestone 2: Sales + purchase + inventory save paths verified end to end
- Milestone 3: Packaging build works from a clean machine with correct assets and DB behavior
