# Business Type Development Plan

## Overview
This plan captures the current state, missing implementation gaps, and a step-by-step development execution path for all business types in `D:\PRM_GST_DESKTOP`.

The plan is based on current code analysis of:
- `services/business_rules.py`
- `services/company_profile_service.py`
- `services/pdf_print.py`
- `views/developer_console_view.py`
- `views/main_window.py`
- `views/sales_bill_view.py`
- `views/purchase_entry_view.py`
- `views/sales_document_view.py`

## Current state

### Supported business type profiles
`services/business_rules.py` defines the following profiles:
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

### Active/default business type codes
`services/company_profile_service.py` currently exposes these fallback business types when `dev_business_types` is unavailable:
- `distributor_wholesale`
- `retail_supermarket`
- `pharmacy_medical`
- `electronics_mobile`

### Current integration points
- `CompanyProfileService.current_profile()` resolves effective business type from `company`, `license`, and `dev_companies`.
- `CompanyProfileService.template_for_business_type()` maps business type code to `invoice_template_code`.
- `pdf_print.resolve_print_options()` selects print options by document type, template rows, and distributor A2 behavior.
- `views/developer_console_view.py` allows selecting business type in the developer console.
- `services.business_rules.validate_item_line()` enforces a small set of required fields and some stock checks.
- `views/sales_bill_view.py`, `views/purchase_entry_view.py`, and `views/sales_document_view.py` use `validate_item_line()` when adding a line.

## Missing implementation details

### 1. Profile code mismatch
There is a critical mismatch between default business type codes and defined profiles:
- `retail_supermarket` exists as a default type but not in `BUSINESS_PROFILES`
- `pharmacy_medical` exists as a default type but not in `BUSINESS_PROFILES`
- `electronics_mobile` exists as a default type but not in `BUSINESS_PROFILES`

That means codes used by default company profiles do not currently resolve to the intended business profile metadata and will fallback to `distributor_wholesale` in `profile_for()`.

### 2. Business profile metadata not fully applied
The business profile metadata contains:
- `required_fields`
- `optional_fields`
- `hidden_fields`
- `columns`
- `validation_rules`
- `print_template_type`

Only a narrow subset is applied today:
- `validate_item_line()` enforces `hsn`, `unit`, `gst_rate`, and stock checks.
- No UI logic currently uses `optional_fields`, `hidden_fields`, or `columns`.
- No screen dynamically rebuilds entry fields or table columns based on business type.

### 3. Business-type-specific menu and workflow gating is missing
- `views/main_window.py` renders ribbon menus from static operation arrays.
- There is no business-type-based filtering of `INDUSTRY_OPERATIONS` or ribbon groups.
- Business-type-specific menu items exist but are not gated or automatically selected by the active business type.

### 4. Print/template mapping coverage is incomplete
- `template_for_business_type()` maps codes to invoice templates, but it is decoupled from `BusinessProfile.print_template_type`.
- `pdf_print.resolve_print_options()` uses `invoice_template_code` and a distributor A2 override, but does not directly reference business profile print template defaults.
- There is no explicit test coverage for business-type-specific print output in the current code base.

### 5. Business type field and validation gaps in UI
- Sales, purchase, and sales document item entry screens use generic fields and do not adapt to specific business-type field sets.
- There is no UI toggle for batch/expiry, serial/warranty, table number, project/unit, branch/event fields based on business type.
- Business-type validation flags like `kot_supported`, `project_unit_required`, `serial_warranty_supported`, `warehouse_required`, `customer_required`, and `invoice_series_required` are not enforced in the entry UI.

## Missing business type coverage by type

### distributor_wholesale
- Present in profile definitions and default fallback.
- Print mapping exists via `wholesale_tax_invoice`.
- Missing: UI hide `batch`/`expiry`, show PO/transport/route/salesman fields, explicit `approved_read_only` behavior.

### retail_supermarket
- Included as active default code, but not in `BUSINESS_PROFILES`.
- Missing: retail POS profile mapping, thermal/A4 selection, fast billing UI, stock-required behavior.

### pharmacy_medical
- Included as active default code, but not in `BUSINESS_PROFILES`.
- Missing: pharmacy profile mapping, batch/expiry required UI, pharmacy invoice template, drug-shop-specific fields.

### electronics_mobile
- Included as active default code, but not in `BUSINESS_PROFILES`.
- Missing: electronics profile mapping, serial/warranty-specific UI, electronics invoice template.

### fmcg
- Profile exists.
- Missing: UI support for category, free_qty, scheme fields, and `free_qty_supported` behavior.

### trading
- Profile exists.
- Missing: unit-required validation and UI emphasis on taxable invoices.

### manufacturing
- Profile exists.
- Missing: raw material / finished goods type UI, batch lot field, warehouse selection, manufacturing-specific print hints.

### service
- Profile exists.
- Missing: service description / SAC / qty_hours input flow and customer-required enforcement.

### warehouse
- Profile exists.
- Missing: warehouse-required item flow, stock availability field, warehouse picking slip print path.

### multi_branch
- Profile exists.
- Missing: branch selector, invoice series field, optional employee/cost center fields, branch-specific invoice routing.

### restaurant
- Profile exists.
- Missing: table number field, KOT flow and restaurant POS screens, POS receipt print behavior.

### real_estate
- Profile exists.
- Missing: project/unit/customer booking flow, booking receipt print mapping, real estate-specific document routing.

## Execution plan

### Phase 1 — Align profile codes and mapping
1. Add missing business profile keys for the active default codes:
   - `retail_supermarket` → map to `retail` or create an explicit retail_supermarket profile
   - `pharmacy_medical` → map to `pharmacy` or create explicit pharmacy_medical profile
   - `electronics_mobile` → map to `electronics` or create explicit electronics_mobile profile
