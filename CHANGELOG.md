# Changelog

## 2026-07-12 - official PRM BILLING INVENTORY V1.0 release lock

- Established one authoritative product identity: semantic/runtime/installer
  version `1.0.0`, compact display `V1.0`, release name
  **PRM BILLING INVENTORY V1.0** and annotated release tag `v1.0.0`.
- Added `RELEASE_LOCK.md` as the permanent non-regression contract for accepted
  UI, master/transaction/list frameworks, keyboard/smart-dropdown behavior,
  GST/stock/account posting, Grand Total, branding, navigation, printing,
  reports, communication and installer data safety.
- Added runtime identity to Qt, the fixed product header, login/window title,
  Dashboard Application Version, Developer Console and diagnostics without
  resetting database schema/migration or protocol versions.
- Updated the stable-AppId installer to official V1.0 metadata and a versioned
  setup filename while preserving the stable installed executable/path and the
  exact seven-entry upgrade-residue cleanup allowlist.
- Added Windows version metadata for the frozen executable and setup. The
  internal 1.7.8 installer correction below remains historical upgrade evidence
  and is superseded as current product identity by official V1.0.
- Locked the product-owned sanitized installer seed so builds do not read or
  package the workstation's runtime/client database.

## 2026-07-12 - installer 1.7.8 stale-runtime upgrade correction

- Reproduced the user-reported native dialog titled **Unhandled exception in
  script** after upgrading the real 1.7.6 installation to optimized 1.7.7.
  The captured traceback ended in `openpyxl.compat.numbers` with
  `AttributeError: module 'numpy' has no attribute 'short'`.
- Root cause: Inno Setup replaces packaged files but does not automatically
  remove files omitted by a newer payload. Old partial `numpy`/`lxml` trees,
  documentation and the legacy requirements file therefore remained in the
  upgraded `_internal` directory even though the 1.7.7 clean payload excluded
  them. `openpyxl` discovered the stale `numpy` before application logging.
- Added a narrowly scoped `[InstallDelete]` upgrade list for the proven obsolete
  runtime paths and bumped setup to 1.7.8. Client database, licence, uploads,
  settings, templates and generated documents are outside this list.
- Real 1.7.7-to-1.7.8 upgrade removed every stale path while preserving the
  database and licence byte-for-byte. The same hidden diagnostic then opened
  `PRM BILLING INVENTORY Login`, remained responsive and produced empty stderr.
- Authenticated installed-resource smoke passed with SQLite integrity, product
  two-pack persistence, Sales/Purchase Grand Totals, themes, PRM/client branding
  separation and canonical Dispatch Summary.

## 2026-07-12 - Product/client branding correction and certified installer 1.7.7

- Replaced the licensed-client widget in the fixed desktop header with an
  explicit PRM-owned `ProductBrandHeader`, using the original PRM logo, product
  name and tagline. Restored the same product ownership to the login header and
  application icon path.
- Introduced an explicit `ClientCompanyIdentityCard` contract for Dashboard
  Company Information, Company Settings/Profile and other client-context
  surfaces. Client logos preserve aspect ratio, use a bounded identity area and
  fall back to client initials only when no client logo resolves.
- Prevented generic page-width fitting from rewriting protected brand/logo
  geometry, which had compressed the client logo into a narrow vertical mark.
- Split document branding resolution into client-company header identity and
  PRM product-footer identity. Client profile paths no longer fall back to a
  same-named product asset.
- Added one permission-aware Dispatch Summary route,
  `reports:daily_dispatch_summary`, backed by the existing Report Center
  `daily_dispatch_summary` report. Added the same destination to the daily-work
  sidebar, Dashboard quick action, Reports operations and Global Search aliases.
- Added route-aware sidebar state, keyboard-capable navigation buttons and
  filtered report/search destinations so hidden report permissions cannot be
  bypassed through a direct shortcut.
- Bumped installer source version to 1.7.7, added PRM setup/uninstall icons,
  split runtime and development dependency manifests, and removed runtime
  documentation from the frozen package definition.
