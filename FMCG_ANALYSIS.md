# FMCG Engine Analysis for PRM_GST_DESKTOP

## 1. Objective
This document analyzes the existing PRM_GST_DESKTOP desktop ERP for the design of a professional FMCG engine.

The goal is to add an FMCG engine as a core business engine of the ERP platform without redesigning the existing architecture, without converting to web, without changing SQLite, and without replacing the existing .prmlic licensing model.

This analysis is product-spec and implementation-planning level only. No application code is modified in this step.

## 2. Current implementation baseline
The current project already contains a strong desktop ERP foundation for general trading and distribution workflows.

### 2.1 Current product master
The existing product master in [views/product_master_view.py](views/product_master_view.py) already supports:
- product code and name
- category, brand, supplier
- HSN and GST
- batch and expiry flags
- pack rows
- barcode and basic pricing fields
- basic stock and reorder fields

### 2.2 Current inventory
The current inventory workflow in [views/stock_out_view.py](views/stock_out_view.py), [views/inventory_entry_view.py](views/inventory_entry_view.py), and [services/transaction_repository.py](services/transaction_repository.py) already supports:
- stock entry
- stock transfer
- stock adjustment
- stock out / loading challan
- dispatch return
- stock movement posting

### 2.3 Current sales and purchase
The current sales and purchase flows in [views/sales_bill_view.py](views/sales_bill_view.py) and [views/purchase_entry_view.py](views/purchase_entry_view.py) already support:
- document entry
- item rows
- GST calculation
- print and share workflows
- basic pricing and quantity handling

### 2.4 Current reports and printing
The existing reporting and printing stack in [views/report_center_view.py](views/report_center_view.py) and [services/pdf_print.py](services/pdf_print.py) already supports:
- report center
- PDF generation
- A4 portrait and A2 landscape-based print behavior
- bulk print concepts
- transaction document printing

### 2.5 Current search and UI
The current search experience in [views/global_search_view.py](views/global_search_view.py) and [services/sqlite_source.py](services/sqlite_source.py) already supports:
- global search
- menu search
- basic record search
- customer, supplier, product, and invoice lookup

The user experience in [views/main_window.py](views/main_window.py) already supports:
- desktop module navigation
- ribbon/menu structure
- keyboard shortcuts and modern desktop UX patterns

### 2.6 Current persistence and security
The current data layer in [database/connection.py](database/connection.py), [services/master_repository.py](services/master_repository.py), [services/transaction_repository.py](services/transaction_repository.py), and [services/license_service.py](services/license_service.py) already provides:
- local SQLite-based persistence
- license validation through .prmlic
- backup-related workflows and installer concerns
- basic audit and role-oriented structure through the existing docs and UI

## 3. FMCG capabilities already partially present
The current system already has a useful base for FMCG work, especially for:
- product master
- item packs
- barcode-based lookups
- basic GST and tax handling
- stock-in / stock-out workflows
- sales and purchase transaction flows
- reports and print output

However, the current implementation is still general trading-oriented rather than fully enterprise FMCG-oriented.

## 4. Missing functionality for a professional FMCG engine
The following areas are currently insufficient for an enterprise-style FMCG distributor platform.

### 4.1 FMCG product structure
The current product model is still too simple for advanced FMCG use.

Missing or weak concepts:
- company / brand / division / department / category / sub-category / product / variant hierarchy
- SKU and internal code hierarchy
- manufacturer code
- barcode and QR handling at a richer level
- FSSAI and manufacturer / supplier linkage
- pack hierarchy across purchase, sales, and stock
- product attributes such as shelf life, weight, volume, and pack details

### 4.2 Multi UOM and pack conversion engine
The current system supports basic pack rows and units, but it does not yet provide a true enterprise FMCG pack conversion engine.

Missing concepts:
- PCS, BOX, CTN, PALLET, DOZEN, PACK, BAG, TIN, BOTTLE, LTR, ML, KG, GM, TRAY, CASE, and custom UOMs
- conversion across purchase, sales, base, and pack units
- automatic stock recalculation when selling by piece, box, carton, or pallet
- structured pack hierarchy such as pallet → carton → box → piece

### 4.3 Pricing engine
The current pricing model is too limited for FMCG distributor pricing workflows.

Missing concepts:
- purchase price and landing cost separation
- distributor, wholesale, retail, and dealer price levels
- customer-specific and area-specific pricing
- offer and scheme pricing
- super stockist / special price structures

### 4.4 Scheme engine
The current product and transaction flows do not yet provide a full FMCG scheme engine.

Missing concepts:
- buy X get Y
- free quantity
- slab discount
- flat discount
- percentage discount
- festival offer
- combo offer
- retailer/distributor/company offers
- customer-wise and area-wise schemes
- date-wise applicability

