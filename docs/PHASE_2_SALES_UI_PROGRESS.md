# Phase 2 Sales UI Progress

## Completed

- Added PyQt Sales Bill desktop screen.
- Added read-only SQLite source service for PRM_GST masters.
- Loaded real customers and product packs from the current PRM_GST database.
- Added compact header layout for bill no, date, employee, route, customer, warehouse, branch, cost center, payment, price level, supplier/brand, shipping, PO, transport, and credit terms.
- Added operator item-entry strip with product search, HSN, qty, scheme/free qty, unit, MRP, rate, discount, GST, and F4 add-row flow.
- Added line table, GST/taxable summary, round off, and grand total.
- Added keyboard shortcuts: Alt+B product focus, F4 add row, Ctrl+S save local draft.
- Added local JSON draft save under `D:\PRM_GST_DESKTOP\drafts` without modifying original SQLite data.
- Added SalesCalculator service and tests.

## Verified

- Project compiles.
- Sales calculator tests pass.
- Offscreen startup test sees pages: dashboard, audit, migration_backlog, sales_bill, ui_rules.
- Sales Bill source status loads real data: 13 customers and 68 packs.
- Visible PyQt app relaunched from `D:\PRM_GST_DESKTOP\app.py`.

## Next

- Build local encrypted database migration design.
- Replace JSON draft save with proper desktop SQLite/SQLCipher transaction save.
- Implement stock, GST posting, ledger posting, and print preview parity for Sales Bill.
