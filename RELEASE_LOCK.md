# PRM BILLING INVENTORY V1.0 Release Lock

## Release identity and authority

- Product: **PRM BILLING INVENTORY**
- Semantic/application/installer version: **1.0.0**
- User-facing display version: **V1.0**
- Release name: **PRM BILLING INVENTORY V1.0**
- Release date: **2026-07-12**
- Release Git commit: **the commit referenced by annotated tag `v1.0.0`**
  (resolve the immutable full SHA with `git rev-list -n 1 v1.0.0`)
- Annotated release tag: **v1.0.0**
- Publisher: **PRM Software Solutions**
- Supported platform: Windows 10/11 x64-compatible desktop
- Stack: Python 3.13, PyQt6, SQLite, ReportLab, PyInstaller and Inno Setup

This file is the authoritative non-regression contract for the official V1.0
baseline. Historical 1.7.x installer identifiers are internal pre-release
evidence; they remain in history and migration records but are not current
product versions.

## Versioning and compatibility policy

Active product code imports the one authoritative version module. Technical
metadata uses `1.0.0`; compact user-facing surfaces use `V1.0`. The stable
installed executable name, Inno `AppId`, application directory and shortcut
identity remain unchanged so an existing 1.7.8 internal pre-release installation
upgrades in place.

Database schema versions, migration ordering, backup format versions, GST API
payload versions and `.prmlic` format dates are compatibility identifiers. They
must not be reset or relabelled merely to match the product version. Historical
release notes and certification hashes must remain accurate.

## Database and licensing lock

- SQLite remains the offline-first Version 1 database.
- Existing database files are never overwritten during upgrade or uninstall.
- Schema changes must be additive/migrated, ordered and backward compatible.
- The installer may include only the sanitized, unbound first-install seed; it
  must never include a production database or client rows.
- Every client may provide a separately named valid `.prmlic` through the
  installer Browse page. Runtime normalization to `license/client.prmlic` is a
  stable internal path, not a one-client binding.
- Licence, activation, plan, expiry, machine binding, super-admin and developer
  access checks remain enforced. No release or test may bypass validation.

## Installer and upgrade lock

The official setup identity is PRM BILLING INVENTORY 1.0.0 by PRM Software
Solutions, with the PRM application/setup/uninstall icon. The stable `AppId`,
installed executable name and install directory are immutable without an
explicit compatibility migration.

The `[InstallDelete]` section is an exact allowlist of seven obsolete frozen
runtime paths and must contain no additional target:

1. `_internal\numpy`
2. `_internal\numpy.libs`
3. `_internal\numpy-*.dist-info`
4. `_internal\lxml`
5. `_internal\lxml-*.dist-info`
6. `_internal\docs`
7. `_internal\requirements.txt`

This list removes only known immutable/rebuildable residue from internal
pre-release upgrades. It must never target database, licence, settings, uploads,
company logo, templates, print settings, SMTP settings, communication logs,
documents, reports, archives or backups. Clean install, 1.7.8-to-V1.0 upgrade,
preserving uninstall and installed launch are mandatory release gates.

## Product and client branding lock

- The fixed shell, login product header, executable/window icon, installer and
  shared product footer are owned only by PRM BILLING INVENTORY.
- Client name, initials and logo appear only in licensed-company/business
  contexts such as Dashboard Company Information, Company Profile and client
  document headers.
- A client identity must never replace the PRM product identity in the fixed
  application header.

## UI layout and framework lock

- The modern shared ERP theme and responsive shell are retained.
- Every live route must fit 1366x768, 1440x900 and 1920x1080 without a page-level
  horizontal scrollbar, overlapping controls or clipped labels.
- Master entry uses the accepted shared master/page-header/compact-action
  framework. List/browse pages use the horizontal or compact wrapped action
  toolbar, not a tall right-side action stack.
- Sales Bill, Buy Stock/Purchase Entry and related documents retain the accepted
  shared transaction header, line grid, action bar and totals panel.
- Grand Total remains visible in the initial viewport, bold, high-contrast and
  consistent with saved and printed values.
- Buttons retain hover, pressed, focus, disabled, busy and success/failure
  feedback. Enabled visible actions must be wired and must not fail silently.

## Keyboard, focus and smart-dropdown lock

- The first mandatory field receives initial focus where applicable.
- Enter advances through the logical entry sequence; Shift+Enter reverses where
  the framework supports it; Esc closes/cancels/goes back safely.
- Ctrl+S, Ctrl+N, Ctrl+F and Ctrl+P retain their defined shared behavior.
- F4 Add Row, F8 Save, F9 Preview, F10 Print and Delete retain page-specific
  behavior where shown in help/tooltips.
- Editable dropdowns use case-insensitive incremental contains filtering,
  arrow-key navigation, Enter acceptance and Esc popup cancellation. Invalid
  custom text cannot silently persist in controlled-value fields.
