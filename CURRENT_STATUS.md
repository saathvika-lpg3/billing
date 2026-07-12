# Current Status

## 2026-07-12 Branding Ownership Correction, Dispatch Route And Certified Installer 1.7.7

- Release state: **1.7.7 code-controlled gates passed and the real local
  installation was upgraded successfully**. The certified setup is
  `installer_output/PRM_Billing_Inventory_Setup.exe` (43,193,577 bytes,
  SHA-256
  `E4ADC9CCCF76E2E1C38ACD042F42C6C9FF44A20329DC5E353A3EA8B83A6EE54C`).
- Safety checkpoint created before this correction:
  `backups/branding_cleanup_checkpoint_20260712_015638.zip` (813,693 bytes,
  SHA-256
  `FF59AC6BAC163CF1A3C429FF114793BBB608DDFB72EB777873E979B11AC2F2A6`).
- Corrected the branding ownership boundary. The fixed application product
  header, login product header, executable/window icon and installer identity
  are owned only by **PRM BILLING INVENTORY** and the original PRM assets.
  A licensed client's name, initials or logo must never replace that product
  identity.
- Client identity is intentionally separate. `ClientCompanyIdentityCard` owns
  the licensed-company presentation on Dashboard Company Information, Company
  Settings/Profile and other company-context surfaces. Transaction, report,
  statement and voucher document headers use the client company; shared PDF
  footers retain PRM product ownership.
- The root cause was direct use of the client-owned branding widget in the
  fixed shell plus generic page-width fitting that overwrote fixed logo
  geometry. `ProductBrandHeader` and `ClientCompanyIdentityCard` now have
  explicit responsibilities, and identity-card geometry is protected from the
  generic fitter.
- Added a single canonical **Dispatch Summary** destination:
  `reports:daily_dispatch_summary`, selecting Report Center key
  `daily_dispatch_summary`. Sidebar, Dashboard quick access, Reports operations
  and Global Search all route to that same report; no duplicate report page was
  introduced.
- Dispatch visibility follows the existing reports permission and licensed
  plan filter. Admin/developer roles retain access; non-admin roles require the
  reports permission; the Basic plan does not expose Dispatch-category reports.
  Filtered routes are also removed from report selection and Global Search.
- Installer **1.7.7** uses the PRM setup/uninstall icon, packages the smaller
  runtime requirement manifest and omits development documentation, `numpy`
  and `lxml`. Frozen startup and installed UI/resource smoke passed; the payload
  contains no `.prmlic`, PowerShell, logs, uploads, tests, audit or backup data.
- The installer accepts any valid per-client `.prmlic` basename through its
  Browse control. Clean install with `sairam.prmlic` and upgrade with
  `lakshmi.prmlic` both passed; setup stores the selected file internally as
  `license/client.prmlic` for a stable runtime path.
- Classified workspace cleanup is complete. Historical client-facing prints
  and reports plus the legacy delivery bundle are preserved under
  `cleanup_quarantine_20260712_075052`; generated caches, test installs, logs,
  build/dist output and `.venv` were removed. Protected licence/upload hashes
  match their pre-cleanup values. The live database is integrity-clean and new
  UI tests/capture tools now operate on disposable database copies.
- Validation: **220 passed** full suite, **44 passed** focused branding/
  navigation/print gate, **14 passed** post-build release gate, **7 passed**
  database-isolation gate, and **59/59 routes** passed all three target sizes.

## 2026-07-12 Production Stabilization And Installer 1.7.6

- Safety checkpoint: `backups/production_stabilization_checkpoint_20260711_224546.zip`
  (788,135 bytes, SHA-256
  `55BE66DAB4B8B05BFEB7576D962BED2597BF10942BA91075A6CA3CAA053A278C`).
- The 1.7.6 checkpoint introduced one reusable client-branding component on
  Login, Dashboard, the main header and Company Settings. The main-header
  placement was subsequently classified as an ownership defect and is
  superseded by the 1.7.7 correction above. Current document headers continue
  to use the client logo-above-name hierarchy and supplied regulatory/contact
  details.
- Product conversion validation was repaired at the save-pipeline root. The
  repository now validates and synchronizes explicit purchase-to-sale UOM
  conversion atomically with the product and its pack rows. Single-UOM,
  Multi-UOM and Pack Conversion saves no longer reject legitimate differing
  purchase/sale units, and a failed conversion cannot partially save.
- Customer, Supplier and Product masters use readable business groups,
  horizontal actions, consistent shortcuts and width-aware controls. Editable
  combo boxes use the shared type-to-filter completer with keyboard and mouse
  support throughout live pages.
- GST resolution now follows item -> HSN tax code -> category default -> zero,
  and party state/place-of-supply data drives CGST/SGST versus IGST on the
  sales, purchase, order, quotation, challan and return transaction families.
- Email delivery attaches the actual PDF through SMTP, Outlook COM where
  available, or Windows Simple MAPI. `mailto:` remains an explicit manual
  fallback because that protocol cannot attach a local file reliably.
- Runtime WhatsApp sharing no longer launches a PowerShell helper. Native
  Windows clipboard/file-drop APIs perform attachment handoff; PowerShell is
  used only by developer build scripts and is not a client runtime dependency.
- List/master/report printing routes through the shared professional PDF
  engine. Dispatch/loading totals use an allowlist of business measures and
  never total record IDs. Profit & Loss, Balance Sheet, receipt and payment
  voucher parity remains locked by multi-page PDF tests.
- Live UI audit: **59/59 routes passed** at 1366x768, 1440x900 and 1920x1080;
  no route fallback, clipping, overlap, unreadable dropdown or missing initial
  Grand Total was found. Typed-widget audit: **35 files, 0 unsafe calls**.
- Performance gate: Product open 0.1402s, add 20 packs 0.0146s, filter
  0.0128s, save/reload 0.1070s, refresh 0.0554s, New response 0.0012s, Sales
  Bill open 0.0683s and Purchase Entry open 0.0530s; all thresholds passed.
- Release test gate: source compile passed and the full native suite completed
  with **213 passed in 183.75 seconds**. Installer version is **1.7.6**; final
  artifact identifiers and install certification are recorded in
  `INSTALLER.md` and `TEST_REPORT.md`.
- Certified setup: 51,873,806 bytes, SHA-256
  `E769D2216540AE04632ACA0E419D013A3D1020C67DD5ED12B865BDDF985FA8E7`.
  Clean install, frozen startup, authenticated installed-resource smoke,
  renamed-license upgrade, byte-identical database preservation and uninstall
  preservation all passed.
- Remaining external release dependency: a trusted Authenticode certificate is
  required only when Windows publisher signing is desired. Live SMTP/Outlook
  delivery also requires the client's mail account/application configuration.

## 2026-07-11 Fast-Track UI Stabilization And Installer 1.7.5

- Created and verified the pre-change source checkpoint
  `backups/source_checkpoint_20260711_114542.zip` (SHA-256
  `A1135D9E8B96C8537F6579799F1345EAB49FF0F74C72062BAF4C500014347A40`).
- Rebuilt Product Master as responsive Basic, Inventory/UoM,
  Identification/Notes and Package/Variant sections with one horizontal action
  toolbar. The exact `QComboBox.text()` / `setText()` failure was replaced by
  typed shared widget access; New no longer clears UoM models, multi-pack
  save/reload works, and editing does not create a duplicate product.
- Migrated Sales Bill and Purchase Entry to the shared transaction header,
  toolbar, details, grid, totals and tax-summary language used by Quotation and
  Sales Order. Grand Total is high-contrast, bold, numerically bound and visible
  in the initial 1366x768 viewport.