- Added focused branding-ownership, Dispatch-navigation and installed-UI smoke
  coverage plus multi-resolution branding/document capture tooling.
- Certified the final 1.7.7 candidate: 220-test full suite, 59-route
  multi-resolution audit, renamed-license clean install, frozen startup,
  authenticated installed-resource smoke, byte-identical upgrade, preserving
  uninstall and real local upgrade all passed. The optimized setup is
  43,193,577 bytes, SHA-256
  `E4ADC9CCCF76E2E1C38ACD042F42C6C9FF44A20329DC5E353A3EA8B83A6EE54C`.
- Completed classified workspace cleanup. Possible client print/report output
  and the legacy delivery bundle were quarantined; generated builds, caches,
  logs, test installs and the rebuildable virtual environment were removed.
  Database, licences, uploads, settings, source, assets, templates, backups and
  release evidence were retained.

## 2026-07-12 - Production stabilization and installer 1.7.6

- Added reusable client branding with aspect-ratio-preserving logo/initials,
  company identity and regulatory/contact details across Login, Dashboard,
  shell, Company Settings and every shared PDF header.
- Replaced the false Product pack-unit consistency rejection with validated,
  atomic purchase-to-sale UOM conversion synchronization. Added an explicit
  factor field and regression coverage for single UOM, Multi-UOM, Pack
  Conversion, prices, packs and rollback behavior.
- Standardized Customer, Supplier and Product master grouping, widths,
  shortcuts and searchable editable combo boxes. The shared smart-combo
  behavior supports contains filtering, arrows, Enter, Escape and mouse use.
- Completed GST precedence and place-of-supply propagation across sales,
  purchase, orders, quotations, delivery challans and returns.
- Implemented real PDF attachments for SMTP, Outlook and Windows Simple MAPI;
  added report/statement/dispatch email actions and retained `mailto:` only as
  a clearly limited manual fallback.
- Removed the client-runtime PowerShell WhatsApp helper in favor of native
  Windows attachment handoff. Developer-only build scripts remain outside the
  packaged runtime dependency chain.
- Routed Product, Customer, Supplier and remaining generic master lists through
  the professional report renderer. Dispatch/loading reports no longer total
  ID columns.
- Preserved and revalidated the locked A4/A2 portrait/landscape print engine,
  multi-page headers/footers, GST/Grand Total continuation, Tally-style Profit
  & Loss and Balance Sheet, and receipt/payment voucher formatting.
- Improved hidden-route relayout and transaction deck sizing so totals remain
  visible at 1366x768 while smaller viewports remain safely scrollable.
- Added company-branding, product-conversion, GST-flow, email-attachment,
  dispatch-total and smart-combo regressions. Final source gate: 59/59 live UI
  routes, 35-file widget audit with zero findings, eight performance checks and
  **213 tests passed**.
- Bumped the installer to 1.7.6. Interactive setup accepts any valid client
  `.prmlic` filename and installs it under the canonical internal name without
  overwriting the client's database during upgrade.

## 2026-07-11 - Commercial UI stabilization and installer 1.7.5

- Rebuilt Product Master into responsive business sections and a professional
  package grid; added Copy, Import, Export, Duplicate Pack and reliable
  New/Save/Refresh behavior.
- Fixed the Product save crash caused by calling QLineEdit APIs on QComboBox,
  introduced shared typed widget value access, and preserved distinct sale and
  purchase UoMs through repository persistence.
- Standardized Sales Bill and Purchase Entry on the shared transaction entry
  framework and corrected responsive page-height reuse across route/resolution
  changes.
- Made Grand Total the strongest, high-contrast totals value and guaranteed its
  initial-viewport visibility at 1366x768.
- Replaced narrow vertical/cramped action regions across shared masters, lists,
  reports, search, imports, labels and document center with a wrapping
  horizontal action toolbar.
- Added global button state styling and no-dead-action feedback behavior.
- Added live route, typed widget API, installer UI and performance evidence plus
  permanent Product, toolbar, totals, screen-fit and packaging regressions.