- Shortcut help remains visible in tooltips or page guidance.

## Navigation lock

Top ribbon, sidebar, Dashboard, module hubs, Ctrl+K Global Search, Report Center
and Document Center must resolve to their canonical live routes with the same
role/plan filtering. Dispatch Summary has one canonical destination:
`reports:daily_dispatch_summary`, selecting `daily_dispatch_summary` in Report
Center. No duplicate or fallback implementation may replace it.

## Transaction and posting lock

Accepted Sales, Purchase, Inventory, Receipt, Payment, Expense, Journal, Contra,
Return and Transfer saves remain atomic. A failed validation must leave no
partial header, item, stock, GST, voucher, ledger or party-balance mutation.

- Debit equals credit for every active posting.
- Editing reverses/supersedes the previous effects and creates no duplicate
  active posting.
- Cancellation/reversal preserves audit history and safely restores stock,
  party outstanding, GST and ledgers.
- Stock movement matches its source transaction and transfer-out equals
  transfer-in.
- Reports derive from live active postings; no hard-coded totals may be used.
- Saved, displayed and printed Grand Total values must reconcile.

## GST lock

GST resolution remains item -> HSN/tax code -> category default -> zero only
when no configured tax applies. Product/party state and Place of Supply determine
CGST+SGST versus IGST. Discounts, returns, free quantity and round-off retain the
accepted calculation and posting behavior. Active GST Summary and HSN Summary
must reconcile to source transactions and exclude cancelled/superseded rows.

## Print, PDF and report lock

Distributor/Wholesale output supports A4 Portrait, A4 Landscape, A2 Portrait
and A2 Landscape. The selected paper/orientation applies consistently to
Preview, Print, PDF, reprint, bulk print and communication attachments.

The canonical document structure is locked: safe non-zero margins, printable
area, client/company header, repeated item headings, continuation header/footer,
GST summary, amount in words, terms, bank details, signature, page numbering and
final-page totals. Rows must not clip and blank/excess continuation pages must
not be introduced.

List-page output must use the matching document family. Sales Invoice, Sales
Order, Quotation, Delivery Challan, Purchase, Purchase Order, Goods Receipt,
Returns, Receipt, Payment, Loading Sheet and Dispatch Summary must not be
replaced by unrelated or generic templates. Profit & Loss retains the accepted
Tally-style presentation; Balance Sheet retains the accepted two-sided
Tally-style presentation with correct continuation pages.

## Email and WhatsApp communication lock

SMTP sends the actual generated PDF attachment. Outlook/MAPI handoff attempts an
attachment when supported. A `mailto:` fallback must explicitly state that the
protocol cannot attach files, keep the PDF path available and never claim that
an attachment was sent. WhatsApp uses the generated document and native Windows
handoff; it must not add a PowerShell runtime dependency or report false
delivery success.

## Regression gate

A release candidate is rejected unless all of the following pass from the
release commit:

- Python compile/import gate and complete pytest suite;
- live route/layout/wiring audit at all three supported resolutions;
- master, transaction, inventory, accounts, GST and integrity lifecycles;
- keyboard/focus, smart dropdown, Grand Total and navigation regressions;
- A4/A2 portrait/landscape, multi-page, statement and document-mapping tests;
- email attachment/fallback tests;
- installer privacy/packaging checks and exact seven-rule deletion allowlist;
- clean install, real pre-release upgrade with byte-preserved client data and
  installed frozen-application launch.

Physical printer output, real SMTP credentials, a logged-in WhatsApp session
and government GST credentials are external acceptance gates and must be
reported separately, never disguised as code passes.

## Change-control process

No future change may alter an accepted locked behavior without:

1. naming the impacted section of this release lock;
2. documenting the business reason and compatibility impact;
3. creating a source/data-safe checkpoint;
4. adding or updating regression coverage before or with the implementation;
5. running affected focused gates and the complete suite;
6. visually verifying affected UI/print output;
7. updating this file and `CHANGELOG.md`;
8. preserving backward compatibility or supplying a tested migration; and
9. obtaining explicit approval for any accepted-format or workflow change.

Code is not preserved merely because a class or function still exists: the live
application must still navigate to and use it.

## Rollback procedure

1. Stop the application and hash/copy the client database, licence, settings,
   uploads and print configuration to a protected location.
2. Preserve logs needed to diagnose the failed release without packaging or
   publishing client data.
3. Reinstall the last certified compatible binaries using the unchanged AppId;
   never replace the existing client database with an installer seed.
4. If a migration was applied, use its documented backward procedure or restore
   the verified pre-upgrade data backup. Never fabricate balancing data.
5. Launch at login, run SQLite integrity/licence checks and execute the critical
   Sales/Purchase/Accounts/print smoke before returning the workstation.
6. Record the rollback reason, artifact hashes and follow-up correction in the
   changelog and release validation record.
