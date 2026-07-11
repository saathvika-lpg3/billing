# PRM Print Engine Production Contract

Updated: 2026-07-12

## Canonical architecture

All desktop print, preview, PDF and bulk-print routes use the shared renderer in
`services/pdf_print.py`. A page may map business data into the renderer, but it
must not copy or replace the page, header, footer, pagination or company-brand
implementation.

The canonical flow is:

`Document -> Template resolution -> Data mapping -> Shared renderer -> Paper adapter -> Preview/PDF/Printer`

## Locked output rules

- Client logo or professional initials placeholder appears above the company
  name and preserves aspect ratio. GSTIN, FSSAI, drug licence, phone, email and
  business type appear when configured.
- A4 Portrait, A4 Landscape, A2 Portrait and A2 Landscape use the same document
  structure. The paper adapter changes only physical sizing, orientation,
  safe scaling and pagination.
- The default safe margin is 9 mm. Headers, tables, footers and signatures must
  stay inside the printable frame with no cropped text, blank spill page,
  overlap or hidden summary.
- Multi-page output repeats the document/page header, table column headings,
  continuation identity and footer/page number. GST Summary, Grand Total,
  amount words and authorised signature remain complete on the final page.
- Product, Customer, Supplier and generic master lists, sales/purchase lists,
  stock/inventory, reports and ledgers use the professional report renderer.
- Profit & Loss and Balance Sheet retain the approved Tally-style two-column
  statement renderer, including continuation pages. Receipt and Payment retain
  the shared voucher identity, bank/reference/instrument and signature layout.
- Dispatch/loading reports total only allowlisted business measures such as
  quantity, weight, boxes, cartons and invoice value. Database IDs are never a
  report total.

## Validation evidence

- The print/report parity batch passed 31 tests in 61.13 seconds and the final
  full release suite passed 213 tests.
- Tests cover A4/A2 portrait/landscape, single- and multi-page reports,
  repeated headings/footers/page numbering, Profit & Loss, Balance Sheet,
  receipt/payment vouchers, list printing, dispatch/loading totals and shared
  company branding.
- Safe visual evidence includes
  `screenshots/production_stabilization_after_profit_loss_1366x768_20260712.png`
  plus the transaction/master screenshots recorded in `TEST_REPORT.md`.

## External acceptance

Physical printer output must be accepted once per client printer/driver because
hardware non-printable regions vary. This does not change the canonical 9 mm
layout contract or permit page-specific print code.
