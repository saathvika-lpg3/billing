# Product Master

## 2026-07-12 Conversion and GST save contract

- Purchase UOM may differ from Sale UOM when a positive explicit
  Purchase-to-Sale Factor is supplied. A legitimate conversion must not be
  rejected merely because pack units differ.
- `UomPriceService.validate_product_conversions()` is the single validation
  boundary. `MasterRepository.save_product()` validates before opening the
  write transaction and synchronizes product-specific conversion rows inside
  the same transaction as the item and package rows.
- Single-UOM products require a factor of 1 when purchase and sale units are
  identical. Multi-UOM/Pack Conversion products require valid units and a
  positive factor; explicit purchase conversion takes precedence over a pack
  row's pack size.
- Selecting a category may apply its default GST rate. Persisted item GST then
  takes precedence in transactions, followed by HSN tax code and category
  default.
- Global smart-combo behavior is installed by the shell. Product Master must
  not create a second completer or use `.text()`/`.setText()` on combo boxes.
- Regression coverage includes single UOM, Multi-UOM, Pack Conversion,
  multiple packs, barcode, MRP/PTR/PTS, purchase/sale prices, save/reload/edit
  and rollback on invalid conversion.

## Current scope
- Product master persistence is now safe on fresh SQLite databases.
- The shared repository handles schema migrations and product pack persistence without breaking existing databases.
- The product view now supports validation, barcode checks, basic search/filtering, keyboard shortcuts, and FMCG-ready fields.

## Business rules implemented
- Product name is required.
- HSN is validated when entered.
- GST, MRP, purchase price, sales price, reorder level, and opening stock must be non-negative numeric values.
- UOM is required.
- Barcode values are checked for uniqueness across products.
- Products can be deactivated safely; deletion is blocked when transaction references exist.

## FMCG-ready fields
- Multi-UOM flag
- Pack conversion flag
- Batch and expiry flags
- Shelf life days and near-expiry alert days
- MRP, PTR, PTS, distributor price, wholesale price, and retail price

## Search and UX
- Search by product name, code, barcode, HSN, category, brand, GST rate, status, batch flag, and expiry flag.
- Search input accepts `Return` to apply filtering immediately.
- Mandatory fields are highlighted and receive focus on load.
- Enter/Shift+Enter move through the main form fields, Ctrl+S saves, Ctrl+N/New clears, Ctrl+F focuses search, F4 adds a pack row, Delete removes selected pack rows, and Escape clears the form safely.

## Stabilized desktop layout
- The canonical action bar is horizontal and contains New, Save, Refresh, Copy, Advanced, Import, Export, and Close.
- Basic, Inventory & UoM, and Identification & Notes are responsive cards; their content must never overlap when the page is reopened or the window is resized.
- Package actions are Add Pack, Duplicate Pack, and Remove Selected. Duplicate Pack intentionally clears barcode and supplier code so unique identifiers are never copied accidentally.
- The page reflows for 1366x768 and larger desktop screens without hiding the package grid or relying on a permanent vertical scrollbar.

## Widget and persistence safety
- Read and write values through `widgets.widget_values`; combo boxes use `currentText()`/`setCurrentText()` rather than line-edit-only APIs.
- New clears the form without destroying the UOM models.
- Save reloads the same product ID and does not issue a second duplicate save.
- Sale UOM and purchase UOM are persisted separately through `MasterRepository`.
- Multi-pack save/reload/edit is covered by the UI stabilization tests against a temporary SQLite database.
