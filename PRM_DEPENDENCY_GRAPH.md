# PRM Dependency Graph

## Core ERP engine dependencies

- `services/master_repository.py`
  - `services/uom_price_service.py`
  - `services/financial_year_service.py`
  - `services/numbering_series_service.py`
  - `services/accounting_setup_service.py`
  - `views/simple_master_view.py` (branch/warehouse/cost center, route/salesman/vehicle/transporter, category/brand/unit/GST/ledger/company)

- `services/financial_year_service.py`
  - standalone engine for financial year management
  - future document flows should depend on this service for active year lookup and validation

- `services/numbering_series_service.py`
  - standalone engine for numbering series management and number generation
  - future document flows should depend on this service for all document numbers

- `services/company_profile_service.py`
  - company profile metadata and developer/admin protection
  - provides invoice prefix metadata used by older document paths until numbering engine is adopted

- `services/order_conversion_service.py`
  - currently generates sales bill numbers inline via company invoice prefix
  - should migrate to `services/numbering_series_service.py`

- `services/transaction_repository.py`
  - transaction persistence and voucher posting
  - should call numbering engine for all future document save operations

- `services/sqlite_source.py`
  - desktop data-source compatibility layer for SQLite-backed views and services
  - product selection for Add Item uses this layer to read from the local SQLite tables `items`, `suppliers`, and `product_packs`
  - remains SQLite-only and does not introduce SQLite runtime dependency
  - resolves the canonical database path from the installer-safe project runtime and environment overrides

- `services/sqlite_source.py`
  - compatibility entry point for SQLite-backed access and future refactors
  - preserves existing imports while making the runtime data-source role explicit

- `services/print_service.py`
  - future print/report engine for A2 Landscape, preview, export, and bulk print
  - should centralize document output behavior and preserve accepted report formats
  - must enforce shared Sales/Purchase/Receipt/Payment header-footer style, support A4 selection, repeat headers on every page, and render page numbers correctly on multi-page documents

- `services/communication_service.py`
  - future communication engine for WhatsApp sharing of invoices, receipts, payment reminders, outstanding statements, ledgers, reports, purchase orders, and PDFs
  - should consume generated PDF output and handle external share workflows

## Recommended dependency direction
- UI / views → service layer
- service layer → `financial_year_service`, `numbering_series_service`
- `numbering_series_service` → database only
- `financial_year_service` → database only
- `master_repository` → bootstrap schema for both engines

## Notes
- Avoid any direct document number construction in views or document services.
- All future document save paths must obtain next document numbers from `NumberingSeriesService`.
- Any financial-year validation should be centralized through `FinancialYearService`.
