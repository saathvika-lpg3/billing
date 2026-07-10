# Safe Development Task Queue

This queue is scoped to the current desktop project structure and keeps the existing Python + SQLite + .prmlic model intact.

## P0 - Must finish before any feature work

### 1. DB path verification
- Objective: Make sure the app always resolves one safe SQLite database path for local desktop runs, installer runs, and test builds.
- Files likely involved: app.py, config/app_config.py, database/connection.py, services/sqlite_source.py, services/master_repository.py, services/transaction_repository.py, PRM_Billing_Inventory.spec
- Risk level: High
- Testing needed:
  - Launch from project root
  - Launch from packaged build folder
  - Verify the same DB file is used in each case
  - Confirm existing local data remains available
- Done condition: A single verified DB path strategy is documented and tested for desktop and packaged execution.

### 2. .prmlic license compatibility
- Objective: Preserve existing valid .prmlic files and ensure new updates do not invalidate them.
- Files likely involved: app.py, services/license_service.py, assets/license_public_key.txt, installer/, README.md
- Risk level: High
- Testing needed:
  - Validate an existing valid .prmlic file
  - Validate a missing/invalid .prmlic case
  - Verify update flow does not break previously working installations
- Done condition: Existing valid .prmlic files continue to work after update and the validation path is stable.

### 3. App startup
- Objective: Ensure the desktop app boots reliably before any feature expansion.
- Files likely involved: app.py, views/main_window.py, config/app_config.py, services/license_service.py
- Risk level: High
- Testing needed:
  - Cold start
  - Start with missing DB folder
  - Start with missing license file
  - Start with valid license and existing DB
- Done condition: App startup reaches the main window reliably in the supported desktop environment.

### 4. Login flow
- Objective: Keep the login and session flow working with the current desktop and license model.
- Files likely involved: views/login_dialog.py, app.py, services/license_service.py, views/main_window.py
- Risk level: Medium
- Testing needed:
  - Valid login
  - Invalid login
  - Empty credentials
  - Session reopen behavior
- Done condition: Login and session entry are stable and do not break startup or licensing behavior.

### 5. Backup before changes
- Objective: Create a safe backup point before any schema, license, print, or installer changes.
- Files likely involved: services/backup_service.py, tools/, backups/, database/, installer_test*/
- Risk level: Medium
- Testing needed:
  - Backup creation
  - Backup restore validation on a local test DB
  - Ensure backup does not overwrite current data unexpectedly
- Done condition: A documented backup and restore path exists and has been verified before implementation work.

## P1 - Core ERP workflows

### 1. Company settings
- Objective: Make company profile and business settings deterministic for invoices, reports, and printing.
- Files likely involved: views/simple_master_view.py, services/company_profile_service.py, services/master_repository.py
- Risk level: Medium
- Testing needed:
  - Save company settings
  - Verify values appear in invoices and reports
  - Test with empty/partial values
- Done condition: Company settings save and are consumed correctly in downstream workflows.

### 2. Product master
- Objective: Keep product master entry and pack-level data consistent for sales, purchase, inventory, and printing.
- Files likely involved: views/product_master_view.py, services/master_repository.py, services/sqlite_source.py
- Risk level: Medium
- Testing needed:
  - Create product with one pack and multiple packs
  - Verify default pack selection
  - Verify stock and price inputs remain consistent
- Done condition: Product master saves correctly and can be used by transaction workflows without manual correction.

### 3. Party master
- Objective: Preserve customer/supplier master quality for billing, accounting, and reporting.
- Files likely involved: views/party_master_view.py, services/master_repository.py, services/sqlite_source.py
- Risk level: Medium
- Testing needed:
  - Create customer and supplier entries
  - Confirm they appear in relevant dropdowns and reports
  - Verify duplicate handling
- Done condition: Party master records are stable and usable across sales, purchase, and ledger flows.

### 4. Sales invoice
- Objective: Ensure invoice entry, totals, stock effect, and save workflow remain correct.
- Files likely involved: views/sales_bill_view.py, services/transaction_repository.py, services/sales_calculator.py
- Risk level: High
- Testing needed:
  - Create a full sales invoice with multiple lines
  - Verify totals, GST, stock impact, and voucher posting
  - Test save and reopen workflow
- Done condition: A sales invoice can be created, saved, and re-read without data mismatch.

### 5. Purchase invoice
- Objective: Keep purchase entry, tax handling, stock movement, and posting consistent.
- Files likely involved: views/purchase_entry_view.py, views/purchase_document_view.py, services/transaction_repository.py
- Risk level: High
- Testing needed:
  - Create a purchase with item lines
  - Verify stock update and tax behavior
  - Verify purchase return compatibility
- Done condition: Purchase entries are saved correctly and reflect in stock and accounting flows.

### 6. Inventory posting
- Objective: Keep stock entry, transfer, adjustment, and stock-out flows accurate and auditable.
- Files likely involved: views/inventory_entry_view.py, views/stock_out_view.py, views/stock_dashboard_view.py, services/transaction_repository.py
- Risk level: High
- Testing needed:
  - Stock entry
  - Stock transfer
  - Stock adjustment
  - Stock-out posting
  - Verify stock balance changes correctly