- Repaired the legacy MySQL-to-SQLite utility's duplicate parameter and wrong
  connector roles discovered by the application-wide compile audit.
- Removed development audit/test output from client packaging, bumped Inno to
  1.7.5 and certified build, install, startup, installed UI save/open flows and
  uninstall data preservation. Full suite: 190 passed.
- Removed the client license key from startup logs, added a permanent disclosure
  regression, and made seed preparation, PyInstaller and Inno Setup fail fast on
  non-zero exits or stale build outputs.

## 2026-07-11 - License-safe desktop installer 1.7.4

- Replaced direct packaging of the activated developer database with a
  deterministic, sanitized and integrity-checked first-install SQLite seed.
- Preserved existing client databases across upgrades/uninstall cleanup.
- Preserved mandatory `.prmlic`, signed/legacy validation and machine binding;
  expanded installer preflight to all required client fields.
- Made PyInstaller/build paths portable and selected a runtime with PyInstaller.
- Removed runtime upload data and obsolete `pysqlite` packaging input.
- Added installer seed, activation, foreign-machine blocking and packaging
  regression tests.
- Verified a real installation and first launch with the supplied client license.

## 2026-07-11

### ERP Business-Flow Audit And Lifecycle Reconciliation

- Added atomic Sales/Purchase/Return/Account/Inventory validation, unique
  document numbers, locked-year protection and negative-stock rollback.
- Added correct free-quantity stock semantics, party outstanding updates,
  balanced positive/negative round-off postings and accurate voucher totals.
- Added Sales/Purchase edit with retained superseded posting history and live
  list-to-edit navigation.
- Added reason-required cancellation/reversal for Sales, Purchase, both return
  types, Receipt, Payment, Expense, Journal/Contra and Stock Transfer.
- Fixed selected Sales/Purchase warehouse IDs so warehouse stock follows the
  live screen selection.
- Added active date-filtered Sales/Purchase Registers and Day Book; excluded
  cancelled/superseded financial and GST rows; added HSN Summary; rewired Stock
  Postings to `stock_log`; and made GSTR-9 Annual derive from GST postings.
- Added query indexes for active ledger/GST/voucher/stock/document report paths
  with logged migration failures instead of silent suppression.
- Added a read-only 12-check business-flow auditor, deterministic lifecycle
  tests, `docs/BUSINESS_FLOW_MATRIX.md`, and a workspace-local pytest temp path.
- Preserved the first tranche in local checkpoint commit `acfb396`.

## 2026-07-10

### GitHub Baseline And ERP Audit Cycle

- Created and pushed the first production baseline commit:
  `8833190 Initial production-ready PRM GST Desktop baseline`.
- Created and pushed the release tag `v1.0.0-production-baseline`.
- Verified the remote branch and tag resolve to the same baseline source state
  and that no generated/runtime/customer-sensitive paths were committed.
- Repaired the schema audit tool to use Python stdlib SQLite instead of a
  hard-coded legacy executable path.
- Regenerated desktop coverage, operation parity and SQLite schema audit
  documents.
- Added regression coverage for the portable schema audit and the accepted
  `ERP Profit & Loss` / `Profit & Loss` operation alias.

### Git Repair And Print Engine Lock

- Created source-only backup before Git repair:
  `backups/source_only_pre_git_repair_20260710_130613.zip`.
- Diagnosed `.git` as an empty invalid directory, preserved it as
  `.git_invalid_backup_20260710_130706`, and repaired the live repository as a
  valid local `main` branch with origin set to
  `https://github.com/saathvika-lpg3/billing.git`.
- Cloned the official GitHub repository into a separate comparison folder and
  confirmed the remote currently has no commits/tracked files, so no live
  source was overwritten from GitHub.
- Added `.gitignore` for Python caches, build/install output, generated
  PDFs/screenshots/reports, local backups, logs, databases, uploads, license
  files, sessions/cookies and secrets.
