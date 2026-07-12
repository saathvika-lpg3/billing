# PRM Current Status

## Official PRM BILLING INVENTORY V1.0 release lock - 2026-07-12

- Current display version is **V1.0** and technical version is `1.0.0`.
  `RELEASE_LOCK.md` owns the accepted-product contract and future change gate.
- Runtime, Windows executable and installer metadata share the same authoritative
  identity. Database schema/migration identifiers and historical 1.7.x evidence
  are intentionally not renumbered.
- Official V1.0 preserves the existing AppId/executable/install path and exact
  seven-entry cleanup allowlist, so internal 1.7.8 upgrades in place without
  broadening deletion or replacing database/licence/settings/client assets.
- Version-source, test, artifact and copy verification evidence is stored only
  in the safe dated `release_validation/2026-07-12_v1.0` folder; it contains no
  private licence, client database, credentials or session files.
- Certified V1.0 setup: 43,187,187 bytes, SHA-256
  `04505DBEC75642B6345D547F4FC1536E3D901AE79DA3F6A0D0E2CAEF7CFBA584`.
  Its frozen executable is version `1.0.0`, 9,842,776 bytes, SHA-256
  `0C521954DE709E1B1FA6CE5EBBD25CBBE9E9188F63D883ECEE9F8429F7748550`.
- Final verification passed: compile, **226 tests**, 59/59 route audit, package
  privacy, clean install, authenticated installed UI, preserving uninstall,
  real local upgrade and exact responsive `PRM BILLING INVENTORY V1.0 Login`.
- The real upgrade preserved the existing client database and `.prmlic`
  byte-for-byte. Windows code signing remains external because no organization
  certificate was supplied; physical printer, live SMTP/WhatsApp and government
  GST credential acceptance remain separate operational gates.

## Branding correction and certified installer 1.7.8 - 2026-07-12

- Status: branding ownership, Dispatch Summary navigation, cleanup, installer
  build, clean/upgrade/uninstall certification and the real local upgrade have
  passed their code-controlled release gates.
- `ProductBrandHeader` owns the immutable PRM identity in the login product
  area and fixed desktop shell. The application/window icon and Inno Setup
  setup/uninstall icon also resolve from the original PRM assets.
- `ClientCompanyIdentityCard` owns only licensed-company identity surfaces such
  as Dashboard Company Information and Company Settings/Profile. Shared print
  headers use the client company and its uploaded logo, while shared print
  footers identify PRM Software. The client card is never embedded in the
  fixed product header.
- Dispatch Summary has one canonical route and one report implementation:
  `reports:daily_dispatch_summary` -> `daily_dispatch_summary` in Report
  Center. Sidebar, Dashboard, Reports and Global Search reuse it and apply the
  existing report-role and plan filters.
- Certified 1.7.8 setup: 43,187,727 bytes, SHA-256
  `0C57293DECCC94ED6FDE2CD6177DBA3D6DB55DFF638A02B98CA2C1D5B5E6B1A2`.
  The real installed executable matches the certified frozen hash and its
  database/licence were byte-identical across the upgrade.
- 1.7.8 supersedes 1.7.7 for upgrades. It removes only obsolete partial
  `numpy`/`lxml`, old runtime docs and legacy `requirements.txt` paths that Inno
  otherwise retained from 1.7.6. This resolves the pre-startup
  `numpy.short`/openpyxl script exception without touching client-owned data.
- Cleanup quarantined uncertain/client-facing historical output and deleted
  only generated/rebuildable material. The exact inventory, hashes and measured
  size accounting are in `audit/cleanup_manifest_20260712.md`.

## Production stabilization release - 2026-07-12

- Status: **all code-controlled release gates passed** for client branding,
  Product UOM/pack conversion, master readability, global smart dropdowns, GST
  propagation, PDF attachment delivery, list printing, dispatch totals and
  shared print parity.
- Product save is transactional across `items`, `product_packs` and
  product-specific UOM conversions. The prior consistency rule confused a
  valid purchase-to-sale conversion with inconsistent pack data; validation is
  now explicit, positive-factor based and covered for single and multi-UOM
  products.
- Tax slabs are read from both supported GST master sources. Item GST wins,
  then HSN tax code, then category default; party place-of-supply determines
  split intrastate tax versus IGST across the shared transaction family.
- Client `.prmlic` selection is **not bound to one filename**. The installer
  accepts any valid export ending in `.prmlic` (for example `lakshmi.prmlic` or
  `sairam.prmlic`), validates its content, and installs it internally as
  `license/client.prmlic` for that client installation.
- Runtime evidence: 59/59 live routes clean at three supported resolutions, 35
  typed-widget files with zero unsafe API use, eight performance checks within
  limits, and **213 automated tests passed**.
- Release target: installer **1.7.6**. The installed client runtime has no
  PowerShell dependency; its only unavoidable external release items are mail
  account/client setup and an optional commercial code-signing certificate.
- Certified artifact: `installer_output/PRM_Billing_Inventory_Setup.exe`,
  51,873,806 bytes, SHA-256
  `E769D2216540AE04632ACA0E419D013A3D1020C67DD5ED12B865BDDF985FA8E7`.
  Clean install, frozen launch, installed UI smoke, byte-identical upgrade and
  uninstall data preservation passed.

## Fast-track commercial UI release - 2026-07-11

- Status: **release gates passed** for the Product Master crash/redesign,
  horizontal actions, shared transaction layout, Grand Total visibility,
  button feedback, route wiring, screen fit and installer 1.7.5.
- Product Master now uses the shared master-entry language and typed widget
  value utilities. The invalid QComboBox line-edit API calls were removed at
  their source and the UoM persistence defect in `MasterRepository` was fixed.
