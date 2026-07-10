# Company Master Specification

## 1. Purpose of Company Master
Company Master is the central business profile for the PRM_GST_DESKTOP desktop ERP. It stores the legal, operational, and print-related identity of the single active client/company for one installation.

This master is used by:
- sales and purchase invoices
- vouchers and accounting entry headers
- print layouts and PDF export
- reports and summaries
- loading sheet and dispatch summary outputs
- installer/update validation context

It acts as the authoritative source for the company name, registration details, business type, print metadata, and default document behavior used by the application.

## 2. Single-company rule for Version 1
- One installation = one client/company unless a future version changes this model.
- Version 1 must not support multi-company switching in the same desktop installation.
- The active Company Master record should represent the current client/company context for that installation.
- The UI and data model should assume a single active company profile unless future multi-company support is explicitly introduced.

## 3. Who can access it
Company Master should be accessible to:
- Developer users for full configuration and maintenance
- Admin users for business-level configuration and safe updates
- Client users only if the deployment and role model allow limited editing
- Normal users should be view-only or have no direct access unless explicitly permitted

Access should be controlled by the existing desktop role model and current .prmlic-based licensing. The feature must not bypass the existing authorization model.

## 4. Developer/admin/client access rules
- Developer: can configure business type, license-sensitive fields, print defaults, and company profile settings.
- Client Admin: can edit company contact, address, and print preference fields only if the deployment allows it.
- Normal user: view-only or no access.
- Unauthorized users must not be able to change company identity, tax details, or print configuration.
- If access is not allowed, the UI should show a clear denial message instead of silently allowing changes.

## 5. Required fields
These fields should be mandatory for a usable Company Master record:
- Company Name
- Business Type
- Address Line 1
- City
- State
- PIN Code
- Mobile / Contact Number
- Email
- Default Currency
- Default print profile or document paper-size default

If the business uses GST-based workflows, the following may also be required depending on deployment:
- GSTIN
- PAN
- HSN context or default HSN usage
- FSSAI number if applicable to the business type

## 6. Optional fields
These fields may be optional but should be supported if available:
- Company Logo
- Website
- Alternate Contact
- GSTIN
- PAN
- FSSAI Number
- CIN / Registration Number
- Bank Details
- Branch / Unit Name
- Default Terms and Conditions
- Print footer text
- Print signature / authorized signatory details
- Default warehouse / branch / cost center references

## 7. Field-level specification table

| Field name | Required / Optional | Validation | Used in printing | Used in reports | Used in license/install |
|---|---|---|---|---|---|
| Company Name | Required | Non-empty text | Yes | Yes | No |
| Business Type | Required | Must be one of the supported business types | Yes | Yes | No |
| Address Line 1 | Required | Non-empty text | Yes | Yes | No |
| City | Required | Non-empty text | Yes | Yes | No |
| State | Required | Non-empty text | Yes | Yes | No |
| PIN Code | Required | Numeric or valid postal format | Yes | Yes | No |
| Mobile / Contact Number | Required | Non-empty phone-like value | Yes | Yes | No |
| Email | Required | Basic email format if present | Yes | No | No |
| Default Currency | Required | Valid currency code or display value | Yes | Yes | No |
| Default Print Profile | Required | Must resolve to a valid document print setting | Yes | No | No |
| GSTIN | Optional | Validate format if present | Yes | Yes | No |
| PAN | Optional | Validate format if present | Yes | Yes | No |
| FSSAI Number | Optional | Validate format if present | Yes | Yes | No |
| Company Logo | Optional | File path or image reference | Yes | No | No |
| Website | Optional | Basic URL format if present | No | No | No |
| Bank Details | Optional | Free text or structured data | No | No | No |
| Branch / Unit Name | Optional | Text | Yes | Yes | No |
| Terms & Conditions | Optional | Free text | Yes | No | No |
| Footer / Signature Text | Optional | Free text | Yes | No | No |
| Default Warehouse / Branch / Cost Center | Optional | Must match existing master data if present | No | Yes | No |

## 8. Business type rules
The Company Master must support the following business types for PRM_GST_DESKTOP:
- Distributor / Wholesale
- Retail / Supermarket
- Medical Shop / Pharmacy
- Medical Distributor
- Restaurant / Food Billing
- Manufacturing
- Services
- Electronics / Mobile
- Garments
- Hardware
- Automobile Parts
- Stationery
- Agriculture
- Others

Locked rule:
- Distributor business type must support both A4 Portrait and A2 Landscape print layouts.
- The system must not treat Distributor as A4-only or A2-only.

## 9. GSTIN rules
- GSTIN should be stored as a string and validated if present.
- If entered, it should follow the expected GSTIN format pattern for the business context.
- The field should be optional unless the deployment requires GST-based invoicing.
- GSTIN must be available for printing when present.
- If missing, the print layer must not show a blank label.

## 10. FSSAI number rules
- FSSAI number should be stored as a string and validated if present.
- It should be optional unless the business type or document type requires it.
- FSSAI number must be displayed in print outputs only when it exists.
- The print layout must hide the field gracefully when absent.
- No blank label such as "FSSAI:" should appear without a value.

## 11. License dependency with .prmlic
- Company Master must remain fully compatible with the existing .prmlic licensing model.
- Existing valid .prmlic files must continue working after updates.
- Company Master changes must not break license validation, application startup, or installation behavior.
- If the license is invalid or missing, the Company Master screen must not be treated as a bypass to unlock the app.

## 12. Printing dependency
Company Master is directly tied to print behavior for the desktop application.

The following print-related values should be available from Company Master:
- company name
- address
- GSTIN
- FSSAI number
- PAN
- logo
- contact details
- footer/signature text