- Added persisted print-template orientation support, including the SQLite
  migration, Developer Console selector, shared resolver query support and
  regression tests.
- Locked the canonical transaction renderer across A4 Portrait, A4 Landscape,
  A2 Portrait and A2 Landscape without forcing Distributor/Wholesale to A4.
- Added structural tests for unchanged canonical transaction sections,
  continuation headers, repeated item headings, footer/final totals/GST summary,
  statement renderers and receipt/payment voucher identity.
- Generated validation artifacts under
  `output/pdf/print_engine_lock_20260710_130706/` and verified the full
  160-test regression suite.

### Locked Reference Print And Statement Validation

- Found the locked reference files in Downloads and rendered reference, before
  and after PNG evidence under `output/pdf/reference_validation_20260710/`.
- Added shared `write_statement_pdf()` for Profit & Loss and Balance Sheet so
  accounting statements print/export as A4 portrait two-sided reports instead
  of generic landscape tables.
- Routed Report Center Profit & Loss and Balance Sheet print/PDF export through
  the shared statement renderer while leaving statement business logic in
  `MySqlSource` unchanged.
- Added receipt/payment voucher reference and instrument metadata to the shared
  voucher PDF layout.
- Added regression locks for required report paper/orientation matrix,
  two-sided statement layout, removal of generic statement report headers, and
  receipt/payment voucher identity.
- Regenerated live-after PDFs/renders for Sales Invoice, Sales Order,
  Quotation, Purchase, Receipt, Payment, Profit & Loss and Balance Sheet.
- Verified focused locks, broader print/report UI tests and the full 159-test
  regression suite.

### Production Readiness Route And Print Audit

- Fixed print-preview paper/orientation detection for large generated PDFs by
  stream-scanning for `/MediaBox` with bounded memory. This prevents A2
  landscape reports from being shown as A4 portrait when the MediaBox appears
  late in the PDF.
- Added regression coverage for preview detection of generated A4 portrait and
  A2 landscape report PDFs.
- Added regression coverage for Report Center Profit & Loss and Balance Sheet
  print-preview handoff. Both statement reports now must generate a non-empty
  PDF and invoke the shared preview layer.
- Added deterministic print metadata fallbacks for known transaction and
  voucher document types in the shared print resolver so Document Center
  reprint/bulk mappings cannot resolve to a blank template key.
- Added regression coverage for Document Center print metadata, all Document
  Center subviews and Module Hub internal operation states.
- Added regression protection for the hidden Report Center Account Closing / CA
  Export panel and for visible button click-receiver wiring across all
  registered live pages.
- Fixed the Report Center Account Closing hidden-state layout so the CA Export
  row expands the filter card instead of being covered by the report table.
- Created source-only production-readiness backup at
  `backups/production_readiness_source_20260710_093457.zip`.
- Audited the live `MainWindow.page_factories` registry: 59 routes opened
  successfully at 1366x768, with no page-level horizontal scrollbar during the
  route sweep.
- Recorded the 18 live transaction routes using the shared transaction
  framework and confirmed the current Report Center routes for Profit & Loss
  and Balance Sheet.
- Added documentation for current print/report mapping evidence, A2/A4 paper
  coverage, voucher/report PDF coverage and remaining external blockers.
- Captured production-readiness screenshots for Report Center, Quotation,
  Receipt Entry and Payment Entry.
- Verified py_compile, focused continuation tests, print/report parity tests,
  the focused UI route/layout suite and the full 156-test regression suite
  after the print-mapping, hidden-state, accounting-preview and preview-detector
  continuations.
- No application code or business behavior was changed in this continuation.

### Production Acceptance Safety Stabilization

- Created source-only pre-acceptance backup at
  `backups/pre_acceptance_source_20260710_082242.zip`.
- Hardened communication logs so new rows store masked recipients, no message
  body and filename-only attachment references.
- Masked historical communication recipients in dashboard and Developer Console
  displays.
- Added Windows DPAPI protection and read-time migration for saved SMTP
  passwords in `app_settings`.