- Sales Bill and Buy Stock/Purchase Entry now share the same transaction decks,
  action order, item-grid actions, totals and tax summary used by the document
  transaction family.
- Evidence: 59 live routes with no detected issue; 33 UI source files with zero
  typed widget API mismatch; five-resolution screen-fit pass; full suite 190
  passed; frozen-startup, installed-resource UI and uninstall checks passed.
- Release artifact: `installer_output/PRM_Billing_Inventory_Setup.exe`, version
  1.7.5, 51,836,487 bytes, SHA-256
  `C54E99B4B714E20D5D7DE2958415ED6FEDA35D9E39D2C694B927F965AF41BFFA`.

This file is updated from a real audit of the current workspace state.

## Historical v1.7.4 installer/license checkpoint - 2026-07-11

- Repaired the Python desktop installer without replacing the existing license
  system: builds now use a sanitized unbound SQLite seed, upgrades preserve the
  client database, and all 12 mandatory `.prmlic` fields remain required.
- Verified the supplied license, a real v1.7.4 build/install, first-machine
  activation, admin creation and launch to the responsive login dialog.
- Added focused installer/license regressions (6 passed), portable build paths,
  safe PyInstaller selection and client-runtime-data exclusions. At this
  checkpoint the native suite passed 177 tests and the v1.7.4 installer compiled. See
  `INSTALLER.md`, `TEST_REPORT.md` and `CURRENT_STATUS.md` for evidence.

## Status summary
- Last completed module: Code-controlled Sales, Purchase, Return, Receipt, Payment, Journal/Contra and Stock Transfer lifecycle posting/reversal is implemented with deterministic reconciliation coverage.
- Current working module: Completed 2026-07-11 UI stabilization and installer 1.7.5 certification on `business-flow-audit-20260710`.
- Recent progress: Local safety commit `acfb396` preserves the first business-flow tranche. Live list-to-edit, reason-required cancellation, warehouse persistence, round-off posting, party outstanding, closed-year/duplicate/negative-stock validation, active financial/GST reports, HSN Summary and read-only integrity diagnostics are implemented.
- Current automated evidence: final native suite `190 passed`; live UI inventory `59/59`; widget API audit `33 files / 0 findings`; performance `8/8`; five-resolution UI fit and installer 1.7.5 certification passed.
- Recent progress: Branch/Warehouse/Cost Center foundation masters now have schema migration support, UI definitions, branch-aware warehouse selection, save validation, and verification tests.
- Recent progress: Added Route/Salesman/Vehicle/Transporter foundation masters, including schema/bootstrap support, generic master UI definitions, admin navigation wiring, lookup helper methods, save validation, and UI tests for combo ID persistence.
- Recent progress: Added Bank, Tax Code and Payment Terms foundation masters, including schema/bootstrap support, generic master UI definitions, account setup navigation, save validation, and repository/UI verification.
- Recent progress: Completed the first Purchase Invoice compatibility pass for the shared print engine by reusing the existing transaction-pdf path and adding normalization support for supplier-style payload fields without introducing a duplicate purchase print engine.
 - Recent progress: Completed receipt and payment voucher compatibility pass. Added `_normalize_voucher_entry` helper to `services/pdf_print.py` and ensured `write_voucher_pdf` uses normalized payloads. Voucher layout rendering remains centralized in the shared `_draw_voucher` function.
 - Recent progress: Refactored shared print headers and title strips into reusable section helpers (`_section_company_center_text`, `_section_title_strip`) and updated callers in report, transaction and voucher headers. This reduces duplication and speeds future migrations.
