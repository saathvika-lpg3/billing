# Desktop UI System

## 2026-07-12 Production UI Foundation

- `widgets/company_branding.py` is the canonical client identity surface. It
  places an aspect-ratio-preserving client logo above the company name, uses an
  initials placeholder when no logo is available, and renders configured
  GSTIN, FSSAI, drug licence, phone, email and friendly business type details.
- `widgets/smart_combo.py` enhances editable combo boxes application-wide with
  case-insensitive contains filtering and normal arrow/Enter/Escape/mouse
  behavior. Combo values continue to pass through typed widget access; no view
  may call line-edit-only APIs on a `QComboBox`.
- Customer and Supplier masters use four consistent business cards; Product
  Master uses the Basic, Inventory/UOM, Identification/Notes and
  Package/Variant structure. Field boxes carry readable minimum-width metadata
  so wrapping occurs before text becomes clipped.
- Master actions are horizontal-first and share Ctrl+S/F8, Ctrl+N,
  Ctrl+F/F3, Ctrl+E/F2, Ctrl+P/F10 and Escape behavior where applicable.
- Lazy pages are explicitly relaid out and scrolled to the top when opened.
  The shared transaction details deck is height-capped so the item grid,
  totals, tax summary and high-contrast Grand Total remain visible at the
  supported desktop sizes.
- Accepted evidence: **59/59 live routes** at 1366x768, 1440x900 and
  1920x1080; **35 UI files / 0 unsafe typed-widget calls**; eight performance
  checks within limits; and **213 automated tests passed**.

## 2026-07-11 Accepted UI Foundation

- `widgets/action_toolbar.py` is the master/list/report action surface. Actions
  are horizontal-first, permission-aware, visibly role-styled and never silent.
- `widgets/widget_values.py` is the typed form access boundary. QComboBox uses
  current text/data; line edits use text; rich/plain edits, dates, times,
  spinboxes, checks, table items and custom lookups use their supported APIs.
- Product Master is the reference professional master-entry page: horizontal
  actions, responsive business cards, explicit required fields, keyboard flow,
  multi-pack editing and a searchable list.
- Transaction pages use shared header/details/grid/summary decks. Sales Bill,
  Purchase Entry, Quotation and Sales Order now follow the same visual language.
- `FitToWidthStack` resynchronizes active page height and hidden responsive
  components after route and resolution changes. This prevents stale wide modes,
  table edge gaps and below-fold totals.
- Accepted evidence: 59 routes pass runtime audit; five desktop/scaling sizes
  pass layout tests; full suite 190 passed. See `audit/live_page_ui_inventory.*`.

The desktop application must preserve PRM_GST business behavior without copying
the old web layout. Screens should feel like a fast operator-focused ERP.

## Navigation

- Use a top module ribbon and command/search entry with the approved compact daily-work rail; do not use the old web-style sidebar layout.
- Keep common actions reachable from the keyboard.
- `Esc` closes the active popup or returns to the previous screen.
- `Ctrl+K` opens command search.
- `Ctrl+S` saves the active form.
- `Ctrl+P` opens print preview where supported.
- `F4` adds a transaction row.
- `Alt+B` focuses barcode/product search on transaction screens.

## Layout

- Use proportional form groups instead of long stretched controls.
- Prefer compact sections with 2, 3, or 4 columns based on task density.
- Use popup windows for focused tasks: customer quick add, item selector,
  batch/pack selector, payment split, print preview, and validation errors.
- Use tables for line-item workflows, with fixed practical column widths.
- Keep totals, GST summary, and save/print actions visible near the bottom.

## Responsive Layout Standard

- Page-level horizontal scrolling is not allowed. Wide item grids and tables may
  scroll horizontally inside the grid only.
- Pages must fit cleanly at 1366x768, 1440x900, and 1920x1080; vertical page
  scrolling is allowed where the workflow needs more height.
- Avoid page-level `setFixedWidth`, `setFixedHeight`, `setFixedSize`,
  oversized `setMinimumWidth`, oversized `setMinimumHeight`, absolute
  `setGeometry`, and QSS `min-width` / `min-height` locks unless they are for a
  small icon or bounded control.