- Kept transaction posting, PDF generation, GST/tax, stock, ledger, numbering,
  templates and communication handoff behavior intact.
- Verified focused safety tests, communication/share tests, UI tests and the
  full 149-test regression suite.

### Communication Delivery Diagnostics Continuation

- Added `EmailDeliveryService.test_connection()` for shared SMTP
  connection/authentication diagnostics without sending a business document.
- Added `whatsapp_readiness()` for safe WhatsApp phone/link validation without
  opening the browser or attaching PDFs.
- Added Developer Console Communication > Delivery Diagnostics controls for
  Test SMTP and Check WhatsApp Link.
- Captured
  `screenshots/after_communication_delivery_diagnostics_1366x768_20260710.png`.
- Verified focused diagnostics tests and the full 149-test regression suite.

### Communication Contact Preview Continuation

- Added SQLite-backed preferred contact-field storage for communication
  templates by channel/document type.
- Added Developer Console Message Templates controls for preferred contact
  source, sample context values, inline rendered preview and resolved-contact
  confirmation.
- Updated communication-template tests and Developer Console UI tests.
- Captured
  `screenshots/after_communication_contact_preview_1366x768_20260710.png`.
- Verified focused suites and the full 148-test regression suite.

### Live Communication Template Wiring Continuation

- Added shared `communication_message()` and `document_message_context()`
  helpers so live Email/WhatsApp actions render active templates with safe
  fallback subject/body text.
- Wired Sales Bill, Purchase/Goods Receipt, sales/purchase documents,
  receipt/payment/account vouchers, inventory, stock out, dispatch return and
  route settlement output actions through the shared template path.
- Expanded default templates for purchase invoice, quotation, sales order,
  sales invoice WhatsApp and receipt WhatsApp scenarios.
- Preserved existing PDF generation, posting, GST/tax, stock, ledger,
  numbering and delivery handoff behavior.
- Verified focused suites and the full 148-test regression suite.

### Communication Templates Continuation

- Added `CommunicationTemplateService` with SQLite-backed message templates,
  default template seeding, safe placeholder rendering and contact-resolution
  helpers.
- Added Developer Console Communication sub-tabs for Delivery and Message
  Templates.
- Seeded default sales invoice, receipt, purchase order and payment reminder
  templates without changing live transaction send behavior.
- Added focused service/UI tests and captured
  `screenshots/after_communication_templates_1366x768_20260710.png`.
- Verified focused suites and the full 147-test regression suite.

### Dashboard Communication Status Continuation

- Added Executive Dashboard `Communication Status` and `Failed Communications`
  cards using the existing shared dashboard card/table widgets.
- Added dashboard service communication metrics for mode, sent-today count,
  failed count, pending retry count, recent history and failed retry rows.
- Fed failed communication rows into Critical Alerts and Daily Tasks while
  keeping retry execution in Developer Console.
- Added focused service/UI tests and captured
  `screenshots/after_dashboard_communication_cards_1366x768_20260710.png`.
- Verified focused suites and the full 146-test regression suite.

### Communication Log And Retry Continuation

- Added shared `CommunicationLogService` with SQLite delivery history, pending
  retry reads and bounded failed-email retry execution.
- Extended SMTP configuration to read from local `app_settings` rows, with
  environment variables still taking precedence.
- Updated transaction email actions to pass the active SQLite path into the
  shared email helper so SMTP, handoff and failure results are recorded.
- Added Developer Console `Communication` tab for SMTP settings, pending email
  retries, recent communication history and manual retry.
- Added focused communication tests and a Developer Console UI guard; full
  regression suite passed with 145 tests.
- Captured `screenshots/after_communication_admin_1366x768_20260710.png`.

### SMTP Email Automation Continuation

- Added `services/email_service.py` with opt-in SMTP delivery for PDF email
  attachments.
- Updated `prepare_email_document()` so all existing Email actions use SMTP
  when `PRM_EMAIL_DELIVERY_MODE=smtp` is configured, otherwise they keep the
  safe mail-client handoff behavior.