- Replaced cramped or vertical master/list/report actions with the shared
  wrapping horizontal toolbar. Global pressed, focus, disabled, checked, busy,
  success, error, positive and destructive feedback is defined in both themes.
- Runtime inventory: 59/59 live routes pass wiring, fallback, horizontal-stack,
  Grand Total and 1366x768 / 1440x900 / 1920x1080 checks. The broader screen-fit
  regression also passes 1093x614 and 911x512 scaling cases.
- Static typed-widget audit: 33 UI files scanned, 0 unsafe method calls.
  Performance smoke: all eight measured operations passed their thresholds.
- Verification: compile/static checks passed; stabilization regressions 8/8;
  full suite **190 passed in 182.32 seconds**.
- Installer 1.7.5 built and certified. Silent install, actual frozen startup,
  QA admin activation, installed-resource Product Master two-pack save/reload,
  required route opening, both themes, Grand Total, horizontal actions,
  byte-identical reinstall preservation and uninstall preservation all passed.
  Setup SHA-256:
  `C54E99B4B714E20D5D7DE2958415ED6FEDA35D9E39D2C694B927F965AF41BFFA`.
- No code-controlled blocker remains in this stabilization scope.

This task-specific status file was created because the requested
`CURRENT_STATUS.md` did not exist. The canonical long-form project status also
remains updated in `PRM_CURRENT_STATUS.md`.

## 2026-07-11 Installer And Client-License Repair

- Audited the supplied `Client_License_Files` `.prmlic` without exposing its
  credentials. It is byte-identical to `license/client.prmlic`, passes all
  required-field/status/key-format/expiry checks, and remains valid through
  2027-07-06.
- Proved the installation failure was not the client file: the PyInstaller spec
  packaged the active developer SQLite database, including a machine activation
  from a different computer. The Inno catch-all also overwrote that database on
  upgrades.
- Added `tools/prepare_installer_database.py`. Every build now creates a
  separate integrity-checked, unbound SQLite seed containing product reference
  data/templates but zero activation, license, user, customer, supplier, item,
  transaction, ledger, GST, app-setting, or communication-log rows.
- Changed the installer so the mutable database is excluded from the general
  payload and installed separately with `onlyifdoesntexist` and
  `uninsneveruninstall`. Existing client databases therefore survive upgrades
  and uninstall file cleanup.
- Preserved the existing mandatory `.prmlic` browse/copy flow, legacy JSON and
  signed PRMLIC1 support, signature verification, status/expiry validation and
  target-machine binding. The installer preflight now checks all 12 required
  snake-case fields.
- Made the PyInstaller spec workspace-portable, made the build select an
  installed Python runtime that actually contains PyInstaller, removed client
  upload data and the obsolete `pysqlite` hidden import from packaging, and
  corrected frozen startup logs to `<app_root>\\logs`.
- Installer/license regressions: **6 passed**. At the v1.7.4 checkpoint, the
  complete native suite was **177 passed** with no product failures.
- Built the v1.7.4 checkpoint installer SHA-256
  `5FA609210B0ECBC4B4145D52C1DF643AC4A5FDE0391FF37248DB15E097CB8412`,
  installed it silently using the supplied `.prmlic`, and verified the installed
  seed started with zero activation/license/user/transaction rows. First launch
  then created exactly one Active activation, one license row and one admin user.
  The installed application reached the login dialog and remained responsive.
- The v1.7.4 checkpoint artifact rebuilt successfully after removing client uploads
  and the obsolete optional import. Its distribution has no uploads directory,
  no `pysqlite` warning, and retains the sanitized seed database.

## 2026-07-11 ERP Business-Flow Completion Audit

- Continued from Git checkpoint `71a4aab` on branch
  `business-flow-audit-20260710`; preserved the first completed tranche in local
  safety commit `acfb396`.
- Added atomic validation, unique-number checks, closed-year checks, negative
  stock protection, item/pack/warehouse reference checks, party outstanding
  updates, round-off ledger posting and non-posting Draft/Hold behavior.
- Added safe Sales and Purchase edit/repost behavior. The live Sales List and
  Purchase List now open saved transactions for edit; the prior stock,
  outstanding, ledger and GST effects are reversed and retained as
  `Superseded` before one active version is posted.
- Added reason-required cancellation for Sales, Purchase, both returns,
  Receipt, Payment, Expense, Journal/Contra and Stock Transfer. Cancellation
  retains source documents and creates auditable stock reversal movements.
- Fixed Sales/Purchase screens to persist the selected warehouse ID instead of
  silently saving warehouse `0`.
- Added active Sales/Purchase Registers, active Day Book, date-aware report
  filtering, active GST/HSN reporting, live `stock_log`-based Stock Postings,
  and financial-year GST aggregation for GSTR-9 Annual.
- Added `docs/BUSINESS_FLOW_MATRIX.md`, classifying all original 59
  preview/list/report operations: 44 fully functional, 7 missing drill-down,
  and 8 live-data/integration-incomplete. HSN Summary is an additional
  completed report.
- Added a read-only 12-check integrity auditor and generated
  `audit/business_flow_audit.json`. A clean deterministic fixture passes all
  12 checks. The inherited live/demo database remains explicitly failed for
  legacy issues including a `0.33` ledger difference, two unbalanced voucher
  groups, one duplicate active source voucher, one negative-stock item and
  older documents/postings that predate the current lifecycle contract.
- Automated evidence in the current environment: lifecycle module `11 passed`;
  broader non-UI regression `90 passed, 1 deselected`; native PyQt/print chunk
  reached `22 passed` before 15 setup errors caused by an inaccessible Windows
  temp directory. `pytest.ini` now directs temp artifacts to the ignored
  workspace `tmp/pytest` path for the next native run.
- No unconditional production-readiness claim is made. Invoice-level payment
  allocations/aging, batch-ID movement, canonical base-UOM conversion,
  cancellable Stock Entry/Adjustment headers and landed cost remain documented
  limitations.
- Manual launch result: `app.py` started the real QApplication and license
  validation path from `D:\PRM_GST_DESKTOP`, then exited because the installed
  client license is bound to another machine. Licensing was not changed or
  bypassed; main-window manual testing is blocked until the client supplies a
  current-machine `.prmlic` file.

## 2026-07-10 GitHub Baseline And ERP Audit Cycle

- Verified GitHub Desktop is running on the workstation and used local Git for
  the controlled repository operations.
- Created root production baseline commit:
  `8833190 Initial production-ready PRM GST Desktop baseline`.
- Pushed `main` to the official remote
  `https://github.com/saathvika-lpg3/billing.git` and verified
  `origin/main` points to commit `8833190`.
- Created and pushed release tag `v1.0.0-production-baseline`; the annotated
  tag resolves to the same baseline commit.
- Verified the remote contains 193 tracked source/documentation/test/resource
  files and no generated-output, runtime database, backup, log, `.prmlic`,
  session/cookie or upload paths.
- Started the next roadmap cycle with an ERP functional audit pass. The desktop
  coverage checklist reports 103/103 rows done, and operation parity now reports
  0 missing labels.
- Repaired `tools/audit_mysql_schema.py` so the schema audit uses Python's
  built-in SQLite support instead of a hard-coded legacy executable path.
- Regenerated schema-only SQLite audit artifacts under `audit/`: 116 tables,
  1731 columns, and 20 index-column entries. Live row counts are not collected
  unless the audit tool is explicitly run with `--include-row-counts`.
- Added regression coverage in `tests/test_audit_tools.py` for the portable
  schema audit and the accepted `ERP Profit & Loss` -> `Profit & Loss` menu
  alias.

## 2026-07-10 Git Repair And Print Engine Lock Continuation

