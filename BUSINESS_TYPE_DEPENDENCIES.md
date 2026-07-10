# Business Type Dependencies

## Purpose
Document business-type dependencies, reusable services, and implementation relationships across current ERP workflows.

## Core reusable engines
- `services/pdf_print.py`: central PDF rendering engine for transactions, vouchers, and print templates.
- `services/business_rules.py`: business profile definitions, validation rules, and per-profile defaults.
- `services/company_profile_service.py`: company business type resolution, invoice template mapping, and license-driven profile lookup.
- `services/sqlite_source.py`: data source abstraction for operation rows and company metadata.
- `views/document_center_view.py`: document print workflow, print type selection, and bulk document operations.

## Business type template dependencies
- Business type profiles are declared in `services/business_rules.py`.
- `print_template_type` is used to map vertical business profiles to print templates such as `POS Receipt`, `Pharmacy Invoice`, `Distributor Invoice`, `A4 Tax Invoice`, `Service Invoice`, `Warehouse Picking Slip`, `Branch-Specific Invoice`, `Booking Receipt`.
- `company_profile_service.template_for_business_type()` resolves invoice template codes used by print logic.

## Workflow dependency map
### Sales / Purchase / Inventory
- `ModuleOperation` definitions in `views/module_hub_view.py` route user actions to data pages and source queries.
- Print/document flows in `views/document_center_view.py` rely on `PRINT_DOC_META` metadata for document title, party label, and document type.
- `DocumentArchiveService`, `OrderConversionService`, and `pdf_print` use metadata-driven document routing for conversions and exports.

### Reporting and compliance
- Report keys like `gst_reports`, `gstr9_annual`, `itc_reconciliation`, `einvoice`, `eway_bill` map to GST-specific workflows.
- `control_check`, `audit_log`, `cash_flow`, `balance_sheet`, and `financial_years` supports cross-business financial compliance.

### Vertical business profiles
- `restaurant` uses `print_template_type='POS Receipt'` and validates `kot_supported`.
- `pharmacy` supports batch/expiry validation and `Pharmacy Invoice` output.
- `electronics` supports serial/tracking validation and electronics-specific POS flows.
- `real_estate` uses `Booking Receipt` and requires `project_unit_required` validations.

## Integration dependencies
- Business type selection depends on `dev_business_types` table fallback data and `dev_companies` / `license` profile fields.
- `services.company_profile_service.CompanyProfileService.current_profile()` merges company and license data to resolve effective business type.
- `services.pdf_print` must be aligned with `company_profile_service.template_for_business_type()` to ensure correct print templates per business type code.

## Risk areas
- `business_type_code` vs `invoice_template_code` mapping must be consistent across `CompanyProfileService` and print rendering.
- Legacy `dev_business_types` table content may differ from hard-coded default business types, so database-driven business type configuration should be audited.
- Print workflow gaps may arise if `PRINT_DOC_META` lacks metadata for a business-specific document type.

## Recommended validation steps
1. Verify `Document Center` print metadata covers all legacy and current document types.
2. Confirm business type-specific template selection for `sales`, `purchases`, `quotation`, `delivery_challan`, and returns.
3. Test print output for `retail_supermarket`, `pharmacy_medical`, `electronics_mobile`, and `distributor_wholesale`.
4. Validate `BusinessProfile` required fields, columns, and validation rules against actual form/data entry workflows.
5. Ensure new operation groups reflecting `GST Reports`, `Loading Sheets`, `Dispatch Summary`, and vertical domains map to legacy workflows.
