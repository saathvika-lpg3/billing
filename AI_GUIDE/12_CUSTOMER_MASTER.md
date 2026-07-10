# Customer Master Specification

## 1. Purpose
This document defines the product specification for Customer Master in PRM_GST_DESKTOP.

The Customer Master is the central business record for all customers and trade parties who receive sales, dispatches, and related commercial documents. It must support the current Python + PyQt6 + SQLite desktop architecture and remain compatible with the existing .prmlic licensing model.

Locked project rules:
- Python + PyQt6 + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve existing .prmlic licensing
- Preserve existing desktop UI and module structure
- Keep all functionality additive and backward-compatible
- A4 Portrait and A2 Landscape printing support must be available where applicable
- Loading Sheet / Dispatch Summary must show GSTIN, HSN, and FSSAI if available and hide missing fields gracefully

## 2. Used by modules
Customer Master must support and integrate with the following areas:
- Sales billing and invoice entry
- Party ledger and customer account tracking
- Delivery challan and dispatch workflows
- Loading Sheet and Dispatch Summary generation
- Reporting and summary analysis
- Bulk print and document print workflows
- Search and lookup during transaction entry
- Customer-wise credit and outstanding analysis

## 3. Core product intent
Customer Master must provide a reliable, operator-friendly record for:
- customer identity and contact information
- GST and tax-related identity
- address and delivery location details
- credit and balance tracking
- sales route / area / territory handling
- document print and dispatch readiness

The master must remain simple enough for daily desktop usage while being rich enough for business reporting and compliance needs.

## 4. Field-level table

| Field | Type | Required | Purpose | Notes |
|---|---|---|---|---|
| Customer Code | Text | Yes | Unique identifier | Auto-generated or manually entered based on deployment policy |
| Customer Name | Text | Yes | Primary business name | Must be clearly visible in transaction UI |
| Customer Type | Select | Yes | Category of customer | Retail, Wholesale, Distributor, Hospital, Restaurant, etc. |
| Contact Person | Text | Optional | Main contact name | Useful for follow-up and dispatch handling |
| Mobile Number | Text | Optional | Primary contact number | Must support search and quick lookup |
| Phone Number | Text | Optional | Secondary contact | Optional |
| Email | Text | Optional | Email communication | Optional, but useful for reports and future integration |
| GSTIN | Text | Optional | GST registration number | Must be validated structurally when present |
| PAN | Text | Optional | PAN number | Optional, used in some reporting contexts |
| HSN Code | Text | Optional | Default HSN for customer-related items if applicable | Used in printed outputs when relevant |
| FSSAI | Text | Optional | Food licensing number if applicable | Used in print output where relevant |
| Drug License | Text | Optional | Pharmacy/medical license if applicable | Used for medical-related workflows |
| Address Line 1 | Text | Yes | Primary address | Must be visible in invoices and dispatch docs |
| Address Line 2 | Text | Optional | Secondary address | Optional |
| City | Text | Yes | Customer city | Used in route/area mapping |
| State | Text | Yes | State | Required for GST handling |
| PIN Code | Text | Optional | Postal code | Optional but recommended |
| Country | Text | Optional | Country | Default to India unless configured otherwise |
| Route / Area | Text / Lookup | Optional | Delivery route or business zone | Used in dispatch and reporting |
| Credit Limit | Decimal | Optional | Allowed credit exposure | Must be enforced where enabled |
| Opening Balance | Decimal | Optional | Beginning balance for ledger | Must support debit/credit sign conventions |
| Balance Type | Select | Optional | Debit or credit opening balance | Required for consistent ledger behavior |
| Status | Select | Yes | Active / Inactive / Hold | Used for filtering and transaction control |
| Remarks | Text | Optional | Internal notes | Used for operational context |
| Default Print Format | Select | Optional | Preferred document print layout | Must support A4 Portrait and A2 Landscape where applicable |
| Barcode / QR Preference | Select | Optional | Label/print preference | Optional, used in selected workflows |

