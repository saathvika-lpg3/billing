# ERP Feature Matrix for PRM_GST_DESKTOP

## 1. Purpose
This document defines the expected feature matrix for different business types in PRM_GST_DESKTOP.

It is intended as a product-spec reference for the current Python + PyQt6 + SQLite desktop ERP and should guide future UI, reporting, printing, and workflow decisions.

Locked project rules:
- Python + PyQt6 + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve .prmlic licensing
- Preserve existing desktop UI and modules
- Keep feature support additive and backward-compatible

## 2. Feature legend
- Yes = expected as a core or commonly required feature
- Conditional = depends on deployment, licensing, or business setup
- Optional = useful but not mandatory for the first release path
- No = not required for this business type in the current scope

## 3. Business-type feature matrix

| Business type | Sales | Purchase | Inventory | Accounts | GST | Batch | Expiry | HSN | FSSAI | Drug License | Loading Sheet | Dispatch Summary | Bulk Print | A4 Portrait | A2 Landscape | Thermal Print | Barcode/QR | Reports |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Distributor / Wholesale | Yes | Yes | Yes | Yes | Yes | Conditional | No | Yes | Conditional | No | Yes | Yes | Yes | Yes | Yes | Conditional | Yes | Yes |
| Retail / Supermarket | Yes | Yes | Yes | Yes | Yes | Conditional | No | Yes | No | No | Conditional | Conditional | Yes | Yes | Conditional | Yes | Yes | Yes |
| Medical Shop / Pharmacy | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Conditional | Yes | Yes | Yes |
| Medical Distributor | Yes | Yes | Yes | Yes | Yes | Yes | Conditional | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Conditional | Yes | Yes |
| Restaurant / Food Billing | Yes | Yes | Conditional | Yes | Yes | Conditional | Conditional | Yes | Yes | No | Conditional | Conditional | Yes | Yes | Conditional | Yes | Conditional | Yes |
| Manufacturing | Yes | Yes | Yes | Yes | Yes | Yes | Conditional | Yes | No | No | Conditional | Conditional | Yes | Yes | Conditional | Conditional | Yes | Yes |
| Services | Yes | Conditional | No | Yes | Conditional | No | No | Conditional | No | No | No | No | Conditional | Yes | Conditional | No | No | Yes |
| Electronics / Mobile | Yes | Yes | Yes | Yes | Yes | Conditional | Conditional | Yes | No | No | Conditional | Conditional | Yes | Yes | Conditional | Conditional | Yes | Yes |
| Garments | Yes | Yes | Yes | Yes | Yes | Conditional | No | Yes | No | No | Conditional | Conditional | Yes | Yes | Conditional | Conditional | Yes | Yes |
| Hardware | Yes | Yes | Yes | Yes | Yes | Conditional | No | Yes | No | No | Conditional | Conditional | Yes | Yes | Conditional | Conditional | Yes | Yes |
| Automobile Parts | Yes | Yes | Yes | Yes | Yes | Conditional | No | Yes | No | No | Conditional | Conditional | Yes | Yes | Conditional | Conditional | Yes | Yes |
| Stationery | Yes | Yes | Yes | Yes | Yes | No | No | Yes | No | No | Conditional | Conditional | Yes | Yes | Conditional | Conditional | Yes | Yes |
| Agriculture | Yes | Yes | Yes | Yes | Yes | Conditional | Conditional | Yes | No | No | Yes | Yes | Yes | Yes | Conditional | Conditional | Yes | Yes |
| Others | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Conditional | Yes | Conditional | Conditional | Conditional | Yes |

## 4. Detailed business-type guidance

### 4.1 Distributor / Wholesale
Expected needs:
- Strong sales and purchase workflows
- Inventory tracking with stock movement
- GST support
- HSN support
- Loading Sheet and Dispatch Summary support
- Bulk print and both A4 Portrait / A2 Landscape support
- Barcode/QR support for packing and dispatch workflows

### 4.2 Retail / Supermarket
Expected needs:
- Fast sales billing
- Inventory updates and stock reconciliation
- GST support
- Barcode/QR support for quick scanning
- Thermal print support for bills and receipts
- Bulk print where needed for labels and summaries