- Recent progress: Added `_section_party_block` and `_section_document_details` helpers in `services/pdf_print.py`, then wired transaction and voucher rendering to use these reusable template sections while preserving existing A2/A4 support and page numbering.
- Pending modules: Invoice-allocation/true aging schema, batch-ID/expiry movement, canonical base-UOM conversion, cancellable Stock Entry/Adjustment headers, landed-cost allocation, and credentialed government GST submission.
- Known issues: The inherited live/demo database contains legacy reconciliation failures recorded in `audit/business_flow_audit.json`. They are classified as data issues and are not auto-balanced or silently suppressed. See `docs/BUSINESS_FLOW_MATRIX.md` for exact business impact and the 59-operation classification.
- Recent fix: Hardened the sales Add Item flow so missing product caches, empty selections, malformed numeric values, and missing product fields now show safe user messages and keep the app open instead of crashing.
- Recent UI rollout: Added reusable ERP transaction components in widgets/erp_components.py and applied them to the sales bill, purchase entry, sales document, and inventory entry views to standardize page headers, field boxes, and transaction toolbars without changing business logic.
- Recent UI cycle 2026-07-09: Applied the locked Quotation Entry design language to the shared desktop shell by registering Segoe UI for readable Qt/offscreen screenshots, widening command search, switching the module ribbon to the approved dark-blue style, expanding the left rail with daily transaction shortcuts, and preserving existing business/service/database code paths.
- Recent UI cycle 2026-07-09: Fixed shared ERP grid keyboard navigation to use the actual key event modifiers, preventing stale global Shift state from moving Tab to the wrong editable column during long UI sessions.
- Transaction framework cycle 2026-07-09: Added one reusable `TransactionPageLayout`, canonical `TransactionToolbar`, named transaction cards and `ERPTransactionGrid` to the existing shared ERP UI framework.
- Transaction framework cycle 2026-07-09: Migrated current sales, purchase, inventory, dispatch, route settlement and account-entry screens to the shared framework while preserving their existing repository, service, GST, voucher, print, SQLite and licensing paths.
- Transaction framework cycle 2026-07-09: Fixed active stacked-page height calculation, wide-grid horizontal scrolling, Sales Bill advanced-control overlap and local item-row Delete behavior.
- Transaction stabilization 2026-07-09: Reproduced the non-Sales-Bill Add Row/F4 crash, traced it to a null Qt item delegate in `SalesDocumentView`, removed the delegate reset, and moved item-grid Add Row focus behavior into shared `ERPItemGrid`, `TransactionGridPanel`, and `GridActionBar` components.
- Transaction stabilization 2026-07-09: Sales Bill, Purchase Entry/Goods Receipt, Quotation, Sales Order, Delivery Challan, Sales Return, Purchase Order, Purchase Return, Stock Entry, Stock Transfer, Stock Adjustment, Stock Out and Dispatch Return were verified for safe Add Row/F4/Delete behavior without changing save, print, GST, repository, numbering or schema logic.
- Executive dashboard cycle 2026-07-09: Replaced the Home Dashboard Work Center panel with a vertically scrollable ERP executive dashboard using shared `ERPDashboardCard`, `ERPDashboardTable`, `ERPLineChart`, `ERPPieChart`, and `ERPBarChart` components.
- Executive dashboard cycle 2026-07-09: Added dashboard sections for company information, business summary, sales/purchase KPIs, cash/bank, receivables, payables, stock value, stock/expiry/dispatch/order alerts, top customers/products, recent documents, daily tasks, backup, database health, and application version.
- Executive dashboard cycle 2026-07-09: Recent Sales, Recent Purchase, Recent Receipts, and Recent Payments rows now route to the existing related document/voucher screens on double-click or Enter; no business posting logic was changed.
- Executive dashboard cycle 2026-07-09: Reduced the left ERP Navigator rail from 220 px to 202 px.
- Responsive layout stabilization 2026-07-09: Relaxed fixed sidebar/topbar/ribbon, QSS, shared form, table/grid, card, dialog, transaction, master, dashboard and developer/admin page locks so major pages fit at 1366x768, 1440x900 and 1920x1080 without page-level horizontal overflow.
- Responsive layout stabilization 2026-07-09: The ERP Navigator rail now uses a compact responsive 168-188 px width band instead of the previous fixed 202 px rail; business logic, required controls, GST/tax/total summaries, Add Row/F4, Delete Row/Del, Save, Preview and Print workflows were preserved.
- Responsive layout continuation 2026-07-09: Reduced note, remarks, narration and address editor heights by about 30%, tightened Receipt Entry and Payment Entry label-to-control gaps, and extended compact rules to Document Center, Report Center, search/import/label, stock dashboard, setup/admin, scheme and route settlement pages.
- Responsive layout third sweep 2026-07-09: Module hub operation panels now use compact internal vertical scroll areas with readable in-card quick buttons, and Report Center statement views were tightened while preserving tested statement-control readability.
- Responsive layout all-route certification 2026-07-09: The target-resolution regression now enumerates all 59 registered page factories automatically; every route passed at 1366x768, 1440x900 and 1920x1080 without page-level horizontal overflow or shared field-label/control overlap.
- Responsive table certification 2026-07-09: Shared visible-page table fitting now prevents clipped headers, distributes unused viewport width and exposes internal horizontal scrollbars for wide tables; all-route clipping and dialog-fit checks pass.
- Windows DPI certification 2026-07-09: The shell now reaches 900x500 logical pixels, uses responsive low-width sidebar bands and wrapping toolbars, and all 59 routes pass both 125% and 150% logical workspace checks.
- Native 125% DPI continuation 2026-07-09: Shared table fitting now also runs from current table geometry when Qt/offscreen scaling reports the stacked page as not visible, dashboard mini tables no longer hard-disable horizontal scrolling, and non-transaction tables get a second fill pass after geometry recalculation.
- Transaction grid stretch-lock cleanup 2026-07-09: Remaining local stretch resize modes were removed from transaction/item grids and account recent-entry grids, with practical interactive starting widths added for item/description columns so wide tables keep overflow inside the grid.
- Reference image alignment 2026-07-09: The shell and Quotation/Sales Document surface were aligned toward the supplied approved reference image using shared UI components and themes: active ribbon state, responsive top info blocks, compact PRM sidebar, three-card transaction header and reference-style grid action colors.
- Responsive reference completion 2026-07-09: The Sales Document footer now uses shared Remarks/Terms, Totals and Tax Summary cards with a visible `No data available` empty state; sales Notes and receipt/payment narration controls were further reduced; Quotation, Receipt and Payment were captured at 1366x768, 1440x900 and 1920x1080; all-route fit, 31 UI tests and the 129-test full suite passed.
- Button/totals stabilization 2026-07-09: Shared ERP buttons now show hover/pressed/focus/recent-click/busy feedback; unsupported transaction/grid actions show a friendly not-available message instead of silently doing nothing; shared `TransactionTotalsPanel` and `TransactionTaxSummaryPanel` now show full totals and highlighted Grand Total on Sales Bill, Purchase/Goods Receipt, Quotation, Sales Order, Delivery Challan, Purchase Order and inherited document pages; 36 focused UI tests and the 134-test full suite passed.
- Pending action wiring 2026-07-09: Removed remaining safe no-op Preview paths by wiring Sales Bill, Purchase Entry and account vouchers to their existing PDF preview flows; added shared PDF/WhatsApp output for Quotation, Sales Order, Delivery Challan, Sales Return, Purchase Order and Purchase Return using existing print/share services; generic and page-local buttons now use shared feedback; 39 focused UI tests and the 137-test full suite passed.
- Output action continuation 2026-07-10: Added shared email mail-client handoff, wired Email on existing PDF-capable transaction/voucher/document screens, and added report-PDF Preview/Print/PDF/WhatsApp/Email output for Stock Entry, Stock Transfer, Stock Adjustment, Stock Out / Load Challan, Dispatch Return and Route Settlement. Static action audit found no remaining output placeholders in `views`; 41 focused UI tests and the 139-test full suite passed.
- SMTP email continuation 2026-07-10: Added opt-in SMTP PDF delivery through `services/email_service.py` and integrated it into `prepare_email_document()` while preserving mail-client handoff when SMTP is not enabled. Focused email/share tests, focused UI tests and the 141-test full suite passed.
- Communication log continuation 2026-07-10: Added shared communication delivery history and failed-email retry support through `services/communication_log_service.py`, extended SMTP settings to read from local `app_settings`, wired transaction email actions to record results, and added a compact Developer Console Communication tab for SMTP settings, pending retries and recent history. Focused communication tests, focused UI tests and the 145-test full suite passed.
- Locked reference print/report validation 2026-07-10: Found and rendered the locked Downloads references, added shared A4 portrait two-sided statement PDFs for Profit & Loss and Balance Sheet, rendered receipt/payment reference/instrument details, regenerated before/after PDF evidence, and locked the paper/orientation, statement-structure and voucher-identity regressions. Full suite passed 159.
- Git repair and print engine lock 2026-07-10: Preserved the empty invalid `.git`, repaired a valid local `main` repository with official origin `https://github.com/saathvika-lpg3/billing.git`, added `.gitignore`, persisted print-template orientation, locked A4/A2 portrait/landscape transaction structure, generated validation artifacts, and passed the 160-test full suite.
- Dashboard communication continuation 2026-07-10: Added Executive Dashboard Communication Status and Failed Communications cards through the shared dashboard framework, with failed communication rows feeding Critical Alerts and Daily Tasks. Focused dashboard/communication tests, focused UI tests and the 146-test full suite passed.
- Communication templates continuation 2026-07-10: Added shared communication template storage, default template seeding, safe placeholder rendering and contact-resolution helpers through `services/communication_template_service.py`, plus Developer Console Communication sub-tabs for Delivery and Message Templates. Focused communication/template tests, focused UI tests and the 147-test full suite passed.
- Live communication template wiring 2026-07-10: Wired transaction Email/WhatsApp actions through shared `communication_message()` and `document_message_context()` helpers while preserving existing PDF generation, save/posting, GST/tax, stock, ledger, numbering and delivery handoff paths. Focused live-template tests, focused UI tests and the 148-test full suite passed.
- Communication contact preview 2026-07-10: Added central preferred contact-field storage/resolution and compact Developer Console Message Templates preview controls so operators can verify rendered text and resolved contact fields before using templates. Focused contact/template tests, focused UI tests and the 148-test full suite passed.
- Communication delivery diagnostics 2026-07-10: Added shared SMTP connection/authentication diagnostics, safe WhatsApp link readiness validation and compact Developer Console Delivery Diagnostics controls without sending business documents or changing transaction output paths. Focused diagnostics tests, focused UI tests and the 149-test full suite passed.
- Production acceptance safety stabilization 2026-07-10: Created a source-only pre-acceptance backup, hardened communication logs to store masked recipients/no message bodies/filename-only attachments, masked historical communication rows in dashboard and Developer Console displays, and added Windows DPAPI protection plus read-time migration for saved SMTP passwords. Focused safety tests, communication/share tests, UI tests and the 149-test full suite passed.
- Production readiness route/print audit 2026-07-10: Created a fresh
  source-only backup at `backups/production_readiness_source_20260710_093457.zip`,
  traced the live 59-route `MainWindow.page_factories` registry, confirmed 18
  transaction routes on the shared framework, captured current-state Report
  Center/Quotation/Receipt/Payment screenshots, and documented print/report
  parity evidence plus external blockers. Py_compile, print/report parity,
  focused UI route/layout tests and the full 149-test regression suite passed.
  No business or UI code was changed in this continuation.