- Created source-only pre-repair backup:
  `backups/source_only_pre_git_repair_20260710_130613.zip`.
- Diagnosed Git root cause: `.git` existed as an empty directory with no
  `HEAD`, no `config`, no `objects`, and no `refs`; `GIT_DIR` was not set and
  no parent repository was found.
- Preserved invalid metadata at:
  `.git_invalid_backup_20260710_130706`.
- Cloned official remote to
  `D:\PRM_GST_DESKTOP_GITHUB_COMPARE_20260710_130706`. The remote
  `https://github.com/saathvika-lpg3/billing.git` is valid but currently has
  no commits/tracked files, so no source was overwritten from GitHub.
- Repaired live repository metadata safely with a new local `main` branch and
  `origin` set exactly to the official remote. No push was performed.
- Added `.gitignore` to exclude runtime/generated/client-sensitive content:
  `.venv`, caches, build/dist/installer output, logs, backups, generated
  PDFs/screenshots/reports, local databases, uploads, `.prmlic` files,
  sessions/cookies and machine-local state.
- Added persisted print-template orientation support. `print_templates` now has
  an idempotent `orientation` migration, the Developer Console template editor
  can save Portrait/Landscape, and the shared print resolver reads the setting
  when present while safely supporting older DBs.
- Kept the approved decision: Distributor/Wholesale is not forced to A4. A4
  Portrait, A4 Landscape, A2 Portrait and A2 Landscape are selected by saved
  template paper/orientation and all use the canonical transaction structure.
- Added structural transaction print locks proving paper/orientation changes do
  not remove document title, Bill To, Ship To, item columns, GST Summary, Grand
  Total, amount words, terms, bank details or authorised signature.
- Generated validation artifacts under:
  `output/pdf/print_engine_lock_20260710_130706/`, including A4/A2
  portrait/landscape transaction PDFs, 6-page sales and purchase PDFs,
  Receipt, Payment, Profit & Loss and Balance Sheet plus rendered PNGs.
- Tests passed after this continuation: py_compile passed; focused print locks
  passed 6; print/report plus accounting preview passed 28; full regression
  passed 160.

## 2026-07-10 Locked Reference Print/Report Validation Continuation

- Superseded the earlier blocked-reference note: the locked files were found in
  Downloads and rendered for comparison:
  `C:\Users\DELL\Downloads\Print_torefer_codex.pdf`,
  `profitandloss.pdf`, `balancesheet.pdf`, and the transaction-entry UI PNG.
- Rendered reference, before and after evidence under
  `output/pdf/reference_validation_20260710/`:
  `references/rendered`, `live/rendered`, and `live_after/rendered`.
- Found the live Profit & Loss and Balance Sheet PDFs were using the generic
  flat report table layout (`Statement / Period / Side / Particulars...`) and
  landscape paper, which failed the approved two-sided accounting-statement
  reference.
- Added shared `write_statement_pdf()` in `services/pdf_print.py` and routed
  Report Center Profit & Loss / Balance Sheet print and PDF export through it.
  The new output is A4 portrait, two-sided, grouped, indented, live-ledger
  backed, and includes a supporting-analysis page.
- Tightened receipt/payment voucher print identity by preserving and rendering
  `Reference` and `Instrument` fields. Receipt and Payment outputs now have
  explicit regression coverage so they cannot map to each other silently.
- Added permanent print/report regression locks in
  `tests/test_print_and_report_parity.py` for required paper/orientation
  matrix, two-sided statement structure, removal of generic statement headers,
  and receipt/payment identity/reference details.
- Validation status:
  Sales Invoice, Sales Order, Quotation, Purchase print sections: partially
  passed against the A4 reference because the current selected company/template
  output is A2 landscape, but selected paper/orientation, header, party blocks,
  QR/payment, item table, GST summary, totals, amount words, terms, bank,
  signature and footer rendered.
- Validation status: Profit & Loss passed after correction; Balance Sheet
  passed after correction; Receipt Voucher passed; Payment Voucher passed.
- Remaining external/manual items: physical printer behavior, operator
  acceptance, SMTP/WhatsApp production sessions, and any client-specific demand
  to force the transaction template to A4 instead of the currently selected A2
  distributor/wholesale print layout.
- Tests passed after this continuation: focused print/report locks passed 3;
  broader print/report plus statement preview suite passed 27; full regression
  passed 159.

## 2026-07-10 Production Readiness Route/Print Audit Continuation

- Continued with a second safe print-preview guard and fixed a preview layout
  detection edge case.
- Found that large generated PDFs can place `/MediaBox` near the end of the
  file, so the preview dialog's earlier first-chunk scan could mis-detect an
  A2 landscape report as A4 portrait.
- Updated `services.print_preview.PrintPreviewDialog._detect_pdf_layout()` to
  stream-scan the PDF for the first MediaBox using bounded memory.
- Added `test_print_preview_detects_generated_report_paper_and_orientation`
  so generated A4 portrait and A2 landscape report PDFs must be detected
  correctly by the preview layer.
- Captured after screenshot:
  `screenshots/production_readiness_print_preview_a2_landscape_20260710.png`.
- Tests passed after this continuation: focused preview detector test passed
  1; print/report parity passed 23; full regression passed 156.

- Continued in fast-track mode with the next non-blocked report/print guard.
- Added regression coverage proving Report Center Profit & Loss and Balance
  Sheet can generate a non-empty PDF and hand it to the print-preview layer
  without opening a real dialog.
- Re-ran the production surface scan for obvious silent UI placeholders and
  hard layout locks. No live production `lambda: None`, `coming soon`, or
  output-action placeholder remained in `views`; remaining fixed/minimum sizes
  are compact bounded rules or existing small-control constraints.
- Tests passed after this continuation: focused accounting print-preview test
  passed 1; combined UI plus print/report suites passed 69; full regression
  passed 155.

- Continued with the next non-blocked production-readiness tasks:
  reference-file re-check, Document Center print mapping, Document Center
  subview layout/button wiring, and module hub internal operation layout/button
  wiring.
- Re-checked `C:\Users\DELL\.codex\attachments`, project screenshots/reports
  and Downloads for the locked reference PDF/images. The current attachment
  set still contains pasted-text instructions only; no readable
  `Print_torefer_codex.pdf`, locked P&L screenshot, locked Balance Sheet
  screenshot or latest list/report problem screenshot was available.
- Found and fixed a print-template metadata gap: Document Center `sales_return`
  resolved to a blank `template_code` when no active DB template row existed.
  The central print resolver now provides deterministic fallback metadata for
  known transaction and voucher document types, including `sales_return` ->
  `Sales Return / Credit Note`.
- Added print mapping regression coverage so every Document Center print type
  must resolve to a non-empty template code/name, supported paper size and
  valid orientation.
- Added UI regression coverage for every Document Center subview and every
  Module Hub operation state to verify fit, internal table scrolling/header
  behavior and visible button click receivers.
- Tests passed after this continuation: py_compile passed; print/report parity
  passed 22; `tests/test_document_and_module_ui.py` passed 46; full regression
  passed 154.

- Continued again by adding regression protection for two previously partial
  areas: the hidden Report Center Account Closing / CA Export panel and
  all-route visible button signal wiring.
- Found and fixed a hidden-state layout defect in Report Center: the Account
  Closing CA Export panel was visible but the filter card kept the normal
  compact height cap, allowing the table area to cover the CA Export controls.
  The filter card now expands only when the CA Export panel is visible and
  returns to compact height for normal reports.
- Added focused UI tests that verify the Account Closing CA Export panel fits
  at 1366x768 without page-level horizontal overflow, clipped controls, clipped
  table headers or hidden table scrollbars.
