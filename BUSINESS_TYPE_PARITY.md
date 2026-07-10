# Business Type Parity Analysis

## Objective
Capture business workflow parity between the legacy `D:\PRM_BILLING_INVENTORY` desktop ERP and the current `D:\PRM_GST_DESKTOP` implementation, focusing on complete workflows rather than menu labels or file names.

## Summary
- Legacy workflow surface: 9 high-level top menu groups and 96 menu keys.
- Current workflow surface: 164 operation definitions across 156 operation groups.
- Current system supports 12 explicit business profiles and 4 default business type templates.
- Feature matrix shows 14 business-type categories plus an "Others" fallback.
- Major workflows are present in the new system, with extensive modernization and specialized vertical modules.

## Supported Business Types
Current business profiles defined in `services/business_rules.py`:
- `retail` — Retail POS
- `pharmacy` — Pharmacy
- `distributor_wholesale` — Distributor / Wholesale
- `fmcg` — FMCG Distribution
- `trading` — Trading GST
- `manufacturing` — Manufacturing
- `service` — Service Billing
- `warehouse` — Warehouse / Picking
- `multi_branch` — Multi Branch
- `electronics` — Electronics
- `restaurant` — Restaurant
- `real_estate` — Real Estate

Default active company business types from `services/company_profile_service.py`:
- `distributor_wholesale`
- `retail_supermarket`
- `pharmacy_medical`
- `electronics_mobile`

## Major Workflow Coverage
### Sales and Quoting
Supported workflows:
- Quotation, quotation list
- Sales order, sales order list
- Sales bill entry
- Delivery challan
- Sales return
- Point-of-sale billing variants including POS Billing, Electronics POS, Pharmacy Retail, Restaurant POS

### Purchase and Procurement
Supported workflows:
- Purchase order, PO list
- Purchase entry, purchase list
- Purchase return
- Debit notes
- Supplier ledger

### Inventory and Logistics
Supported workflows:
- Stock entry, stock transfer, stock adjustment
- Stock alerts, negative stock, expiry/wastage monitoring
- Vehicle stock out, stock movement
- Load challans, dispatch returns, loading sheets, dispatch summary
- Warehouses, branches, routes, transporters

### Accounts and Finance
Supported workflows:
- Receipts, payments, expenses, journal entry
- Cash / bank book, day book
- Voucher registry and review
- Ledgers, outstanding, aging report
- Trial balance, profit & loss, balance sheet, cash flow, fund flow
- Account closing and bank reconciliation

### Reporting and Compliance
Supported workflows:
- Sales reports, purchase reports, stock reports, inventory valuation
- GST reports, GST return, GST postings, ITC reconciliation, GSTR-9 annual
- E-invoice and E-way bill
- Audit log and control check

### Administration and Setup
Supported workflows:
- Company settings, users, role permissions
- Financial years, numbering series, print settings
- Backup / restore
- Developer admin and dashboard settings
- Business type configuration

## Document Center and Print Workflow
The current Document Center defines:
- `Print Bills`
- `Print Batches`
- `Print Templates`
- `Template Families`
- `Product Labels`
- `Print Logs`
- `Order Conversions`

Print metadata currently supports document types for:
- sales, purchases, quotation, sales_order, purchase_order, delivery_challan, sales_return, purchase_return

This aligns with business-type-aware PDF rendering via `services/pdf_print.py` and business profile template mapping in `services/company_profile_service.py`.

## Parity Observations
- 45 legacy menu keys overlap directly with current operation keys after normalizing prefixes.
- 51 legacy keys are not exact matches in current operation keys; these are largely covered by renamed or more granular operations.
- 104 current operation keys are new or represent expanded workflows beyond the legacy menu surface.
- Current architecture prioritizes workflow decomposition and vertical business specialization over a one-to-one menu mapping.

## Workflow Parity Notes
- Legacy Reports and Administration workflows are preserved but restructured into dedicated operation groups like `GST Reports`, `Loading Sheet`, `Dispatch Summary`, `Developer Admin`, and `Business Types`.
- Current system explicitly adds modern vertical modules for `restaurant`, `pharmacy`, `electronics`, `real_estate`, `manufacturing`, and `warehouse` workflows.
- Print and template management are now centralized in Document Center and print metadata rather than scattered across menu modules.

## Gaps and Risks
### Potential parity gaps
- `account_ledgers`, `cash_flow_statement`, `day_book`, `balance_sheet` and some legacy report names appear under new keys but should be validated for exact workflow equivalence.
- `document_archive_file` from legacy Document Center may map to `Print Logs` or archive/scan workflows; verify archive semantics.
- Legacy `enkvoices`, `eway_bills`, `audit`, and `control_check` appear re-implemented as `einvoice`, `eway_bill`, `audit_log`, and `control_check`, but testing is required to confirm parity.

### Implementation risks
- Business-type print layout behavior depends on the combination of `business_type_code`, `invoice_template_code`, and `print_template_type`.
- Business workflow parity should be validated at the document flow level, not by menu label alone.

## Conclusion
The current workspace delivers a much richer and more modular business workflow set than the legacy menu surface, with explicit business type profiles and a dedicated print/document center. Remaining work should focus on verifying the 51 legacy-only workflow labels against current equivalents and ensuring the print/document flows behave identically for all supported business type templates.