- Use compact ERP defaults through shared framework components: 24-30 px
  controls, 26-30 px action buttons, compact card margins, short page headers,
  and field labels that wrap or compress before forcing page overflow.
- Keep note, remarks and narration controls compact. The standard note editor
  height is reduced by about 30% from the earlier oversized text-edit style,
  with a capped height so nearby grids and summary areas remain visible.
- Use shared scroll-safe containers, responsive field helpers, dashboard cards,
  transaction cards, grid panels, and table widgets from the existing ERP UI
  framework. Do not create duplicate dashboard or layout component families.
- Use the shared toolbar/button feedback helpers for every visible action.
  Unsupported actions must acknowledge the click and show the shared
  not-available message; silent no-op callbacks are not part of the approved
  UI system.
- Approved reference direction for the desktop shell: white brand/search top
  bar, dark-blue module ribbon with active state, compact dark PRM sidebar, and
  financial-year/branch/user info blocks on normal desktop widths.
- Approved reference direction for sales documents: Customer Information, Other
  Details, and Additional Information cards before product search and item grid.
- Keep selected cells and keyboard focus visible. `F4`, `Delete`, `Ctrl+S`,
  `Ctrl+P`, `Esc`, and other established workflow shortcuts must remain active.
- The target-resolution UI regression must enumerate `MainWindow.page_factories`
  rather than maintain a representative page list. Every registered page is
  checked at 1366x768, 1440x900, and 1920x1080 for page-level horizontal
  overflow and field-label/control overlap.
- The same regression checks visible labels and buttons for horizontal clipping,
  verifies table-header captions fit their sections, expands narrow tables to
  use available width, and requires an internal horizontal scrollbar whenever
  a table is wider than its viewport.
- Run table normalization after the page becomes visible. Qt table geometry
  calculated while a stacked page is hidden is stale and must not be used to
  lock final column widths.
- DPI-scaled stacked pages may report the page itself as not visible while
  child table geometry is valid. Shared table normalization should still size
  headers and internal scrollbars from the current widget geometry.
- Dashboard mini tables follow the same internal horizontal-scroll rule as
  other reusable ERP tables; do not hide table overflow at the card level.
- Transaction and item grids should use interactive columns with practical
  starting widths. Local stretch-mode locks on transaction grids are not part
  of the approved responsive pattern.
- The desktop shell minimum is 900x500 logical pixels. At widths below 1000
  logical pixels the ERP Navigator uses a 136-148 px compact band, shared
  toolbars wrap, and dense transaction summary actions use two rows.
- DPI certification includes 1093x614 and 911x512 logical workspaces, matching
  a 1366x768 display at 125% and 150% Windows scaling.

## 2026-07-10 Production Readiness Specification Lock

- The live route registry is the source of truth for page certification. The
  current registry has 59 routes and the latest route sweep opened all of them
  at 1366x768 without page-level horizontal scrolling.
- Current shared-framework transaction routes:
  `sales_bill`, `quotation_entry`, `sales_order_entry`,
  `delivery_challan_entry`, `sales_return_entry`, `purchase_entry`,
  `purchase_order_entry`, `purchase_return_entry`, `stock_entry_entry`,
  `stock_transfer_entry`, `stock_adjustment_entry`, `stock_out_entry`,
  `dispatch_return_entry`, `route_settlement`, `receipt_entry`,
  `payment_entry`, `expense_entry`, and `journal_entry`.
- Report Center is the live route for Profit & Loss, Balance Sheet, Trial
  Balance, Day Book, ledger/GST/stock and list reports. Financial statement
  screens must keep the two-side statement tree behavior rather than reverting
  to a generic flat table.
- Profit & Loss and Balance Sheet must keep using the shared statement PDF and
  print-preview path. `write_statement_pdf()` renders the approved A4 portrait
  two-sided statement layout, and
  `test_accounting_statement_pdfs_use_locked_two_sided_layout` prevents
  reverting to a generic flat report table.
- Print and preview behavior must remain centralized in the existing print
  engine and share services. Do not add page-local alternate PDF engines for
  transaction, voucher, report or communication output.