- Added an all-registered-route audit test that opens every live page and
  fails if any visible enabled `QPushButton` has no click receiver.
- Refreshed screenshot:
  `screenshots/production_readiness_audit_account_closing_ca_export_1366x768_20260710.png`.
- Tests passed after the fix: py_compile passed; focused continuation tests
  passed 2; `tests/test_document_and_module_ui.py` passed 44; print/report
  parity passed 21; full regression passed 151.

- Continued the production-readiness cycle from the attached principal-owner
  instructions and completed the non-blocked audit/documentation portion of
  the current pass.
- Created a fresh source-only safety backup before this continuation:
  `backups/production_readiness_source_20260710_093457.zip`. Runtime database,
  logs, session data and client data were excluded.
- Traced the live desktop route registry from `MainWindow.page_factories`.
  Current live inventory: 59 registered routes opened successfully at
  1366x768; no route raised during the live route sweep.
- Confirmed 18 live transaction routes use the shared transaction framework:
  `sales_bill`, `quotation_entry`, `sales_order_entry`,
  `delivery_challan_entry`, `sales_return_entry`, `purchase_entry`,
  `purchase_order_entry`, `purchase_return_entry`, `stock_entry_entry`,
  `stock_transfer_entry`, `stock_adjustment_entry`, `stock_out_entry`,
  `dispatch_return_entry`, `route_settlement`, `receipt_entry`,
  `payment_entry`, `expense_entry`, and `journal_entry`.
- Confirmed the current Report Center exposes the live accounting statement
  routes for Profit & Loss and Balance Sheet through `ReportCenterView`, backed
  by statement data from `MySqlSource.operation_rows()` and protected by the
  existing statement-tree UI tests.
- Confirmed the print/report engine has existing A2/A4,
  portrait/landscape, repeated-header, transaction PDF, voucher PDF and report
  PDF regression coverage in `tests/test_print_and_report_parity.py`.
- Captured current-state production audit screenshots:
  `screenshots/production_readiness_audit_reports_1366x768_20260710.png`,
  `screenshots/production_readiness_audit_quotation_entry_1366x768_20260710.png`,
  `screenshots/production_readiness_audit_receipt_entry_1366x768_20260710.png`,
  and
  `screenshots/production_readiness_audit_payment_entry_1366x768_20260710.png`.
- Visual spot check passed for Report Center fit, Quotation vertical scrolling,
  and compact Receipt/Payment note-control and label-to-control spacing.
- Tests passed after documentation updates: py_compile passed; print/report
  parity suite passed 21; `tests/test_document_and_module_ui.py` passed 42;
  full regression passed 149. Superseded by the later continuation above,
  where UI tests passed 44 and full regression passed 151 after the Account
  Closing panel regression guard was added.
- No UI/business code was changed in this continuation. Existing transaction
  save/posting, GST/tax, stock, ledger, numbering, PDF, communication and
  licensing paths were left intact.
- Genuine blockers remain for external acceptance: the latest locked reference
  PDF/report screenshots were described in the attachment but were not
  available as readable files in this run; real SMTP/WhatsApp/operator and
  installer acceptance also require production credentials, sessions and
  approved acceptance records.

## 2026-07-10 Production Acceptance Safety Stabilization

- Started the production acceptance cycle from the attached instructions and
  completed Phase 1 pre-acceptance safety review.
- Created a source-only safety backup before making changes:
  `backups/pre_acceptance_source_20260710_082242.zip`. Runtime database,
  logs, session data and client data were not included in that backup.
- Found and fixed a communication-log privacy defect: new communication log rows
  no longer store full recipient values, message bodies or full attachment
  paths. They store masked recipient, safe subject/result summary and
  attachment filename only.
- Updated dashboard and Developer Console communication tables so historical
  full-recipient rows are masked when displayed.
- Preserved legacy retry support for already-existing full-payload retry rows,
  while new privacy-safe rows are not auto-retried from masked data.
- Added Windows DPAPI protection for saved SMTP passwords in `app_settings`.
  Existing plain `smtp.password` rows are read for backward compatibility and
  protected in-place when settings are loaded.
- Preserved business logic: transaction save/posting, PDF generation, GST/tax,
  stock, ledger, numbering, templates and normal send/handoff paths were not
  changed.
- Real SMTP acceptance was not executed: no production SMTP credentials were
  provided in this run.
- Real WhatsApp acceptance was not executed: no verified logged-in
  workstation/browser WhatsApp session was provided in this run.
- Operator validation with real customer/supplier data was not executed.
- Installer/build validation was not executed because real SMTP/WhatsApp and
  operator acceptance have not passed yet.
- Tests passed: py_compile passed; focused safety tests 4 passed;
  `tests/test_data_maintenance_and_share.py` 14 passed;
  `tests/test_document_and_module_ui.py` 42 passed; full suite 149 passed.
- Remaining manual acceptance items: configure real SMTP, run Test SMTP, send
  sample invoice/receipt PDFs, verify real WhatsApp link/session/PDF workflow,
  validate approved customer/supplier records, then proceed to installer/build
  validation.

## 2026-07-10 Communication Delivery Diagnostics Continuation

- Continued after approval by adding safe delivery-readiness diagnostics for
  Communication without changing transaction business logic.
- Added `EmailDeliveryService.test_connection()` so SMTP host/TLS/login can be
  checked through the same shared connection path used by real sends, without
  sending a business document.
- Added `whatsapp_readiness()` in `services/share_service.py` to validate the
  phone number and generate native/web WhatsApp links without opening the
  browser or attaching PDFs.
- Added a compact Developer Console Communication > Delivery Diagnostics panel
  for Test Email, WhatsApp No., `Test SMTP`, `Check WhatsApp Link`, and the
  resulting diagnostic status.
- Preserved business logic: transaction save/posting, PDF generation,
  GST/tax, stock, ledger, numbering and normal delivery handoff paths were not
  changed.
- Screenshot captured:
  `screenshots/after_communication_delivery_diagnostics_1366x768_20260710.png`.
- Tests passed: py_compile passed; focused diagnostics tests 4 passed;
  `tests/test_data_maintenance_and_share.py` 14 passed;
  `tests/test_document_and_module_ui.py` 42 passed; full suite 149 passed.
- Remaining approval-gated item: real SMTP/WhatsApp acceptance with configured
  production accounts and logged-in browser/device sessions.

## 2026-07-10 Communication Contact Preview Continuation

- Continued after approval by adding richer contact-source controls to the
  Developer Console Communication > Message Templates workflow.
- Added `communication_contact_preferences` support in
  `CommunicationTemplateService`, including preferred contact field save/load
  and resolver ordering by channel/document type.
- Added a compact Message Templates preview/contact-check panel with sample
  party, document, amount, email and mobile inputs. Operators can preview the
  rendered subject/body and confirm which contact field resolves before using a
  template.
- Preserved business logic: transaction save/posting, PDF generation,
  GST/tax, stock, ledger, numbering and delivery handoff paths were not
  changed.
- Screenshot captured:
  `screenshots/after_communication_contact_preview_1366x768_20260710.png`.
- Tests passed: py_compile passed; focused contact/template tests 2 passed;
  `tests/test_data_maintenance_and_share.py` 13 passed;
  `tests/test_document_and_module_ui.py` 42 passed; full suite 148 passed.
- Superseded by the Communication Delivery Diagnostics Continuation above:
  delivery-readiness diagnostics are now implemented. Real SMTP/WhatsApp
  acceptance with configured production accounts remains approval-gated.

## 2026-07-10 Live Communication Template Wiring Continuation

- Continued after approval by wiring live transaction Email and WhatsApp
  actions through the shared communication-template helpers.