### 4.5 Batch and expiry engine
The current system has batch/expiry flags, but not a full batch engine.

Missing concepts:
- batch master and lot tracking
- manufacturing date and expiry date
- near-expiry visibility
- expired stock handling
- FEFO / FIFO selection logic
- batch selection during sales and dispatch

### 4.6 Inventory engine for FMCG trade
The current inventory model is functional but not yet FMCG-grade.

Missing concepts:
- reserved stock
- available stock
- transit stock
- damaged stock
- near-expiry stock
- location/rack/bin management
- route-wise and van-wise stock movement

### 4.7 Route sales and van sales engine
Current workflows include loading and dispatch patterns, but not a fully structured FMCG route and van sales engine.

Missing concepts:
- vehicle / driver / salesman / route / beat linkage
- opening stock, sales, returns, damage, closing stock, and collections
- route-wise outstanding and collection behavior
- van stock reconciliation and dispatch summary

### 4.8 Printing engine for FMCG documents
The current printing engine is already capable but still needs stronger FMCG-specific outputs.

Missing concepts:
- thermal 58 and thermal 80 document support
- loading sheet and dispatch summary layouts that are rich and structured
- document-wise paper-size control in more complete FMCG flows
- barcode and QR print support
- route-wise loading and dispatch document outputs

### 4.9 Search engine for FMCG workflows
The current search layer is useful, but not yet enterprise-grade for FMCG complexity.

Missing concepts:
- barcode search
- product search by brand, category, company, batch, expiry, route, invoice, and customer
- multi-field search for pack and price contexts
- faster search behavior with large FMCG catalogs

### 4.10 Reports for FMCG distributors
The current reports are general-purpose and must be expanded for FMCG-specific operations.

Missing concepts:
- fast moving / slow moving analysis
- near-expiry and expired stock reports
- brand-wise, category-wise, company-wise, route-wise, salesman-wise, and customer-wise reports
- batch-wise stock and movement reports
- stock ageing and margin/profit reports
- scheme report

## 5. Required database additions
The FMCG engine should be implemented as additive schema changes in SQLite, preserving the existing data model.

### 5.1 Core product and hierarchy tables
Recommended additions:
- fmcg_product_hierarchy
- fmcg_product_attributes
- fmcg_brand_master
- fmcg_company_master
- fmcg_division_master
- fmcg_department_master
- fmcg_category_master
- fmcg_subcategory_master
- fmcg_variant_master

### 5.2 UOM and pack conversion tables
Recommended additions:
- uom_master
- uom_conversion_rules
- product_pack_hierarchy
- product_pack_conversion

### 5.3 Pricing and scheme tables
Recommended additions:
- price_matrix
- customer_price_matrix
- area_price_matrix
- scheme_master
- scheme_applicability
- scheme_offer_lines

### 5.4 Batch and expiry tables
Recommended additions:
- batch_lots
- batch_stock_balances
- batch_movement_log

### 5.5 Inventory and route tables
Recommended additions:
- stock_reservations
- stock_transit
- stock_damaged
- route_sales_headers
- route_sales_lines
- van_sales_headers
- van_sales_lines
- loading_sheet_headers
- loading_sheet_lines
- dispatch_summary_headers
- dispatch_summary_lines

### 5.6 Existing tables to extend safely
The existing tables should be extended rather than replaced where practical:
- items
- product_packs
- customers
- suppliers
- sales / sales_items
- purchases / purchase_items
- stock_log
- stock_outs / stock_out_items
- company
- users
- documents / prints

## 6. Required UI changes
The FMCG engine should reuse the current desktop UI pattern rather than creating a separate architecture.

### 6.1 Product master enhancements
The current [views/product_master_view.py](views/product_master_view.py) should evolve to support:
- company / brand / division / department / category / sub-category / product / variant fields
- SKU, internal code, manufacturer code, barcode, QR code
- multi-UOM and pack hierarchy
- pricing matrix entry
- scheme flags and product attributes
- shelf life and manufacturing/expiry data
- images and document references

### 6.2 Sales and purchase enhancement
The current [views/sales_bill_view.py](views/sales_bill_view.py) and [views/purchase_entry_view.py](views/purchase_entry_view.py) should evolve to support:
- product selection by pack and UOM
- pricing level selection
- scheme application
- batch selection
- route and van context
- dispatch summary and loading sheet readiness

### 6.3 Inventory and dispatch enhancement
The current [views/stock_out_view.py](views/stock_out_view.py) should evolve to support:
- vehicle, driver, salesman, route, beat
- van stock and load summary
- batch and expiry visibility during load and dispatch
- loading sheet and dispatch summary output

