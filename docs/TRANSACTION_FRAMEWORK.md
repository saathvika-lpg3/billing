# Transaction Entry Framework

## Purpose

The transaction entry framework is the single shared PyQt6 UI foundation for
sales, purchase, inventory, dispatch and account transaction screens. It lives
in `widgets/erp_components.py` and preserves each view's existing services,
repositories, GST logic, save logic and print logic.

## 2026-07-11 Lifecycle Contract

- Sales and Purchase List rows can open the saved transaction editor. Saving
  an edit reverses stock/outstanding, marks the prior voucher/ledger/GST rows
  `Superseded`, then posts one active version in the same SQLite transaction.
- Cancellation requires a reason and retains the source document. Sales,
  Purchase, Returns, Receipt, Payment, Expense, Journal/Contra and Stock
  Transfer reverse their applicable stock, party balance, GST and ledger effect.
- Draft/Hold account vouchers and draft transfers are non-posting.
- Selected warehouse IDs from Sales/Purchase screens are part of the saved
  header; warehouse movement no longer silently falls back to ID `0`.
- Validation rejects missing document identity/date/party/item, malformed or
  inconsistent totals, duplicate numbers, locked financial years, invalid
  item/pack/warehouse references, invalid quantities/GST/discount, same-store
  transfers and unavailable stock. A failed save rolls back all effects.
- Active financial/GST reports exclude Cancelled/Void/Deleted/Superseded rows;
  auditable lists retain statuses.
- `services.business_flow_audit_service.BusinessFlowAuditService` owns read-only
  lifecycle diagnostics. Do not insert balancing rows from diagnostics.
- See `docs/BUSINESS_FLOW_MATRIX.md` for complete flow/status/limitation evidence.

## Shared Components

- `TransactionPageLayout`: fixed page order for header, toolbar, sections, grid and summary.
- `TransactionHeader`: common title, description and source/status region.
- `TransactionToolbar`: canonical action order and styling.
- `CustomerCard`: party and customer-facing document fields.
- `DocumentCard`: document, warehouse, route and status fields.
- `AdditionalInfoCard`: notes, communication and future attachment fields.
- `ProductSearchCard`: product, HSN, pack, quantity, rate and GST entry fields.
- `GridActionBar`: shared Add Row / F4, Delete Row, Import and Scan Barcode strip above item grids.
- `TransactionGridPanel`: shared item-grid card that owns the action strip and grid focus-after-add behavior.
- `ERPTransactionGrid`: keyboard-first editable transaction grid.
- `ERPItemGrid`: item-entry specialization used by item transaction pages.
- `RemarksCard`: reusable remarks and terms container.
- `TaxSummaryCard`: reusable GST/tax breakup container.
- `BottomTotalsCard`: sticky-like totals and primary summary container.
- `TransactionTotalsPanel`: shared item-entry totals panel for Total Quantity,
  Discount, Taxable Amount, CGST, SGST, IGST, Total Tax, Round Off, Total
  Amount and highlighted Grand Total.
- `TransactionTaxSummaryPanel`: shared tax breakup table with a visible
  `No data available` empty state.
- `TransactionSectionCard`: shared item, source and recent-entry section.

## Canonical Toolbar

The toolbar order is:

`New`, `Preview`, `Print`, `PDF`, `WhatsApp`, `Email`, `Save`, `Close`,
`Delete`, `Export`, `Import`, `Refresh`, `Search`.

Actions without a safe callback remain visible and clickable. The shared toolbar
shows hover, pressed, focus, recent-click and short busy feedback, then opens a
friendly "not available on this screen yet" message instead of silently doing
nothing. This keeps every screen structurally consistent without adding fake
business behavior.

Generic `ERPToolbar` and page-local buttons installed through
`TransactionPageLayout` use the same shared feedback helpers. Do not wire future
actions with silent no-op callbacks; use `None` so the framework can show the
friendly unavailable message until the business workflow exists.

## Document Output Actions

- Sales Bill and Purchase Entry `Preview`, `Print`, and `PDF` use their existing
  draft PDF print-preview flow.
- Receipt, Payment, Expense and Journal `Preview`, `Print`, and `PDF` use the
  existing voucher PDF print-preview flow.
- Quotation, Sales Order, Delivery Challan, Sales Return, Purchase Order and
  Purchase Return use the shared transaction PDF writer, print preview and
  WhatsApp preparation helpers.
- Email uses the shared `prepare_email_document()` helper, and specialized
  stock/dispatch/route output uses report PDFs. No duplicate or placeholder
  print engine should be added.

## Canonical Print Renderer Contract

- Transaction documents must flow through the shared transaction PDF renderer:
  `Document -> Template Registry -> Data Mapper -> Canonical Renderer -> Paper
  Adapter -> Preview/PDF/Printer/Bulk Print`.
