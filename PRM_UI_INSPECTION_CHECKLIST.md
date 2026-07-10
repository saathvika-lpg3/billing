PRM UI Inspection Checklist

1. Login / Startup
- Verify app starts and shows login dialog
- Login with test credentials (if available)
- Check license dialog does not block startup

2. Dashboard
- Confirm dashboard widgets load
- Check navigation to modules from dashboard
- Note any slow-loading widgets

3. Product Master
- Open `Product Master` view
- Verify list load, search, add/edit dialogs
- Verify pack rows display correctly and barcode column
- Confirm multi-UOM / pack conversion fields visible
- Check save/edit success and validation messages

4. Party Master
- Open `Party Master` (Customers and Suppliers)
- Verify list, search, add/edit dialogs
- Confirm new Phase 3 fields are visible (area, shipping_address, customer_type/supplier_type, balance, credit_limit)
- Test save with minimal fields and with extended fields
- Confirm validation messages match behavior

5. UOM / Price availability (Phase 4 basics)
- Confirm UOM maintenance UI (if present) or verify via DB that `uoms` table exists
- Confirm pack conversion entries present in `product_packs` and `pack_conversions` tables
- Verify price levels and product price lookups via Product Master pack rows

6. Sales Screen (visual only)
- Open Sales screen
- Verify UI elements render (customer selector, products, totals)
- Ensure price levels dropdown or indicators are visible

7. Purchase Screen (visual only)
- Open Purchase screen
- Verify UI elements render (supplier selector, items, totals)

8. Reports (visual only)
- Open Reports screen
- Navigate to a few key reports and confirm render

9. Search
- Use global search to find a product and a party
- Verify results and navigation

10. Known issues (pre-inspection)
- Recent schema migrations added `area` to `suppliers` and many party/product columns; ensure upgrades do not crash
- `uom_price_service.py` added for Phase 4 but UI integration not implemented yet
- Relaxed party validation to allow missing legacy fields (code/city) — validate behavior in UI

11. Screens needing screenshots/testing
- Product Master add/edit dialog (packs area)
- Party Master add/edit dialog (extended fields)
- Sales screen with product selection
- Purchase screen with supplier selection
- Dashboard with widgets

Notes:
- Do not redesign UI; only visual/manual inspection is required.
- Capture screenshots for failing or suspicious screens and attach to bug report.
