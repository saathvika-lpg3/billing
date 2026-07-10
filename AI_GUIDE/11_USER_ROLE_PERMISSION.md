# User Role and Permission Specification

## 1. Purpose
This document defines the user roles and permission boundaries for PRM_GST_DESKTOP in its current Python + SQLite desktop form.

The goal is to keep the application secure, predictable, and compatible with the existing desktop workflow while preserving the current .prmlic licensing model.

## 2. Platform constraints
- Python + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve existing .prmlic licensing
- Preserve existing desktop UI and module structure
- Keep all permissions compatible with local desktop usage and local SQLite storage

## 3. Role summary

| Role | Purpose | Primary access |
|---|---|---|
| Developer | System setup, configuration, maintenance | Full technical access |
| Admin / Client Owner | Business administration and client-level control | Most operational access |
| Manager | Oversight and review | High-level operations and reports |
| Sales User | Sales document entry and related workflows | Sales modules |
| Purchase User | Purchase document entry and related workflows | Purchase modules |
| Inventory User | Stock movement and inventory operations | Inventory modules |
| Accounts User | Accounting and ledger workflows | Accounts modules |
| Report User | Reporting and document review | Report access |
| Read Only User | Review-only access | View-only access |

## 4. Developer
### Purpose
System configuration, installation safety, technical troubleshooting, and application maintenance.

### Access levels
- Full access to desktop application settings
- Access to developer/admin tools when allowed by the build and license context
- Access to system-level configuration and backup/restore workflows
- Ability to review logs and audit data

### Restricted areas
- Must not bypass .prmlic validation
- Must not disable license protection without proper authorization
- Must not expose insecure access paths for client users

### Company Master permissions
- Full create/edit/view access
- Can configure business type and license-sensitive fields
- Can update print preferences and defaults

### License-sensitive permissions
- Can review and troubleshoot license state
- Must not create a bypass for invalid or missing licenses

### Print-setting permissions
- Full access to print configuration and document-wise settings

### Backup/restore permissions
- Full backup and restore access if permitted by deployment policy

### Delete/edit/cancel permissions
- Can delete or cancel records only when this is part of the approved business workflow and backup safety rules

### Audit log requirements
- All critical changes must be logged
- Audit trail should capture user, time, and affected module

## 5. Admin / Client Owner
### Purpose
Business administration, company-level operational control, and day-to-day configuration for the installed client.

### Access levels
- High access to day-to-day business data
- Access to Company Master, print settings, and most master data
- Access to reports and key transactions

### Restricted areas
- Must not be able to bypass license checks
- Must not change system-level technical settings outside the permitted desktop UI scope
- Must not overwrite data without backup verification where required

### Company Master permissions
- Can edit company contact, address, and print-related settings when permitted by deployment
- Can manage business type-related configuration where appropriate
- Cannot override license-sensitive protections without Developer approval

### License-sensitive permissions
- Can view license state and related warnings
- Must not disable or bypass licensing restrictions

### Print-setting permissions
- Can choose per-document paper size and print preferences when allowed
- Must not hard-code A2-only or A4-only behavior

### Backup/restore permissions
- May perform backup operations
- Restore access should be limited and protected by confirmation steps

### Delete/edit/cancel permissions
- Can edit and cancel transactions within allowed business workflow rules
- Delete permissions should be limited to approved operations only

### Audit log requirements
- All major changes must be logged
- Audit trail must be visible or retrievable for review

## 6. Manager
### Purpose
Operational oversight, review, and approval of business workflows.

### Access levels
- Can view most business documents and reports
- Can review transactions and stock/account status
- May approve or review certain business actions if the workflow requires it

### Restricted areas
- Should not perform low-level system configuration
- Should not change license or installer settings
- Should not perform destructive restore actions

### Company Master permissions
- View-only or limited edit access depending on deployment

### License-sensitive permissions
- View-only access to license status

### Print-setting permissions
- No direct change to global print configuration unless explicitly permitted

### Backup/restore permissions
- No backup/restore access unless specifically granted

### Delete/edit/cancel permissions
- Limited edit/cancel permissions depending on workflow policy

### Audit log requirements
- Must be able to review audit-related activity relevant to their workflow

## 7. Sales User
### Purpose
Create and manage sales documents and related customer workflows.

### Access levels
- Access to sales invoice, sales document, delivery challan, and customer-related views
- Can create and save sales transactions
- Can use print preview and print/export for sales documents

### Restricted areas
- Should not access purchase, accounting setup, or developer tools
- Should not change company master or license settings
- Should not perform restore operations

### Company Master permissions
- View-only access to company identity fields if required
- No edit access unless explicitly allowed

### License-sensitive permissions
- No license-management access

### Print-setting permissions
- Can use available print options but should not change document-wide print policy unless permitted

### Backup/restore permissions
- No backup/restore access

### Delete/edit/cancel permissions
- Can edit or cancel only within the allowed sales workflow
- Must follow validation rules before saving

### Audit log requirements
- Sales changes should be logged for traceability

## 8. Purchase User
### Purpose
Create and manage purchase documents and supplier workflows.

### Access levels
- Access to purchase invoice, purchase documents, and supplier-facing workflows
- Can create and save purchase transactions

### Restricted areas
- Should not change sales or accounting configuration outside their scope
- Should not access developer tools or license settings

### Company Master permissions
- View-only access to company profile values when needed

### License-sensitive permissions
- No license-management access

### Print-setting permissions
- Can use print options for purchase documents but should not alter policy-level settings

### Backup/restore permissions
- No backup/restore access

### Delete/edit/cancel permissions
- Limited edit/cancel ability within the purchase workflow

### Audit log requirements
- Purchase entry changes should be logged