- Production readiness hidden-state continuation 2026-07-10: Fixed the Report
  Center Account Closing / CA Export panel height so optional controls are not
  covered by the table, added regression coverage for that hidden panel, added
  an all-route visible button click-receiver audit, captured the corrected CA
  Export screenshot, and reran py_compile, 44 UI tests, 21 print/report parity
  tests and the 151-test full regression suite.
- Production readiness print/list continuation 2026-07-10: Re-checked the
  attachment/reference folders and confirmed the locked PDF/report screenshots
  are still unavailable as readable files in this run. Fixed a central print
  metadata fallback gap so `sales_return` no longer resolves with a blank
  template key, added Document Center print mapping coverage, added Document
  Center subview coverage, added Module Hub operation-state coverage, and reran
  py_compile, 46 UI tests, 22 print/report parity tests and the 154-test full
  regression suite.
- Production readiness accounting-preview continuation 2026-07-10: Added
  regression coverage proving Report Center Profit & Loss and Balance Sheet
  generate non-empty PDFs and invoke the shared print-preview layer. The
  combined UI/print suites passed 69 tests and the full regression suite passed
  155 tests.
- Production readiness preview-detector continuation 2026-07-10: Fixed
  print-preview paper/orientation detection for large generated PDFs by
  stream-scanning for `/MediaBox`; added generated A4 portrait and A2 landscape
  detection coverage. Print/report parity passed 23 tests and the full
  regression suite passed 156 tests.
