# Company Settings Rules

## Product and client branding ownership

- The fixed desktop shell and login product area belong to PRM Software and
  must use `ProductBrandHeader` with the original PRM logo, **PRM BILLING
  INVENTORY** and **Way to future, Today**.
- Company Settings/Profile and Dashboard Company Information belong to the
  licensed client and use `ClientCompanyIdentityCard`.
- A client logo is aspect-ratio preserved in a protected 144x96 area. Missing
  client logos may use client initials only inside client-context components.
- Client document/report headers use client identity; the accepted shared PDF
  footer uses PRM Software attribution. Never use one ambiguous logo resolver
  for both ownership domains.

Administration → Company page rules

Editable by Business Owner (Admin):
- Company name/title
- Logo
- Phone
- Mobile
- Email
- Website
- Address
- City
- State
- PIN
- Country
- Contact person

Not editable by Business Owner (requires Developer/Admin/License):
- Business type
- Modules
- Subscription/edition
- License
- Machine binding
- Security settings
- Engine settings
- Developer settings

Single Source of Truth
- Company information for Developer Dashboard and Administration pages must reference the same `company` table and repository.
- Differences in Developer UI vs Admin UI must be permission-only (visibility/editability), not duplicate records.

Audit and Logging
- All edits must be recorded in an audit log capturing previous value, new value, timestamp, and user identity.
Implementation notes:
- Admin UI and business owner edits are restricted to a safe subset of fields (name, contact, address, logo, GST/FSSAI, invoice prefix).
- Developer Console continues to manage developer-only fields (license, subscription, business type, templates). Developer Console saves call `save_profile(..., developer=True)`.
- `CompanyProfileService.save_profile()` enforces allowed fields for non-developer saves, prunes unknown DB columns, and writes audit entries for changes using the existing company DB connection.
- The audit log is stored in the `company_profile_audit` table.
- UI: `SimpleMasterView` company form shows restricted fields as read-only with tooltip "Managed by Developer Dashboard". Developer Console allows full edits.