### 6.4 Reporting and search enhancement
The current [views/report_center_view.py](views/report_center_view.py) and [views/global_search_view.py](views/global_search_view.py) should evolve to support:
- FMCG-specific reports
- search across brand, category, company, barcode, batch, HSN, route, customer, invoice, and expiry

## 7. Required business rules
The FMCG engine must follow clear business rules.

### 7.1 Product hierarchy rule
Every product must support the structured hierarchy:
- company
- brand
- division
- department
- category
- sub category
- product
- variant
- SKU
- internal code
- manufacturer code
- barcode
- QR code

### 7.2 Pack and conversion rule
The system must support multi-UOM and pack hierarchy and allow sales by:
- piece
- box
- carton
- pallet

Stock movement must update automatically when a conversion is used.

### 7.3 Pricing rule
The system must support multiple price levels with clear business logic:
- purchase
- landing cost
- cost price
- distributor price
- wholesale price
- retail price
- MRP
- offer price
- special customer price
- area price
- dealer price
- super stockist price

### 7.4 Scheme rule
The system must support flexible scheme application and preserve the scheme context in document output and reporting.

### 7.5 Batch rule
Batch selection must be available and must support:
- batch tracking
- manufacturing date
- expiry date
- near expiry detection
- expired stock detection
- FIFO / FEFO logic

### 7.6 Route and van rule
Route and van workflows must support:
- opening stock
- sales
- returns
- damage
- closing stock
- collection tracking
- outstanding visibility

### 7.7 Printing rule
FMCG documents must support:
- A4 Portrait
- A4 Landscape
- A2 Landscape
- Thermal 58
- Thermal 80
- PDF
- bulk print
- barcode and QR output
- loading sheet and dispatch summary

Loading Sheet and Dispatch Summary must show GSTIN, HSN, and FSSAI when available, and hide missing fields gracefully.

## 8. Files affected
The initial implementation scope is expected to touch these existing areas:
- [views/product_master_view.py](views/product_master_view.py)
- [views/sales_bill_view.py](views/sales_bill_view.py)
- [views/purchase_entry_view.py](views/purchase_entry_view.py)
- [views/stock_out_view.py](views/stock_out_view.py)
- [views/dispatch_return_view.py](views/dispatch_return_view.py)
- [views/report_center_view.py](views/report_center_view.py)
- [views/global_search_view.py](views/global_search_view.py)
- [services/master_repository.py](services/master_repository.py)
- [services/transaction_repository.py](services/transaction_repository.py)
- [services/sqlite_source.py](services/sqlite_source.py)
- [services/pdf_print.py](services/pdf_print.py)
- [services/print_preview.py](services/print_preview.py)
- [views/main_window.py](views/main_window.py)
- [database/connection.py](database/connection.py)
- [config/app_config.py](config/app_config.py)

## 9. Risk analysis
### 9.1 Data compatibility risk
Adding rich FMCG fields can break or confuse existing customer data if implemented too aggressively.

Mitigation:
- use additive SQLite schema changes
- preserve existing tables and columns where possible
- provide safe migration and rollback steps

### 9.2 Print complexity risk
FMCG print flows can become inconsistent if different print modes are managed separately.

Mitigation:
- centralize print behavior through one print engine
- preserve A4/A2 support and document-specific choices

### 9.3 Search and performance risk
Large FMCG inventories can slow search and UI performance if implemented naively.

Mitigation:
- use indexed SQLite columns
- keep search asynchronous and non-blocking
- implement progressive filtering

### 9.4 Licensing and security risk
FMCG expansion should not weaken .prmlic or local data protection.

Mitigation:
- preserve .prmlic-based control
- keep database protection and backup strategy intact

### 9.5 UI complexity risk
A rich FMCG UI can become too heavy for operators if not designed carefully.

Mitigation:
- keep the desktop UX keyboard-first and operator-friendly
- add fields progressively
- avoid overloading the main entry screen

## 10. Migration plan
The migration should be additive and safe.

### Phase 1 - Foundation and schema
- add new SQLite tables and columns for FMCG data
- keep existing product and transaction tables working
- make new fields optional where possible

### Phase 2 - Product and pack model
- extend product master for hierarchy, UOM, pack, and price structure
- preserve existing general product records

### Phase 3 - Pricing and schemes
- add pricing matrix and scheme model
- keep default values for existing records

### Phase 4 - Batch and inventory
- add batch and stock reservation logic
- preserve stock movement history

### Phase 5 - Route, van, and print
- add route and van workflows
- expand loading sheet and dispatch summary outputs

### Phase 6 - Reports and search
- add FMCG-specific reporting and search enhancements
- preserve existing report flows

## 11. Implementation principle for this phase
This phase is analysis and planning only.

No application code should be modified yet.

The next implementation step is to build the FMCG engine in a controlled sequence, one engine at a time, and to stop after each engine is completed and documented.
