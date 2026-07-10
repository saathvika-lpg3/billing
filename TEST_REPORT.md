# Test Report

## 2026-07-10 GitHub Baseline And ERP Audit Cycle

### Scope

- Verified GitHub Desktop is running and completed repository initialization
  with local Git.
- Committed and pushed the first production baseline to the official remote.
- Created and pushed release tag `v1.0.0-production-baseline`.
- Continued with the next roadmap cycle: ERP functional audit tooling,
  operation parity, desktop coverage, and schema-audit portability.

### Git Evidence

- Baseline commit: `8833190 Initial production-ready PRM GST Desktop baseline`.
- Remote branch: `origin/main` at `8833190`.
- Release tag: `v1.0.0-production-baseline`, resolving to `8833190`.
- Remote tracked file count: 193.
- Forbidden path scan after push: no generated output, local databases, logs,
  backups, `.prmlic`, sessions/cookies, uploads or cache paths were present in
  `origin/main`.

### Audit Evidence

- `docs/DESKTOP_COVERAGE_CHECKLIST.md`: 103 generated rows, 103 done.
- `docs/operation_parity_checklist.md`: 0 missing labels.
- Accepted alias documented by tooling: `ERP Profit & Loss` maps to desktop
  `Profit & Loss` route key `erp_profit_loss`.
- `audit/sqlite_schema_summary.md`: schema-only output with 116 tables, 1731
  columns, 20 index-column entries, and no live row counts unless explicitly
  requested.

### Automated Tests

- `python -m py_compile tools\audit_operation_parity.py tools\audit_mysql_schema.py tests\test_audit_tools.py`
  - Result: passed.
- `python -m pytest -q tests\test_audit_tools.py`
  - Result: 2 passed.
- `python -m pytest -q tests\test_audit_tools.py tests\test_document_and_module_ui.py`
  - Result: 49 passed in 189.63s.

### Acceptance Status

- GitHub baseline branch push: PASSED.
- Release tag push: PASSED.
- Post-push forbidden-file verification: PASSED.
- ERP audit tooling cycle: PASSED.
- Remaining external validation: physical printer, real SMTP, real WhatsApp
  session, operator acceptance data, and clean-machine installer validation.

## 2026-07-10 Git Repair And Print Engine Lock Continuation

### Scope

- Created source-only backup before Git repair and additional print changes.
- Diagnosed invalid Git metadata, preserved the broken `.git` folder, cloned
  the official GitHub remote for comparison, and repaired the live repository
  metadata without overwriting source files.
- Added `.gitignore` hygiene for generated/runtime/client-sensitive content.
- Added persisted print-template orientation support so client-selected paper
  settings can cover A4 Portrait, A4 Landscape, A2 Portrait and A2 Landscape.
- Kept the accepted canonical transaction structure and did not force
  Distributor/Wholesale output to A4.

### Git Evidence

- Backup: `backups/source_only_pre_git_repair_20260710_130613.zip`.
- Invalid Git metadata preserved:
  `.git_invalid_backup_20260710_130706`.
- Diagnostics before repair:
  `git --version` passed; `git rev-parse --show-toplevel`, `git rev-parse
  --git-dir`, `git status`, and `git remote -v` failed because `.git` was an
  empty directory.
- Official comparison clone:
  `D:\PRM_GST_DESKTOP_GITHUB_COMPARE_20260710_130706`.
- GitHub comparison: official remote had 0 tracked files and no commits; live
  source had 203 source candidates after ignore rules.
- Repaired origin: `https://github.com/saathvika-lpg3/billing.git`.
- Current branch after repair: `main`.

### Print Evidence

- Validation PDFs and rendered PNGs:
  `output/pdf/print_engine_lock_20260710_130706/`.
- Generated artifacts include:
  A4 Portrait, A4 Landscape, A2 Portrait, A2 Landscape transaction PDFs;
  6-page Sales and Purchase PDFs; Receipt Voucher; Payment Voucher; Profit &
  Loss; Balance Sheet.
- Visual check passed on representative matrix, multi-page, voucher and
  statement renders. Poppler emitted display-font warnings for
  Symbol/ArialUnicode but produced PNGs successfully.

### Automated Tests

- `python -m py_compile services\pdf_print.py services\mysql_source.py views\developer_console_view.py tests\test_print_and_report_parity.py`
  - Result: passed.
- Focused print locks:
  `test_transaction_pdf_honors_paper_orientation_matrix_without_changing_structure`,
  `test_heavy_a4_invoice_paginates_with_final_summary`,
  `test_heavy_a2_invoice_template_paginates_landscape`,
  `test_report_pdf_honors_required_paper_orientation_matrix`,
  `test_accounting_statement_pdfs_use_locked_two_sided_layout`,
  `test_receipt_and_payment_voucher_pdfs_keep_identity_and_reference_details`
  - Result: 6 passed in 57.07s.
- Print/report plus accounting preview:
  `python -m pytest -q tests\test_print_and_report_parity.py tests\test_document_and_module_ui.py::test_accounting_statement_reports_open_print_preview`
  - Result: 28 passed in 104.64s.
- Full regression:
  `python -m pytest -q tests`
  - Result: 160 passed in 294.70s.

### Acceptance Status

- Git repair: PASSED. Repository metadata is valid, origin is official, branch
  is `main`, and no live source was overwritten.
- GitHub/live comparison: PASSED. Remote is empty; live source is the only
  current implementation source.
- `.gitignore` hygiene: PASSED. Local DBs, license files, uploads, generated
  PDFs/screenshots, backups, logs, caches and secrets are excluded.
- Canonical transaction renderer: PASSED. All tested paper/orientation variants
  preserve canonical sections.
- Distributor paper matrix: PASSED for A4/A2 portrait/landscape via persisted
  template orientation.
- Multi-page headers/footers/final totals: PASSED by structural PDF assertions
  and rendered 6-page Sales/Purchase artifacts.
- Profit & Loss, Balance Sheet, Receipt and Payment locks: PASSED.
- Physical printer, real SMTP/WhatsApp and clean-machine installer acceptance:
  BLOCKED pending external environment/operator validation.

## 2026-07-10 Locked Reference Print/Report Validation Continuation

### Scope

- Located and rendered locked references from Downloads after checking the
  current attachment manifest, upload/reference folders and project docs:
  `Print_torefer_codex.pdf`, `profitandloss.pdf`, `balancesheet.pdf`, and the
  approved transaction-entry UI PNG.
- Compared reference renders with live generated output for Sales Invoice,
  Sales Order, Quotation, Purchase, Receipt Voucher, Payment Voucher, Profit &
  Loss and Balance Sheet.
- Corrected the live Profit & Loss and Balance Sheet print/export path from a
  generic landscape table to the approved A4 portrait two-sided statement
  layout.
