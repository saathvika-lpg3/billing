# Business Type Completion Matrix

## Purpose
Provide a compact coverage matrix for current business type workflows and identify the degree of implementation completeness relative to legacy module/workflow categories.

## Dataset Summary
- Legacy menu/workflow keys: 96
- Current operation keys: 149
- Overlap between legacy and current keys: 45
- Legacy-only keys: 51
- Current-only keys: 104
- Current business profiles: 12
- Current default active business types: 4

## Completion Categories
- Core workflows: sales, purchase, inventory, accounts, GST, print/document management
- Vertical workflows: pharmacy, restaurant, electronics, real estate, manufacturing, warehouse, service
- Reporting workflows: ledgers, vouchers, GST returns, audit, stock reports, dispatch summaries
- Admin workflows: company settings, business types, developer console, numbering series, backup

## Estimated Completion
| Category | Legacy surface | Current surface | Parity status |
|---|---|---|---|
| Sales/Quoting | Present | Present | High |
| Purchase/Procurement | Present | Present | High |
| Inventory/Logistics | Present | Present | High |
| Accounts/Finance | Present | Present | Medium-High |
| GST & Compliance | Present | Present | High |
| Business-specific verticals | Partial | Expanded | High |
| Document Center / Print | Present | Centralized | High |
| Reports | Present | Expanded | High |
| Admin / Setup | Present | Expanded | High |

## Notes
- `Current surface` is broader than `Legacy surface` because the current system exposes more granular workflows and multiple operation variants per business type.
- `Accounts/Finance` is rated Medium-High mainly because legacy names such as `cash_flow_statement`, `day_book`, `account_ledgers`, and `closing_management` require exact workflow validation, even though their current equivalents exist.
- `Business-specific verticals` are now explicitly implemented and should be validated by `services/business_rules.py` and business-type template mappings.

## Business Profile Coverage
### Active business types
- `distributor_wholesale` — wholesale distributor invoice workflows and default template mapping
- `retail_supermarket` — retail POS and thermal print workflows
- `pharmacy_medical` — pharmacy billing, batch/expiry, drug-license, FSSAI workflows
- `electronics_mobile` — electronics sales, serial/warranty, POS workflows

### Defined business profiles
The application defines formal profiles for 12 business domains, supporting both generic and vertical behaviors.

### Print-format coverage
- All business profiles should support A4 Portrait by default.
- Distributor and Medical Distributor should support A2 Landscape.
- Retail and Restaurant should support Thermal Print.

## Parity focus for next validation
- Match legacy report and account workflow names to current operation keys
- Verify `document_archive_file` and legacy print archive semantics against current `Print Logs` / `Print Templates`
- Validate business type print template selection for sales/purchase/invoice flows
- Confirm `dev` / license-driven business type selection does not break current workflow routing
