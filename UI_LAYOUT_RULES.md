# UI Layout Rules

Updated: 2026-07-12

These rules define the compact responsive ERP layout standard for the PyQt
desktop application. The goal is to preserve all business controls and logic
while preventing page-level overflow, clipped labels, clipped buttons, and
overlapping widgets on normal desktop screens.

## 2026-07-12 Locked Product/Client Identity And Dispatch Rules

- Product and client identity are separate component contracts.
  `ProductBrandHeader` is the only full branding component allowed in the fixed
  shell header and login product area. It always resolves the PRM product logo,
  **PRM BILLING INVENTORY** name and product tagline; it must not accept or
  render a client profile.
- `ClientCompanyIdentityCard` is for licensed-company context only: Dashboard
  Company Information, Company Settings/Profile and similar company-detail
  cards. Login may show this card only as a separate **Licensed Company** area,
  never as a replacement for the PRM product header.
- Client-logo rendering must preserve aspect ratio with smooth scaling. Full
  identity cards reserve a 144x96 logo area; compact cards reserve 84x56.
  Missing client logos use client initials. They must never silently resolve to
  a PRM product asset.
- Brand and logo widgets marked `erpPreserveGeometry` are outside the generic
  fit-to-width rewrite. Responsive fitting may reflow their containing card,
  but must not erase their minimum/maximum geometry or compress the logo into a
  narrow vertical strip.
- Printed/PDF document headers belong to the licensed client company. Shared
  product footers belong to PRM Software. Do not use one ambiguous logo
  resolver for both ownership domains.
- Dispatch Summary has one destination:
  `reports:daily_dispatch_summary`, which selects
  `daily_dispatch_summary` in Report Center. Sidebar, Dashboard, Reports hub
  and Global Search must reuse that route instead of creating another page.
- Sidebar navigation must expose keyboard focus, arrow traversal, Enter
  activation and Escape/back behavior. Active highlighting follows the full
  current route so Dispatch Summary remains selected while its Report Center
  report is open.
- Report shortcuts, search results and Report Center choices must use the same
  role/plan permission filter as direct route opening. A hidden report must not
  remain reachable through search or a hand-built shortcut.

## 2026-07-12 Locked Master, Branding And Dropdown Rules

- Editable `QComboBox` controls are enhanced once through
  `widgets/smart_combo.py`. Typing performs case-insensitive contains filtering;
  arrow keys, Enter, Escape and mouse selection remain available. Do not add a
  competing page-local completer.
- Field boxes marked `erpMinimumWidth` must retain a readable control width
  when cards wrap. Flow layouts may move the entire field box to the next row;
  they must not compress a GST treatment, state, UOM or status value until only
  its trailing characters remain visible.
- Customer and Supplier masters use Identity & Contact, GST & Compliance,
  Location & Credit, and Addresses & Notes groups. Product Master uses Basic,
  Inventory/UOM, Identification/Notes and Package/Variant groups. Preserve all
  business fields and the horizontal action surface.
- Master shortcuts use the same handlers as their buttons: Ctrl+S/F8 Save,
  Ctrl+N New, Ctrl+F/F3 Search, Ctrl+E/F2 Edit, Ctrl+P/F10 Print and Escape for
  the safe local back/cancel action. Tooltips expose the available shortcuts.
- `ClientCompanyIdentityCard` owns licensed-company logo-above-name rendering,
  aspect-ratio scaling, initials fallback and regulatory/contact details on
  client-context surfaces. It must not be placed in the fixed PRM product
  shell; follow the ownership rules above.
- Lazy route activation must invalidate and reactivate the active page layout,
  then reset the page scroll position. This prevents a hidden route from
  retaining stale widths or opening below its header.
- `TransactionDetailsDeck` stays compact enough that the grid and summary deck
  keep Grand Total inside the initial 1366x768 viewport. Smaller windows may
  scroll vertically; required fields and totals must never be hidden or
  overlapped.
- Communication actions that promise an attachment must use SMTP, Outlook or
  Simple MAPI. `mailto:` is an explicit manual fallback and must never be
  labelled as verified automatic attachment delivery.