- Added regression tests for SMTP attachment creation and SMTP-disabled
  fallback behavior.
- Verified focused email/share tests, output action fit tests, focused UI tests
  and the full regression suite.

### Output Actions And Email Continuation

- Added shared email handoff helpers that open the operator's default email
  client with recipient, subject, message body and PDF path.
- Wired Email actions on Sales Bill, Purchase/Goods Receipt, account vouchers
  and sales/purchase document screens through the existing PDF creation flows.
- Added report-style PDF Preview/Print/PDF/WhatsApp/Email output for Stock
  Entry, Stock Transfer, Stock Adjustment, Stock Out / Load Challan, Dispatch
  Return and Route Settlement using the existing report PDF and share services.
- Removed the remaining placeholder output action wiring from `views`; static
  audit found no remaining `Preview`, `Print`, `PDF`, `WhatsApp`, `Email` or
  `lambda: None` placeholders.
- Added focused tests for email URL encoding and report-PDF output actions;
  target fit, focused UI and full regression suites passed.
- Captured fresh 1366x768 screenshots for Stock Entry, Stock Out, Dispatch
  Return and Route Settlement.

## 2026-07-09

### Pending Action Wiring Continuation

- Replaced safe no-op Preview actions on Sales Bill, Purchase Entry and
  receipt/payment-style account entries with their existing print-preview PDF
  flows.
- Added shared PDF preview/PDF/WhatsApp output for Quotation, Sales Order,
  Delivery Challan, Sales Return, Purchase Order and Purchase Return using the
  existing print/share services.
- Hardened `ERPToolbar` and `TransactionPageLayout` so generic toolbars and
  direct page-local buttons get the same click feedback and friendly
  not-available handling as transaction toolbars.
- Added regression coverage for generic toolbar feedback, direct local-button
  feedback, and sales-document PDF preview creation.
- Captured fresh 1366x768 screenshots for Quotation, Sales Bill, Purchase
  Entry and Receipt Entry; target fit, focused UI and full regression suites
  passed.

### Button Feedback, Wiring And Totals Stabilization

- Added shared button feedback helpers for hover/pressed/focus/recent-click and
  short busy states, then applied them through the shared ERP toolbar,
  transaction toolbar, grid action bar, dashboard cards and main-window page
  creation.
- Changed shared transaction toolbar and grid action behavior so unsupported
  actions are clickable and show a friendly not-available message instead of
  appearing dead or silently doing nothing.
- Added reusable `TransactionTotalsPanel` and `TransactionTaxSummaryPanel`
  components and applied them to Sales Bill, Purchase/Goods Receipt, Quotation,
  Sales Order, Delivery Challan, Purchase Order and inherited sales/purchase
  document pages.
- Grand Total, Total Quantity, Discount, Taxable Amount, CGST, SGST, IGST,
  Total Tax, Round Off and Total Amount now update from the existing
  `SalesCalculator` totals without changing business logic.
- Reduced repeated page-switch feedback scanning so button feedback is installed
  when the shell/page is created rather than on every page open.
- Added regression tests for button feedback, toolbar wiring, transaction
  totals updates, return empty totals and core page-open performance smoke.
- Captured new 1366x768 screenshots for button feedback and totals on Sales
  Bill, Purchase/Goods Receipt and Quotation.

### Responsive Reference Completion

- Replaced the final one-line sales-document totals strip with shared
  `RemarksTermsCard`, `TotalsCard`, and `TaxSummaryCard` panels that mirror the
  approved Quotation reference while keeping all GST and save logic unchanged.
- Added a real tax-summary empty state (`No data available`) and grouped
  CGST/SGST/IGST rows from the existing `SalesCalculator` line output.
- Reduced the remaining sales-document Notes control plus Receipt/Payment
  narration controls by about 30%, tightening the label-to-control gaps without
  hiding required fields.
- Captured refreshed 1366x768, 1440x900, and 1920x1080 screenshots for
  Quotation, Receipt Entry, and Payment Entry, plus a scrolled 1366x768
  Quotation footer capture.