- Corrected voucher print metadata so receipt/payment PDFs render reference and
  instrument details and keep receipt/payment identity locked.

### Evidence

- Reference renders:
  `output/pdf/reference_validation_20260710/references/rendered`.
- Before live renders:
  `output/pdf/reference_validation_20260710/live/rendered`.
- After live PDFs and renders:
  `output/pdf/reference_validation_20260710/live_after` and
  `output/pdf/reference_validation_20260710/live_after/rendered`.
- Live-after summary:
  `output/pdf/reference_validation_20260710/live_after/live_after_generation_summary.json`.
- Visual checks performed on rendered statement, voucher and transaction PNGs.
  Poppler emitted display-font warnings for Symbol/ArialUnicode, but rendered
  the PNG evidence successfully.

### Automated Tests

- Focused new locks:
  `test_report_pdf_honors_required_paper_orientation_matrix`,
  `test_accounting_statement_pdfs_use_locked_two_sided_layout`,
  `test_receipt_and_payment_voucher_pdfs_keep_identity_and_reference_details`
  - Result: 3 passed in 30.33s.
- Broader print/report plus report-center statement preview:
  `python -m pytest -q tests\test_print_and_report_parity.py tests\test_document_and_module_ui.py::test_accounting_statement_reports_open_print_preview`
  - Result: 27 passed in 79.08s.
- Full regression:
  `python -m pytest -q tests`
  - Result: 159 passed in 273.65s.

### Acceptance Status

- Profit & Loss: PASSED. A4 portrait, two-sided accounting statement, live
  groups/details, equal totals and supporting analysis are rendered.
- Balance Sheet: PASSED. A4 portrait, Liabilities/Assets sides, capital/current
  profit treatment, stock/cash/bank/debtor/creditor style groups, equal totals
  and supporting analysis are rendered.
- Receipt Voucher: PASSED. Receipt title, party block, amount/words, mode,
  reference, instrument, narration, signatures and footer are rendered; it does
  not map to Payment.
- Payment Voucher: PASSED. Payment title, party block, amount/words, mode,
  reference, instrument, narration, signatures and footer are rendered; it does
  not map to Receipt.
- Sales Invoice / Sales Order / Quotation / Purchase transaction prints:
  PARTIALLY PASSED for exact visual reference parity. Required sections render
  and selected paper/orientation are honored, but the active company/template
  output is A2 landscape while `Print_torefer_codex.pdf` is A4 portrait.
- Multi-page and paper/orientation locks: PASSED by automated matrix/repeated
  header coverage for generated PDFs; physical printer behavior remains
  BLOCKED pending real printer/operator acceptance.
- SMTP, WhatsApp and installer acceptance: BLOCKED because those require real
  production credentials/sessions/operator approval and were outside this
  print/rendering code pass.

## 2026-07-10 Production Readiness Route/Print Audit Continuation

### Scope

- Continuation update: fixed print-preview paper/orientation detection for
  large generated PDFs whose `/MediaBox` appears after the first file chunk.
  Added a guard for generated A4 portrait and A2 landscape report PDFs.
- Continuation update: added accounting statement print-preview coverage for
  Report Center Profit & Loss and Balance Sheet, and re-ran the full
  regression suite.
- Continuation update: re-checked locked reference availability, fixed
  deterministic print metadata for known transaction/voucher document types,
  and added regression coverage for Document Center print mapping, Document
  Center subviews and Module Hub operation states.
- Continuation update: fixed and regression-tested the hidden Account Closing
  CA Export layout and added all-route visible button click-receiver wiring.
- Continued the production-readiness stabilization cycle with a fresh backup,
  live route inventory, route/widget audit, current-state screenshots and
  documentation updates.
- Source-only backup created:
  `backups/production_readiness_source_20260710_093457.zip`.
- Live route audit opened all 59 registered `MainWindow.page_factories` routes
  at 1366x768; failures: none.
- Transaction framework inventory found 18 live transaction routes using the
  shared framework components.
- No business logic or UI code was changed in this continuation.

### Automated / Scripted Evidence

- Live route inventory script:
  - Result: 59 routes opened, 18 transaction-framework routes identified,
    page-level horizontal scrollbar maximum was 0 for each opened route at
    1366x768.
- `python -m py_compile app.py views\main_window.py views\report_center_view.py services\pdf_print.py tests\test_document_and_module_ui.py tests\test_print_and_report_parity.py`
  - Result: passed.
- `python -m py_compile services\pdf_print.py tests\test_print_and_report_parity.py tests\test_document_and_module_ui.py views\document_center_view.py views\module_hub_view.py`
  - Result: passed after the print-mapping and subview regression continuation.
- Focused print/list continuation tests:
  `test_document_center_print_meta_resolves_configured_templates`,
  `test_document_center_all_subviews_fit_and_keep_buttons_wired`,
  `test_module_hub_operation_states_fit_and_keep_buttons_wired`
  - Result: passed.
- Focused accounting statement print-preview continuation test:
  `test_accounting_statement_reports_open_print_preview`
  - Result: 1 passed in 7.40s.
- Focused print-preview detector continuation test:
  `test_print_preview_detects_generated_report_paper_and_orientation`
  - Initial Result: failed because an A2 landscape PDF was detected as A4
    portrait when `/MediaBox` appeared near the end of the file.
  - After detector fix: 1 passed in 9.33s.
- Focused continuation tests:
  `test_report_center_account_closing_ca_export_panel_fits_target_width`,
  `test_all_registered_pages_visible_buttons_have_click_receivers`
  - Initial Result: 2 passed in 17.22s.
  - After Report Center height fix: 2 passed in 12.65s.
- `python -m pytest tests\test_print_and_report_parity.py -q`
  - Result: 22 passed in 18.60s after the print-mapping continuation.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 46 passed in 95.60s after adding the subview/module-hub guards.
- `python -m pytest -q`
  - Result: 154 passed in 129.37s after the print-mapping and hidden-state
    guards.
- `python -m pytest tests\test_document_and_module_ui.py tests\test_print_and_report_parity.py -q`
  - Result: 69 passed in 157.41s after the accounting print-preview guard.
- `python -m pytest -q`
  - Result: 155 passed in 273.42s after the accounting print-preview guard.
- `python -m py_compile services\print_preview.py tests\test_print_and_report_parity.py`
  - Result: passed after the preview detector fix.
- `python -m pytest tests\test_print_and_report_parity.py -q`
  - Result: 23 passed in 43.96s after the preview detector fix.
- `python -m pytest -q`
  - Result: 156 passed in 276.09s after the preview detector fix.