## 2026-07-11 Locked Master, Toolbar And Totals Rules

- Primary/master/list/report actions use `CompactActionToolbar`: left-to-right,
  one row when space permits and compact wrapping only when required. Do not
  place a FlowLayout or action group in a narrow right-side grid column.
- Keep one canonical button instance per action. State/permission changes must
  update the same visible button; do not create hidden state-managed duplicates.
- Product Master at standard desktop width uses Basic Product Information and
  Inventory & UoM side-by-side, then full-width Identification & Notes and the
  Package/Variant grid. Re-evaluate layout when a hidden page becomes current.
- A card's allocated height must never be below its minimum size hint. Permanent
  tests must detect intersecting Product Master field boxes.
- Transaction pages size the shared stack to the greater of viewport height and
  true page minimum. The item grid yields space before totals leave the initial
  viewport; genuine smaller-window overflow remains vertically scrollable.
- Transaction totals use one row only at 720 px or wider; below that breakpoint
  they return to the readable two-row, five-column layout.
- Grand Total always includes label and currency value, bold +2pt emphasis,
  accessible name/description and explicit high-contrast light/dark fallback.
- Button themes must retain normal, hover, pressed, focus, checked, disabled,
  busy, success, error, positive and destructive states.

## 2026-07-10 Locked Print/Report Addendum

- Profit & Loss and Balance Sheet PDFs must use the shared A4 portrait
  two-sided statement renderer. Do not route them through the generic report
  table writer for print, preview or PDF export.
- Receipt and Payment voucher PDFs must render reference/instrument metadata
  and keep voucher identity explicit.
- Sales Invoice, Sales Order, Quotation, Purchase and other transaction prints
  must honor selected paper and orientation. When a company/template selects
  A2 landscape, exact visual parity with an A4 portrait reference is only a
  template-selection question, not a reason to ignore the active print setting.
- Print templates persist both paper size and orientation. Transaction output
  must support A4 Portrait, A4 Landscape, A2 Portrait and A2 Landscape through
  the same canonical renderer and paper adapter.
- Reference validation artifacts are stored in
  `output/pdf/reference_validation_20260710/` for future visual comparison.

## Target Resolutions

- 1366x768
- 1440x900
- 1920x1080
- 1093x614 logical workspace for 1366x768 at 125% scaling
- 911x512 logical workspace for 1366x768 at 150% scaling

## Locks Found And Relaxed

- Fixed shell geometry: the left rail was fixed at 202 px, the command search
  was locked to a wide 260-380 px band, and top/ribbon bars had larger height
  caps than the compact workspace needed.
- QSS size locks: buttons, quick actions, sidebar buttons, inputs, text edits,
  module menus, table cells, and headers carried oversized padding, min-height,
  or min-width values.
- Shared form locks: field boxes and form helpers had large minimum heights,
  label spacing, input heights, and text-edit heights that forced form cards to
  grow vertically.
- Dashboard locks: executive dashboard cards, chart widgets, tables, and card
  reflow thresholds kept too much empty space and reduced columns too early.
- Transaction locks: header cards, item grids, totals, summary areas, action
  bars, advanced dialogs, and print-template panes used large minimum heights or
  button sizes.
- Master/admin locks: product master, developer console, login dialog, and stock
  dashboard controls used wide fixed controls or tall table/card bands.
- Table/grid locks: page-level scroll areas were vulnerable to horizontal
  overflow where tables should own the horizontal scroll themselves.
- DPI table locks: stacked pages can report false visibility during offscreen or
  scaled rendering, so table normalization must use current table geometry
  rather than skip fitting based only on the page visibility flag.

## Global Rules

- No page-level horizontal scrollbar.
- Vertical page scrolling is allowed for dense workflows and dashboards.
- Grid/table horizontal scrolling is allowed only inside the item grid or table.
- Avoid absolute `setGeometry` for managed layouts.
- Avoid page-level `setFixedWidth`, `setFixedHeight`, and `setFixedSize`.
- Use minimum sizes only for practical readability; cap them so the page can
  shrink at 1366x768.