- Recent master rollout: Extended the same ERP page-shell components to the product master, party master, and simple master forms so masters now share the same header and field-box structure as the transaction views.
- Recent fix: Clarified that the historical SQLiteSource module is a SQLite-only compatibility wrapper for desktop usage, and the product lookup path now safely reads from the local SQLite tables items, suppliers, and product_packs.
- Future requirements: Print and reporting must include A2 Landscape support for report preview, export, and bulk print. Multi-page reports must be validated for repeated header/footer, page numbers, total pages, and last-page totals. The Communication Engine should support WhatsApp sharing for invoices, receipts, payment reminders, outstanding statements, ledgers, reports, purchase orders, and PDFs. All important controls should have helpful tooltip/help text, and forms should include placeholder/sample text for operators and demo/testing. Reuse `D:\PRM_BILLING_INVENTORY` as a reference implementation where existing working code already exists, especially for Profit & Loss and Balance Sheet formatting.
- Files already modified: AI_GUIDE/00_PROJECT_RULES.md, AI_GUIDE/101_DEVELOPMENT_PRINCIPLES.md, PRM_CURRENT_STATUS.md, FMCG_ANALYSIS.md, FMCG_EXECUTION_PLAN.md, services/company_profile_service.py, services/developer_audit_service.py, services/financial_year_service.py, services/numbering_series_service.py, services/master_repository.py, services/sqlite_source.py, tests/test_developer_dashboard.py, tests/test_financial_year_and_numbering_engines.py, tests/test_master_repository_and_industry.py, tests/test_document_and_module_ui.py, views/main_window.py, views/developer_console_view.py, views/module_hub_view.py, views/simple_master_view.py, views/financial_years_view.py, views/numbering_series_view.py, AI_GUIDE/FINANCIAL_YEAR_ENGINE.md, AI_GUIDE/NUMBERING_ENGINE.md, PRM_DEPENDENCY_GRAPH.md.
- Next safe implementation step: Add the Financial Year UI and Numbering Series UI integration layer, then migrate existing transaction modules to the new services in a controlled way.
 - Recent change: Added a canonical DB path resolver and minimal first-run schema bootstrap in `services/sqlite_source.py` to ensure a deterministic SQLite path and safe initial tables on first run.
 - Recent change: Added a UI profile adapter `services/ui_profile_adapter.py` and `services/business_rules.profile_metadata()` to expose UI-friendly profile metadata for views.
 - Recent change: Added lightweight DB startup diagnostics `services/db_diagnostics.py` that logs DB info to `logs/db_startup.log`.
 - Recent change: Wired `services/ui_profile_adapter` into `views/sales_bill_view.py` and `views/purchase_entry_view.py` so controls auto-configure visibility and placeholders based on profile metadata.
 - Recent change: Wired `services/ui_profile_adapter` into `views/sales_bill_view.py`, `views/purchase_entry_view.py`, and `views/sales_document_view.py` to auto-configure controls by profile.
 - Recent change: Wired `services/ui_profile_adapter` into `views/simple_master_view.py` to adapt master form controls by profile where applicable.
 - Recent change: Replaced '(required)' placeholder with a visible required badge in `widgets/form_layout_helpers.py` and updated views to use `mark_widget_required()`.
 - Recent change: Added `services/ui_adapter_runner.py` to centralize applying profile attributes to widgets and refactored `views/simple_master_view.py` to build `_profile_widget_map` and use the runner.
 - Recent change: Refactored `views/sales_bill_view.py` to use `services/ui_adapter_runner.apply_profile_to_widgets()` for applying profile-driven visibility/enabled/required attributes to entry controls (with fallback).
 - Recent change: Refactored `views/purchase_entry_view.py` to use `services/ui_adapter_runner.apply_profile_to_widgets()` and added missing imports; tests validated.
 - Recent change: Refactored `views/sales_document_view.py` to use `services/ui_adapter_runner.apply_profile_to_widgets()` for item-entry controls and updated fallback behaviour; tests validated.

### Recent changes (Phase 3, 4 & 5 foundation)
- Party Master Phase 3: Extended customer/supplier fields, validation, and migrations. Files modified: `views/party_master_view.py`, `services/master_repository.py`, `tests/test_party_master.py`.
- UOM & Price foundation (Phase 4): Added `services/uom_price_service.py`, wired schema creation into `MasterRepository.ensure_schema()`, and added `tests/test_uom_price_service.py`.
- Company audit completion: Added `company_profile_audit` logging table, Developer Dashboard access gating, Company Admin field protection, and service-level audit writes for company profile updates. Files modified: `services/company_profile_service.py`, `services/developer_audit_service.py`, `views/main_window.py`, `views/developer_console_view.py`, `views/simple_master_view.py`, `tests/test_developer_dashboard.py`.
- Phase 5 foundation: Added reusable Financial Year and Universal Numbering services, seeded schemas, and focused engine tests. Services added: `services/financial_year_service.py`, `services/numbering_series_service.py`. Tests added: `tests/test_financial_year_and_numbering_engines.py`. Docs added: `AI_GUIDE/FINANCIAL_YEAR_ENGINE.md`, `AI_GUIDE/NUMBERING_ENGINE.md`, `PRM_DEPENDENCY_GRAPH.md`.
- Branch/Warehouse/Cost Center foundation: Added `views/simple_master_view.py` master specs, `services/master_repository.py` schema and save support, and `tests/test_master_repository_and_industry.py` plus `tests/test_document_and_module_ui.py` verification.