- Done condition: Inventory posting updates stock consistently and leaves a traceable audit trail.

### 7. Ledger posting
- Objective: Confirm account entries and voucher posting remain correct for receipt, payment, expense, and journal modes.
- Files likely involved: views/account_entry_view.py, services/transaction_repository.py
- Risk level: High
- Testing needed:
  - Receipt entry
  - Payment entry
  - Expense entry
  - Journal entry
  - Verify ledger balance behavior
- Done condition: Ledger posting is consistent and matches the entered accounting data.

### 8. GST calculation
- Objective: Preserve GST computation logic and ensure output matches expected tax behavior.
- Files likely involved: services/sales_calculator.py, services/transaction_repository.py, views/sales_bill_view.py, views/purchase_entry_view.py
- Risk level: Medium
- Testing needed:
  - Single-line invoice
  - Multi-line invoice
  - Tax slab changes
  - Reverse calculation validation
- Done condition: GST totals are correct for the tested billing and purchase scenarios.

## P2 - Printing

### 1. A4 Portrait support
- Objective: Keep A4 Portrait available as a supported print option for invoices, vouchers, and labels.
- Files likely involved: services/pdf_print.py, services/print_preview.py, views/sales_bill_view.py, views/account_entry_view.py, print_templates/
- Risk level: Medium
- Testing needed:
  - Generate a print from a sales invoice
  - Verify layout on A4 Portrait
  - Confirm no forced A2 layout
- Done condition: A4 Portrait output is generated correctly and selectable in the print flow.

### 2. A2 Landscape support
- Objective: Keep A2 Landscape available for distributor workflows without making it the only supported option.
- Files likely involved: services/pdf_print.py, services/print_preview.py, views/document_center_view.py, views/report_center_view.py
- Risk level: Medium
- Testing needed:
  - Generate a document in A2 Landscape mode
  - Verify layout and margins
  - Confirm the option can be selected without breaking other paper sizes
- Done condition: A2 Landscape output is generated correctly and remains optional.

### 3. Client-selectable paper size
- Objective: Allow client/admin users to choose paper size per document type without hard-coding one format.
- Files likely involved: views/developer_console_view.py, views/main_window.py, services/pdf_print.py, services/print_preview.py
- Risk level: High
- Testing needed:
  - Select A4 Portrait for one document type
  - Select A2 Landscape for another
  - Confirm the selection persists for the active session or saved settings
- Done condition: Paper size can be selected per document type and is honored by the print pipeline.

### 4. Document-wise print settings
- Objective: Ensure document type-specific settings are applied correctly in the print workflow.
- Files likely involved: services/pdf_print.py, views/sales_bill_view.py, views/purchase_entry_view.py, views/account_entry_view.py, views/document_center_view.py
- Risk level: Medium
- Testing needed:
  - Invoice print settings
  - Voucher print settings
  - Label print settings
  - Verify the chosen settings are used for the correct document type
- Done condition: Each document type uses the correct configured print settings.

### 5. Bulk print
- Objective: Make bulk printing honor the selected paper size and document-specific settings.
- Files likely involved: views/document_center_view.py, views/report_center_view.py, services/pdf_print.py, services/share_service.py
- Risk level: High
- Testing needed:
  - Bulk print a group of invoices
  - Bulk print a group of labels or reports
  - Confirm each generated file uses the selected paper size correctly
- Done condition: Bulk print completes and respects the selected paper settings for each output.

### 6. Loading Sheet / Dispatch Summary print fields
- Objective: Ensure Loading Sheet and Dispatch Summary outputs show GSTIN, HSN, and FSSAI when available, while hiding them gracefully when absent, across preview, PDF export, and bulk print for distributor documents and both A4 Portrait and A2 Landscape layouts.
- Files likely involved: services/pdf_print.py, services/print_preview.py, services/share_service.py, views/dispatch_return_view.py, views/document_center_view.py, print_templates/
- Risk level: High
- Testing needed:
  - Preview a loading sheet or dispatch summary with GSTIN, HSN, and FSSAI present
  - Preview the same document when one or more fields are missing
  - Export to PDF and run bulk print for both A4 Portrait and A2 Landscape
  - Verify no blank labels appear and the layout remains correct
- Done condition: Preview, PDF export, and bulk print all show the available fields without blank labels and honor the selected paper size for distributor documents.

### 7. Print preview
- Objective: Provide reliable print preview before saving or printing.
- Files likely involved: services/print_preview.py, views/sales_bill_view.py, views/purchase_entry_view.py, views/account_entry_view.py
- Risk level: Medium
- Testing needed:
  - Preview a sales invoice
  - Preview a voucher
  - Preview a report or document
- Done condition: Preview opens correctly and reflects the selected print configuration.

### 8. PDF export
- Objective: Ensure PDF export remains stable for print and sharing workflows.
- Files likely involved: services/pdf_print.py, services/share_service.py, views/account_entry_view.py, views/sales_bill_view.py
- Risk level: Medium
- Testing needed:
  - Export invoice to PDF
  - Export voucher to PDF
  - Verify file generation and naming