- Prefer `QSizePolicy.Expanding` horizontally and compact fixed heights for
  common line inputs, combos, date edits, spin boxes, and buttons.
- Keep the shell minimum at or below 900x500 logical pixels. Use the responsive
  136-148 px sidebar band below 1000 px window width.
- Shared action toolbars must use wrapping layout behavior. Dense transaction
  totals and action controls should use a compact two-row grid when one row
  cannot preserve full captions.
- Visible toolbar and grid-action buttons must always acknowledge keyboard or
  mouse activation. If a workflow is not implemented for a page, use the
  shared friendly not-available feedback path; do not leave disabled-looking,
  silent, or `lambda: None` actions.
- Desktop shell visual pattern: white brand/search top bar, dark-blue ribbon
  with active module state, compact dark left navigation, and top info blocks
  for financial year, branch and user on normal desktop widths.
- Use shared ERP components and helpers before adding local layout code.
- Preserve all required fields, controls, GST/tax summaries, totals, item-grid
  commands, save/preview/print actions, and keyboard shortcuts.

## Compact Defaults

- Inputs and combos: 24-30 px high.
- Toolbar/action buttons: 26-30 px high.
- Field labels: compact wrapping labels with minimum height around 14 px.
- Note, remarks, narration and address editors: reduce oversized note-control
  height by about 30%; use compact 38-48 px editor minimums with practical
  56-98 px maximum caps unless the editor is a dedicated template/code editor.
- Page headers: short, dense, and non-dominant.
- Cards: small margins and spacing; do not use empty height as visual padding.
- Tables: compact row heights, internal horizontal scroll for wide documents,
  and important columns sized first.
- Table headers must remain fully readable. Tables narrower than their viewport
  should distribute unused width across non-compact columns; tables wider than
  the viewport must expose their own horizontal scrollbar even when empty.
- Dashboard tables must follow the same internal horizontal-scroll behavior as
  other reusable ERP tables; do not hard-disable table overflow inside cards.
- Transaction/item grids should use `Interactive` column sizing with practical
  starting widths. Avoid local `Stretch` resize locks on transaction grids
  because they can fight DPI-aware header fitting and internal scrolling.
- Sales-document transaction headers should use the shared three-card pattern
  where practical: Customer Information, Other Details, and Additional
  Information. Top info blocks and dense labels may collapse or wrap on DPI
  workspaces to preserve fit.
- Dialogs: bounded minimum widths; content scrolls vertically where needed.
- Dense operation hubs may use an internal vertical scroll area for operation
  buttons. Operation buttons must use readable in-card button styling, not the
  dark ribbon style.
- Report statement trees may keep a practical readability minimum, but should
  use compact indentation, spacing and section heights so the report page still
  fits the target desktop resolutions.
- Developer/admin tabs must use compact settings cards and bounded log tables.
  Dense history/retry tables should occupy available vertical space and show a
  clear empty state instead of expanding the page horizontally.

## Shared Containers

- Use the main shell page-fit normalizer for visible pages.
- Use `ERPPageHeader`, `ERPToolbar`, `ERPFieldBox`, `ERPSectionCard`,
  `TransactionPageLayout`, `TransactionToolbar`, `TransactionGridPanel`,
  `GridActionBar`, `ERPItemGrid`, `ERPDashboardCard`, `ERPDashboardTable`,
  `ERPLineChart`, `ERPPieChart`, and `ERPBarChart`.
- Do not create a parallel dashboard, transaction, or form framework.

## Transaction Layout Rules

- Header, toolbar, party details, document details, product search, item grid,
  tax summary, totals, remarks, and footer must remain visible or vertically
  reachable without page-level horizontal overflow.
- Preserve Add Row/F4, Delete Row/Del, Import, Scan Barcode, Save, Preview, and
  Print controls.
- Preview/PDF/WhatsApp actions must use existing approved print/share services
  where a safe document payload already exists. Do not add duplicate print
  engines or fake business output only to satisfy a button.