## 5. Required fields
The following fields must be available and enforced as required for creating a usable customer record:
- Customer Code
- Customer Name
- Customer Type
- Address Line 1
- City
- State
- Status

If the deployment uses a strict business setup, the system may enforce additional fields such as GSTIN for taxable customers or route/area for dispatch-based operations. However, a minimal valid customer record must still be creatable with the core required fields above.

## 6. Optional fields
The following fields should be optional but available for richer business usage:
- Contact Person
- Mobile Number
- Phone Number
- Email
- GSTIN
- PAN
- HSN Code
- FSSAI
- Drug License
- Address Line 2
- PIN Code
- Country
- Route / Area
- Credit Limit
- Opening Balance
- Balance Type
- Remarks
- Default Print Format
- Barcode / QR Preference

## 7. GSTIN rules
- GSTIN must be stored as text and validated structurally when present.
- Empty GSTIN must be allowed for non-registered customers.
- GSTIN should be visible in customer search and transaction screens where relevant.
- GSTIN should appear on print outputs and dispatch/ loading documents when available.
- Missing GSTIN must not break transaction entry or document generation.
- The UI should not force GSTIN entry for customers who do not have it.

## 8. Address rules
- At least one address line and a city/state are required for a usable customer record.
- Address must be displayed clearly in billing and dispatch workflows.
- For dispatch and loading operations, the address should be preserved as entered and should not be silently truncated.
- The address should support a multi-line display in print and preview contexts.
- Missing address elements should be hidden gracefully in print output when not available.

## 9. Opening balance rules
- Opening balance must be supported for ledger initialization and account migration scenarios.
- Opening balance must allow both debit and credit values.
- The opening balance must be stored consistently and shown in reports.
- The system must not create ambiguous opening balance behavior when the sign convention is unclear.
- The UI should make the balance nature explicit and easy to understand.

## 10. Credit limit rules
- Credit limit should be optional and configurable per customer.
- When enabled, the system should be able to warn or block further billing when the customer exceeds the limit.
- Credit limit validation should be configurable to avoid breaking simple retail workflows.
- The UI should clearly show the remaining credit where applicable.
- Credit checks should remain compatible with the desktop workflow and should not require a web backend.

## 11. Customer type rules
Customer Type must support business-driven segmentation, including but not limited to:
- Retail
- Wholesale
- Distributor
- Supermarket
- Pharmacy
- Hospital
- Restaurant
- Government
- Services
- Other

The system should allow flexible customer-type configuration without forcing a rigid schema for all deployments.

## 12. Route / area mapping
- Route or area should be supported for delivery planning and dispatch-based workflows.
- Route / area mapping can be used for loading sheet grouping and dispatch summary preparation.
- The field should be optional so that simple customer records remain easy to create.
- The mapping should be usable in reporting and document grouping.

## 13. Sales invoice dependency
Customer Master is directly dependent on sales invoice workflows:
- Customer selection must be quick and reliable in sales documents.
- Sales invoice documents should carry the customer’s relevant name, address, GSTIN, and print preferences.
- The customer record should support default values for invoice-related fields where appropriate.
- Customer information must be available even when the customer is created just before transaction entry.

## 14. Dispatch / loading sheet dependency
Customer Master must support dispatch and loading workflows:
- Dispatch and loading sheet generation must be able to use the customer name, address, city, state, GSTIN, and route/area.
- Loading Sheet / Dispatch Summary must show GSTIN, HSN, and FSSAI if available.
- Missing fields must be hidden gracefully without blank or broken output.
- The customer record should support print layouts suitable for A4 Portrait and A2 Landscape where applicable.

## 15. Reports dependency
Customer Master should feed the following reports and analyses:
- customer ledger
- outstanding balance report
- sales by customer
- dispatch and loading sheet summary
- route / area-wise reporting
- customer-wise GST and document summary

