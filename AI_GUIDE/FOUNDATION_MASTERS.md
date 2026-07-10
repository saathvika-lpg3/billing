# Foundation Masters

## Purpose
This guide captures the foundational master data model for the desktop ERP, specifically the new branch, warehouse, and cost center masters.

## Scope
- Branch Master: business units or legal entities with GST/state context.
- Warehouse Master: physical store or stock location tied to a branch.
- Cost Center Master: department/project/profit-center tagging for accounting and reporting.
- Route Master: route definitions used for van sales, dispatch and collection planning.
- Salesman Master: route sales and collection personnel records.
- Vehicle Master: fleet vehicles used for route delivery and loading.
- Transporter Master: transporters used for outward dispatch and logistics.

## Key implementation notes
- `views/simple_master_view.py` now contains reusable master UI definitions for branch, warehouse, cost center, route, salesman, vehicle, and transporter.
- `services/master_repository.py` now bootstraps schema for these masters and provides `save_simple()` support.
- `SQLiteSource` provides branch, warehouse, cost center, salesman, vehicle, and transporter lookup rows for form population and document flows.
- The desktop runtime uses this source layer as a SQLite-only compatibility wrapper. The Add Item flow reads product data from the local SQLite tables `items`, `suppliers`, and `product_packs` through this layer.

## Schema details
### branches
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `code TEXT`
- `name TEXT`
- `address TEXT`
- `city TEXT`
- `state TEXT`
- `pin_code TEXT`
- `phone TEXT`
- `email TEXT`
- `gstin TEXT`
- `is_default INTEGER DEFAULT 0`
- `is_active INTEGER DEFAULT 1`

### warehouses
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `code TEXT`
- `name TEXT`
- `branch_id INTEGER DEFAULT 0`
- `address TEXT`
- `contact_person TEXT`
- `phone TEXT`
- `is_default INTEGER DEFAULT 0`
- `is_active INTEGER DEFAULT 1`

### cost_centers
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `code TEXT`
- `name TEXT`
- `type TEXT`
- `notes TEXT`
- `is_active INTEGER DEFAULT 1`

## UI notes
- Warehouse form now includes a `branch_id` combo that loads branch names and saves branch IDs.
- Route form now includes `salesman_id` and `vehicle_id` combos that load actual records and persist selected IDs.
- Branch, cost center, salesman, vehicle, and transporter forms include code/name validation and active state toggles.
- Placeholders and tooltips were added to improve data entry clarity.

## Validation rules
- Branch: `code` and `name` are required; `code` must be unique.
- Warehouse: `code`, `name`, and branch selection are required; `code` must be unique; branch must exist.
- Cost Center: `code`, `name`, and `type` are required; `code` must be unique.

## Verification
- Added repository-level tests for branch, warehouse, and cost center persistence.
- Added repository-level tests for route, salesman, vehicle, and transporter persistence.
- Added UI-level test coverage for screen loading, route salesman/vehicle ID combo behavior, and operational master navigation.

## Commercial and statutory masters
- Bank Master: bank code, account number, IFSC, branch, account type, opening balance and active status.
- Tax Code Master: tax code, tax name, HSN/SAC, GST rate, CGST, SGST, IGST, cess, effective date, and active flag.
- Payment Terms Master: term code, term name, credit days, due date rule, discount percent, and active status.
- These masters are now part of the foundation master layer and use the same generic master UI framework in `views/simple_master_view.py` with repository persistence in `services/master_repository.py`.

## Print layout compliance note
- Print output must support both A4 and A2 Landscape as required by the distributor business type.
- Sales, Purchase, Receipt and Payment print templates must share the same header/footer style.
- The header must repeat on every printed page.
- Page numbers must be validated on multi-page print outputs.
- Entry item grid layouts must follow the approved invoice/print layout style.
- Use the uploaded sample invoice PDF as a reference for layout direction and consistent header/footer behavior.

## Future work
- Integrate branch/warehouse/cost center selection into purchase/sales/account transaction flows.
- Add warehouse default logic and branch-aware numbering/document routing.
- Add cost center reporting and reconciliation filters.
- Add import/export and bulk update support for these masters.