- Added shared `communication_message()` and `document_message_context()`
  helpers in `services/share_service.py`, backed by
  `CommunicationTemplateService.render_for_document()` with existing
  subject/body fallback when no active template exists.
- Wired Sales Bill, Purchase/Goods Receipt, sales and purchase document
  screens, receipt/payment/account vouchers, inventory entries, stock out/load
  challans, dispatch returns and route settlements to render Email/WhatsApp
  message text from the shared template path.
- Preserved business logic: document PDF generation, save/posting, GST/tax,
  stock, ledger, numbering and SMTP/mail-client handoff logic were not changed.
- No new visual surface was added in this continuation, so no new screenshot was
  required; the existing template admin screenshot remains
  `screenshots/after_communication_templates_1366x768_20260710.png`.
- Tests passed: py_compile passed; focused live-template tests 2 passed;
  `tests/test_data_maintenance_and_share.py` 13 passed;
  `tests/test_document_and_module_ui.py` 42 passed; full suite 148 passed.
- Superseded by the Communication Contact Preview Continuation above: richer
  contact-source selection UI is now implemented. Operator acceptance with real
  SMTP/WhatsApp accounts and further dashboard/layout enhancements remain
  approval-gated.

## 2026-07-10 Communication Templates Continuation

- Continued after approval by adding shared communication message templates and
  contact-resolution helpers without changing transaction save/posting logic.
- Added `services/communication_template_service.py` with the
  `communication_templates` table, default template seeding, template save/list,
  safe placeholder rendering, and email/WhatsApp/SMS contact resolution.
- Added compact Developer Console Communication sub-tabs: `Delivery` for SMTP,
  retry and logs, and `Message Templates` for template maintenance.
- Seeded default templates for sales invoice email, receipt email, purchase
  order email and payment reminder WhatsApp.
- Screenshot captured:
  `screenshots/after_communication_templates_1366x768_20260710.png`.
- Tests passed: py_compile passed; focused template/UI tests 2 passed;
  `tests/test_data_maintenance_and_share.py` 12 passed; focused UI suite 42
  passed; full suite 147 passed.
- Superseded by the Live Communication Template Wiring Continuation above:
  selected templates are now wired into live document Email/WhatsApp actions.
  Later contact-preview and delivery-diagnostics continuations also completed
  richer contact-source controls. Real SMTP/WhatsApp acceptance remains
  production-account gated.

## 2026-07-10 Dashboard Communication Status Continuation

- Continued after approval by adding communication health to the Executive
  Dashboard using the existing shared ERP dashboard card/table framework.
- Added `Communication Status` and `Failed Communications` dashboard cards.
  `Communication Status` shows delivery mode, sent-today count, failed count,
  pending retry count and recent delivery rows. `Failed Communications` lists
  retry-needed email rows with result code, attempts and next retry time.
- Updated `DashboardService.snapshot()` so communication failures also feed
  `Critical Alerts` and `Daily Tasks`. Dashboard loading remains read-only; the
  retry action stays in Developer Console.
- If `communication_logs` has no rows or does not exist, the cards show clear
  empty states instead of blank panels.
- Screenshot captured:
  `screenshots/after_dashboard_communication_cards_1366x768_20260710.png`.
- Tests passed: py_compile passed; focused dashboard/communication tests 2
  passed; `tests/test_data_maintenance_and_share.py` 11 passed; focused UI
  suite 42 passed; full suite 146 passed.
- Superseded by the later Communication Templates, Live Template Wiring,
  Contact Preview and Delivery Diagnostics continuations. Real SMTP/WhatsApp
  operator acceptance on the production workstation remains production-account
  gated.

## 2026-07-10 Communication Log And Retry Continuation

- Continued after approval from the SMTP stop point by adding a shared
  communication history and retry layer while preserving existing transaction
  save/posting/GST/stock/ledger logic.
- Added `services/communication_log_service.py` with the
  `communication_logs` table, recent-history reads, pending-retry reads, and
  bounded email retry execution.
- Extended `services/email_service.py` so SMTP configuration can come from
  local `app_settings` rows as well as environment variables. Environment
  variables still override database settings when present.
- Updated `prepare_email_document()` to record email SMTP, handoff and failure
  results when a database path or log service is supplied.
- Updated Sales Bill, Purchase/Goods Receipt, sales/purchase document pages,
  receipt/payment/account vouchers, inventory, stock out, dispatch return and
  route settlement email actions to pass the active SQLite path into the shared
  email helper for delivery logging.
- Added a compact Developer Console `Communication` tab with SMTP settings,
  pending retry rows, recent communication history, and a `Retry Failed Email`
  action. Password entry is masked and only updates the saved password when a
  new value is entered.
- Screenshot captured:
  `screenshots/after_communication_admin_1366x768_20260710.png`.
- Tests passed: py_compile passed; focused communication/share suite 10 passed;
  focused Developer Console communication UI test 1 passed; focused UI suite
  42 passed; full suite 145 passed.
- Superseded by the Dashboard Communication Status Continuation above:
  dashboard communication status cards are now implemented.

## 2026-07-10 SMTP Email Automation Continuation

- Continued after approval from the output-actions stop point by adding an
  opt-in SMTP communication layer while preserving the existing mail-client
  handoff as the default safe behavior.
- Added `services/email_service.py` with `SmtpEmailConfig` and
  `EmailDeliveryService`. SMTP sends are enabled only when
  `PRM_EMAIL_DELIVERY_MODE=smtp` and SMTP host/from settings are configured.
- Updated `services/share_service.prepare_email_document()` so all existing
  Email buttons can send PDFs through SMTP when explicitly configured, or fall
  back to the default mail-client handoff when SMTP is not enabled.
- Environment settings supported:
  `PRM_EMAIL_DELIVERY_MODE`, `PRM_SMTP_HOST`, `PRM_SMTP_PORT`,
  `PRM_SMTP_USERNAME`, `PRM_SMTP_PASSWORD`, `PRM_SMTP_FROM`,
  `PRM_SMTP_USE_TLS`, `PRM_SMTP_USE_SSL`, and `PRM_SMTP_TIMEOUT`.
- Added tests for SMTP PDF attachment delivery and fallback handoff behavior.
- Tests passed: py_compile passed; focused SMTP/email tests 3 passed;
  `tests/test_data_maintenance_and_share.py` 7 passed; output/fit UI batch
  3 passed; focused UI suite 41 passed; full suite 141 passed.
- No UI layout changed in this pass; existing 2026-07-10 output-action
  screenshots remain valid for the affected screens.
- Remaining caveat: SMTP is configuration-driven and not enabled by default.
  WhatsApp attachment automation still depends on Windows/WhatsApp Web login
  state.
- Superseded by the 2026-07-10 Communication Log And Retry Continuation above:
  the in-app communication settings, delivery log table and retry queue are now
  implemented. The later Dashboard Communication Status Continuation also
  implements dashboard communication cards.

## 2026-07-10 Output Actions And Email Continuation

- Continued from the remaining approved task list and replaced all remaining
  placeholder `Preview` / `Print` / `PDF` / `WhatsApp` / `Email` transaction
  actions in `views` with real handlers or shared framework feedback.
- Added shared email handoff helpers in `services/share_service.py`:
  `email_url`, `open_email_share`, and `prepare_email_document`. This opens
  the operator's default email client with recipient, subject, body and PDF
  path; it does not add hidden SMTP sending or bypass operator review.
- Wired Email on Sales Bill, Purchase/Goods Receipt, receipt/payment/account
  vouchers, Quotation, Sales Order, Delivery Challan, Sales Return, Purchase
  Order and Purchase Return using the already-existing PDF creation paths.