2. Ensure `profile_for()` resolves every `business_type_code` used by company/license/dev data.
3. Normalize business_type_code values in `company_profile_service` and `license_service` if needed.
4. Update `BusinessProfile` metadata for any missing fields required by actual business types.

### Phase 2 — Enforce business type validation
1. Expand `validate_item_line()` to support profile-specific validation rules:
   - `batch_required`, `expiry_required`, `expired_batch_blocked`
   - `free_qty_supported`, `scheme_supported`
   - `unit_required`
   - `serial_warranty_supported`
   - `customer_required`
   - `project_unit_required`
2. Add higher-level validation for document headers where required:
   - `table_no` for restaurant
   - `branch` and `invoice_series` for multi_branch
   - `project` and `unit` for real_estate
3. Add tests covering business-specific validation scenarios.

### Phase 3 — Adapt UI fields and forms
1. Make entry-screen UI adaptive to the resolved business type:
   - Sales bill, purchase entry, and document screens should show/hide fields and columns based on `BusinessProfile.hidden_fields`, `optional_fields`, and `columns`.
   - Example: restaurant should show `table_no`; pharmacy should show `batch` and `expiry`; electronics should show serial/warranty values.
2. Use profile metadata to set required markers on the UI and display contextual prompts.
3. Build a small UI policy layer or helper that maps `BusinessProfile` metadata to field visibility/required state.

### Phase 4 — Business-type menu and workflow gating
1. Implement business-type filtering for industry-specific operation groups in `views/main_window.py`.
2. Keep core ribbon menus available for all businesses, but show/hide `INDUSTRY_OPERATIONS` entries based on current business type.
3. Ensure `Business Types` configuration remains accessible for admin/developer users.
4. Add tests or manual validation for menu visibility per business type.

### Phase 5 — Print/template verification
1. Align template mapping between `CompanyProfileService.template_for_business_type()` and `BusinessProfile.print_template_type`.
2. Add or update business-type-specific print template definitions for:
   - Retail POS / thermal print
   - Pharmacy invoice
   - Electronics invoice
   - Distributor A2 invoice
   - Service invoice
   - Warehouse picking slip
   - Restaurant receipt
   - Real estate booking receipt
3. Validate `pdf_print.resolve_print_options()` for each business type and key document type.
4. Add targeted print regression tests for at least:
   - `distributor_wholesale` sales invoice and purchase invoice
   - `retail_supermarket` POS bill
   - `pharmacy_medical` pharmacy invoice
   - `electronics_mobile` electronics sales invoice
   - `restaurant` receipt/KOT output

### Phase 6 — Testing and delivery
1. Expand unit tests in:
   - `tests/test_developer_dashboard.py`
   - `tests/test_print_and_report_parity.py`
   - new tests for `services/business_rules.validate_item_line()` behavior per business type
2. Add business-type smoke tests for UI field sets and validation conditions.
3. Perform manual sign-off for each business type against expected workflow and print output.
4. Document the mapping from business type to screen/print requirements in developer guide.

## Per-business-type development tasks

### distributor_wholesale
- Confirm profile key and default type mapping.
- Ensure Po/transport/route/salesman fields are visible in `SalesBillView` and relevant headers.
- Hide batch/expiry fields and show GST/HSN/discount fields.
- Validate `approved_read_only` workflow as required.
- Verify A2 landscape invoice behavior and `wholesale_tax_invoice` template.

### retail_supermarket
- Add profile mapping for `retail_supermarket`.
- Ensure POS-style UI and fast billing entry.
- Validate stock checks and retail billing behavior.
- Confirm thermal or A4 print selection as appropriate.

### pharmacy_medical
- Add profile mapping for `pharmacy_medical`.
- Enforce batch and expiry fields in entry screens.
- Confirm pharmacy invoice template selection.
- Validate expired-batch blocking and HSN requirements.

### electronics_mobile
- Add profile mapping for `electronics_mobile`.
- Show serial/warranty or model fields in item entry and print metadata.
- Confirm electronics invoice template selection.
- Validate serial/warranty supported behavior.

### fmcg
- Ensure category and scheme/free_qty workflow is visible.
- Validate free_qty and scheme logic in entry and print.

### trading
- Ensure unit selection and taxable invoice fields are required.
- Confirm HSN/qty/unit validation.

### manufacturing
- Add raw_material_finished_goods_type and batch_lot_no flow.
- Ensure warehouse selection is visible and required.
- Validate manufacturing-specific print guidance.

### service
- Add service_description, SAC, qty_hours fields.
- Validate customer requirement and service item handling.
- Confirm service invoice template.

### warehouse
- Ensure warehouse and stock_availability fields are visible and required.
- Validate warehouse picking slip print path.

### multi_branch
- Ensure branch selector and invoice_series are required.
- Add optional warehouse, cost center, employee, branch_gstin, discount fields.
- Validate branch-specific invoice routing.

### restaurant
- Add `table_no` and restaurant order flow UI.
- Enable KOT or restaurant-specific operations.
- Confirm POS receipt print formatting.

### real_estate
- Add project/unit/customer/amount booking flow.
- Validate project/unit required logic.
- Confirm booking receipt print path.

## Recommended action file
Create a development execution file named `BUSINESS_TYPE_DEVELOPMENT_PLAN.md` containing:
- current status
- missing gaps
- per-business-type tasks
- phase-by-phase action plan
- test and validation checkpoints

This file is now created in the workspace and can serve as the single execution reference.