- Existing regression coverage already protects:
  - all registered page fit at 1366x768, 1440x900, 1920x1080, 125% logical
    workspace and 150% logical workspace;
  - visible label/button clipping;
  - table-header clipping and internal table scrollbars;
  - shared transaction framework usage;
  - Add Row/F4 transaction grid behavior;
  - transaction output actions;
  - report/PDF A2/A4 and multi-page parity;
  - voucher PDF rendering;
  - Profit & Loss and Balance Sheet statement-tree routing.

### Screenshot Evidence

- `screenshots/production_readiness_audit_reports_1366x768_20260710.png`
- `screenshots/production_readiness_audit_quotation_entry_1366x768_20260710.png`
- `screenshots/production_readiness_audit_receipt_entry_1366x768_20260710.png`
- `screenshots/production_readiness_audit_payment_entry_1366x768_20260710.png`
- `screenshots/production_readiness_audit_account_closing_ca_export_1366x768_20260710.png`
- `screenshots/production_readiness_print_preview_a2_landscape_20260710.png`

### Acceptance Status

- Fresh backup: passed.
- Live route inventory: passed.
- Current-state visual spot check: passed for the captured pages.
- Hidden Account Closing CA Export panel: passed after Report Center dynamic
  filter-height fix.
- Visible button signal wiring: passed for all registered routes through the
  new receiver audit.
- Document Center print mapping: passed. `sales_return` now resolves to
  non-empty fallback metadata (`sales_return`, `Sales Return / Credit Note`,
  A4 portrait) if no active DB template row exists.
- Document Center subviews and Module Hub operation states: passed through
  focused UI regression coverage.
- Profit & Loss and Balance Sheet print-preview path: passed through the new
  Report Center regression; both reports produced non-empty PDFs and invoked
  the shared preview handoff.
- Print-preview paper/orientation detection: passed after streaming MediaBox
  detection; generated A4 portrait and A2 landscape reports are detected
  correctly.
- Full hidden-state/modal/action click-through of every secondary panel:
  partially passed through automated coverage; not manually exhausted in this
  continuation.
- Locked external reference comparison: blocked because the current run only
  provided the instruction text, not readable copies of the latest locked PDF,
  list/report screenshots, Profit & Loss screenshot or Balance Sheet screenshot.
- Real production SMTP/WhatsApp/operator/installer acceptance: blocked pending
  production accounts, logged-in sessions and approved acceptance records.

## 2026-07-10 Production Acceptance Safety Stabilization

### Scope

- Executed Phase 1 pre-acceptance safety review from the production acceptance
  instructions.
- Created source-only backup:
  `backups/pre_acceptance_source_20260710_082242.zip`.
- Hardened communication logs so new rows store masked recipient values, no
  message body and filename-only attachment references.
- Masked historical recipients when shown in dashboard and Developer Console
  communication tables.
- Added Windows DPAPI protection for saved SMTP passwords in `app_settings`,
  with backward-compatible read/migration of existing plain `smtp.password`
  rows.
- Preserved business logic: transaction save/posting, PDF generation,
  GST/tax, stock, ledger, numbering and normal communication handoff paths were
  not changed.

### Automated Tests

- `python -m py_compile services\email_service.py services\communication_log_service.py services\dashboard_service.py views\developer_console_view.py tests\test_data_maintenance_and_share.py`
  - Result: passed.
- Focused safety tests:
  `test_smtp_config_reads_app_settings`,
  `test_prepare_email_document_records_delivery_log`,
  `test_communication_retry_sends_pending_email`,
  `test_dashboard_snapshot_includes_communication_status`
  - Result: 4 passed in 1.23s.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 14 passed in 2.79s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: first run timed out at the command limit; rerun passed, 42 passed
    in 140.27s.
- `python -m pytest -q`
  - Result: 149 passed in 183.35s.

### Acceptance Status

- Pre-acceptance safety: passed after fixes.
- SMTP production acceptance: not executed; blocked by missing real SMTP
  credentials/account confirmation in this run.
- WhatsApp production acceptance: not executed; blocked by missing confirmed
  logged-in WhatsApp Web/native session in this run.
- Operator validation: not executed; requires approved real acceptance-test
  customer/supplier records.
- Installer/build validation: not executed; gated until SMTP, WhatsApp and
  operator acceptance pass.

### Remaining Validation

- Run real `Test SMTP`, sample invoice email and sample receipt email on the
  production workstation without documenting credentials.
- Run real WhatsApp link/session/PDF workflow and fallback test on the
  production workstation.
- Validate templates, recipient resolution and document totals using approved
  customer/supplier records.
- Run installer/build validation only after the above acceptance passes.

## 2026-07-10 Communication Delivery Diagnostics Continuation

### Scope

- Added shared SMTP connection/authentication diagnostics through
  `EmailDeliveryService.test_connection()`.
- Added safe WhatsApp link-readiness validation through
  `whatsapp_readiness()`.
- Added Developer Console Communication > Delivery Diagnostics controls for
  SMTP test and WhatsApp link check.
- Preserved business logic: no transaction save/posting, PDF generation,
  GST/tax, stock, ledger, numbering or normal delivery handoff paths were
  changed.

### Automated Tests

- `python -m py_compile services\email_service.py services\share_service.py views\developer_console_view.py tests\test_data_maintenance_and_share.py tests\test_document_and_module_ui.py`
  - Result: passed.
- Focused diagnostics tests:
  `test_smtp_email_service_sends_pdf_attachment`,
  `test_smtp_email_diagnostic_reports_disabled_or_missing_config`,
  `test_whatsapp_links_support_native_and_web_fallbacks`,
  `test_developer_console_exposes_communication_admin_tab`
  - Result: 4 passed in 2.84s.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 14 passed in 2.45s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 42 passed in 87.06s.
- `python -m pytest -q`
  - Result: 149 passed in 107.63s.

### Screenshot Evidence

- `screenshots/after_communication_delivery_diagnostics_1366x768_20260710.png`

### Remaining Validation

- Diagnostics are verified locally. Real production SMTP send acceptance and
  WhatsApp Web/device acceptance still require configured accounts, network
  access and an operator logged into the target workstation session.

## 2026-07-10 Communication Contact Preview Continuation

### Scope

- Added preferred contact-field storage and resolution ordering for
  communication templates by channel/document type.
- Added compact Developer Console controls for preferred contact, template
  preview and sample contact resolution.
- Preserved business logic: transaction save/posting, PDF generation,
  GST/tax, stock, ledger, numbering and delivery handoff behavior remain on
  existing paths.

### Automated Tests

- `python -m py_compile services\communication_template_service.py views\developer_console_view.py tests\test_data_maintenance_and_share.py tests\test_document_and_module_ui.py`
  - Result: passed.
- Focused contact/template tests:
  `test_communication_templates_seed_render_and_resolve_contacts`,
  `test_developer_console_exposes_communication_admin_tab`
  - Result: 2 passed in 2.29s.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 13 passed in 2.27s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 42 passed in 83.18s.