- Wired report-style PDF output on Stock Entry, Stock Transfer, Stock
  Adjustment, Stock Out / Load Challan, Dispatch Return and Route Settlement
  using the existing `write_report_pdf` and `show_print_preview` services.
  WhatsApp and Email reuse the same generated PDF paths.
- Static scan result: no remaining `("Preview", None)`, `("Print", None)`,
  `("PDF", None)`, `("WhatsApp", None)`, `("Email", None)` or
  `lambda: None` placeholders in `views`.
- Screenshots captured:
  `screenshots/after_output_actions_stock_entry_1366x768_20260710.png`,
  `screenshots/after_output_actions_stock_out_entry_1366x768_20260710.png`,
  `screenshots/after_output_actions_dispatch_return_entry_1366x768_20260710.png`,
  and
  `screenshots/after_output_actions_route_settlement_1366x768_20260710.png`.
- Tests passed: py_compile passed; focused email/report-output tests 3 passed;
  performance smoke 1 passed; all-route target fit 1 passed; focused UI suite
  41 passed; full suite 139 passed.
- Remaining caveat: email is a mail-client handoff with PDF path text, not
  background SMTP delivery. Automatic attachment still depends on the user's
  mail client; physical operator acceptance on the real monitor/DPI setup is
  still recommended.
- Stop point: wait for approval before deeper communication automation or
  extra dashboard/layout enhancements.

## 2026-07-09 Pending Action Wiring Continuation

- Continued the pending UI/layout task by removing the remaining safe no-op
  action paths. Sales Bill and Purchase Entry `Preview` now use their existing
  PDF print-preview flow; Receipt/Payment/Expense/Journal `Preview` now uses
  the existing voucher print-preview flow.
- Sales-document pages now use the existing shared print/share services for
  Quotation, Sales Order, Delivery Challan, Sales Return, Purchase Order and
  Purchase Return: `write_transaction_pdf`, `show_print_preview`,
  `prepare_whatsapp_document`, and `document_share_caption`. No posting,
  repository, GST, stock, ledger or save logic was changed.
- Shared UI framework hardening: `ERPToolbar` now gives the same friendly
  not-available message as `TransactionToolbar`, and `TransactionPageLayout`
  installs shared button feedback on page-local buttons as each region is
  added. This covers direct view opens as well as main-window navigation.
- Remaining intentionally unavailable actions are now documented as future
  business workflows, not UI locks: Email everywhere, plus Preview/Print/PDF/
  WhatsApp on Stock Out, Inventory Entry, Dispatch Return and Route Settlement
  until approved document-output logic exists for those screens.
- New screenshots captured at 1366x768:
  `screenshots/after_pending_actions_quotation_entry_1366x768_20260709.png`,
  `screenshots/after_pending_actions_sales_bill_1366x768_20260709.png`,
  `screenshots/after_pending_actions_purchase_entry_1366x768_20260709.png`,
  and
  `screenshots/after_pending_actions_receipt_entry_1366x768_20260709.png`.
- Tests passed: py_compile passed; focused action/feedback/PDF tests 5 passed;
  all-route target fit 1 passed in 68.20s; performance smoke 1 passed in
  11.09s; totals smoke 2 passed; focused UI suite 39 passed; full suite 137
  passed.
- Remaining task list: implement true business Email/communication workflows
  and specialized stock/dispatch/route print/share documents only after
  approval; physical monitor/DPI operator acceptance is still recommended.
- Stop point: wait for approval before additional dashboard/layout
  enhancements.

## 2026-07-09 Button Feedback, Wiring And Totals Stabilization

- Root cause: shared `TransactionToolbar` and `GridActionBar` created visible
  actions without callbacks as disabled buttons, so Preview/Print/PDF/Email,
  Import and similar actions looked present but gave no click response. Page
  migration also left Sales Bill and Purchase Entry on older compact text
  totals, while the sales-document footer had totals but not the full required
  field set.
- Button feedback implemented through shared helpers in
  `widgets/erp_components.py`: hover, pressed, keyboard focus, recent-click and
  short busy states. `MainWindow` installs the shared feedback on page creation
  for page-local buttons as well.
- Button wiring fixed in shared components: unsupported transaction/grid
  actions now remain clickable, show click feedback and display a friendly
  "not available on this screen yet" message instead of silently doing nothing.
- Grand Total/totals fixed: added shared `TransactionTotalsPanel` and
  `TransactionTaxSummaryPanel`, then applied them to Sales Bill,
  Purchase/Goods Receipt, Quotation, Sales Order, Delivery Challan, Purchase
  Order and inherited sales/purchase document pages. Returns show visible zero
  totals and a `No data available` tax state until source items are loaded.
- Performance improvement: button feedback tree installation now runs at shell
  and page creation instead of every page switch; shared callbacks acknowledge
  clicks immediately and show a short busy state for longer actions.
- Files changed in this pass:
  `widgets/erp_components.py`, `views/main_window.py`,
  `views/sales_document_view.py`, `views/sales_bill_view.py`,
  `views/purchase_entry_view.py`, `themes/light.qss`, `themes/dark.qss`,
  `tests/test_document_and_module_ui.py`, `CHANGELOG.md`,
  `CURRENT_STATUS.md`, `PRM_CURRENT_STATUS.md`, `TEST_REPORT.md`,
  `docs/DESKTOP_UI_SYSTEM.md`, and `docs/TRANSACTION_FRAMEWORK.md`.
- Screenshots captured:
  `screenshots/after_button_feedback_quotation_preview_1366x768_20260709.png`,
  `screenshots/after_totals_sales_bill_1366x768_20260709.png`,
  `screenshots/after_totals_purchase_entry_1366x768_20260709.png`, and
  `screenshots/after_totals_quotation_1366x768_20260709.png`.
- Performance smoke: dashboard, sales bill, purchase entry, quotation,
  document center, reports, receipt and payment opened in about 3.1 seconds
  total in the local offscreen run.
- Tests passed: py_compile passed; new focused button/totals/performance tests
  5 passed; all-route fit 1 passed; focused UI suite 36 passed; full suite 134
  passed.
- Remaining risk: actions that are genuine future work still show a friendly
  not-available message; they are not fake-implemented.
- Stop point: wait for approval before more dashboard/layout enhancements.

## 2026-07-09 Responsive Reference Completion

- Completed the requested continuation pass across the three remaining work
  areas: reference-style transaction footer, practical operator walkthrough,
  and target-resolution acceptance evidence.
- Files changed in this pass:
  `views/sales_document_view.py`, `views/account_entry_view.py`,
  `themes/light.qss`, `themes/dark.qss`, `CHANGELOG.md`,
  `CURRENT_STATUS.md`, `PRM_CURRENT_STATUS.md`, `TEST_REPORT.md`,
  `UI_LAYOUT_RULES.md`, and `docs/DESKTOP_UI_SYSTEM.md`.
- UI locks relaxed/adjusted: replaced the fixed 52 px sales-document totals
  strip with flexible shared cards; reduced oversized Notes/narration editor
  heights in sales documents and receipt/payment entries; kept transaction
  tables on internal horizontal scrolling only.
- Sales-document footer now uses the shared ERP framework cards for Remarks,
  Terms & Conditions, Totals, and Tax Summary. Tax Summary renders
  `No data available` on empty documents and real CGST/SGST/IGST groups after
  rows are added.
- Receipt Entry and Payment Entry were rechecked at 1366x768 after note-height
  and label-gap trimming; required fields and Save/Print/PDF/WhatsApp controls
  remain visible.
