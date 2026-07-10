# FMCG Execution Plan for PRM_GST_DESKTOP

## 1. Purpose
This document defines a phased implementation plan for the FMCG engine in the existing PRM_GST_DESKTOP desktop ERP.

The plan preserves the current architecture, the desktop-first product model, the SQLite persistence approach, and the existing .prmlic licensing workflow.

The implementation must proceed one engine at a time, with a pause after each completed engine for review and validation.

## 2. Implementation principles
- Preserve the current desktop product architecture.
- Do not convert to web.
- Do not replace SQLite in this release.
- Do not replace .prmlic licensing.
- Keep the system additive and backward-compatible.
- Implement one engine at a time.
- Reuse existing UI, repository, and print patterns where possible.
- Keep new database changes optional and safe for existing deployments.

## 3. Engine sequence
The recommended sequence is:

1. Product and pack foundation engine
2. Pricing engine
3. Scheme engine
4. Batch and expiry engine
5. Inventory and stock reservation engine
6. Route and van sales engine
7. Print and document engine
8. Reporting and search engine

Each engine should be implemented as a standalone milestone and then paused before the next one begins.

## 4. Engine 1 - Product and pack foundation engine
### Goal
Create a stronger FMCG product foundation that supports structured hierarchy, SKU handling, pack hierarchy, and improved product master UX.

### Scope
- extend product master with hierarchy fields
- add SKU and internal code fields
- add manufacturer code and barcode/QR fields
- improve pack structure and default pack handling
- add optional product attributes fields
- preserve existing product records

### Expected database additions
- new optional columns on items and product_packs
- optional helper tables for category / brand / company hierarchy if needed

### Expected UI changes
- enhance product master form
- add product hierarchy fields
- add pack hierarchy fields
- maintain existing simple entry flow and desktop ergonomics

### Completion checkpoint
Pause after the product and pack foundation is implemented, tested, and documented.

## 5. Engine 2 - Pricing engine
### Goal
Add a multi-level pricing model suitable for FMCG distributors and dealers.

### Scope
- support purchase price and cost fields
- support distributor, wholesale, retail, dealer, and special price levels
- support customer and area-specific pricing where appropriate
- preserve general pricing behavior for existing customers

### Expected database additions
- price_matrix
- customer_price_matrix
- area_price_matrix

### Expected UI changes
- pricing tab or pricing matrix panel in product master and customer master
- simple price selection in sales entry

### Completion checkpoint
Pause after pricing logic is implementable through product master and sales entry without breaking existing billing.

## 6. Engine 3 - Scheme engine
### Goal
Implement flexible offer and scheme workflows that can be applied to products and transactions.

### Scope
- define scheme master
- define scheme applicability rules
- apply scheme lines in sales entry
- show scheme impact in preview and print documents

### Expected database additions
- scheme_master
- scheme_applicability
- scheme_offer_lines

### Expected UI changes
- scheme selection in sales entry
- scheme configuration in product or master settings

### Completion checkpoint
Pause after scheme application is available in a controlled way and documents preserve the scheme context.

## 7. Engine 4 - Batch and expiry engine
### Goal
Add proper batch and expiry tracking for FMCG stock movement.

### Scope
- add batch and expiry fields to stock and transaction lines
- support batch master and lot tracking
- support FEFO/FIFO selection logic
- support near-expiry and expired stock visibility

### Expected database additions
- batch_lots
- batch_stock_balances
- batch_movement_log

### Expected UI changes
- batch selection in sales, purchase, and stock entry
- batch visibility in stock dashboard and reports

### Completion checkpoint
Pause after batch and expiry behavior is working without breaking existing stock handling.

## 8. Engine 5 - Inventory and stock reservation engine
### Goal
Introduce a more robust FMCG-style stock engine.

### Scope
- add reserved, available, damaged, and transit stock concepts
- support stock reservation for loading and dispatch workflows
- support warehouse / route stock visibility
- keep stock movement audit intact

### Expected database additions
- stock_reservations
- stock_transit
- stock_damaged

### Expected UI changes
- stock dashboard enhancements
- reservation and damage visibility
- route and loading-related status updates

### Completion checkpoint
Pause after inventory state is understandable and consistent for all transaction types.

## 9. Engine 6 - Route and van sales engine
### Goal
Support route-based FMCG dispatch and van sales operations.

### Scope
- vehicle, driver, salesman, route, and beat management
- loading sheet and dispatch summary flow
- route sales / van sales summary flow
- opening stock, sales, returns, damage, closing stock, and collections

### Expected database additions
- route_sales_headers
- route_sales_lines
- van_sales_headers
- van_sales_lines
- loading_sheet_headers
- loading_sheet_lines
- dispatch_summary_headers
- dispatch_summary_lines

### Expected UI changes
- enhance stock out and dispatch UI
- add route/vehicle/salesman selection flow
- add dispatch summary output

### Completion checkpoint
Pause after route and van operations are working and document output is stable.

## 10. Engine 7 - Print and document engine
### Goal
Support FMCG-oriented documents and print outputs.

### Scope
- thermal 58 and thermal 80 print support
- loading sheet and dispatch summary document templates
- barcode and QR output support
- maintain existing A4/A2/PDF logic

### Expected database additions
- document settings and document template preferences if needed

### Expected UI changes
- print preview and layout selection in sales, purchase, stock out, and dispatch flows

### Completion checkpoint
Pause after printing is reliable and document templates are consistent.

## 11. Engine 8 - Reporting and search engine
### Goal
Complete the FMCG reporting and search experience.

### Scope
- fast-moving/slow-moving analysis
- near-expiry and expired stock reports
- batch movement reports
- brand/category/company/route/salesman/customer analysis
- enhanced global search for barcode, batch, product, route, invoice, and customer

### Expected database additions
- reporting views or helper tables if needed

### Expected UI changes
- reporting center enhancements
- global search enhancements

### Completion checkpoint
Pause after reports and search are validated against real FMCG usage patterns.

## 12. Review and validation gates after each engine
After each engine implementation, the following should be checked:
- existing sales and purchase flows still work
- existing product and stock flows still work
- print outputs remain functional
- license installation and local deployment still work
- database migrations are safe and optional
- no forced migration breaks older databases

## 13. Suggested milestone order for this repository
The current repository already has clear starting points for the first engines:
- product master: [views/product_master_view.py](views/product_master_view.py)
- sales billing: [views/sales_bill_view.py](views/sales_bill_view.py)
- purchase entry: [views/purchase_entry_view.py](views/purchase_entry_view.py)
- stock / dispatch: [views/stock_out_view.py](views/stock_out_view.py)
- print engine: [services/pdf_print.py](services/pdf_print.py)
- repositories: [services/master_repository.py](services/master_repository.py) and [services/transaction_repository.py](services/transaction_repository.py)
- shell and module access: [views/main_window.py](views/main_window.py)

## 14. Immediate next step
The next implementation action should be the first engine only: Product and Pack Foundation.

After that engine is completed and reviewed, the work should pause and the next engine should be planned or started only after confirmation.