- `python -m pytest -q`
  - Result: 148 passed in 98.65s.

### Screenshot Evidence

- `screenshots/after_communication_contact_preview_1366x768_20260710.png`

### Remaining Validation

- Contact preference and preview behavior are covered locally. Real production
  SMTP and WhatsApp delivery still need operator acceptance with configured
  accounts on the production workstation.

## 2026-07-10 Live Communication Template Wiring Continuation

### Scope

- Wired live Email and WhatsApp actions to the shared communication-template
  render path through `communication_message()` and
  `document_message_context()`.
- Covered Sales Bill, Purchase/Goods Receipt, sales/purchase document screens,
  receipt/payment/account vouchers, inventory entries, stock out/load challans,
  dispatch returns and route settlements.
- Preserved business logic: PDF generation, save/posting, GST/tax, stock,
  ledger, numbering and SMTP/mail-client handoff behavior remain on their
  existing paths.

### Automated Tests

- `python -m py_compile services\communication_template_service.py services\share_service.py views\sales_bill_view.py views\purchase_entry_view.py views\sales_document_view.py views\account_entry_view.py views\inventory_entry_view.py views\stock_out_view.py views\dispatch_return_view.py views\route_settlement_view.py tests\test_data_maintenance_and_share.py`
  - Result: passed.
- Focused live-template tests:
  `test_share_service_renders_active_communication_template`,
  `test_communication_templates_seed_render_and_resolve_contacts`
  - Result: 2 passed in 0.64s.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 13 passed in 1.31s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 42 passed in 59.80s.
- `python -m pytest -q`
  - Result: 148 passed in 82.11s.

### Screenshot Evidence

- No new visual layout was introduced by this continuation. Existing visual
  evidence for the Communication Message Templates UI remains:
  `screenshots/after_communication_templates_1366x768_20260710.png`.

### Remaining Validation

- Template rendering is covered by automated tests. Real production SMTP and
  WhatsApp delivery still need operator acceptance with configured accounts on
  the production workstation.

## 2026-07-10 Communication Templates Continuation

### Scope

- Added shared communication template management and contact-resolution helpers.
- Added Developer Console `Communication` sub-tabs for Delivery and Message
  Templates.
- Seeded safe default templates for sales invoice email, receipt email,
  purchase order email and payment reminder WhatsApp.
- Historical checkpoint: live transaction email/WhatsApp actions still used
  their existing prepared subject/body until the later Live Communication
  Template Wiring Continuation.

### Automated Tests

- `python -m py_compile services\communication_template_service.py views\developer_console_view.py tests\test_data_maintenance_and_share.py tests\test_document_and_module_ui.py`
  - Result: passed.
- Focused template/UI tests:
  `test_communication_templates_seed_render_and_resolve_contacts`,
  `test_developer_console_exposes_communication_admin_tab`
  - Result: 2 passed in 2.09s.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 12 passed in 1.40s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 42 passed in 80.77s.
- `python -m pytest -q`
  - Result: 147 passed in 106.78s.

### Screenshot Evidence

- `screenshots/after_communication_templates_1366x768_20260710.png`

### Remaining Validation

- Template rendering and contact resolution were tested locally. Live template
  selection was wired in the later continuation; production SMTP/WhatsApp
  delivery still needs operator acceptance.

## 2026-07-10 Dashboard Communication Status Continuation

### Scope

- Added Executive Dashboard communication status cards using the existing
  shared `ERPDashboardCard` and `ERPDashboardTable` components.
- Surfaced delivery mode, sent-today count, failed count, pending retry count,
  recent communication history and failed communication rows.
- Fed failed communication rows into dashboard Critical Alerts and Daily Tasks.
- Preserved business logic: dashboard reads communication state only; email
  retry remains in Developer Console.

### Automated Tests

- `python -m py_compile services\dashboard_service.py views\dashboard_view.py tests\test_data_maintenance_and_share.py tests\test_document_and_module_ui.py`
  - Result: passed.
- Focused dashboard tests:
  `test_dashboard_snapshot_includes_communication_status`,
  `test_executive_dashboard_uses_shared_cards_and_real_charts`
  - Result: 2 passed in 2.22s.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 11 passed in 1.76s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 42 passed in 82.54s.
- `python -m pytest -q`
  - Result: 146 passed in 117.52s.

### Screenshot Evidence

- `screenshots/after_dashboard_communication_cards_1366x768_20260710.png`

### Remaining Validation

- Dashboard cards were verified with seeded test logs and the current local
  SQLite workspace. Production SMTP/WhatsApp delivery still needs real
  operator acceptance on the production workstation.

## 2026-07-10 Communication Log And Retry Continuation

### Scope

- Added shared communication delivery logging and bounded failed-email retry
  support.
- Added Developer Console communication administration for SMTP settings,
  pending retry rows and recent delivery history.
- Integrated transaction email actions with delivery logging by passing the
  active SQLite path into `prepare_email_document()`.
- Preserved business logic: no posting, repository, GST, stock, ledger or save
  paths were changed.

### Automated Tests

- `python -m py_compile services\email_service.py services\communication_log_service.py services\share_service.py tests\test_data_maintenance_and_share.py views\developer_console_view.py`
  - Result: passed.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 10 passed in 2.68s.
- `python -m pytest tests\test_document_and_module_ui.py::test_developer_console_exposes_communication_admin_tab -q`
  - Result: 1 passed in 4.90s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 42 passed in 194.23s.
- `python -m pytest -q`
  - Result: 145 passed in 230.37s.

### Screenshot Evidence

- `screenshots/after_communication_admin_1366x768_20260710.png`

### Remaining Validation

- SMTP retry was tested with fake SMTP services; no real email was sent.
- Production SMTP credentials and mail delivery should be verified on the
  operator workstation before enabling background SMTP in live use.

## 2026-07-10 SMTP Email Automation Continuation

### Scope

- Added an opt-in SMTP delivery service for PDF email communication.
- Integrated SMTP into `prepare_email_document()` so existing transaction
  Email buttons inherit the new behavior without additional UI rewiring.
- Preserved safe default behavior: when SMTP is not explicitly enabled,
  Email still opens the operator's default mail client with the PDF path.
- No repository, posting, GST, stock, ledger or layout behavior was changed.

### Automated Tests

- `python -m py_compile services\email_service.py services\share_service.py tests\test_data_maintenance_and_share.py`
  - Result: passed.
- Focused SMTP/email tests:
  `test_smtp_email_service_sends_pdf_attachment`,
  `test_prepare_email_document_uses_smtp_or_falls_back_to_mail_client`,
  `test_email_url_encodes_subject_and_body`
  - Result: 3 passed in 1.79s.