- Locked external reference files mentioned by the production-readiness
  instruction must be compared only when the actual files are available in the
  workspace. If they are unavailable, mark the comparison blocked rather than
  claiming visual parity.
- Hidden but supported panels must be tested explicitly when they carry
  required controls. The Account Closing / CA Export panel in Report Center is
  now covered by a dedicated fit regression.
- Every visible enabled `QPushButton` on every registered live route must have
  at least one click receiver. Buttons may show a shared "not available"
  message for unsupported workflows, but they must never be silent.
- Document Center subviews and Module Hub expanded operation states are part of
  the screen-fit contract, not optional visual extras. Their filters, action
  rows, tables and buttons must remain compact and wired.

## 2026-07-10 Locked Reference Print/Report Lock

- Reference-based validation artifacts live under
  `output/pdf/reference_validation_20260710/`. Keep `references/rendered`,
  `live/rendered`, and `live_after/rendered` when comparing future print
  changes.
- Accounting statements are not ordinary list reports. Profit & Loss and
  Balance Sheet must render from the existing statement dictionaries returned
  by `MySqlSource.erp_profit_loss_statement()` and
  `MySqlSource.balance_sheet_statement()` through `write_statement_pdf()`.
- Statement PDFs must stay A4 portrait with two side-by-side columns, visible
  group headings, indented ledger details, right-aligned amounts, equal totals,
  page count, company header and footer branding.
- Receipt and Payment voucher PDFs must preserve their own identity and render
  voucher number/date, party/account, amount, words, mode, reference,
  instrument, narration, signatures and footer. Receipt must never print as
  Payment and Payment must never print as Receipt.
- Transaction PDFs must honor the active selected paper and orientation from
  print settings. The current distributor/wholesale company output renders A2
  landscape; exact A4 visual parity with `Print_torefer_codex.pdf` is only
  expected if the selected template/paper is changed to A4 portrait.
- Print Templates must persist both paper size and orientation. Supported
  transaction paper matrix: A4 Portrait, A4 Landscape, A2 Portrait and A2
  Landscape. The selected matrix adapts the canonical transaction structure; it
  must not switch to an unrelated template or remove required sections.
- Permanent regression locks are in `tests/test_print_and_report_parity.py`:
  required paper/orientation matrix, statement two-sided structure, generic
  statement-header prevention, and receipt/payment identity/reference fields.

## 2026-07-10 Git And Release Hygiene Lock

- The live repository was repaired after `.git` was found empty and invalid.
  The invalid metadata was preserved as `.git_invalid_backup_20260710_130706`.
- Official origin is `https://github.com/saathvika-lpg3/billing.git`; the
  GitHub comparison clone had no commits/tracked files, so live source remains
  authoritative for the first reviewed commit.
- `.gitignore` must keep runtime/client material out of source control:
  databases, uploaded logos/QR/customer files, `.prmlic`, SMTP/WhatsApp/session
  secrets, logs, generated PDFs, screenshots, reports, backups, caches and
  build output.
- Do not push, force-pull, reset, clean or overwrite the live tree without a
  reviewed diff. The safe first commit should be user-reviewed from the current
  `main` branch.

## Visual Style

- Light theme first, dark theme later.
- Background: `#F5F7FB`
- Surface: `#FFFFFF`
- Primary text: `#0F172A`
- Muted text: `#475569`
- Accent: `#2563EB`
- Success: `#0F766E`
- Warning: `#B45309`
- Error: `#B91C1C`
- Radius: 8-12 px depending on component density.
- Font: Segoe UI or Inter-style system sans-serif.

## Validation

- Validate on field exit and on save.
- Show concise inline errors near the field.
- Use blocking dialogs only for destructive actions or save failure.
- Never silently skip invalid rows.
- Keep business-rule validation inside services, not inside UI widgets.

## Performance

- Lazy-load heavy lists.
- Use searchable dialogs for large product/customer selectors.
- Cache stable master data during an open transaction.
- Keep navigation instant; long jobs run in background workers with progress.

## Screen Migration Standard

