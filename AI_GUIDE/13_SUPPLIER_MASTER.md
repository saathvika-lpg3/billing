# Supplier Master Specification

## 1. Purpose
This document defines the product specification for Supplier Master in PRM_GST_DESKTOP.

Supplier Master is the central business record for all suppliers and vendors who provide goods, services, or stock to the business. It must support the current Python + PyQt6 + SQLite desktop architecture and remain compatible with the existing .prmlic licensing model.

Locked project rules:
- Python + PyQt6 + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve existing .prmlic licensing
- Preserve existing valid customer and supplier data during updates
- Keep all functionality additive and backward-compatible
- A4 Portrait and A2 Landscape printing support must be available where applicable
- Missing print fields must be hidden gracefully
- Database protection/security requirements must be considered in all supplier data handling

## 2. Used by modules
Supplier Master must support and integrate with the following areas:
- Purchase invoice and purchase entry workflows
- Purchase return and vendor return workflows
- Accounts and party ledger workflows
- Purchase register and vendor reports
- Print and export workflows
- Search and lookup during transaction entry
- Supplier-wise balance and outstanding analysis

## 3. Core product intent
Supplier Master must provide a reliable, operator-friendly record for:
- supplier identity and contact information
- GST and tax-related identity
- address and delivery / correspondence details
- opening balance and accounts tracking
- supplier type and classification
- document print readiness

The master must remain simple enough for daily desktop entry while being rich enough for reporting and compliance needs.

## 4. Field-level table

| Field | Type | Required | Purpose | Notes |
|---|---|---|---|---|
| Supplier Code | Text | Yes | Unique identifier | Auto-generated or manually assigned based on deployment policy |
| Supplier Name | Text | Yes | Primary business name | Must be clearly visible in purchase workflows |
| Supplier Type | Select | Yes | Category of supplier | Trader, Manufacturer, Distributor, Service Vendor, etc. |
| Contact Person | Text | Optional | Main contact name | Useful for vendor follow-up |
| Mobile Number | Text | Optional | Primary contact number | Should support quick lookup |
| Phone Number | Text | Optional | Secondary contact | Optional |
| Email | Text | Optional | Email communication | Optional but useful for future workflows |
| GSTIN | Text | Optional | GST registration number | Must be validated structurally when present |
| PAN | Text | Optional | PAN number | Optional |
| HSN Code | Text | Optional | Default item classification if applicable | Used where relevant in documents |
| FSSAI | Text | Optional | Food license if applicable | Used for food-related procurement workflows |
| Drug License | Text | Optional | Pharmacy/medical license if applicable | Used for medical supply workflows |
| Address Line 1 | Text | Yes | Primary address | Must be visible in purchase and print contexts |
| Address Line 2 | Text | Optional | Secondary address | Optional |
| City | Text | Yes | Supplier city | Useful for reporting and location-based logic |
| State | Text | Yes | State | Needed for tax and reporting workflows |
| PIN Code | Text | Optional | Postal code | Optional |
| Country | Text | Optional | Country | Default to India unless configured otherwise |
| Opening Balance | Decimal | Optional | Beginning balance | Must support debit/credit conventions |
| Balance Type | Select | Optional | Debit or credit opening balance | Needed for accurate ledger behavior |
| Status | Select | Yes | Active / Inactive / Hold | Used for filtering and transaction controls |
| Remarks | Text | Optional | Internal notes | Useful for operational context |
| Default Print Format | Select | Optional | Preferred document print layout | Supports A4 Portrait and A2 Landscape where applicable |

## 5. Required fields
The following fields must be available and enforced as required for creating a usable supplier record:
- Supplier Code
- Supplier Name
- Supplier Type
- Address Line 1
- City
- State
- Status

If the deployment uses a stricter setup, additional fields such as GSTIN may be enforced for taxable suppliers. However, a minimal valid supplier record must still be creatable with the core required fields above.

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
- Opening Balance
- Balance Type
- Remarks
- Default Print Format

## 7. GSTIN rules
- GSTIN must be stored as text and validated structurally when present.
- Empty GSTIN must be allowed for non-registered suppliers.
- GSTIN should be visible in supplier search and purchase transaction screens where relevant.
- GSTIN should appear in print outputs when available.
- Missing GSTIN must not break purchase entry or document generation.
- The UI should not force GSTIN entry for suppliers who do not have it.

## 8. Address rules
- At least one address line and a city/state are required for a usable supplier record.
- Address should be preserved accurately for purchase and reporting workflows.
- Address should support multi-line display in print and preview contexts.
- Missing address elements should be hidden gracefully in print output when not available.

## 9. Opening balance rules
- Opening balance must be supported for ledger initialization and accounts setup.
- Opening balance must allow both debit and credit values.
- The opening balance must be stored consistently and shown in reports.
- The UI should make the balance nature explicit and easy to understand.

## 10. Supplier type rules
Supplier Type must support business-driven classification, including but not limited to:
- Trader
- Manufacturer
- Distributor
- Service Vendor
- Pharmacy / Medical Supplier
- Food Supplier
- Other

The system should allow flexible supplier-type configuration without forcing a rigid schema for all deployments.