- Screenshots captured:
  `screenshots/after_responsive_quotation_entry_1366x768_20260709.png`,
  `screenshots/after_responsive_quotation_entry_1366x768_bottom_20260709.png`,
  `screenshots/after_responsive_quotation_entry_1440x900_20260709.png`,
  `screenshots/after_responsive_quotation_entry_1920x1080_20260709.png`,
  `screenshots/after_responsive_receipt_entry_1366x768_20260709.png`,
  `screenshots/after_responsive_receipt_entry_1440x900_20260709.png`,
  `screenshots/after_responsive_receipt_entry_1920x1080_20260709.png`,
  `screenshots/after_responsive_payment_entry_1366x768_20260709.png`,
  `screenshots/after_responsive_payment_entry_1440x900_20260709.png`, and
  `screenshots/after_responsive_payment_entry_1920x1080_20260709.png`.
- Before evidence remains available at
  `screenshots/reference_align_before_quotation_1366x768_20260709.png`.
- Tests passed: py_compile passed; transaction height contract 1 passed;
  all-registered-pages target fit 1 passed; focused UI suite 31 passed; full
  suite 129 passed.
- Operator walkthrough passed: Quotation Add Row/F4 handler, Delete Row and
  Save stub; Receipt Entry Save and Print Preview; Payment Entry Save and Print
  Preview.
- Stop point: wait for approval before additional dashboard or layout
  enhancements.

## 2026-07-09 Reference Image Alignment Pass

- Analyzed the supplied Quotation Entry reference image and aligned the desktop
  shell toward its approved ERP look while preserving existing business logic.
- Updated the shared shell with a white brand/search top bar, responsive
  financial-year/branch/user info blocks, active dark-blue ribbon state, and a
  tighter dark PRM sidebar.
- Reworked the shared sales-document/Quotation header into three reusable
  transaction cards: Customer Information, Other Details, and Additional
  Information.
- Added reference-style grid action coloring for Add Row, Delete Row, Import
  and Scan Barcode in both light and dark themes.
- Kept the approved shell search width contract after tests caught an oversized
  search box; responsive top info blocks collapse on narrower/DPI workspaces.
- Captured before/after evidence:
  `screenshots/reference_align_before_quotation_1366x768_20260709.png`,
  `screenshots/reference_align_after_quotation_1366x768_20260709.png`, and
  `screenshots/reference_align_after_quotation_911x512_20260709.png`.
- Tests passed: shell contract 1 passed; five-size all-route fit matrix
  1 passed; focused UI suite 31 passed; full suite 129 passed.
- Remaining optional visual alignment: deeper document-title metadata/actions
  bar and bottom tax/totals panel can be refined after approval.

## 2026-07-09 Transaction Grid Stretch-Lock Cleanup

- Continued the application-wide layout lock audit and rescanned `views`,
  `widgets`, `themes`, `config` and `app.py` for fixed sizes, minimums,
  geometry calls, QSS min-size rules and page-level scroll policies.
- Removed remaining local transaction-grid `Stretch` resize locks from Sales
  Bill, Purchase Entry, sales document derivatives, inventory entry derivatives,
  Stock Out, Dispatch Return, Route Settlement and account recent-entry tables.
- Added practical interactive item-grid widths for item/description columns so
  wide transaction grids own horizontal overflow internally instead of relying
  on page-level stretch behavior.
- Remaining fixed-size findings are compact line-control heights, logo previews,
  login/dialog minimum widths, flow-layout geometry implementation, and bounded
  report statement panes; these are covered by the all-route fit matrix and are
  not known page-fit blockers.
- Screenshots captured:
  `screenshots/responsive_after_gridlocks_sales_bill_1366x768_20260709.png`,
  `screenshots/responsive_after_gridlocks_purchase_entry_1366x768_20260709.png`,
  `screenshots/responsive_after_gridlocks_sales_return_entry_1366x768_20260709.png`,
  `screenshots/responsive_after_gridlocks_stock_adjustment_entry_1366x768_20260709.png`,
  `screenshots/responsive_after_gridlocks_stock_out_entry_1366x768_20260709.png`,
  `screenshots/responsive_after_gridlocks_dispatch_return_entry_1366x768_20260709.png`,
  `screenshots/responsive_after_gridlocks_route_settlement_1366x768_20260709.png`,
  and
  `screenshots/responsive_after_gridlocks_receipt_entry_1366x768_20260709.png`.
- Tests passed: five-size all-route fit matrix 1 passed; focused UI suite
  31 passed; full suite 129 passed.
- Remaining task: physical monitor acceptance at 1366x768, 1440x900 and
  1920x1080 with the user's production Windows scaling/display settings.
- Stop point: wait for approval before additional dashboard/layout
  enhancements.

## 2026-07-09 Native 125% DPI Table Fit Continuation

- Continued the responsive certification after approval and captured a native
  Qt 125% scale pass using a 1093x614 logical window, producing 1366x768
  physical screenshots.
- Fixed the remaining table-fit lock by allowing the shared page-fit pass to
  normalize table headers even when Qt/offscreen scaling reports the stacked
  page itself as not visible.
- Relaxed dashboard mini-table horizontal scrollbar locking so dashboard tables
  follow the same internal-scroll rule as other ERP tables.
- Added a second non-transaction table fill pass after Qt geometry recalculation
  so wide screens do not leave underfilled table viewports.
- No business, posting, save, print, GST, voucher, repository or schema logic
  was changed.
- Tests passed: five-size all-route fit matrix 1 passed; focused UI suite
  31 passed; full suite 129 passed.
- New 125% physical screenshot evidence:
  `screenshots/responsive_qt125_dashboard_1366x768_physical_20260709.png`,
  `screenshots/responsive_qt125_receipt_1366x768_physical_20260709.png`,
  `screenshots/responsive_qt125_payment_1366x768_physical_20260709.png`,
  `screenshots/responsive_qt125_sales_bill_1366x768_physical_20260709.png`,
  `screenshots/responsive_qt125_purchase_entry_1366x768_physical_20260709.png`,
  `screenshots/responsive_qt125_reports_1366x768_physical_20260709.png`,
  `screenshots/responsive_qt125_document_center_1366x768_physical_20260709.png`,
  `screenshots/responsive_qt125_stock_dashboard_1366x768_physical_20260709.png`,
  and
  `screenshots/responsive_qt125_administration_1366x768_physical_20260709.png`.
- Remaining responsive task: user acceptance on actual Windows monitors at
  1366x768, 1440x900 and 1920x1080 with production display drivers.
- Stop point: wait for approval before additional dashboard/layout enhancements.

## 2026-07-09 Windows DPI Scaling Certification

- Relaxed the remaining 980x620 main-window lock to 900x500 logical pixels.
- Added responsive sidebar bands: 136-148 px below 1000 px, 152-168 px below
  1200 px, and the approved 168-188 px band on normal desktop widths.
- Converted shared `ERPToolbar` actions to wrapping flow layout.
- Reworked Sales Bill and Purchase Entry totals/actions into compact two-row
  grids so GST summary, totals, template, Save, Print, WhatsApp, Remove and
  Clear remain available without clipped captions.
- Enabled wrapping for return-document guidance and removed local stretch-mode
  table overrides from Stock Dashboard and module hubs.
- Expanded the 59-route matrix with 1093x614 and 911x512 logical workspaces,
  representing a 1366x768 display at 125% and 150% scaling.
- Tests passed: focused UI suite 31 passed; full suite 129 passed.
- Captured eight 911x512 logical screenshots and Qt-native 150% screenshots
  rendering Dashboard, Purchase Entry and Reports at 1367x768 physical pixels.
- No known automated DPI/layout failure remains. Final validation on the
  user's physical Windows monitors is an acceptance check, not a known defect.