### Verification performed
- 2026-07-09 UI cycle: `python -m py_compile app.py config\qt_fonts.py views\main_window.py tests\test_document_and_module_ui.py widgets\erp_components.py` passed.
- 2026-07-09 UI cycle: Launch/navigation/theme smoke opened Dashboard, Quotation, Purchase Order and Reports, toggled dark theme, and returned to Quotation successfully.
- 2026-07-09 UI cycle: `python -m pytest -q D:\PRM_GST_DESKTOP\tests\test_document_and_module_ui.py` passed: 22 passed.
- 2026-07-09 UI cycle: `python -m pytest -q D:\PRM_GST_DESKTOP\tests` passed: 120 passed.
- 2026-07-09 UI cycle: performance/memory smoke opened six key pages in 5.44 seconds with a 3.92 MB Python allocation peak under `tracemalloc`.
- 2026-07-09 UI cycle: before/after Quotation screenshots captured at `screenshots/cycle_20260709_before_quotation_entry.png` and `screenshots/cycle_20260709_after_quotation_entry.png`.
- 2026-07-09 transaction framework: focused UI and row-operation tests passed: 32 passed.
- 2026-07-09 transaction framework: full regression suite passed: 124 passed.
- 2026-07-09 transaction framework: 17 transaction routes opened successfully; dark theme toggle passed; SQLite integrity returned `ok`.
- 2026-07-09 transaction framework: performance/memory smoke completed in 15.00 seconds with a 5.20 MB peak Python allocation.
- 2026-07-09 transaction framework: representative before/after screenshots captured under `screenshots/cycle_20260709_framework_*`.
- 2026-07-09 responsive all-route certification: focused UI suite passed 30 tests and the full suite passed 128 tests after replacing the representative fit list with all 59 registered page factories.
- 2026-07-09 responsive table certification: focused UI suite passed 31 tests and the full suite passed 129 tests; Financial Years, Numbering Series and Delivery Challan after screenshots were captured at 1366x768.
- 2026-07-09 Windows DPI certification: the five-size 59-route matrix passed, focused UI tests passed 31, full tests passed 129, and Qt-native 150% screenshots rendered at 1367x768 physical pixels.
- 2026-07-09 Native 125% DPI continuation: Qt-native 125% screenshots rendered at 1366x768 physical pixels for Dashboard, Receipt, Payment, Sales Bill, Purchase Entry, Reports, Document Center, Stock Dashboard and Administration; five-size all-route fit passed, focused UI suite passed 31, and full suite passed 129.
- 2026-07-09 transaction grid stretch-lock cleanup: fresh 1366x768 screenshots captured for Sales Bill, Purchase Entry, Sales Return, Stock Adjustment, Stock Out, Dispatch Return, Route Settlement and Receipt Entry; five-size all-route fit passed, focused UI suite passed 31, and full suite passed 129.
- 2026-07-09 reference image alignment: before/after Quotation screenshots captured at `screenshots\reference_align_before_quotation_1366x768_20260709.png`, `screenshots\reference_align_after_quotation_1366x768_20260709.png`, and `screenshots\reference_align_after_quotation_911x512_20260709.png`; shell contract, five-size fit matrix, focused UI suite and full 129-test suite passed.
- 2026-07-09 executive dashboard: before screenshot captured at `screenshots/dashboard_executive_before_20260709.png`.
- 2026-07-09 executive dashboard: after screenshots captured at `screenshots/dashboard_executive_after_20260709.png` and `screenshots/dashboard_executive_after_scrolled_20260709.png`.
- 2026-07-09 executive dashboard: `python -m py_compile widgets\erp_components.py services\dashboard_service.py views\dashboard_view.py views\main_window.py views\document_center_view.py views\account_entry_view.py tests\test_document_and_module_ui.py` passed.
- 2026-07-09 executive dashboard: `python -m pytest -q tests\test_document_and_module_ui.py` passed: 28 passed.
- 2026-07-09 executive dashboard: `python -m pytest -q tests` passed: 126 passed.
- 2026-07-09 transaction Add Row/F4: crash reproduction saved to `tmp\add_row_repro.log`; post-fix direct check saved to `tmp\add_row_repro_after_fix.log`; page sweep saved to `tmp\add_row_sweep_after_root_fix.log`.
- 2026-07-09 transaction Add Row/F4: `python -m py_compile widgets\erp_components.py views\sales_bill_view.py views\purchase_entry_view.py views\sales_document_view.py views\purchase_document_view.py views\inventory_entry_view.py views\stock_out_view.py views\dispatch_return_view.py tests\test_document_and_module_ui.py` passed.
- 2026-07-09 transaction Add Row/F4: `python -m pytest -q tests\test_document_and_module_ui.py` passed: 29 passed.
- 2026-07-09 transaction Add Row/F4: `python -m pytest -q tests` passed: 127 passed.
- 2026-07-09 transaction Add Row/F4: after screenshots captured at `screenshots\transaction_addrow_after_sales_bill_20260709.png`, `screenshots\transaction_addrow_after_quotation_20260709.png`, `screenshots\transaction_addrow_after_purchase_order_20260709.png`, and `screenshots\transaction_addrow_after_stock_transfer_20260709.png`.
- 2026-07-09 pending action wiring: `python -m py_compile widgets\erp_components.py views\sales_document_view.py views\sales_bill_view.py views\purchase_entry_view.py views\account_entry_view.py tests\test_document_and_module_ui.py` passed; focused action/feedback/PDF tests passed 5; all-route target fit passed; performance smoke passed; focused UI suite passed 39; full regression passed 137.
- 2026-07-10 live communication template wiring: py_compile passed for the shared template/share services and wired transaction views; focused live-template tests passed 2; `tests\test_data_maintenance_and_share.py` passed 13; `tests\test_document_and_module_ui.py` passed 42; full regression passed 148.
- 2026-07-10 communication contact preview: py_compile passed for the communication template service, Developer Console and tests; focused contact/template tests passed 2; `tests\test_data_maintenance_and_share.py` passed 13; `tests\test_document_and_module_ui.py` passed 42; full regression passed 148.
- 2026-07-10 communication delivery diagnostics: py_compile passed for email/share services, Developer Console and tests; focused diagnostics tests passed 4; `tests\test_data_maintenance_and_share.py` passed 14; `tests\test_document_and_module_ui.py` passed 42; full regression passed 149.
- 2026-07-10 production acceptance safety stabilization: source-only backup created at `backups\pre_acceptance_source_20260710_082242.zip`; py_compile passed for email/log/dashboard/developer-console safety changes; focused safety tests passed 4; `tests\test_data_maintenance_and_share.py` passed 14; `tests\test_document_and_module_ui.py` rerun passed 42 after an initial command timeout; full regression passed 149.
- 2026-07-10 production readiness route/print audit: source-only backup created
  at `backups\production_readiness_source_20260710_093457.zip`; live route
  inventory opened all 59 registered routes at 1366x768 with no page-level
  horizontal scrollbar in the sweep; 18 transaction-framework routes were
  identified; Report Center, Quotation, Receipt Entry and Payment Entry
  screenshots were captured under `screenshots\production_readiness_audit_*`;
  py_compile passed, print/report parity passed 21, focused UI tests passed 42
  and full regression passed 149.