- Done condition: PDF export works for supported document types and uses the correct paper settings.

## P3 - Reports

### 1. Sales register
- Objective: Provide a trustworthy sales register based on stored transactions.
- Files likely involved: views/report_center_view.py, services/dashboard_service.py, services/sqlite_source.py, services/transaction_repository.py
- Risk level: Medium
- Testing needed:
  - Create and save a sales invoice
  - View the sales register
  - Check totals and document counts
- Done condition: Sales register displays the correct data from saved sales transactions.

### 2. Purchase register
- Objective: Provide a trustworthy purchase register from saved purchase data.
- Files likely involved: views/report_center_view.py, services/sqlite_source.py, services/transaction_repository.py
- Risk level: Medium
- Testing needed:
  - Create and save a purchase invoice
  - Check purchase register totals
  - Verify purchase return impact if applicable
- Done condition: Purchase register is accurate for saved purchase documents.

### 3. Stock report
- Objective: Keep stock reporting aligned with stock entry, transfer, adjustment, and sales/purchase transactions.
- Files likely involved: views/stock_dashboard_view.py, services/sqlite_source.py, services/transaction_repository.py
- Risk level: High
- Testing needed:
  - After stock entry and sale, verify stock report values
  - Verify adjustment and transfer workflow changes
- Done condition: Stock report reflects current stock after core movement workflows.

### 4. Party ledger
- Objective: Keep customer and supplier ledger reports aligned with saved sales, purchases, and account entries.
- Files likely involved: views/report_center_view.py, services/sqlite_source.py, services/transaction_repository.py
- Risk level: Medium
- Testing needed:
  - Create a sales invoice and receipt
  - Create a purchase and payment
  - Verify ledger totals and opening balances
- Done condition: Party ledger shows the correct balances and transaction history.

### 5. GST summary
- Objective: Keep GST summary reporting consistent with invoice and purchase tax calculations.
- Files likely involved: views/report_center_view.py, services/sales_calculator.py, services/transaction_repository.py
- Risk level: Medium
- Testing needed:
  - Sales invoice with GST
  - Purchase invoice with GST
  - Verify summary amounts and tax slab grouping
- Done condition: GST summary matches the saved transaction values.

### 6. GSTR reports
- Objective: Keep GSTR-style reporting aligned with the current GST data model and transaction history.
- Files likely involved: views/report_center_view.py, services/gst_payload_service.py, services/sqlite_source.py
- Risk level: Medium
- Testing needed:
  - Generate summary for sales and purchase data
  - Verify HSN/GST grouping logic
  - Check that the report is consistent with saved transactions
- Done condition: GSTR-related reports are generated from valid saved transactional data without obvious mismatches.

## P4 - Installer and release

### 1. .prmlic preservation
- Objective: Ensure installer and update packaging preserve existing .prmlic files and license validation behavior.
- Files likely involved: installer/, PRM_Billing_Inventory.spec, assets/license_public_key.txt, services/license_service.py
- Risk level: High
- Testing needed:
  - Install over an existing valid installation
  - Confirm the existing .prmlic is still recognized
  - Confirm the new version can start successfully
- Done condition: New installer builds preserve and honor existing .prmlic files.

### 2. SQLite DB preservation
- Objective: Ensure the installer and update process preserve the correct SQLite DB instead of replacing it with a blank or wrong copy.
- Files likely involved: PRM_Billing_Inventory.spec, database/, installer/, build/
- Risk level: High
- Testing needed:
  - Install on a clean machine
  - Upgrade over an existing installation
  - Verify the correct DB file remains available
- Done condition: The active SQLite database is preserved across install and update scenarios.

### 3. Backup preservation
- Objective: Keep backup and restore assets intact through installation and upgrade flows.
- Files likely involved: backups/, services/backup_service.py, installer/, tools/
- Risk level: Medium
- Testing needed:
  - Create a backup
  - Install/update
  - Confirm backup files remain accessible and unchanged
- Done condition: Backup files are preserved and remain usable after installation.

### 4. Update installer
- Objective: Keep the installer workflow aligned with the current desktop app structure and runtime paths.
- Files likely involved: installer/, PRM_Billing_Inventory.spec, README.md, build/
- Risk level: High
- Testing needed:
  - Build installer from a clean environment
  - Install and launch the built app
  - Verify assets, DB, license, and templates are packaged correctly
- Done condition: The installer builds and installs successfully without breaking core functionality.

### 5. Uninstall safety
- Objective: Avoid destructive uninstall behavior that removes user data or the active SQLite DB by mistake.
- Files likely involved: installer/, PRM_Billing_Inventory.spec, database/
- Risk level: High
- Testing needed:
  - Uninstall from a test system
  - Confirm user data and backup files are not accidentally deleted unless explicitly intended
- Done condition: Uninstall behavior is safe and documented for user data preservation.

## Constraints
- Do not edit application Python files as part of this documentation task.
- Keep the project in the current Python + SQLite desktop form.
- Do not introduce SQLite for this release.
- Preserve the existing desktop UI and module structure.
- Keep all changes backward-compatible with existing .prmlic licenses and current SQLite data.