- Stop point: wait for approval before additional layout enhancements.

## 2026-07-09 Responsive Layout Header And Grid Certification

- Continued the all-page visual pass and added explicit checks for clipped
  labels, buttons and table headers, underfilled narrow tables, internal table
  scrollbar visibility, and compact secondary-dialog fit.
- Fixed shared table normalization so readable header widths are preserved,
  spare viewport width is distributed across normal data columns, and wide
  tables expose an internal horizontal scrollbar.
- Moved final table fitting to the next Qt event tick after a page becomes
  visible, avoiding stale column geometry from hidden stacked pages.
- Visually verified Expense Entry, Administration, Financial Years and
  Numbering Series at 1366x768. Financial Years now uses the available table
  width; Numbering Series shows an internal horizontal scrollbar.
- Tests passed: focused UI suite 31 passed; full suite 129 passed.
- New screenshot evidence:
  `screenshots/responsive_cert_expense_entry_1366x768_20260709.png`,
  `screenshots/responsive_cert_administration_1366x768_20260709.png`,
  `screenshots/responsive_after_headerfit_financial_years_1366x768_20260709.png`,
  `screenshots/responsive_after_headerfit_numbering_series_1366x768_20260709.png`,
  and
  `screenshots/responsive_after_headerfit_delivery_challan_entry_1366x768_20260709.png`.
- Remaining responsive task: physical-display acceptance at the three target
  resolutions and common Windows DPI/font-scaling settings. No known code-side
  layout defect remains in the registered-page audit.
- Stop point: wait for approval before additional layout enhancements.

## 2026-07-09 Responsive Layout All-Route Certification

- Continued after approval and audited all 59 page factories registered by the
  application, including secondary master, account, hub, search, import,
  administration, audit and roadmap pages.
- Replaced the hand-maintained 12-page fit sample with a registry-driven test,
  so every current and future registered page is checked automatically.
- All registered pages passed at 1366x768, 1440x900 and 1920x1080 with no
  page-level horizontal scrollbar and no shared field-label/control overlap.
- No further production UI edits were required in this pass; existing compact
  note controls and Receipt/Payment spacing remained within the approved rules.
- Tests passed: focused UI suite 30 passed; full suite 128 passed.
- Existing responsive before/after screenshots remain the visual evidence
  because this continuation strengthened coverage without changing rendering.
- Stop point: wait for approval before additional layout enhancements.

## 2026-07-09 Responsive Layout Third Sweep

- Re-scanned the application for remaining layout locks after the continuation
  pass.
- Converted dense module-hub operation panels to compact internal vertical
  scroll areas so long operation lists do not reserve excessive page height.
- Fixed module-hub operation button contrast by using the in-card quick button
  style instead of the dark ribbon style inside white cards.
- Reduced Report Center statement-tree spacing, indentation and side-tree
  heights while preserving the tested 220 px minimum for the control statement
  tree.
- Tests passed: focused UI suite 30 passed; full suite 128 passed; expanded
  target fit audit returned `target_fit_failures=0`.
- New screenshots captured:
  `screenshots/responsive_after_accounts_module_1366x768_20260709_continued2.png`,
  `screenshots/responsive_after_reports_statement_1366x768_20260709_continued2.png`,
  and
  `screenshots/responsive_after_masters_module_1366x768_20260709_continued2.png`.
- Stop point: wait for approval before additional layout enhancements.

## 2026-07-09 Responsive Layout Continuation

- Continued the same application-wide responsive layout pass after approval to
  cover remaining page families and note-style controls.
- Reduced note, remarks, narration, address and similar text-edit control
  heights by about 30% through shared form helpers, QSS, the shell fit
  normalizer, and local page helpers.
- Tightened Receipt Entry and Payment Entry label-to-control gaps, form card
  height, note height, recent-entry table rows, and compact field sizing while
  preserving Save, Print, PDF, WhatsApp and voucher posting behavior.
- Extended compact sizing to Document Center, Report Center, Global Search,
  Excel Import, Label Print, Stock Dashboard, Financial Years, Numbering
  Series, Scheme Master, Route Settlement, Developer Console and generic master
  pages.
- Target resolution audit across the expanded route list returned
  `target_fit_failures=0`; note controls are capped and no tested page-level
  horizontal scrollbars were found.
- Tests passed: compile check passed; focused UI suite 30 passed; full suite
  128 passed.
- New screenshots captured:
  `screenshots/responsive_after_receipt_entry_1366x768_20260709_continued.png`,
  `screenshots/responsive_after_payment_entry_1366x768_20260709_continued.png`,
  `screenshots/responsive_after_document_center_1366x768_20260709_continued.png`,
  `screenshots/responsive_after_report_center_1366x768_20260709_continued.png`,
  and
  `screenshots/responsive_after_developer_console_1366x768_20260709_continued.png`.
- Stop point: wait for approval before additional layout enhancements.

## 2026-07-09 Responsive Layout Stabilization

- Relaxed page-fitting UI locks across the shared ERP shell, approved light/dark
  themes, shared form helpers, dashboard cards, transaction layouts, master
  screens, admin/developer screens, dialogs, and table/grid sizing.
- Replaced the fixed 202 px left rail with a responsive compact 168-188 px
  sidebar band, giving the content area more width while retaining the approved
  navigation surface.
- Removed or capped oversized fixed/minimum widths, heights, padding, margins,
  card heights, input heights, button sizes, dialog widths, page-level scroll
  restrictions, and table/grid locks that forced overflow.
- Preserved business logic, GST/tax/total summaries, item-grid controls, Add
  Row/F4, Delete Row/Del, Import, Scan Barcode, Save, Preview, and Print
  workflows.
- Added regression coverage for major pages at 1366x768, 1440x900, and
  1920x1080 with no page-level horizontal scrollbar and no field-label/control
  overlap.
- Tests passed: target fit audit `target_fit_failures=0`; focused UI suite
  30 passed; full suite 128 passed.
- Screenshots captured:
  `screenshots/responsive_after_dashboard_1366x768_20260709.png`,
  `screenshots/responsive_after_sales_bill_1366x768_20260709.png`,
  `screenshots/responsive_after_product_master_1366x768_20260709.png`,
  `screenshots/responsive_after_developer_console_1366x768_20260709.png`,
  `screenshots/responsive_after_quotation_1440x900_20260709.png`, and
  `screenshots/responsive_after_dashboard_1920x1080_20260709.png`.
- Stop point: wait for approval before additional dashboard or layout
  enhancements.

## 2026-07-09 Transaction Add Row / F4 Stabilization

- Reproduced the crash on Quotation and captured the access-violation trace in
  `tmp/add_row_repro.log`.
- Root cause: `SalesDocumentView` cleared the Qt table item delegate with
  `setItemDelegate(None)`, then crashed during row redraw/resize after Add Row.
- Fixed by removing the null delegate and centralizing Add Row/F4 focus behavior
  in `ERPItemGrid`, `TransactionGridPanel`, and `GridActionBar`.
- Migrated item-entry grids to the shared `ERPItemGrid` surface for Sales Bill,
  Purchase Entry/Goods Receipt, Quotation, Sales Order, Delivery Challan,
  Purchase Order, Stock Entry, Stock Transfer, Stock Adjustment, Stock Out and
  Dispatch Return.
- Sales Return and Purchase Return remain source-document-driven; Add Row/F4 is
  safe and does not crash, but manual row creation is intentionally blocked
  until an original document is loaded.
- Tests passed: focused UI suite 29 passed; full suite 127 passed.
- Screenshots captured in `screenshots/transaction_addrow_after_*_20260709.png`.
- Stop point: wait for approval before additional transaction/dashboard
  enhancements.