## 16. Printing dependency
Customer records and transaction outputs must support print behavior that is consistent with the product rules:
- A4 Portrait support where applicable
- A2 Landscape support where applicable
- Print output should use customer details correctly and without layout errors
- Missing print fields should be hidden gracefully
- A customer’s preferred print layout may be used when available

## 17. Bulk print dependency
Customer-related documents should be compatible with bulk print workflows:
- Bulk print should support selected customer documents without breaking the layout
- Print selection should be based on document type and configured print settings
- Bulk print must honor the same A4 Portrait and A2 Landscape rules as other documents

## 18. SQLite storage expectations
- Customer Master data must be stored in local SQLite as part of the desktop model.
- New fields must be additive and backward-compatible.
- The structure should remain suitable for local desktop use and not require SQLite for this release.
- The customer table should support indexing for search, code, GSTIN, mobile, and status fields.
- Existing data should remain readable after new schema additions.

## 19. UI behavior
The Customer Master screen should provide:
- a clean form layout with clearly grouped sections
- customer code and name as primary entry fields
- easy navigation between profile, address, tax, credit, and notes sections
- search and filter tools for quickly locating existing customers
- save, cancel, and clear actions that are straightforward for operators
- a preview-friendly layout for printing and dispatch use

## 20. Operator-friendly rules
- The form should minimize unnecessary clicks.
- Frequently used fields should be placed near the top of the form.
- The operator should be able to create a new customer and immediately use it in sales entry.
- Validation errors should be clear and specific.
- The UI must not require unnecessary tax or print details before a basic customer record can be saved.
- The system should support keyboard-friendly data entry and efficient navigation.

## 21. Hotkeys / tooltips
The desktop UI should support operator-friendly interaction:
- Enter should move to the next relevant field where appropriate
- Esc should cancel or close the current entry flow when appropriate
- Ctrl+S should save when supported by the desktop pattern
- F4 or similar quick-search support may be used where appropriate
- Tooltips should explain fields such as GSTIN, opening balance, credit limit, route, and print preference
- Help text should be short and action-oriented

## 22. Audit log rules
All important Customer Master actions should be logged, including:
- create
- edit
- status change
- credit limit change
- opening balance change
- print preference change
- deletion or cancellation if permitted by workflow

Required audit details:
- user identity
- role
- timestamp
- action type
- affected customer record
- impacted module or workflow

Audit logging must remain compatible with the current desktop + SQLite model and should not require a web backend.

## 23. Testing checklist
- Verify a new customer can be created with the minimum required fields.
- Verify GSTIN can be entered and displayed correctly when present.
- Verify address fields are preserved and displayed correctly in billing and dispatch flows.
- Verify opening balance and credit limit behave consistently.
- Verify customer type and route/area mapping work correctly.
- Verify sales invoice, dispatch, and loading sheet workflows can use the customer master data.
- Verify print output supports A4 Portrait and A2 Landscape where applicable.
- Verify Loading Sheet / Dispatch Summary show GSTIN, HSN, and FSSAI when available and hide missing fields gracefully.
- Verify search and selection are fast and reliable.
- Verify audit logs capture the expected create/edit actions.
- Verify the desktop UI remains usable and operator-friendly.

## 24. Done condition
Customer Master is considered complete when:
- a valid customer can be created and edited from the desktop UI
- the record is usable in sales, dispatch, reporting, and print workflows
- GSTIN, address, opening balance, credit limit, and route/area handling behave as specified
- print behavior is compatible with A4 Portrait and A2 Landscape where applicable
- Loading Sheet / Dispatch Summary output handles available and missing fields gracefully
- the feature works in the existing Python + PyQt6 + SQLite structure without requiring SQLite or web services

## 25. Future roadmap
- Add configurable customer-type templates for common business categories
- Improve route/area-based dispatch planning and grouping
- Add more advanced credit-control rules and alerts
- Expand print customization per customer and document type
- Improve reporting depth for customer-wise outstanding, sales, and dispatch summaries
- Keep all future work aligned with the current desktop-only architecture and .prmlic licensing model