A screen is complete only when:

- It opens from the desktop navigation.
- It loads migrated data.
- It can create, edit, search, and export where PRM_GST supports it.
- It applies the same validations, calculations, and stock/account/GST effects.
- Its print/export totals match PRM_GST.
- It has keyboard flow and Escape/back behavior.

## 2026-07-09 Action Wiring Continuation

- Sales Bill, Purchase Entry and account voucher `Preview` buttons use the same
  existing PDF preview route as Print/PDF.
- Quotation, Sales Order, Delivery Challan, Sales Return, Purchase Order and
  Purchase Return now use the shared transaction PDF and WhatsApp preparation
  helpers for Preview/PDF/WhatsApp.
- At this point Email and specialized stock/dispatch/route output were still
  acknowledged through shared feedback; the 2026-07-10 continuation below
  replaced those placeholders with real shared output handlers.

## 2026-07-10 Output Action Continuation

- Email actions now use the shared mail-client handoff in
  `services.share_service`. The operator still reviews/sends the message; no
  background SMTP behavior was added.
- Inventory, stock-out/load-challan, dispatch-return and route-settlement
  output actions now generate report PDFs with `write_report_pdf` and reuse the
  shared preview/WhatsApp/email handoff services.
- Static action audits should remain clean: transaction pages should not add
  `lambda: None` or placeholder `None` callbacks for visible output actions.

## 2026-07-10 SMTP Email Continuation

- `services.email_service.EmailDeliveryService` provides opt-in SMTP delivery
  for generated PDF documents.
- SMTP must be explicitly enabled with `PRM_EMAIL_DELIVERY_MODE=smtp` and SMTP
  host/from settings. Without that configuration, Email remains a safe
  mail-client handoff.
- Required/optional environment settings:
  `PRM_SMTP_HOST`, `PRM_SMTP_PORT`, `PRM_SMTP_USERNAME`,
  `PRM_SMTP_PASSWORD`, `PRM_SMTP_FROM`, `PRM_SMTP_USE_TLS`,
  `PRM_SMTP_USE_SSL`, and `PRM_SMTP_TIMEOUT`.
- UI screens should continue to call `prepare_email_document()` rather than
  constructing SMTP, mailto, or attachment logic locally.

## 2026-07-10 Communication Log Continuation

- `services.communication_log_service.CommunicationLogService` is the shared
  communication history and failed-email retry layer.
- Transaction pages must keep using `prepare_email_document()` and pass the
  active SQLite path when delivery history should be recorded. Do not add local
  SMTP, retry, or logging code inside transaction views.
- Developer Console owns communication administration: SMTP settings, pending
  retry rows, recent delivery history and manual retry.
- Communication admin UI must use compact shared ERP styling, bounded tables,
  visible empty states and no page-level horizontal overflow.

## 2026-07-10 Dashboard Communication Continuation

- Executive Dashboard communication health must be rendered with the existing
  shared dashboard components. Do not create a separate communication dashboard
  framework.
- `Communication Status` shows mode, sent-today, failed, pending retry and
  recent communication rows. `Failed Communications` shows retry-needed rows.
- Dashboard communication cards are read-only. Retry execution belongs to
  Developer Console.

## 2026-07-10 Communication Templates Continuation

- `services.communication_template_service.CommunicationTemplateService` owns
  message-template storage, default template seeding, placeholder rendering and
  contact resolution.
- Developer Console Communication uses compact sub-tabs: Delivery and Message
  Templates.
- Live transaction send actions use the shared communication-message helpers
  from the later wiring continuation; they should not render templates locally.

## 2026-07-10 Live Communication Template Wiring

- Transaction Email and WhatsApp actions must use
  `services.share_service.communication_message()` and
  `document_message_context()` to render active templates.
- If no active template exists for the channel/document type, the existing
  prepared fallback subject/body must be used so operator output remains safe.
- Views should keep PDF generation, delivery handoff, SMTP logging, save,
  posting, GST/tax, stock, ledger and numbering logic on the existing shared
  services. Do not add local template databases or rendering code in views.