- The canonical renderer owns content and order: company header, title, Bill
  To, Ship To, QR/payment, document number/date/operator, item grid, HSN, qty,
  unit, MRP/rate/scheme/discount, taxable/GST/amount, GST summary, Grand Total,
  amount words, terms, bank details, authorised signature and footer.
- The paper adapter owns only A4/A2 size, portrait/landscape orientation,
  printable margins, safe column widths, row capacity and pagination.
- Saved template paper size and orientation must be honored by Preview, Print,
  PDF, reprint, bulk print and communication attachment PDFs. Paper selection
  must not silently switch document identity or remove required sections.
- Distributor/Wholesale is allowed to use A2 Landscape by default, but can use
  A4 Portrait, A4 Landscape, A2 Portrait or A2 Landscape through persisted
  template settings.
- Multi-page transaction output must repeat compact headers and item column
  headings, avoid cut rows, place GST Summary/Grand Total/amount words only in
  the final section, and keep footers clear of item rows and totals.

## 2026-07-10 Output Action Update

- Email is now implemented as a shared mail-client handoff through
  `prepare_email_document`; it prepares the message and PDF path for operator
  review rather than silently sending mail.
- Stock Entry, Stock Transfer, Stock Adjustment, Stock Out / Load Challan,
  Dispatch Return and Route Settlement now generate output through
  `write_report_pdf`, then reuse the same preview, WhatsApp and email handoff
  services.
- A static scan should find no visible transaction output actions wired as
  `None` or `lambda: None` in `views`.

## 2026-07-10 SMTP Email Update

- `prepare_email_document()` now attempts SMTP delivery first only when
  `PRM_EMAIL_DELIVERY_MODE=smtp` is explicitly configured.
- When SMTP is disabled, the framework continues to use the mail-client handoff
  path. Transaction views should not call SMTP APIs directly.
- SMTP attachments use the same generated PDF path that Preview, PDF and
  WhatsApp actions use, so output content stays consistent across channels.

## 2026-07-10 Communication Log Update

- Transaction views pass their active SQLite path into
  `prepare_email_document()` when delivery history should be recorded.
- Delivery history and failed-email retry belong to
  `CommunicationLogService` and Developer Console, not to local transaction
  widgets.

## 2026-07-10 Live Communication Template Update

- Transaction Email and WhatsApp actions render subject/body text through
  `communication_message()` and `document_message_context()` in
  `services.share_service`.
- If no active template exists, actions keep their existing prepared fallback
  message. Views must not add local template SQL or placeholder rendering.
- Preferred recipient/contact-field ordering is owned by
  `CommunicationTemplateService`. Transaction views should use shared resolver
  behavior when recipient fields are needed instead of adding local priority
  lists.
- This update changes presentation text only. Existing PDF generation,
  save/posting, GST/tax, stock, ledger, numbering and delivery handoff logic
  remains intact.

## 2026-07-10 Delivery Diagnostics Update

- SMTP and WhatsApp readiness checks belong to Developer Console diagnostics,
  not transaction widgets.
- Transaction views should keep using the normal shared output and delivery
  handoff services. Do not replace real send/share actions with diagnostic
  helpers.

## 2026-07-10 Acceptance Safety Update

- Transaction views must keep using `prepare_email_document()` and shared
  communication helpers so logging remains sanitized.
- New communication log rows must not store message bodies, full private
  recipients or full local attachment paths. Dashboard and Developer Console
  displays should show masked recipients and safe status summaries only.

## Grid Keyboard Contract

- `F2`: edit current editable cell.
- `F3`: duplicate row when the page provides a handler.
- `F4`: add row.
- `F5` or `Ctrl+P`: focus product/source search.
- `F6`: batch command when supported.
- `F7`: stock command when supported.
- `F8`: save.
- `F9`: preview when supported.
- `F10`: print when supported.
- `Delete`: remove a local editable row when supported.
- `Enter` / `Tab`: next visible editable cell.
- `Shift+Enter` / `Shift+Tab`: previous visible editable cell.
- `Home` / `End`: first/last visible editable column.
- `Ctrl+Home` / `Ctrl+End`: first/last row and editable boundary.
- `Ctrl+C`, `Ctrl+X`, `Ctrl+V`: tab-separated grid clipboard operations.
- `Esc`: cancel editing or clear selection.

Read-only, calculated and hidden columns are skipped. Reaching the last
editable cell emits `lastEditableCellReached`; the framework does not mutate a
page's business model automatically.

## Add Row / F4 Crash Fix

The failing Quotation/Sales Order/Purchase Order family reproduced as a Windows
access violation while redrawing rows after Add Row. The traceback pointed at
`views/sales_document_view.py` in `_redraw_lines()` during
`self.table.resizeRowsToContents()`.