- 2026-07-10 hidden-state/button audit continuation: Account Closing / CA
  Export screenshot captured at
  `screenshots\production_readiness_audit_account_closing_ca_export_1366x768_20260710.png`;
  focused continuation tests passed 2, focused UI tests passed 44,
  print/report parity passed 21 and full regression passed 151.
- 2026-07-10 print/list hidden-state continuation: Document Center
  `sales_return` print mapping now resolves to deterministic non-empty
  fallback metadata; Document Center subviews and Module Hub operation states
  are covered by focused fit/button receiver tests; py_compile passed, focused
  UI tests passed 46, print/report parity passed 22 and full regression passed
  154.
- 2026-07-09 pending action wiring: screenshots captured at `screenshots\after_pending_actions_quotation_entry_1366x768_20260709.png`, `screenshots\after_pending_actions_sales_bill_1366x768_20260709.png`, `screenshots\after_pending_actions_purchase_entry_1366x768_20260709.png`, and `screenshots\after_pending_actions_receipt_entry_1366x768_20260709.png`.
- 2026-07-10 output actions: `python -m py_compile services\share_service.py views\inventory_entry_view.py views\stock_out_view.py views\dispatch_return_view.py views\route_settlement_view.py views\sales_bill_view.py views\purchase_entry_view.py views\account_entry_view.py views\sales_document_view.py tests\test_document_and_module_ui.py` passed; focused email/report-output tests passed 3; performance smoke passed; all-route target fit passed; focused UI suite passed 41; full regression passed 139.
- 2026-07-10 output actions: screenshots captured at `screenshots\after_output_actions_stock_entry_1366x768_20260710.png`, `screenshots\after_output_actions_stock_out_entry_1366x768_20260710.png`, `screenshots\after_output_actions_dispatch_return_entry_1366x768_20260710.png`, and `screenshots\after_output_actions_route_settlement_1366x768_20260710.png`.
- 2026-07-10 SMTP email continuation: `python -m py_compile services\email_service.py services\share_service.py tests\test_data_maintenance_and_share.py` passed; focused SMTP/email tests passed 3; `tests\test_data_maintenance_and_share.py` passed 7; output/fit UI batch passed 3; focused UI suite passed 41; full regression passed 141.
- 2026-07-09 responsive layout: `python -m py_compile views\sales_bill_view.py views\product_master_view.py views\login_dialog.py views\stock_dashboard_view.py views\main_window.py widgets\erp_components.py widgets\form_layout_helpers.py tests\test_document_and_module_ui.py` passed.
- 2026-07-09 responsive layout: target resolution fit audit across major pages at 1366x768, 1440x900 and 1920x1080 returned `target_fit_failures=0`.
- 2026-07-09 responsive layout: `python -m pytest -q tests\test_document_and_module_ui.py` passed: 30 passed.
- 2026-07-09 responsive layout: `python -m pytest -q tests` passed: 128 passed.
- 2026-07-09 responsive layout: screenshots captured at `screenshots\responsive_after_dashboard_1366x768_20260709.png`, `screenshots\responsive_after_sales_bill_1366x768_20260709.png`, `screenshots\responsive_after_product_master_1366x768_20260709.png`, `screenshots\responsive_after_developer_console_1366x768_20260709.png`, `screenshots\responsive_after_quotation_1440x900_20260709.png`, and `screenshots\responsive_after_dashboard_1920x1080_20260709.png`.
- 2026-07-09 responsive continuation: expanded target resolution audit across the navigation route list returned `target_fit_failures=0`; note controls are capped and receipt/payment label-to-control gaps were visually checked.
- 2026-07-09 responsive continuation: compile check passed for shared helpers, shell, account entry, remaining compacted pages and affected tests.
- 2026-07-09 responsive continuation: `python -m pytest -q tests\test_document_and_module_ui.py` passed: 30 passed.
- 2026-07-09 responsive continuation: `python -m pytest -q tests` passed: 128 passed.
- 2026-07-09 responsive continuation: screenshots captured at `screenshots\responsive_after_receipt_entry_1366x768_20260709_continued.png`, `screenshots\responsive_after_payment_entry_1366x768_20260709_continued.png`, `screenshots\responsive_after_document_center_1366x768_20260709_continued.png`, `screenshots\responsive_after_report_center_1366x768_20260709_continued.png`, and `screenshots\responsive_after_developer_console_1366x768_20260709_continued.png`.
- 2026-07-09 responsive third sweep: `python -m py_compile views\module_hub_view.py views\report_center_view.py` passed.
- 2026-07-09 responsive third sweep: expanded target resolution audit returned `target_fit_failures=0`.
- 2026-07-09 responsive third sweep: `python -m pytest -q tests\test_document_and_module_ui.py` passed: 30 passed.
- 2026-07-09 responsive third sweep: `python -m pytest -q tests` passed: 128 passed.
- 2026-07-09 responsive third sweep: screenshots captured at `screenshots\responsive_after_accounts_module_1366x768_20260709_continued2.png`, `screenshots\responsive_after_reports_statement_1366x768_20260709_continued2.png`, and `screenshots\responsive_after_masters_module_1366x768_20260709_continued2.png`.
- Ran focused engine tests: `python -m pytest tests/test_financial_year_and_numbering_engines.py -q` → 6 passed.
- Ran full test suite earlier in the project history: 65 passed, 0 failed.
- Relaxed party validation to preserve compatibility with legacy test fixtures and imports.
- Confirmed `app.py` imports without GUI runtime errors during the import smoke test.