- `python -m pytest tests\test_data_maintenance_and_share.py -q`
  - Result: 7 passed in 2.20s.
- Output/fit UI batch:
  `test_remaining_transaction_output_actions_create_report_pdfs`,
  `test_sales_document_preview_uses_pdf_print_path`,
  `test_all_registered_pages_fit_target_resolutions_without_horizontal_overflow`
  - Result: 3 passed in 71.50s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 41 passed in 163.10s.
- `python -m pytest -q`
  - Result: 141 passed in 248.14s.

### Remaining Validation

- SMTP delivery requires explicit environment configuration and was tested with
  a fake SMTP transport; no real email was sent during tests.
- Superseded by later 2026-07-10 continuations: in-app communication settings,
  delivery history, retry queue and dashboard failure/status cards are now
  covered. Rich message-template/contact-resolution management remains future
  work.

## 2026-07-10 Output Actions And Email Continuation

### Scope

- Added shared mail-client handoff helpers for email preparation without adding
  silent SMTP sending.
- Wired Email on all transaction pages that already generate transaction or
  voucher PDFs.
- Added report-style PDF Preview/Print/PDF/WhatsApp/Email output for inventory,
  stock out/load challan, dispatch return and route settlement screens using
  existing print/share services.
- Rechecked that toolbar action changes did not reintroduce page-level
  horizontal overflow.

### Automated Tests

- `python -m py_compile services\share_service.py views\inventory_entry_view.py views\stock_out_view.py views\dispatch_return_view.py views\route_settlement_view.py views\sales_bill_view.py views\purchase_entry_view.py views\account_entry_view.py views\sales_document_view.py tests\test_document_and_module_ui.py`
  - Result: passed.
- Focused continuation tests:
  `test_email_url_encodes_subject_and_body`,
  `test_remaining_transaction_output_actions_create_report_pdfs`,
  `test_sales_document_preview_uses_pdf_print_path`
  - Result: 3 passed in 15.72s.
- Static placeholder audit:
  - Result: no remaining `Preview`, `Print`, `PDF`, `WhatsApp`, `Email`, or
    `lambda: None` placeholder action wiring in `views`.
- Performance smoke:
  `python -m pytest tests\test_document_and_module_ui.py::test_core_page_open_performance_smoke -q`
  - Result: 1 passed in 4.89s.
- Target fit:
  `python -m pytest tests\test_document_and_module_ui.py::test_all_registered_pages_fit_target_resolutions_without_horizontal_overflow -q`
  - Result: 1 passed in 62.94s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 41 passed in 88.38s.
- `python -m pytest -q`
  - Result: 139 passed in 119.66s.

### Screenshot Evidence

- `screenshots/after_output_actions_stock_entry_1366x768_20260710.png`
- `screenshots/after_output_actions_stock_out_entry_1366x768_20260710.png`
- `screenshots/after_output_actions_dispatch_return_entry_1366x768_20260710.png`
- `screenshots/after_output_actions_route_settlement_1366x768_20260710.png`

### Remaining Validation

- Email handoff opens the default mail client and includes the PDF path in the
  message body. Background SMTP sending and guaranteed automatic attachment are
  intentionally not implemented in this UI pass.
- Physical operator acceptance on the user's real display and DPI settings is
  still recommended.

## 2026-07-09 Pending Action Wiring Continuation

### Scope

- Removed remaining safe no-op transaction actions without changing posting,
  repositories, GST calculation, stock movement, ledger logic or save paths.
- Wired Sales Bill, Purchase Entry and voucher `Preview` buttons to their
  existing PDF print-preview actions.
- Added shared PDF/preview/WhatsApp output to sales and purchase document pages
  using the existing `services.pdf_print`, `services.print_preview` and
  `services.share_service` helpers.
- Hardened shared toolbar feedback so direct page-local buttons and generic
  ERP toolbars acknowledge clicks consistently.

### Automated Tests

- `python -m py_compile widgets\erp_components.py views\sales_document_view.py views\sales_bill_view.py views\purchase_entry_view.py views\account_entry_view.py tests\test_document_and_module_ui.py`
  - Result: passed.
- Focused action/feedback/PDF batch:
  `test_generic_erp_toolbar_unavailable_action_feedback`,
  `test_transaction_layout_installs_feedback_for_local_buttons`,
  `test_sales_document_preview_uses_pdf_print_path`,
  `test_shared_transaction_buttons_feedback_and_unimplemented_message`,
  `test_transaction_toolbars_do_not_leave_silent_disabled_actions`
  - Result: 5 passed in 9.93s.
- Target fit:
  `python -m pytest tests\test_document_and_module_ui.py::test_all_registered_pages_fit_target_resolutions_without_horizontal_overflow -q`
  - Result: 1 passed in 68.20s.
- Performance smoke:
  `python -m pytest tests\test_document_and_module_ui.py::test_core_page_open_performance_smoke -q`
  - Result: 1 passed in 11.09s.
- Totals smoke:
  `test_item_entry_totals_panel_updates_grand_total_and_tax_summary`,
  `test_return_documents_keep_visible_zero_totals_without_source_items`
  - Result: 2 passed in 5.25s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 39 passed in 134.27s.
- `python -m pytest -q`
  - Result: 137 passed in 187.82s.

### Screenshot Evidence

- `screenshots/after_pending_actions_quotation_entry_1366x768_20260709.png`
- `screenshots/after_pending_actions_sales_bill_1366x768_20260709.png`
- `screenshots/after_pending_actions_purchase_entry_1366x768_20260709.png`
- `screenshots/after_pending_actions_receipt_entry_1366x768_20260709.png`

### Remaining Validation

- This 2026-07-09 limitation was superseded by the 2026-07-10 continuation:
  Email and stock/dispatch/route output actions now use shared output handlers.
- Physical operator acceptance on the user's actual monitor/DPI settings is
  still recommended.

## 2026-07-09 Button Feedback, Wiring And Totals Stabilization

### Scope

- Audited shared transaction toolbar/grid action behavior, local page buttons
  through main-window page creation, and transaction totals rendering.
- Fixed silent/no-response toolbar and grid actions through shared components.
- Added full shared totals/tax panels without changing repositories, database
  schema, GST calculation, print generation or posting services.

### Root Cause

- `TransactionToolbar` and `GridActionBar` showed actions whose callbacks were
  `None` as disabled buttons, so users could not tell whether a click was
  accepted.
- Unsupported actions were visually present but did not explain that the
  feature was not implemented for that page yet.
- Sales Bill and Purchase Entry still used an older one-line text summary, and
  the sales-document footer did not show all required total fields.
- Reinstalling page-local button feedback on every page switch would have
  added unnecessary page-open overhead, so feedback is now installed once at
  shell/page creation.

### Automated Tests