- This wiring is non-visual; the existing Communication Message Templates
  screenshot remains the visual reference:
  `screenshots/after_communication_templates_1366x768_20260710.png`.

## 2026-07-10 Communication Contact Preview

- Developer Console Communication > Message Templates owns preferred
  contact-source selection for templates.
- Preferred fields are stored centrally through
  `CommunicationTemplateService`; transaction views should not hardcode local
  recipient-field priority lists.
- The template preview panel renders sample subject/body text and shows the
  resolved contact field/value before operators rely on a template.
- Visual reference:
  `screenshots/after_communication_contact_preview_1366x768_20260710.png`.

## 2026-07-10 Communication Delivery Diagnostics

- Developer Console Communication > Delivery owns operator diagnostics for
  outbound delivery readiness.
- SMTP diagnostics must use `EmailDeliveryService.test_connection()` so the
  host/TLS/login path is checked without sending a business document.
- WhatsApp diagnostics must use `whatsapp_readiness()` so phone/link readiness
  is checked without opening the browser or attaching PDFs.
- Diagnostics are admin/operator checks only. Transaction views continue to use
  the existing shared send/handoff paths.
- Visual reference:
  `screenshots/after_communication_delivery_diagnostics_1366x768_20260710.png`.

## 2026-07-10 Production Acceptance Safety

- Communication acceptance screens and reports must never expose SMTP
  passwords, WhatsApp session data, API tokens, login cookies or private
  recipient lists.
- Communication logs store operational summaries only: masked recipient, safe
  subject/result summary, status, result code, attempt counts, timestamps and
  attachment filename. Message bodies and full local attachment paths are not
  stored in new log rows.
- Saved SMTP passwords use the shared protected settings path. On Windows,
  existing plain `smtp.password` rows are migrated to DPAPI-protected values
  when settings are loaded.
- Real SMTP/WhatsApp production acceptance must be reported as passed only
  after the operator verifies actual credentials/session, sample document sends
  and safe log entries on the workstation.

## Migration Plan

This document tracks the migration of screens to the approved Quotation Entry design standard.

### Locked reference

- Current locked visual reference: `C:\Users\DELL\Downloads\ChatGPT Image Jul 7, 2026, 03_02_58 PM.png`.
- The locked reference includes a dark left daily-work rail, a dark-blue top module ribbon, a white brand/search/user header, compact rounded cards, blue primary actions, and a bottom operator shortcut/status strip.
- The design must be inherited through the existing shared ERP UI framework, not by creating a parallel framework.

### Current phase

- Phase 1: Shared shell and transaction screens completed for current routes.
- Completed 2026-07-09 cycle: readable Segoe UI screenshots, locked dark ribbon styling, locked left-rail transaction shortcuts, wider command search, and shared grid Tab navigation fix.
- Completed 2026-07-09 transaction cycle: one shared `TransactionPageLayout`, canonical `TransactionToolbar`, named transaction cards and `ERPTransactionGrid` now compose sales, purchase, inventory, dispatch, route settlement and account entry screens.
- Completed 2026-07-09 transaction Add Row/F4 stabilization: item-entry screens now use shared `ERPItemGrid`, `TransactionGridPanel`, and `GridActionBar` handling, with no page-level null item delegates.
- Completed 2026-07-09 executive dashboard cycle: the Home Dashboard now uses the shared ERP framework dashboard cards, dashboard tables and reusable chart widgets instead of the old Work Center shortcut panel.
- Completed 2026-07-09 responsive layout cycle: shell, theme, shared components, dashboard, transaction pages, masters, admin/developer pages, dialogs, and tables were compacted to remove page-level overflow locks while preserving business logic.
- Completed 2026-07-09 responsive continuation: note/remarks/narration controls were reduced by about 30%, receipt/payment label-to-control spacing was tightened, and Document Center, Report Center, setup/admin, search/import, label print, stock dashboard, scheme and route settlement pages were brought onto the same compact rules.
- Completed 2026-07-09 third responsive sweep: module hub operation panels now use compact scroll-safe operation lists with readable in-card buttons, and Report Center statement trees keep tested readability while using tighter spacing.
- Completed 2026-07-09 final responsive/reference pass: the sales-document
  footer now uses shared Remarks/Terms, Totals and Tax Summary cards with a
  visible empty state, Receipt/Payment narration controls are tighter, and the
  target-resolution evidence covers 1366x768, 1440x900 and 1920x1080.