## 9. Inventory User
### Purpose
Manage stock entry, transfer, adjustments, and stock movement activities.

### Access levels
- Access to stock dashboards, stock entry, transfer, adjustment, and stock-out views
- Can update inventory movement records

### Restricted areas
- Should not access license or installer configuration
- Should not edit Company Master beyond allowed view-only needs

### Company Master permissions
- View-only access unless explicitly permitted

### License-sensitive permissions
- No license-management access

### Print-setting permissions
- Limited print access for inventory-related documents if applicable

### Backup/restore permissions
- No backup/restore access

### Delete/edit/cancel permissions
- Can edit or cancel inventory documents only within the supported workflow

### Audit log requirements
- Inventory changes should be logged for traceability

## 10. Accounts User
### Purpose
Handle account entries, ledger posting, receipts, payments, expenses, and journals.

### Access levels
- Access to accounting entry views and related financial workflows
- Can post accounting transactions and review ledger-related data

### Restricted areas
- Should not alter the license or installer model
- Should not edit Company Master except for view-only use if needed

### Company Master permissions
- View-only or limited access unless explicitly permitted

### License-sensitive permissions
- No license-management access

### Print-setting permissions
- May use print and PDF export for vouchers and related documents

### Backup/restore permissions
- No backup/restore access unless explicitly granted

### Delete/edit/cancel permissions
- Can edit or cancel within the accounting workflow if allowed
- Must follow validation and posting rules

### Audit log requirements
- Accounting changes must be logged

## 11. Report User
### Purpose
Run reports and review business data without editing transactions.

### Access levels
- Access to report center and summary data views
- Can review sales, purchase, stock, party ledger, GST summary, and GSTR-related data

### Restricted areas
- Should not edit transactions, Company Master, or license-related settings
- Should not perform restore or installer tasks

### Company Master permissions
- View-only access

### License-sensitive permissions
- No access to license controls

### Print-setting permissions
- May use report print/export functions if allowed

### Backup/restore permissions
- No backup/restore access

### Delete/edit/cancel permissions
- No delete/edit/cancel permissions

### Audit log requirements
- Report access should be logged where required by policy

## 12. Read Only User
### Purpose
Review business data without changing anything.

### Access levels
- Read-only access to selected modules and reports
- Can view transactions, masters, and reports as allowed

### Restricted areas
- No create/edit/cancel/delete access
- No print configuration changes
- No Company Master changes
- No backup/restore or license changes

### Company Master permissions
- View-only access

### License-sensitive permissions
- No access

### Print-setting permissions
- No access to change print settings

### Backup/restore permissions
- No access

### Delete/edit/cancel permissions
- None

### Audit log requirements
- Read activity should be logged where appropriate

## 13. Company Master permissions
Company Master should be protected by role-based rules:
- Developer: full access
- Admin / Client Owner: configurable edit access for company contact/address/print preference fields when allowed
- Manager: view-only or limited edit if explicitly permitted
- Other operational users: view-only or no access
- Read Only User: no edit access

## 14. License-sensitive permissions
These permissions must remain protected by the existing .prmlic model:
- changing license state
- bypassing license validation
- modifying installer or update behavior
- changing system-level activation state

These actions must stay with Developer or explicitly authorized admin workflows only.

## 15. Print-setting permissions
- Developer: full print-setting access
- Admin / Client Owner: can change document-wise paper size and print preference fields if allowed
- Manager: view-only or limited assistance-based access
- Sales/Purchase/Inventory/Accounts users: print usage access only, not policy-level configuration
- Report User and Read Only User: no configuration access

Locked rule:
- Print settings must support both A4 Portrait and A2 Landscape.
- Paper size must be saved per document type, not only globally.
- Loading Sheet / Dispatch Summary must show GSTIN, HSN, and FSSAI when available and hide them gracefully when not available.

## 16. Backup/restore permissions
- Developer: full backup/restore access when permitted by deployment policy
- Admin / Client Owner: backup access and limited restore access with confirmation
- Other roles: no backup/restore access

Restore actions must be protected by confirmation steps and should not silently overwrite current SQLite data.

## 17. Delete/edit/cancel permissions
- Delete actions should be limited and controlled
- Cancel actions should be allowed only for workflows that support them
- Edit actions should follow validation and business rules
- Sensitive edits such as Company Master, license-sensitive settings, and document print policy should require higher-level access

## 18. Audit log requirements
All user actions that affect business data or configuration should be logged.

Required audit details:
- user identity
- role
- action type
- timestamp
- impacted module or document
- affected record identifier where available

Audit logging must remain compatible with the current desktop + SQLite model and should not require a web backend.

## 19. SQLite storage expectations
- The application stays in the Python + SQLite desktop model.
- User roles and permissions should be stored in local SQLite data or a local configuration store as needed.
- No SQLite migration is required for this release.
- Any new SQLite fields must be additive and backward-compatible.

## 20. Testing checklist
- Verify each role can access the correct modules.
- Verify restricted modules are blocked for unauthorized roles.
- Verify Company Master access follows the role rules.
- Verify print-setting access follows the role rules.
- Verify backup/restore access is restricted to allowed roles.
- Verify delete/edit/cancel permissions follow workflow rules.
- Verify audit logs capture the expected action data.
- Verify the desktop UI remains usable with the defined role model.
- Verify .prmlic licensing remains intact and unaffected by role configuration.

## 21. Future roadmap
- Add a formal role configuration screen for the developer/admin workflow.
- Improve role-based access for specific document types and print policies.
- Expand audit visibility for high-risk operations.
- Keep all future role and permission work compatible with the current Python + SQLite desktop architecture and existing .prmlic licensing model.