## 11. Purchase invoice dependency
Supplier Master is directly dependent on purchase invoice workflows:
- Supplier selection must be quick and reliable in purchase documents.
- Purchase invoice documents should carry the supplier’s relevant name, address, GSTIN, and print preferences.
- The supplier record should support default values for purchase-related fields where appropriate.
- Supplier information must be available even when the supplier is created just before transaction entry.

## 12. Purchase return dependency
Supplier Master should support purchase return workflows:
- Purchase return documents should be able to use the supplier identity and address correctly.
- Supplier-specific print settings should be respected where applicable.
- Return documents should remain consistent with the supplier master data.

## 13. Accounts dependency
Supplier Master must integrate with accounts and party-ledger workflows:
- Outstanding balances should be tied to supplier records.
- Opening balance and subsequent purchase/payment activity must remain visible in accounts reports.
- Vendor balances must be understandable and auditable.

## 14. Reports dependency
Supplier Master should feed the following reports and analyses:
- supplier ledger
- outstanding balance report
- purchase by supplier
- purchase return summary
- GST summary by supplier
- supplier-wise document summary

## 15. Printing dependency
Supplier records and transaction outputs must support print behavior consistent with the product rules:
- A4 Portrait support where applicable
- A2 Landscape support where applicable
- Missing print fields should be hidden gracefully
- Supplier details must be printed clearly and without layout errors
- Preferred print layout may be used when available

## 16. SQLite storage expectations
- Supplier Master data must be stored in local SQLite as part of the desktop model.
- New fields must be additive and backward-compatible.
- The structure should remain suitable for local desktop use and should not require SQLite for this release.
- The supplier table should support indexing for search, code, GSTIN, mobile, and status fields.
- Existing data should remain readable after new schema additions.
- Supplier data must be protected according to the local database security requirements.

## 17. UI behavior
The Supplier Master screen should provide:
- a clean form layout with clearly grouped sections
- supplier code and name as primary entry fields
- easy navigation between profile, address, tax, accounts, and notes sections
- search and filter tools for quickly locating existing suppliers
- save, cancel, and clear actions that are straightforward for operators
- a preview-friendly layout for printing and document use

## 18. Operator-friendly rules
- The form should minimize unnecessary clicks.
- Frequently used fields should be placed near the top of the form.
- The operator should be able to create a new supplier and immediately use it in purchase entry.
- Validation errors should be clear and specific.
- The UI must not require unnecessary tax or print details before a basic supplier record can be saved.
- The system should support keyboard-friendly data entry and efficient navigation.

## 19. Hotkeys / tooltips
The desktop UI should support operator-friendly interaction:
- Enter should move to the next relevant field where appropriate
- Esc should cancel or close the current entry flow when appropriate
- Ctrl+S should save when supported by the desktop pattern
- F4 or similar quick-search support may be used where appropriate
- Tooltips should explain fields such as GSTIN, opening balance, supplier type, and print preference
- Help text should be short and action-oriented

## 20. Audit log rules
All important Supplier Master actions should be logged, including:
- create
- edit
- status change
- opening balance change
- print preference change
- deletion or cancellation if permitted by workflow

Required audit details:
- user identity
- role
- timestamp
- action type
- affected supplier record
- impacted module or workflow

Audit logging must remain compatible with the current desktop + SQLite model and should not require a web backend.

## 21. Backup/security considerations
Supplier Master data is part of the core business data set and must be protected.

Required rules:
- Supplier data must be stored in a protected local database context.
- If the database file is copied, it should not be directly usable without the proper application protection context.
- Backups must also be protected and should not be trivially restorable by casual file access.
- Restore operations must validate backup integrity and require confirmation before overwriting current data.
- Updates must preserve existing supplier data and should not break current purchase or accounts workflows.

## 22. Testing checklist
- Verify a new supplier can be created with the minimum required fields.
- Verify GSTIN can be entered and displayed correctly when present.
- Verify address fields are preserved and displayed correctly in purchase and print flows.
- Verify opening balance behaves consistently.
- Verify supplier type classification works correctly.
- Verify purchase invoice and purchase return workflows can use the supplier master data.
- Verify print output supports A4 Portrait and A2 Landscape where applicable.
- Verify missing print fields are hidden gracefully.
- Verify search and selection are fast and reliable.
- Verify audit logs capture the expected create/edit actions.
- Verify backup/restore and database protection requirements are respected.
- Verify the desktop UI remains usable and operator-friendly.

## 23. Done condition
Supplier Master is considered complete when:
- a valid supplier can be created and edited from the desktop UI
- the record is usable in purchase, accounts, reporting, and print workflows
- GSTIN, address, opening balance, and supplier type handling behave as specified
- print behavior is compatible with A4 Portrait and A2 Landscape where applicable
- the feature works in the existing Python + PyQt6 + SQLite structure without requiring SQLite or web services
- core database and backup protection requirements remain satisfied

## 24. Future roadmap
- Add supplier-type templates for common procurement categories
- Improve supplier-wise reporting and payable analysis
- Expand print customization per supplier and document type
- Improve backup validation and restore safeguards
- Keep all future work aligned with the current desktop-only architecture and .prmlic licensing model