- Verified quotation Add Row/F4/Delete/Save, receipt save/print-preview, and
  payment save/print-preview with a safe operator walkthrough; all-route fit,
  focused UI, and full regression tests passed.

### Reference Image Alignment Pass

- Aligned the desktop shell toward the supplied Quotation Entry reference image:
  white brand/search top bar, responsive financial-year/branch/user info blocks,
  active dark-blue ribbon state, and tighter PRM sidebar.
- Reworked the shared sales-document header into Customer Information, Other
  Details, and Additional Information cards.
- Added reference-style grid action coloring in both light and dark themes.
- Preserved the approved responsive shell search-width contract after test
  feedback.
- Captured before/after Quotation screenshots and verified 31 focused UI tests
  plus the 129-test full suite.

### Transaction Grid Stretch-Lock Cleanup

- Re-ran the application layout-lock scan and removed remaining local
  transaction-grid stretch locks from sales, purchase, inventory, stock-out,
  dispatch-return, route-settlement and account recent-entry tables.
- Added practical interactive item-grid widths so wide transaction tables keep
  overflow inside the grid and preserve readable item/description columns.
- Captured fresh 1366x768 screenshots for the edited transaction/account pages.
- Verified the five-size all-route fit matrix, 31 focused UI tests and the
  129-test full suite.

### Native 125% DPI Table Fit Continuation

- Captured native Qt 125% physical screenshots for Dashboard, Receipt, Payment,
  Sales Bill, Purchase Entry, Reports, Document Center, Stock Dashboard and
  Administration at 1366x768 output pixels.
- Updated shared table fitting so DPI-scaled stacked pages still get readable
  table headers, internal table scrolling and full-width non-transaction
  tables.
- Relaxed the dashboard mini-table horizontal-scroll lock.
- Verified the five-size all-route fit matrix, 31 focused UI tests and the
  129-test full suite.

### Windows DPI Scaling Certification

- Relaxed the shell minimum from 980x620 to 900x500 logical pixels.
- Added responsive low-width sidebar bands and wrapping shared ERP toolbars.
- Converted Sales Bill and Purchase Entry summary/action areas to compact
  two-row layouts without removing GST totals or workflow actions.
- Wrapped return guidance and removed narrow-table stretch overrides from Stock
  Dashboard and module hubs.
- Expanded all-route validation to 125% and 150% Windows scaling workspaces.
- Captured Qt-native 150% screenshots at approximately 1366x768 physical
  pixels; 31 focused and 129 full-suite tests passed.

### Responsive Table And Clipping Certification

- Added all-route regression checks for clipped label/button text, table-header
  clipping, unused table viewport width and hidden internal table scrollbars.
- Added compact-screen coverage for Sales Bill and Product Master secondary
  dialogs.
- Updated shared page fitting to size table headers after the page is visible,
  distribute spare width across normal data columns and show an internal
  horizontal scrollbar for wide tables.
- Corrected Financial Years header truncation and unused table width, plus
  Numbering Series internal scrollbar visibility.
- Verified 31 focused UI tests and 129 full-suite tests.

### Responsive Layout All-Route Certification

- Expanded the target-resolution regression from 12 representative pages to
  all 59 page factories registered by the application.
- Made route coverage registry-driven so newly registered pages cannot silently
  bypass fit checks.
- Verified all registered pages at 1366x768, 1440x900 and 1920x1080 with no
  page-level horizontal overflow or shared field-label/control overlap.
- Confirmed the compact note-control and Receipt/Payment layout work remains
  valid; no production UI or business-logic changes were needed.

### Responsive Layout Third Sweep

- Re-scanned the application for remaining page-fitting locks after the
  continuation pass.
- Converted module-hub operation panels to compact internal vertical scroll
  areas so long operation groups do not reserve excessive page height.
- Fixed module-hub operation button contrast by using the normal in-card quick
  button style instead of the dark ribbon style.
- Reduced Report Center statement spacing, indentation and side-tree heights
  while preserving tested statement-control readability.