Root cause: the shared sales-document table was explicitly clearing its Qt item
delegate with `setItemDelegate(None)`. Qt can hard-crash when row sizing or
editing later asks a table with a null delegate to paint/measure items. The
fix removed the null delegate assignment and moved Add Row/F4 behavior into
shared framework components.

Current rule: no transaction item grid should set a null item delegate. Use
`ERPItemGrid` plus `TransactionGridPanel`/`GridActionBar`; page handlers remain
responsible for business validation and model mutation.

## Migrated Pages

- Sales Bill
- Sales Order
- Quotation
- Delivery Challan
- Sales Return
- Purchase Entry / Goods Receipt
- Purchase Order
- Purchase Return
- Stock Entry / Material Receipt foundation
- Stock Transfer
- Stock Adjustment / Opening Stock foundation
- Stock Out / Material Issue foundation
- Dispatch Return
- Route Settlement
- Receipt, Payment, Expense and Journal entries

Future production, job-work and specialized material pages should compose the
same components instead of creating new headers, toolbars or grids.

## 2026-07-10 Live Transaction Route Inventory

The production-readiness route sweep confirmed these live routes instantiate
transaction-framework pages:

- `sales_bill` -> `SalesBillView`
- `quotation_entry`, `sales_order_entry`, `delivery_challan_entry`,
  `sales_return_entry` -> `SalesDocumentView`
- `purchase_entry` -> `PurchaseEntryView`
- `purchase_order_entry`, `purchase_return_entry` -> `PurchaseDocumentView`
- `stock_entry_entry`, `stock_transfer_entry`, `stock_adjustment_entry` ->
  `InventoryEntryView`
- `stock_out_entry` -> `StockOutView`
- `dispatch_return_entry` -> `DispatchReturnView`
- `route_settlement` -> `RouteSettlementView`
- `receipt_entry`, `payment_entry`, `expense_entry`, `journal_entry` ->
  `AccountEntryView`

All listed routes opened during the 1366x768 route sweep. Sales, purchase and
sales/purchase document pages expose shared item grids plus shared totals and
tax-summary panels where those summaries apply. Voucher and stock movement
pages use the same framework shell and grid behavior, but intentionally do not
show item-level GST summary panels unless the document type has item tax data.

## Layout Behavior

`FitToWidthStack` reports the active page's height-for-width value. Hidden
pages no longer force the active transaction screen to scroll to their height,
so the bottom totals panel remains visible at normal desktop resolutions.
Wide transaction grids allow horizontal scrolling and resizable columns.
The page itself remains fit-to-width; vertical scrolling is allowed where the
active page needs it.

## Known Limitations

- Automatic creation of a new business row at the last cell is intentionally
  left to page handlers so grid UI cannot desynchronize repository payloads.
- Sales Return and Purchase Return intentionally refuse manual Add Row until an
  original source document is loaded; this is treated as safe no-crash behavior.
- Undo and redo command hooks are future-ready; page-level history is not yet implemented.
- Batch, stock, export, import and attachment behavior is enabled only on pages
  that already have safe business callbacks; otherwise the shared toolbar/grid
  action displays a friendly not-available message.
- Specialized remarks content still depends on each transaction type's
  available persistence data.

## Verification

- Add Row/F4 reproduction before fix: hard crash logged in `tmp/add_row_repro.log`.
- Add Row/F4 direct fix verification: `tmp/add_row_repro_after_fix.log` shows Quotation adds one row.
- Add Row/F4 page sweep: `tmp/add_row_sweep_after_root_fix.log` covers Sales Bill, Purchase Entry, Quotation, Sales Order, Delivery Challan, returns, Purchase Order, inventory, Stock Out and Dispatch Return.
- Focused UI and row-operation tests: 29 passed.
- Full regression suite: 127 passed.
- Launch/navigation/theme smoke: 17 transaction routes opened successfully.
- Smoke performance: 15.00 seconds, 5.20 MB peak Python allocation.
- SQLite integrity check: `ok`.
- Before/after evidence is stored in `screenshots/cycle_20260709_framework_*`.
- Fresh after evidence is stored in `screenshots/transaction_addrow_after_*_20260709.png`.
- Button/totals stabilization verification on 2026-07-09:
  `tests/test_document_and_module_ui.py` 36 passed; full suite 134 passed.
- Button feedback screenshot:
  `screenshots/after_button_feedback_quotation_preview_1366x768_20260709.png`.
- Totals screenshots:
  `screenshots/after_totals_sales_bill_1366x768_20260709.png`,
  `screenshots/after_totals_purchase_entry_1366x768_20260709.png`, and
  `screenshots/after_totals_quotation_1366x768_20260709.png`.