- Keep GST/tax/total summary visible near the lower workflow area.
- Item grids may scroll horizontally inside the table; the page itself must not.
- Keyboard navigation and selected-cell focus must remain visible.

## Pages Tested

- All 59 page factories currently registered by `MainWindow`, including shell,
  module hub, transaction, master, account, report, administration, search,
  import, document, dashboard, developer, audit, and roadmap pages.
- Home Dashboard
- Sales Bill
- Purchase Entry / Goods Receipt
- Quotation
- Sales Order
- Delivery Challan
- Sales Return
- Purchase Order
- Purchase Return
- Stock Entry
- Stock Transfer
- Stock Adjustment
- Stock Out
- Dispatch Return
- Product Master
- Developer Console
- Receipt Entry
- Payment Entry
- Expense Entry
- Journal Entry
- Document Center
- Report Center
- Global Search
- Excel Import
- Label Print
- Stock Dashboard
- Financial Years
- Numbering Series
- Scheme Master
- Route Settlement
- Reports and supporting module shell pages through the focused UI suite

The automated target-resolution test derives this list from the live page
registry. New registered pages are therefore included without manually
updating a representative route list. It also checks visible label/button
clipping, table-header clipping, table-width use and internal scrollbar
visibility.

## 2026-07-09 Final Acceptance Addendum

- Sales-document bottom totals must not return to a fixed one-line
  height-locked strip. Use the shared `RemarksTermsCard`, `TotalsCard`, and
  `TaxSummaryCard` pattern so remarks, terms, totals and tax summary are
  vertically reachable and responsive.
- Empty tax/chart/table-like panels must show a visible state message. For
  sales-document tax summary, empty documents render `No data available`.
- Notes, narration, remarks and terms editors in transaction entry screens
  should remain compact by default. The current sales-document Notes editor is
  capped at 50-68 px; receipt/payment narration is capped at 40-56 px.

## 2026-07-10 Production Readiness Audit Addendum

- The current live route inventory contains 59 routes from
  `MainWindow.page_factories`. A fresh 1366x768 sweep opened every route without
  page-level horizontal scrolling.
- The shared route-fit regression remains the permanent guard for the target
  resolutions: 1366x768, 1440x900, 1920x1080, 1093x614 and 911x512.
- List/report pages should continue to use compact horizontal or wrapping
  action toolbars. Do not reintroduce tall vertical action stacks.
- Receipt and Payment narration controls are part of the compact note-control
  lock: they should remain in the 40-56 px default band unless a future
  approved voucher workflow requires a dedicated expanded editor.
- Hidden secondary states such as expanded optional report panels and modal
  dialogs need explicit tests if they gain new required controls; the default
  route sweep alone is not enough to certify an untested hidden state.
- Do not widen the page to fit transaction totals or tax summaries. At
  1366x768, the footer may require vertical scroll; the page-level horizontal
  scrollbar must remain absent.
- Operator acceptance paths checked in this pass:
  Quotation Add Row/F4, Delete Row and Save; Receipt Entry Save and Print
  Preview; Payment Entry Save and Print Preview.
- Latest screenshots for acceptance are under
  `screenshots/after_responsive_*_20260709.png`, including a scrolled footer
  capture for Quotation at 1366x768.

## 2026-07-09 Pending Action Addendum

- Sales Bill, Purchase Entry and account voucher Preview buttons now use the
  same PDF preview path as Print/PDF.
- Sales and purchase document pages now use the shared transaction PDF and
  WhatsApp preparation helpers for Quotation, Sales Order, Delivery Challan,
  Sales Return, Purchase Order and Purchase Return.
- Historical checkpoint: at this stage Email and specialized stock/dispatch/
  route print/share actions were still acknowledged with shared unavailable
  feedback. The 2026-07-10 output and communication addenda supersede that
  limitation.
- Latest continuation screenshots are
  `screenshots/after_pending_actions_quotation_entry_1366x768_20260709.png`,
  `screenshots/after_pending_actions_sales_bill_1366x768_20260709.png`,
  `screenshots/after_pending_actions_purchase_entry_1366x768_20260709.png`,
  and
  `screenshots/after_pending_actions_receipt_entry_1366x768_20260709.png`.