- Captured new after screenshots for Accounts module, Report Center statement
  view and Masters module.

### Responsive Layout Continuation

- Reduced note, remarks, narration and address text-edit heights by about 30%
  through shared form helpers, theme QSS, shell fit normalization and page-local
  helpers.
- Tightened Receipt Entry and Payment Entry label-to-control spacing, form
  height, note height and recent-entry grid row height while preserving voucher
  save/print/share behavior.
- Extended compact sizing to Document Center, Report Center, Global Search,
  Excel Import, Label Print, Stock Dashboard, Financial Years, Numbering
  Series, Scheme Master, Route Settlement, Developer Console and generic master
  pages.
- Reduced shared table row-size locks and keyboard-flow table polishing so
  compact grid rows are not inflated after focus/navigation setup.
- Captured new after screenshots for Receipt Entry, Payment Entry, Document
  Center, Report Center and Developer Console.

### Responsive Layout Stabilization

- Relaxed page-fitting UI locks across the shared shell, ERP themes, shared form
  helpers, dashboard cards, transaction framework, master screens,
  administration/developer screens, dialogs, and tables.
- Replaced the fixed 202 px ERP Navigator rail with a responsive compact
  168-188 px rail band, preserving the approved navigation design while giving
  dense pages more usable content width.
- Reduced oversized QSS padding, margins, min-heights, min-widths, page headers,
  card heights, input heights, action button sizes, table row heights, and
  dialog minimum widths.
- Added target-resolution regression coverage for 1366x768, 1440x900, and
  1920x1080 to prevent page-level horizontal overflow and field label/control
  overlap on major pages.
- Preserved all business logic, required fields, GST/tax/total summaries,
  item-grid commands, keyboard navigation, Save, Preview, and Print workflows.
- Captured responsive after screenshots for Dashboard, Sales Bill, Product
  Master, Developer Console, Quotation, and 1920x1080 Dashboard.

### Transaction Add Row / F4 Stabilization

- Reproduced the non-Sales-Bill Add Row/F4 hard crash and captured the Windows
  access-violation traceback in `tmp/add_row_repro.log`.
- Removed the null Qt item delegate from the shared sales-document item table,
  fixing Quotation, Sales Order, Delivery Challan, Purchase Order and inherited
  document entry screens.
- Added shared `GridActionBar`, `TransactionGridPanel` and `ERPItemGrid`
  adoption across item-entry pages so Add Row, F4 and Delete Row behavior stay
  centralized in the ERP UI framework.
- Added regression coverage for Add Row/F4/Delete safety across Sales Bill,
  Purchase Entry, Quotation, Sales Order, Delivery Challan, returns, Purchase
  Order, inventory entries, Stock Out and Dispatch Return.
- Preserved existing schema, GST, save, print, PDF, WhatsApp, numbering,
  repository and licensing logic.

### Transaction Entry Framework

- Added one reusable transaction page scaffold, canonical toolbar, named cards
  and keyboard-first transaction grid to the existing shared ERP UI framework.
- Migrated current sales, purchase, inventory, dispatch, route settlement and
  account entry views to the shared framework without changing repositories,
  services, SQLite architecture, GST, vouchers, printing or licensing.
- Added Home/End, Ctrl+Home/Ctrl+End, F2-F10 command hooks, clipboard commands,
  hidden/read-only column skipping and event-specific modifier handling.
- Fixed active-page height calculation so hidden stacked pages no longer push
  transaction totals below the viewport.
- Fixed Sales Bill advanced-detail controls appearing outside their intended
  More Details dialog.
- Enabled horizontal scrolling for wide transaction grids while preserving
  compact non-transaction tables.
- Added regression coverage for framework adoption, toolbar order, keyboard
  navigation, active-page sizing and transaction route initialization.

### Verification

- Focused UI and row-operation tests: 32 passed.
- Full test suite: 124 passed.
- Transaction route smoke: 17 pages opened; dark theme toggle passed.
- SQLite integrity: `ok`.
