# PRM Billing Inventory Desktop Project Audit

## 1. App purpose
This project is a desktop ERP-style application for PRM Billing Inventory. It is built around:
- PyQt6 desktop UI
- SQLite as the local desktop database model
- optional SQLite-compatible data access path for migration or legacy workflows
- license-gated startup
- master data, sales, purchase, inventory, accounts, reports, printing, and backup features

The project appears aimed at running as a locally installed desktop application for a business user, not as a web app.

## 2. Main entry flow from app.py
The startup path is centered in app.py and proceeds as follows:
1. Determine the runtime root directory.
   - If running from a frozen build, it uses the executable directory.
   - Otherwise it uses the project root.
2. Create an AppConfig object with the project and source roots.
3. Choose a starting page. The app supports a --page argument.
4. Create the QApplication instance and set application metadata and icon.
5. Load the license via LicenseService.require_license().
6. Apply the license to the database via LicenseService.apply_to_database().
7. Open the login dialog.
8. If login succeeds, create MainWindow with the selected page and session context.
9. Show the window maximized and start the Qt event loop.

In short, the app boot sequence is: license -> login -> main window -> feature pages.

## 3. Folder-by-folder explanation
### Root
- app.py: main application entry point
- README.md: high-level project description
- requirements.txt: Python dependencies
- PRM_Billing_Inventory.spec: PyInstaller packaging specification

### config/
Contains runtime configuration helpers.
- app_config.py defines the application root and resource directories.

### views/
This is the UI layer. It contains most of the desktop screens and dialogs.
Important views include:
- login_dialog.py
- main_window.py
- dashboard_view.py
- module_hub_view.py
- global_search_view.py
- sales_bill_view.py
- sales_document_view.py
- purchase_entry_view.py
- purchase_document_view.py
- product_master_view.py
- party_master_view.py
- simple_master_view.py
- scheme_master_view.py
- stock_dashboard_view.py
- stock_out_view.py
- inventory_entry_view.py
- dispatch_return_view.py
- route_settlement_view.py
- label_print_view.py
- excel_import_view.py
- document_center_view.py
- report_center_view.py
- account_entry_view.py
- developer_console_view.py

### services/
This folder contains most of the business logic and data access helpers.
Key services include:
- license_service.py
- sqlite_source.py
- master_repository.py
- transaction_repository.py
- sales_calculator.py
- import_service.py
- backup_service.py
- company_profile_service.py
- accounting_setup_service.py
- dashboard_service.py
- data_maintenance_service.py
- document_archive_service.py
- gst_payload_service.py
- order_conversion_service.py
- pdf_print.py
- print_preview.py
- share_service.py
- audit_reader.py

### repositories/
This folder exists but is currently empty. Persistence logic is mostly implemented under services/ rather than a formal repositories layer.

### controllers/
This folder exists but is empty. There is no visible controller layer in the current structure.

### database/
Contains the database helper layer and the main SQLite database file.
- connection.py builds SQLite engines using SQLAlchemy.
- prm_billing_inventory.db is the primary local database candidate.

### models/
Contains model definitions and base classes. The folder appears minimal compared with the volume of views and services.

### tests/
Contains test files for key behavior areas such as:
- sales calculator
- print/report parity
- operator keyboard flow
- master repository and industry logic
- license security
- document/module UI
- data maintenance and share
- backup and transaction flows

### tools/
Contains migration, audit, backup, and packaging support scripts.
Examples include:
- migrate_sqlite_to_sqlite.py
- audit_portal.py
- audit_sqlite_schema.py
- audit_desktop_coverage.py
- backup_sqlite.py

### installer/
Contains packaging and installer assets.
- prm_billing_inventory.iss: Inno Setup installer script
- PRM_Billing_Inventory_Electronic_Agreement.txt: legal text for packaging

### assets/, themes/, docs/, print_templates/, uploads/, reports/, prints/
These folders support branding, style, docs, templates, uploads, and generated output.

## 4. SQLite database location issue
The SQLite path handling is inconsistent and is one of the biggest architectural risks.

Current behavior shows multiple competing location strategies:
- Some code expects the database under the project root database folder.
- Some code uses the environment variable PRM_SQLITE_DB.
- Some runtime paths assume an _internal/database structure for bundled builds.
- The PyInstaller spec packages the SQLite file into a different location than the runtime code appears to expect.

This means the same app can resolve different database files depending on how it is launched, packaged, or installed.

## 5. Why prm_billing_inventory.db appears many times
The database file appears in many locations because the project contains multiple build, test, and packaging snapshots.
Examples include:
- the main project database folder
- multiple installer_test_* directories
- a dist output folder
- a bundled build folder