- Completed 2026-07-09 button/totals stabilization: shared ERP buttons now
  provide hover, pressed, focus, recent-click and busy feedback; unsupported
  transaction/grid actions show a friendly not-available message; shared
  transaction totals/tax panels show all required total fields and highlighted
  Grand Total across sales and purchase item-entry pages.
- Completed 2026-07-10 communication continuation: email delivery now has a
  shared log/retry service, `app_settings` SMTP configuration, transaction
  email logging, and a compact Developer Console Communication tab.
- Completed 2026-07-10 dashboard communication continuation: the Executive
  Dashboard now surfaces communication health and failed communication rows
  through shared dashboard cards, with failed rows feeding Critical Alerts and
  Daily Tasks.
- Completed 2026-07-10 communication templates continuation: message templates
  and contact-resolution helpers are centralized in a shared service, with a
  compact Developer Console Message Templates tab.
- The left daily-work rail now uses a responsive compact width band of 168-188 px, replacing the previous fixed 202 px rail and preserving the approved navigation surface.
- Active-page height now follows the visible page, keeping transaction totals in the first viewport at normal desktop height.
- Validation: before/after screenshots, application launch/navigation/theme smoke, focused UI tests, and full regression tests.

### Executive dashboard standard

- The Home Dashboard must be composed from `widgets/erp_components.py` shared dashboard primitives: `ERPDashboardCard`, `ERPDashboardTable`, `ERPLineChart`, `ERPPieChart`, and `ERPBarChart`.
- Do not reintroduce the Work Center / frequently used operations panel on the dashboard.
- Every dashboard card must expose refresh, loading, empty, and error states through `ERPDashboardCard`.
- Empty data must render as `No data available` instead of a blank panel.
- Recent Sales, Recent Purchase, Recent Receipts, and Recent Payments rows should open their related existing document/voucher route on double-click or Enter.
- The dashboard is intentionally vertically scrollable; keep responsive card reflow inside the page rather than creating a second dashboard framework.

### Button feedback standard

- All ERP buttons should receive shared feedback via
  `install_button_feedback()` or `install_button_feedback_tree()`.
- Button states must include hover, pressed, keyboard focus, recent-click,
  disabled and short busy feedback.
- Transaction toolbar and grid actions must never silently do nothing. If a
  callback is not yet implemented for a screen, keep the action clickable and
  show the shared friendly not-available message.
- Do not create a parallel button system for individual pages.

### Transaction totals standard

- Item-entry pages that calculate GST totals should use
  `TransactionTotalsPanel` and `TransactionTaxSummaryPanel`.
- Required visible fields are Total Quantity, Discount, Taxable Amount, CGST,
  SGST, IGST, Total Tax, Round Off, Total Amount and highlighted Grand Total.
- Empty tax summaries must show `No data available`.
- Totals must bind to the existing calculation service output; UI code should
  not duplicate business calculations.

### Approach

1. Analyze the existing shared UI framework and reusable components.
2. Identify current Sales Bill and Sales Order page layouts and use of shared widgets.
3. Apply the approved design language using existing `widgets/erp_components.py` components.
4. Preserve all business logic, data services, and current hotkeys.
5. Run the app, capture real screenshots, compare to Quotation Entry standard.
6. Fix visible layout differences until the page matches the approved visual language.

### Resume instructions

If this session ends and work continues later, resume from this document.

- Document: `docs/DESKTOP_UI_SYSTEM.md`
- Current task: fast-track Product Master, shared transaction, horizontal action,
  button feedback and Grand Total stabilization is complete and release-tested.
- Extend the existing shared transaction framework; do not create a parallel UI framework.
- Preserve the accepted Product Master overlap guard and transaction viewport
  regression whenever shared layout code changes.
- Do not redesign shared framework or business logic without a new approved task.
