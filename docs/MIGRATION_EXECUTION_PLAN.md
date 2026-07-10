# Migration Execution Plan

## Source Facts

- Portal folder: `D:\PRM_GST_DESKTOP`
- Main PHP file: `index.php`
- Database: SQLite `prm_gst`
- Migration target folder: `D:\PRM_GST_DESKTOP`

## Phase Order

1. Portal and database audit.
2. Data migration tools.
3. SQLAlchemy model strategy.
4. Desktop shell and UI system.
5. Master modules.
6. Sales Bill workflow.
7. Purchase workflow.
8. Inventory and dispatch workflow.
9. Accounts and vouchers.
10. GST, e-invoice, e-way, and compliance.
11. Reports, prints, exports, archive.
12. Security, backup, installer, and client deployment.

## First Real Workflow

Sales Bill is the first full migration target because it touches customers,
products, packs, stock, GST, ledger posting, prints, and reports.

The desktop Sales Bill screen will be redesigned for desktop speed while
preserving PRM_GST calculations and database effects.