## Historical baseline audit findings (superseded)

### Modules that are implemented in a working-basic form
- App bootstrap and desktop shell: [app.py](app.py), [views/main_window.py](views/main_window.py)
- Product master UI and save workflow: [views/product_master_view.py](views/product_master_view.py), [services/master_repository.py](services/master_repository.py)
- Customer/supplier master UI and save workflow: [views/party_master_view.py](views/party_master_view.py), [services/master_repository.py](services/master_repository.py)
- Sales entry and print workflow: [views/sales_bill_view.py](views/sales_bill_view.py), [services/transaction_repository.py](services/transaction_repository.py)
- Purchase entry and print workflow: [views/purchase_entry_view.py](views/purchase_entry_view.py), [services/transaction_repository.py](services/transaction_repository.py)
- Account entry and voucher posting: [views/account_entry_view.py](views/account_entry_view.py), [services/transaction_repository.py](services/transaction_repository.py)
- Report center and export/print helpers: [views/report_center_view.py](views/report_center_view.py), [services/pdf_print.py](services/pdf_print.py)
- Global search and menu record search: [views/global_search_view.py](views/global_search_view.py), [services/sqlite_source.py](services/sqlite_source.py)
- Basic master helpers for category/brand/unit/GST/warehouse/branch/ledger/company: [views/simple_master_view.py](views/simple_master_view.py)

### Modules that are partially complete
- Company foundation: company settings exists, but financial year, numbering series, godown, and related enterprise controls are not yet clearly implemented as full modules.
- Advanced masters: route, salesman, vehicle, transporter, bank, payment terms, credit limits, area/beat, UOM/multi-UOM/conversion, batch/expiry/shelf life, scheme/discount, and opening balance flows are not yet represented as complete, dedicated ERP modules in the reviewed code.
- Purchase flow: quotation/order/GRN/purchase return/debit note/payment/register/analysis are not fully represented as separate end-to-end workflows in the current audit.
- Sales flow: quotation/order/delivery challan/retail/wholesale/tax invoice/cash memo/return/credit note/outstanding/receipt/customer ledger/register are not fully represented as dedicated, complete flows in the reviewed code.
- Inventory engine: stock ledger/register/item movement/godown transfer/adjustment/damage/expiry/near expiry/batch/FIFO/FEFO/reservation/reorder/min-max/valuation/physical verification are not fully represented as a complete engine in the current audit.
- Accounts engine: chart of accounts, voucher engine, contra/journal/opening balance/outstanding/trial balance/balance sheet/P&L/day book/cash book/bank book and GST integration are not fully represented as a complete end-to-end engine.
- Search engine: search exists, but fuzzy ranking, background indexing, favorites, recent searches, and command palette behavior are not fully implemented from the current audit.
- Print engine: the universal print service exists, but the full document matrix (A4 portrait/landscape, A2 landscape, thermal 58/80, bulk print, preview, printer selection, margins, header/footer, QR/Barcode, loading sheet, dispatch summary) is not fully validated across all modules.

### Modules that are mostly UI-only or still thin wrappers
- Module hub and dashboard screens are present and navigable, but some are more navigation shells than completed business engines.
- The simple master view is a reusable UI layer, but several master types still depend on generic fields rather than dedicated, fully audited business rules.
- Report center is present and rich, but several report types are catalog entries rather than fully implemented report sources.

### Modules with no clear implementation yet in the current audit
- Financial Year UI integration
- Numbering Series UI integration
- Godown
- Price list
- Transporter
- Bank
- Opening balance management as a full workflow
- Dedicated batch/expiry/shelf life management for full ERP use
- Full scheme/discount engine and pricing matrix workflows
- Full voucher engine, financial statement engine, and audit/closing flows

## Risk and quality notes
- No IDE-reported Python errors were found from the current static workspace diagnostics.
- The audit did not find evidence of a full, centralized SQLite index strategy or a cross-module foreign-key strategy for the ERP foundation.
- Existing transaction modules are not yet integrated with the new Financial Year and Numbering Series engines.
- Duplicate old numbering/year logic must not be removed until a safe migration plan is in place.
- Some logic is duplicated across view-level handling and service-level handling, especially around validation, print, and persistence.
- The current print path is centralized in [services/pdf_print.py](services/pdf_print.py), which is positive, but several modules still call print helpers from their own views rather than relying on a single universal print flow for every document type.
- The current search path is present, but it is not yet a full enterprise search engine with fuzzy ranking, background indexing, recent search history, favorites, and palette-style command flow.

## Recommended next step
- Implement the company and foundation layer first, with a strong focus on:
  1. Financial Year UI integration
  2. Numbering Series UI integration
  3. Branch / warehouse / cost center
  4. Basic opening balance and ledger foundation
  5. Safe database schema updates with no breakage to existing SQLite data

## Notes
- Keep this file updated after each completed milestone.
- Continue to avoid guessing and rely on the actual codebase, docs, database, and AI_GUIDE before changing implementation.