## 2026-07-10 Output Action Addendum

- Transaction output actions should now use real shared handlers: transaction
  PDFs, voucher PDFs, report PDFs, WhatsApp handoff or email handoff. Do not
  add silent placeholder actions.
- Email uses `prepare_email_document()`. SMTP PDF delivery is available only
  when explicitly enabled with `PRM_EMAIL_DELIVERY_MODE=smtp`; otherwise it
  remains a mail-client handoff for operator review.
- Inventory and route workflows that do not use invoice/voucher payloads should
  use `write_report_pdf` rather than a duplicate print engine.
- Latest output-action screenshots are
  `screenshots/after_output_actions_stock_entry_1366x768_20260710.png`,
  `screenshots/after_output_actions_stock_out_entry_1366x768_20260710.png`,
  `screenshots/after_output_actions_dispatch_return_entry_1366x768_20260710.png`,
  and
  `screenshots/after_output_actions_route_settlement_1366x768_20260710.png`.

## 2026-07-10 Communication Addendum

- Email delivery history and failed-email retry must stay centralized in
  `CommunicationLogService` and Developer Console.
- Message template storage, rendering and contact resolution must stay
  centralized in `CommunicationTemplateService` and Developer Console.
- Live Email/WhatsApp actions must render message text through the shared
  `communication_message()` and `document_message_context()` helpers. Do not
  add local template SQL, placeholder rendering or per-page template rules.
- Preferred recipient/contact-source selection belongs to
  `CommunicationTemplateService` and Developer Console. Store channel/document
  contact preferences centrally and use the shared resolver when a workflow
  needs recipient fields.
- Transaction pages should pass the active SQLite path into
  `prepare_email_document()` and the shared communication-message helper
  instead of adding local logging, SMTP, retry or status-table code.
- Developer Console Communication pages should use compact sub-tabs when
  delivery/logs and templates would otherwise compete for vertical space.
- Delivery Diagnostics belongs in Developer Console Communication > Delivery.
  SMTP tests must use `EmailDeliveryService.test_connection()` and WhatsApp
  checks must use `whatsapp_readiness()` so diagnostics do not send documents,
  post transactions or bypass shared delivery services.
- Production acceptance logging must remain privacy-safe. Communication status
  tables may show masked recipients and safe summaries only; do not display or
  write SMTP passwords, WhatsApp session data, message bodies, full private
  recipient lists or full local attachment paths in logs, screenshots or
  Markdown documentation.
- Saved SMTP passwords must use the shared protected settings path. On Windows,
  existing `smtp.password` values are protected with DPAPI when settings are
  loaded; UI code must not save plain SMTP passwords directly.
- The Message Templates preview/contact-check panel must stay compact,
  scroll-safe and operator-focused: sample fields, rendered preview, resolved
  contact and template table share one vertical workflow without page-level
  horizontal overflow.
- Dashboard communication health must use the existing shared dashboard card
  and table widgets. Wide recent-history tables may scroll horizontally inside
  their card, but the dashboard page itself must not gain horizontal overflow.
- Live template wiring is non-visual; if no active template exists for a
  document/channel pair, the existing prepared fallback message must be used.
- Communication admin screenshots:
  `screenshots/after_communication_admin_1366x768_20260710.png`.
- Dashboard communication screenshots:
  `screenshots/after_dashboard_communication_cards_1366x768_20260710.png`.
- Template admin screenshots:
  `screenshots/after_communication_templates_1366x768_20260710.png`.
- Template contact preview screenshots:
  `screenshots/after_communication_contact_preview_1366x768_20260710.png`.
- Delivery diagnostics screenshots:
  `screenshots/after_communication_delivery_diagnostics_1366x768_20260710.png`.

## Current Acceptance Rule

Do not regress the accepted horizontal toolbar, typed widget access, Product
Master card placement, shared transaction stack sizing or Grand Total hierarchy.
Run the stabilization, live-route and multi-resolution gates after related UI
changes.