### 4.3 Medical Shop / Pharmacy
Expected needs:
- Batch and expiry tracking
- GST and HSN support
- FSSAI and drug-license-related data handling
- Purchase and sales workflows with strict inventory control
- Loading Sheet and Dispatch Summary support for deliveries
- Barcode/QR support for item handling

### 4.4 Medical Distributor
Expected needs:
- Batch and expiry support where applicable
- Strong purchase/sales and inventory control
- GST and HSN support
- FSSAI and drug-license support
- Loading Sheet and Dispatch Summary support
- Bulk print and both A4 Portrait / A2 Landscape support

### 4.5 Restaurant / Food Billing
Expected needs:
- Fast sales billing and invoice generation
- GST support
- FSSAI support for food-related operations
- Batch/expiry support when raw materials or packaging are tracked
- Thermal print support for bills
- Bulk print when needed for summaries or kitchen docs

### 4.6 Manufacturing
Expected needs:
- Strong purchase and inventory workflows
- Batch tracking and production-related stock movement
- GST and HSN support
- Barcode/QR support for components and finished goods
- Reports for stock and movement

### 4.7 Services
Expected needs:
- Sales and accounts support
- Conditional purchase support
- GST may be conditional based on service tax rules
- Limited inventory and barcode requirements
- Report support for invoices and accounts

### 4.8 Electronics / Mobile
Expected needs:
- Sales, purchase, inventory, and accounting support
- GST and HSN support
- Barcode/QR support
- Bulk print and document printing support
- Reports for stock and sales performance

### 4.9 Garments
Expected needs:
- Sales, purchase, inventory, and GST support
- Barcode/QR support for SKU handling
- Bulk print and report generation
- Size/color variant awareness if needed in later versions

### 4.10 Hardware
Expected needs:
- Sales, purchase, inventory, and accounting support
- GST and HSN support
- Barcode/QR support
- Reports for stock and sales

### 4.11 Automobile Parts
Expected needs:
- Sales, purchase, inventory, and accounting support
- GST and HSN support
- Barcode/QR support
- Strong stock and report support

### 4.12 Stationery
Expected needs:
- Sales, purchase, inventory, and reporting support
- GST and HSN support
- Barcode/QR support where relevant
- Bulk print support for labels or price sheets

### 4.13 Agriculture
Expected needs:
- Sales, purchase, inventory, and accounting support
- GST support
- Loading Sheet and Dispatch Summary support where transport is involved
- Barcode/QR support for product handling and dispatch
- Report support for stock and movement

### 4.14 Others
Expected needs:
- Feature support should be configurable and business-driven
- The application should not assume a single fixed workflow for all custom businesses
- Print, reporting, and inventory needs may vary by deployment

## 5. Print and paper-size expectations
Across business types:
- A4 Portrait is mandatory for all business types.
- A2 Landscape is mandatory for Distributor / Wholesale and Medical Distributor, and optional/conditional for other business types.
- Thermal print is mandatory for Retail / Supermarket and Restaurant / Food Billing, and optional/conditional for other business types.
- Bulk print must respect the selected paper settings per document type.
- Loading Sheet and Dispatch Summary must show GSTIN, HSN, and FSSAI if available and hide missing fields gracefully.
- Missing print fields must be hidden gracefully without blank labels.

## 6. Reporting expectations
All supported business types should be able to use:
- sales register
- purchase register
- stock report
- party ledger
- GST summary
- document-level reports and summaries

## 7. Product-spec guidance for implementation
- Keep the feature matrix additive and backward-compatible
- Do not force every business type into the same workflow
- Preserve the desktop ERP structure and current .prmlic licensing model
- Allow business-type-specific modules and print rules to be configured without breaking the base app
- Ensure printing and reporting remain consistent across supported business types

## 8. Future roadmap
- Add business-type-specific defaults for print layout and report templates
- Add more configurable rules for batch, expiry, and document flow per business type
- Expand bulk print and paper-size behavior per document type
- Keep future work aligned with the current Python + PyQt6 + SQLite desktop architecture