- `python -m py_compile widgets\erp_components.py views\main_window.py views\sales_document_view.py views\sales_bill_view.py views\purchase_entry_view.py tests\test_document_and_module_ui.py`
  - Result: passed.
- New focused regression batch:
  `test_shared_transaction_buttons_feedback_and_unimplemented_message`,
  `test_transaction_toolbars_do_not_leave_silent_disabled_actions`,
  `test_item_entry_totals_panel_updates_grand_total_and_tax_summary`,
  `test_return_documents_keep_visible_zero_totals_without_source_items`,
  `test_core_page_open_performance_smoke`
  - Result: 5 passed.
- Fit and stability batch including all registered pages:
  - Result: 6 passed in 108.76s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 36 passed in 149.89s.
- `python -m pytest -q`
  - Result: 134 passed in 205.62s.

### Manual / Smoke Validation

- Core page-open smoke in offscreen mode:
  dashboard 108.7 ms, sales bill 578.1 ms, purchase entry 499.4 ms,
  quotation 529.5 ms, document center 409.8 ms, reports 355.6 ms,
  receipt 315.8 ms, payment 333.6 ms; total 3130.9 ms.
- Static toolbar audit found remaining `None` actions in transaction pages; all
  are now handled by the shared clickable not-available feedback path.

### Screenshot Evidence

- `screenshots/after_button_feedback_quotation_preview_1366x768_20260709.png`
- `screenshots/after_totals_sales_bill_1366x768_20260709.png`
- `screenshots/after_totals_purchase_entry_1366x768_20260709.png`
- `screenshots/after_totals_quotation_1366x768_20260709.png`

### Remaining Risks

- Friendly not-available messages identify future-work actions; those workflows
  still need business implementation before they can perform real Preview,
  Email, Import or other unsupported actions.
- Physical operator acceptance on the user's real display/DPI settings remains
  recommended.

## 2026-07-09 Responsive Reference Completion

### Scope

- Finished the final approved-reference pass for the sales-document footer and
  compact note controls while preserving all repositories, posting services,
  GST calculations, print helpers, database schema and business validation.
- Rechecked Quotation, Receipt Entry and Payment Entry at 1366x768, 1440x900
  and 1920x1080 with page-level horizontal overflow rejected.

### Automated Tests

- `python -m py_compile views\sales_document_view.py widgets\erp_components.py views\account_entry_view.py views\main_window.py`
  - Result: passed.
- `python -m pytest tests\test_document_and_module_ui.py::test_transaction_page_height_tracks_active_viewport -q`
  - Result: 1 passed.
- Target capture/audit script for Quotation, Receipt Entry and Payment Entry
  at 1366x768, 1440x900 and 1920x1080.
  - Result: page-level horizontal scrollbar maximum was 0 for every captured
    page/resolution.
- Operator walkthrough script for Quotation Add Row/F4/Delete/Save, Receipt
  Save/Print Preview and Payment Save/Print Preview.
  - Result: passed; repository writes were stubbed to avoid changing real
    business records.
- `python -m pytest tests\test_document_and_module_ui.py::test_all_registered_pages_fit_target_resolutions_without_horizontal_overflow -q`
  - Result: 1 passed in 93.00s.
- `python -m pytest tests\test_document_and_module_ui.py -q`
  - Result: 31 passed in 120.75s.
- `python -m pytest -q`
  - Result: 129 passed in 176.99s.

### Screenshot Evidence

- Before: `screenshots/reference_align_before_quotation_1366x768_20260709.png`
- After:
  `screenshots/after_responsive_quotation_entry_1366x768_20260709.png`
- After footer scrolled:
  `screenshots/after_responsive_quotation_entry_1366x768_bottom_20260709.png`
- After target matrix:
  `screenshots/after_responsive_quotation_entry_1440x900_20260709.png`,
  `screenshots/after_responsive_quotation_entry_1920x1080_20260709.png`,
  `screenshots/after_responsive_receipt_entry_1366x768_20260709.png`,
  `screenshots/after_responsive_receipt_entry_1440x900_20260709.png`,
  `screenshots/after_responsive_receipt_entry_1920x1080_20260709.png`,
  `screenshots/after_responsive_payment_entry_1366x768_20260709.png`,
  `screenshots/after_responsive_payment_entry_1440x900_20260709.png`, and
  `screenshots/after_responsive_payment_entry_1920x1080_20260709.png`.

### Remaining Validation

- Physical operator acceptance on the user's real monitor/DPI settings remains
  recommended, but the offscreen target-resolution matrix passed for the
  requested desktop resolutions.
- Stop point reached: no additional dashboard/layout enhancements should be
  made until approval.

## 2026-07-09 Reference Image Alignment Pass

### Scope

- Compared the supplied Quotation Entry reference image with the current PyQt
  shell and transaction page.
- Aligned shared shell/theme elements and the sales-document header layout
  toward the reference without changing posting, save, print, GST, repository,
  schema, or validation logic.

### Automated Tests

- `python -m py_compile views\main_window.py views\sales_document_view.py widgets\erp_components.py`
  - Result: passed.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py -k main_window_shell_matches_locked_navigation_surface`
  - Result: 1 passed, 30 deselected.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py -k all_registered_pages_fit`
  - Result: 1 passed, 30 deselected.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py`
  - Result: 31 passed.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests`
  - Result: 129 passed.

### Screenshot Evidence

- `screenshots/reference_align_before_quotation_1366x768_20260709.png`
- `screenshots/reference_align_after_quotation_1366x768_20260709.png`
- `screenshots/reference_align_after_quotation_911x512_20260709.png`

### Remaining Validation

- Physical Windows monitor acceptance remains open.
- Optional next visual pass: exact reference-style document metadata/action bar
  and bottom remarks/totals/tax summary layout, only after approval.

## 2026-07-09 Transaction Grid Stretch-Lock Cleanup

### Scope

- Re-ran the static layout-lock scan for fixed sizes, minimums, geometry calls,
  QSS min-size rules, stretch table modes and page-level scroll policies.
- Cleaned up transaction-grid stretch locks in the edited transaction/account
  table builders while preserving fields, commands, GST/tax summaries, save,
  preview, print and keyboard behavior.

### Automated Tests

- `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py -k all_registered_pages_fit`
  - Result: 1 passed, 30 deselected.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py`
  - Result: 31 passed.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests`
  - Result: 129 passed.

### Screenshot Evidence

- `screenshots/responsive_after_gridlocks_sales_bill_1366x768_20260709.png`
- `screenshots/responsive_after_gridlocks_purchase_entry_1366x768_20260709.png`
- `screenshots/responsive_after_gridlocks_sales_return_entry_1366x768_20260709.png`
- `screenshots/responsive_after_gridlocks_stock_adjustment_entry_1366x768_20260709.png`
- `screenshots/responsive_after_gridlocks_stock_out_entry_1366x768_20260709.png`
- `screenshots/responsive_after_gridlocks_dispatch_return_entry_1366x768_20260709.png`
- `screenshots/responsive_after_gridlocks_route_settlement_1366x768_20260709.png`
- `screenshots/responsive_after_gridlocks_receipt_entry_1366x768_20260709.png`