This strongly suggests the project is being used for repeated installer/build validation, and each test run or packaging attempt is producing its own local database copy. The repetition is not a sign of a single canonical DB location; it is a sign of duplicated deployment/test artifacts.

## 6. All important screens/views
The main UI surface is broad. The most important screens are:
- Login dialog
- Main window shell and module ribbon
- Dashboard
- Global search
- Module hub pages
- Sales bill entry
- Sales document entry (quotation, sales order, delivery challan, sales return)
- Purchase entry
- Purchase document entry (purchase order, purchase return)
- Product master
- Party master (customer and supplier)
- Simple master views for category, brand, unit, GST rate, warehouse, branch, cost center, ledger, company settings, employee
- Scheme master
- Inventory entry and stock movement views
- Stock dashboard and stock out flow
- Dispatch return
- Route settlement
- Label printing
- Excel import
- Document center
- Report center
- Account entry
- Developer console

## 7. All controllers/services/repositories
### Controllers
- No controller modules are present in the current workspace structure.

### Services
The business logic is concentrated in the services layer:
- license_service.py
- sqlite_source.py
- master_repository.py
- transaction_repository.py
- sales_calculator.py
- import_service.py
- backup_service.py
- company_profile_service.py
- accounting_setup_service.py
- dashboard_service.py
- data_maintenance_service.py
- document_archive_service.py
- gst_payload_service.py
- order_conversion_service.py
- pdf_print.py
- print_preview.py
- share_service.py
- audit_reader.py

### Repositories
- The repositories/ folder is empty.
- Persistence-related operations are currently implemented in services/ rather than a dedicated repository abstraction.

## 8. Missing or incomplete modules
The project is large and feature-rich, but several structural gaps are visible:
- No controllers layer
- No repositories layer
- No clearly centralized database migration system
- No single authoritative application state/service container
- Some modules appear to exist as scaffolding or partial implementations rather than fully polished, end-to-end flows
- The project includes many views and services, but the architectural separation is still relatively flat and inconsistent

## 9. Bugs or risky areas
The following areas are especially risky:
1. Database path ambiguity
   - The app may resolve different SQLite files depending on environment and packaging context.
2. Hard-coded packaging path
   - The PyInstaller spec uses a hard-coded Windows path, which is not portable.
3. Frozen-build path mismatch
   - The build spec and runtime logic do not appear to agree on the packaged database location.
4. Startup dependency on license and database state
   - The app requires a valid license file and a usable database before it can proceed.
5. Schema assumptions across services
   - Many services directly create or update tables and columns with raw SQL. This can break if the schema changes or is incomplete.
6. Backup and restore safety
   - Backup and restore logic is present, but destructive operations are risk-prone and should be tightly validated.
7. Environment-sensitive behavior
   - The app depends on environment variables and runtime context in ways that can create inconsistent behavior across machines.
8. UI breadth without clear modularization
   - The UI is broad, but the project structure still mixes screen logic, business logic, and data access in ways that can make maintenance harder.

## 10. Installer/build issues
The packaging side has clear concerns:
- The PyInstaller spec uses a hard-coded absolute path to the development machine.
- The database is packaged into a path that may not match the runtime path expected by the app.
- There are many installer test directories, which usually indicates iterative build testing but also suggests the release pipeline may not be fully stabilized.
- The app uses both local database assets and runtime-generated files, so packaging must carefully preserve the correct folder structure.
- The app likely needs a more deterministic install layout, especially for database, assets, templates, and logs.

## 11. Exact recommended development order
The recommended order is:
1. Stabilize the database strategy
   - Define one canonical database path.
   - Make the app create or migrate the database consistently.
   - Remove the current ambiguity between project-root, _internal, and environment-variable-based paths.
2. Fix startup/bootstrap flow
   - License validation
   - initial database bootstrap
   - first-run user creation and login flow
3. Complete the core transaction workflows
   - sales bill
   - purchase entry
   - inventory movement
   - account entries
4. Finish master data and reference screens
   - products
   - customers/suppliers
   - settings and simple masters
5. Harden reporting and printing
   - report center
   - document center
   - label and invoice printing
6. Stabilize backup/restore and developer tools
   - backup service
   - data maintenance
   - restore validation
7. Fix packaging and installer workflow
   - ensure the packaged app can find the DB, assets, templates, and licensing files reliably
8. Expand regression testing
   - add tests for startup, DB path resolution, license flow, core forms, and installer execution

## Summary
The project is ambitious and structurally large, with a strong desktop-ERP feature set and a visible UI layer. Its biggest weaknesses are not the presence of features, but the inconsistency of runtime configuration, database path handling, and packaging assumptions. The highest-value next step is to make the app’s database location and bootstrap flow deterministic before adding more features.