These values must be available for:
- print preview
- PDF export
- bulk print
- document-specific layouts

## 13. Document-wise print usage
The Company Master and its print settings must be used by the following document types:
- Sales Invoice
- Purchase Invoice
- Delivery Challan
- Loading Sheet
- Dispatch Summary
- Credit Note
- Debit Note
- Bulk Print

Each document type should be able to use its own print settings and paper size profile.

## 14. Paper-size setting rule
Paper size should be saved per document type, not only globally.

This means:
- Sales Invoice may use A4 Portrait by default
- Delivery Challan may use A4 Portrait or A2 Landscape depending on the deployment
- Loading Sheet / Dispatch Summary may use A4 Portrait or A2 Landscape depending on the business type and admin choice
- Bulk Print must respect the per-document print setting rather than using one global paper size for every document

The system must support both A4 Portrait and A2 Landscape and must not hard-code only one of them.

## 15. Loading Sheet / Dispatch Summary dependency
Company Master data must support loading sheet and dispatch summary printing.

Locked print requirements:
- Loading Sheet / Dispatch Summary must show GSTIN if available.
- Loading Sheet / Dispatch Summary must show HSN if available.
- Loading Sheet / Dispatch Summary must show FSSAI number if available.
- These fields must appear in print preview, PDF export, and bulk print.
- If a field is not available, hide it gracefully.
- Do not display blank labels like "GSTIN:" with no value.
- This applies especially to Distributor business type.
- Must support both A4 Portrait and A2 Landscape.

## 16. Reports dependency
Company Master should feed the following reporting areas:
- sales register
- purchase register
- party ledger
- GST summary
- stock report
- GSTR-related reports
- document headers and footers

Reports should use the stored company profile consistently and not rely on hard-coded values.

## 17. Backup/restore dependency
- Company Master data must be preserved in backup and restore operations.
- Backup and restore must not destroy company profile values unexpectedly.
- Restore operations should preserve the current company profile unless an explicit overwrite action is chosen.
- Backup/restore behavior must remain compatible with the current SQLite-based storage model.

## 18. Installer/update dependency
- Company Master data and related print preferences must remain intact through installation and updates.
- Installer and update flows must preserve the active SQLite database and any company master content.
- Updates must not break the current .prmlic license validation or destroy company settings.
- The installer must not silently replace a valid company profile with an empty/default one.

## 19. SQLite storage expectations
- The application remains a Python + SQLite desktop ERP.
- Company Master data should be stored in the local SQLite database.
- No SQLite migration is required for this release.
- Company Master updates should be compatible with the existing SQLite schema and local desktop deployment model.
- Any new SQLite fields must be additive and backward-compatible.

## 20. Validation rules
The Company Master should validate the following:
- Company Name is required.
- Business Type is required and must be one of the supported values.
- Address and contact details should not be empty when required by the deployment.
- GSTIN should be validated when present.
- FSSAI number should be validated when present.
- Email and phone should be checked for basic structure if present.
- Print settings must be valid for the selected document type.
- Paper size selection must support A4 Portrait and A2 Landscape.
- Empty print fields must not render as blank labels.

## 21. UI behavior
The Company Master UI should remain part of the existing desktop interface and should follow the current module structure.

Expected UI behavior:
- Appears in the existing master/settings area of the desktop app.
- Supports create, edit, save, and view actions.
- Shows clear validation messages for missing or invalid values.
- Offers print-related options such as document-wise paper size and default print profile where applicable.
- Displays company profile values clearly in the form and in preview contexts.
- Does not break the current navigation or module organization.

## 22. Audit log rules
- Company Master changes should be logged for traceability.
- The audit trail should capture:
  - changed fields
  - timestamp
  - user or session identity
  - action type such as create/update
- Audit logging must not break the desktop workflow or require a web backend.
- Audit log entries should be stored in the local SQLite environment or the existing audit mechanism if present.

## 23. Testing checklist
- Create a new Company Master record with required fields.
- Save and reopen the record.
- Verify that the company details appear in invoices and reports.
- Verify print preview shows the company name, address, GSTIN, FSSAI, and HSN only when available.
- Verify PDF export and bulk print behave correctly.
- Verify A4 Portrait and A2 Landscape output are both supported.
- Verify Distributor business type works with both paper sizes.
- Verify missing values hide gracefully without blank labels.
- Verify backup and restore preserve the company profile.
- Verify installer/update flow preserves the company profile and .prmlic license behavior.
- Verify UI, SQLite save/load, reports, printing, bulk print, backup/restore, installer/update, audit log, and tests all work together.

## 24. Done condition
Company Master is complete only when all of the following pass together:
- UI works correctly for Developer/Admin/Client access rules
- SQLite save/load works correctly
- Reports consume the saved company profile correctly
- Printing works for Sales Invoice, Purchase Invoice, Delivery Challan, Loading Sheet, Dispatch Summary, Credit Note, Debit Note, and Bulk Print
- Bulk print respects document-wise paper-size settings
- A4 Portrait and A2 Landscape both work
- Loading Sheet / Dispatch Summary displays GSTIN, HSN, and FSSAI when available and hides them gracefully when not available
- Backup/restore preserves the company profile
- Installer/update preserves the company profile and existing .prmlic license behavior
- Audit logging and regression tests pass

## 25. Future roadmap
- Add a dedicated Company Master screen if one is not yet fully surfaced in the current UI.
- Improve role-based editing rules for client/admin/developer access.
- Add more print layout profiles for different business types.
- Expand print presets for invoice, delivery challan, loading sheet, dispatch summary, and bulk print documents.
- Improve validation and audit coverage for company profile changes.
- Ensure the feature remains fully compatible with the current Python + SQLite desktop architecture and existing .prmlic licensing.