### Remaining Validation

- Remaining static findings are bounded controls or widgets already covered by
  the all-route fit matrix.
- Physical Windows monitor acceptance remains the only open validation task.

## 2026-07-09 Native 125% DPI Table Fit Continuation

### Scope

- Rechecked representative dense pages under native Qt 125% scaling with a
  1093x614 logical window that renders to 1366x768 physical pixels.
- Covered Dashboard, Receipt Entry, Payment Entry, Sales Bill, Purchase Entry,
  Reports, Document Center, Stock Dashboard and Administration.
- Corrected shared table fitting for DPI-scaled stacked pages and dashboard
  mini-table internal scrolling.

### Automated Tests

- Native 125% capture/check:
  - Window: 1093x614 logical, 1366x768 physical, DPR 1.25.
  - Result: no page-level horizontal overflow, no clipped controls and no
    clipped table headers in the captured pages.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py -k all_registered_pages_fit`
  - Result: 1 passed, 30 deselected.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py`
  - Result: 31 passed.
- `python -m pytest -q D:\PRM_GST_DESKTOP\tests`
  - Result: 129 passed.

### Screenshot Evidence

- `screenshots/responsive_qt125_dashboard_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_receipt_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_payment_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_sales_bill_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_purchase_entry_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_reports_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_document_center_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_stock_dashboard_1366x768_physical_20260709.png`
- `screenshots/responsive_qt125_administration_1366x768_physical_20260709.png`

### Remaining Validation

- Physical Windows monitor acceptance at 1366x768, 1440x900 and 1920x1080.
- No known automated registered-page layout failure remains.

## 2026-07-09 Windows DPI Scaling Certification

### Scope

- Added 125% and 150% logical workspace sizes to the complete 59-route fit
  matrix.
- Checked page and shell controls, page-level horizontal overflow, label/control
  overlap, table-header readability, table width use and internal scrollbars.
- Verified responsive sidebar, wrapping toolbars, transaction summaries,
  return guidance, Stock Dashboard and module-hub tables.

### Automated Tests

- Five-size 59-route fit matrix:
  1366x768, 1440x900, 1920x1080, 1093x614 and 911x512.
  - Result: passed.
- `python -m pytest -q tests\test_document_and_module_ui.py`
  - Result: 31 passed.
- `python -m pytest -q tests`
  - Result: 129 passed.

### Screenshot Evidence

- `screenshots/responsive_dpi150_dashboard_911x512_20260709.png`
- `screenshots/responsive_dpi150_sales_bill_911x512_20260709.png`
- `screenshots/responsive_dpi150_purchase_entry_911x512_20260709.png`
- `screenshots/responsive_dpi150_sales_return_entry_911x512_20260709.png`
- `screenshots/responsive_dpi150_reports_911x512_20260709.png`
- `screenshots/responsive_dpi150_document_center_911x512_20260709.png`
- `screenshots/responsive_dpi150_stock_dashboard_911x512_20260709.png`
- `screenshots/responsive_dpi150_administration_911x512_20260709.png`
- `screenshots/responsive_qt150_dashboard_1366x768_physical_20260709.png`
- `screenshots/responsive_qt150_purchase_entry_1366x768_physical_20260709.png`
- `screenshots/responsive_qt150_reports_1366x768_physical_20260709.png`

### Remaining Validation

- Optional user acceptance on the actual Windows monitors and display drivers.
- No known automated layout or DPI-scaling failure remains.

## 2026-07-09 Responsive Layout Header And Grid Certification

### Scope

- Added all-route checks for clipped label/button text, clipped table headers,
  unused table viewport width and hidden internal horizontal scrollbars.
- Added compact-screen checks for the Sales Bill More Details and Product
  Master Advanced Product Details dialogs.
- Corrected shared visible-page table fitting and internal scrollbar behavior.

### Automated Tests

- `python -m pytest -q tests\test_document_and_module_ui.py`
  - Result: 31 passed.
- `python -m pytest -q tests`
  - Result: 129 passed.

### Screenshot Evidence

- `screenshots/responsive_cert_erp_search_1366x768_20260709.png`
- `screenshots/responsive_cert_excel_import_1366x768_20260709.png`
- `screenshots/responsive_cert_financial_years_1366x768_20260709.png`
- `screenshots/responsive_cert_numbering_series_1366x768_20260709.png`
- `screenshots/responsive_cert_expense_entry_1366x768_20260709.png`
- `screenshots/responsive_cert_journal_entry_1366x768_20260709.png`
- `screenshots/responsive_cert_administration_1366x768_20260709.png`
- `screenshots/responsive_cert_stock_out_entry_1366x768_20260709.png`
- `screenshots/responsive_after_headerfit_financial_years_1366x768_20260709.png`
- `screenshots/responsive_after_headerfit_numbering_series_1366x768_20260709.png`
- `screenshots/responsive_after_headerfit_delivery_challan_entry_1366x768_20260709.png`

### Remaining Validation

- Physical Windows display checks at target resolutions and common DPI/font
  scaling remain a user-acceptance step; offscreen Qt tests cannot fully model
  monitor scaling and platform font rendering.
- No known registered-page fit failure remains.

## 2026-07-09 Responsive Layout All-Route Certification

### Scope

- Enumerated all 59 page factories from `MainWindow.page_factories`.
- Replaced the representative 12-page target-resolution test list with the
  complete live registry.
- Rechecked 1366x768, 1440x900 and 1920x1080 for page-level horizontal
  overflow, content-stack width and shared field-label/control overlap.

### Automated Tests

- `python -m pytest -q tests\test_document_and_module_ui.py`
  - Result: 30 passed.
- `python -m pytest -q tests`
  - Result: 128 passed.

### Result

- All registered pages passed all target resolutions.
- No production UI or business-logic changes were required.
- Existing responsive before/after screenshots remain applicable because this
  pass changed regression coverage only.

## 2026-07-09 Responsive Layout Third Sweep

### Scope

- Re-scanned the UI for remaining layout locks after the note-control and
  receipt/payment continuation.
- Made dense module hub operation panels scroll-safe internally and corrected
  operation-button contrast inside the white operation card.
- Tightened Report Center statement spacing and side-tree heights while
  preserving the tested control-tree readability minimum.

### Automated Tests

- `python -m py_compile views\module_hub_view.py views\report_center_view.py`
  - Result: passed.
- Expanded target resolution audit at 1366x768, 1440x900 and 1920x1080.
  - Result: `target_fit_failures=0`.
- `python -m pytest -q tests\test_document_and_module_ui.py`
  - Result: 30 passed.
- `python -m pytest -q tests`
  - Result: 128 passed.

### Screenshot Evidence

- `screenshots/responsive_after_accounts_module_1366x768_20260709_continued2.png`
- `screenshots/responsive_after_reports_statement_1366x768_20260709_continued2.png`
- `screenshots/responsive_after_masters_module_1366x768_20260709_continued2.png`

### Notes

- The Accounts module screenshot was visually checked after the button contrast
  fix.
- No business-service, posting, reporting calculation, schema, print, voucher,
  numbering or licensing logic was changed.

## 2026-07-09 Responsive Layout Continuation

### Scope

- Reduced note, remarks, narration and similar text editors by about 30% across
  shared helpers, QSS, shell normalization and local page helpers.
- Tightened Receipt Entry and Payment Entry label/control spacing, note height,
  form-card height and recent-entry table row height.
- Extended compact rules to remaining setup/admin/search/report/import/label
  and stock dashboard pages covered by the application navigation.

### Automated Tests

- `python -m py_compile widgets\form_layout_helpers.py widgets\erp_components.py widgets\enter_key_flow.py views\main_window.py views\account_entry_view.py views\route_settlement_view.py views\scheme_master_view.py views\party_master_view.py views\product_master_view.py views\sales_bill_view.py views\simple_master_view.py views\financial_years_view.py views\numbering_series_view.py views\excel_import_view.py views\label_print_view.py views\global_search_view.py views\module_hub_view.py views\developer_console_view.py views\document_center_view.py views\report_center_view.py views\stock_dashboard_view.py views\sales_document_view.py views\inventory_entry_view.py views\stock_out_view.py views\dispatch_return_view.py`
  - Result: passed.
- Expanded target resolution audit at 1366x768, 1440x900 and 1920x1080.
  - Result: `target_fit_failures=0`.
- `python -m pytest -q tests\test_document_and_module_ui.py`
  - Result: 30 passed.
- `python -m pytest -q tests`
  - Result: 128 passed.

### Screenshot Evidence

- `screenshots/responsive_after_receipt_entry_1366x768_20260709_continued.png`
- `screenshots/responsive_after_payment_entry_1366x768_20260709_continued.png`
- `screenshots/responsive_after_document_center_1366x768_20260709_continued.png`
- `screenshots/responsive_after_report_center_1366x768_20260709_continued.png`
- `screenshots/responsive_after_developer_console_1366x768_20260709_continued.png`

### Notes

- Receipt and Payment screenshots were visually checked after capture.
- No database schema, posting, GST calculation, voucher, repository, print
  engine, numbering, licensing or business-service logic was changed.

## 2026-07-09 Responsive Layout Stabilization

### Scope

- Scanned and corrected layout locks from fixed widths/heights/sizes, oversized
  minimum dimensions, absolute/fixed shell sizing, hardcoded QSS min-height and
  min-width values, oversized padding/margins, page-level horizontal scroll
  policies, and grid/table sizing behavior.
- Applied compact responsive rules to the shared shell, Home Dashboard, sales
  pages, purchase pages, inventory pages, masters, accounts/navigation shell,
  reports shell, administration/developer screens, dialogs, and search/filter
  surfaces covered by the UI suite.

### Automated Tests

- `python -m py_compile views\sales_bill_view.py views\product_master_view.py views\login_dialog.py views\stock_dashboard_view.py views\main_window.py widgets\erp_components.py widgets\form_layout_helpers.py tests\test_document_and_module_ui.py`
  - Result: passed.
- Target resolution fit audit at 1366x768, 1440x900, and 1920x1080 across
  major pages.
  - Result: `target_fit_failures=0`.
- `python -m pytest -q tests\test_document_and_module_ui.py`
  - Result: 30 passed.
- `python -m pytest -q tests`
  - Result: 128 passed.

### Screenshot Evidence

- `screenshots/responsive_after_dashboard_1366x768_20260709.png`
- `screenshots/responsive_after_sales_bill_1366x768_20260709.png`
- `screenshots/responsive_after_product_master_1366x768_20260709.png`
- `screenshots/responsive_after_developer_console_1366x768_20260709.png`
- `screenshots/responsive_after_quotation_1440x900_20260709.png`
- `screenshots/responsive_after_dashboard_1920x1080_20260709.png`

### Notes

- Page-level horizontal scroll is blocked by the regression audit; transaction
  tables retain internal horizontal scroll for wide line-item grids.
- Add Row/F4, Delete Row/Del, Save, Preview, and Print behavior remain covered
  by the focused UI tests.
- No database schema, posting, GST calculation, voucher, repository, print
  engine, numbering, licensing, or business-service logic was changed.

## 2026-07-09 Transaction Add Row / F4 Stabilization

### Reproduction

- `tmp/add_row_repro.log`: Quotation Add Row reproduced a Windows access
  violation in `views/sales_document_view.py` during `_redraw_lines()` at
  `self.table.resizeRowsToContents()`.
- `tmp/add_row_repro_after_fix.log`: Quotation Add Row completed with
  `after add_line rows=1`.
- `tmp/add_row_sweep_after_root_fix.log`: Add Row/F4 sweep completed without
  process exit across Sales Bill, Purchase Entry, Quotation, Sales Order,
  Delivery Challan, Sales Return, Purchase Order, Purchase Return, Stock Entry,
  Stock Transfer, Stock Adjustment, Stock Out and Dispatch Return.

### Automated Tests

- `python -m py_compile widgets\erp_components.py views\sales_bill_view.py views\purchase_entry_view.py views\sales_document_view.py views\purchase_document_view.py views\inventory_entry_view.py views\stock_out_view.py views\dispatch_return_view.py tests\test_document_and_module_ui.py`
  - Result: passed.
- `python -m pytest -q tests\test_document_and_module_ui.py`
  - Result: 29 passed.
- `python -m pytest -q tests`
  - Result: 127 passed.

### Screenshot Evidence

- Before framework screenshots: `screenshots/cycle_20260709_framework_before_*`.
- After Add Row screenshots:
  - `screenshots/transaction_addrow_after_sales_bill_20260709.png`
  - `screenshots/transaction_addrow_after_quotation_20260709.png`
  - `screenshots/transaction_addrow_after_purchase_order_20260709.png`
  - `screenshots/transaction_addrow_after_stock_transfer_20260709.png`

### Notes

- No database schema, GST calculation, save, print, PDF, WhatsApp, numbering,
  financial year, licensing, installer or repository logic was changed.
- The local `.git` folder is not usable by `git status` in this checkout, so
  file evidence was gathered with direct filesystem/search commands.
