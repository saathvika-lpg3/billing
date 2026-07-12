# Print Engine Guide

> **Official V1.0 release lock (2026-07-12):** [`RELEASE_LOCK.md`](../RELEASE_LOCK.md)
> is authoritative. Its accepted print/PDF/report structure, document-family
> mapping, A4/A2 portrait/landscape behavior and output parity are locked for
> V1.0. Dated test counts and 1.7.x references below are preserved as historical
> evidence, not current version identifiers or final-release certification.
> Physical-printer margins, real SMTP credentials, a logged-in WhatsApp session
> and government GST credentials remain external acceptance gates.

## 2026-07-12 production lock

- The company logo/initials block is drawn above the company name by the shared
  renderer. GSTIN, FSSAI, drug licence, phone, email and business type are
  included only when configured; individual views must not implement a
  competing header.
- Canonical A4/A2 portrait/landscape rendering retains 9 mm safe margins,
  printable-area calculations, repeated page/column headings, page numbering,
  continuation footers and final-page GST, Grand Total, amount words and
  signature safety.
- Product, Customer, Supplier and generic master lists now use the same report
  renderer as transaction lists and Report Center. Profit & Loss and Balance
  Sheet stay on the approved Tally-style two-sided statement renderer;
  receipt/payment output stays on the shared voucher renderer.
- Dispatch and loading totals are allowlisted business measures (quantity,
  weight, boxes/cartons and invoice value). Record IDs and unrelated numeric
  metadata must never be totaled.
- Print/report parity regressions cover paper/orientation variants, multi-page
  repetition, statements, vouchers, list output and dispatch totals. Physical
  printer margins remain an operator/site acceptance item because hardware
  non-printable areas differ by printer driver.

## Continuing print/report requirements

- Preserve A2 Landscape support in print preview, export, and bulk print workflows.
- Validate multi-page reports for:
  - repeated header rows on every page
  - repeated footer rows on every page if needed
  - page numbering (current page / total pages)
  - correct total pages count
  - last-page totals and summary rows
- Print QA should include at least:
  - 1-page reports
  - 2-page reports
  - 5-page reports
  - 20-page reports
  - large reports beyond 20 pages
- Reuse existing implementation patterns from `D:\PRM_BILLING_INVENTORY` when the code is stable and accepted.
- Preserve accepted report format for Profit & Loss and Balance Sheet screens; improve only if safe.
- The print engine should centralize document layout so report output is consistent across preview, PDF export, and bulk print.
- Missing print values should be hidden gracefully, not rendered as blank labels.
- Print preview must reflect the same paper size selection used for actual output.

## Canonical print architecture

The accepted print path is:

`Document -> Template Registry -> Data Mapper -> Canonical Renderer -> Paper Adapter -> Preview/PDF/Printer/Bulk Print`

- The canonical transaction renderer owns document structure, section order,
  company header, party blocks, QR/payment block, item grid, GST summary,
  totals, amount words, terms, bank details, signatures, repeated headers and
  footers.
- The paper adapter owns only physical page size, orientation, printable
  margins, safe column scaling, font scaling, row capacity and pagination.
- Paper size or orientation must not select an unrelated document template.
  It may adapt the same canonical structure to A4/A2 portrait/landscape.
- Distributor/Wholesale output must not be forced to A4. The saved template
  paper size and orientation are authoritative.

## 2026-07-10 Git repair and paper-orientation lock

- The project Git metadata was repaired after `.git` was found to be an empty
  invalid directory. The invalid folder was preserved as
  `.git_invalid_backup_20260710_130706`; origin is
  `https://github.com/saathvika-lpg3/billing.git`.
- `.gitignore` now excludes generated/runtime/client-sensitive artifacts,
  including databases, `.prmlic` files, uploads, backups, logs, generated
  PDFs/screenshots and communication/session secrets.
- `print_templates.orientation` is now persisted with an idempotent SQLite
  migration and editable from Developer Console Print Templates.
- `resolve_print_options()` and report-template resolution read orientation
  when available and fall back safely for older databases.
- `test_transaction_pdf_honors_paper_orientation_matrix_without_changing_structure`
  locks A4 Portrait, A4 Landscape, A2 Portrait and A2 Landscape so all preserve
  canonical transaction content.
- Multi-page transaction tests assert repeated item headings, continuation
  title, GST Summary, Grand Total, amount words and authorised signature.
- Validation artifacts:
  `output/pdf/print_engine_lock_20260710_130706/`.
## Foundation progress

- Added page numbering support for transaction and report PDFs using a page-aware canvas wrapper.
- Added report export overrides for explicit `paper_size` and `orientation`, enabling A2 landscape output from the desktop report layer.
- Retained the existing report header/footer layout while making pagination support reusable for future bulk print and preview workflows.
- Added a shared transaction-header compatibility layer so Sales Invoice and Purchase Invoice can reuse the same print path with safe legacy-key normalization.
- Added a voucher-entry normalization helper so Receipt and Payment payloads map to the shared voucher renderer without creating a separate engine.
- Refactored shared company header and title strip drawing into `_section_company_center_text` and `_section_title_strip` to standardize header rendering across documents.
- Added `_section_party_block` and `_section_document_details` helpers in `services/pdf_print.py`, then wired transaction and voucher blocks to use these reusable sections while preserving current A2/A4 layout and page numbering.

## 2026-07-10 Production readiness print mapping evidence

- Transaction PDFs are generated through `write_transaction_pdf()` and use
  `PrintOptions` resolved by document type/template rows.
- Voucher PDFs are generated through `write_voucher_pdf()` and covered for
  receipt/payment payload normalization.
- Report PDFs are generated through `write_report_pdf()` and can force A2/A4
  paper size and portrait/landscape orientation.
- Existing parity tests cover transaction A4 portrait, A2 landscape,
  multi-page transaction output, dispatch/report repeated headers, report page
  numbers, voucher PDFs, list-report template resolution, and migrated
  database/report totals.
- Report Center Profit & Loss and Balance Sheet print-preview handoff is now
  covered by `test_accounting_statement_reports_open_print_preview`; both
  statement routes must produce a non-empty report PDF before calling the
  shared preview layer.
- `PrintPreviewDialog._detect_pdf_layout()` must scan for `/MediaBox` beyond
  the first chunk because large ReportLab PDFs can store page boxes near the
  end of the file. `test_print_preview_detects_generated_report_paper_and_orientation`
  protects generated A4 portrait and A2 landscape detection.
- External locked-PDF visual comparison is still blocked unless
  `Print_torefer_codex.pdf` is provided as a readable file in the current
  workspace.

### Live output mapping matrix

| UI route/source | Document type | Writer | Preview/output path |
| --- | --- | --- | --- |
| Sales Bill | `sales_invoice` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Purchase Entry / Goods Receipt | `purchase_invoice` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Quotation | `quotation` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Sales Order | `sales_order` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Delivery Challan | `delivery_challan` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Sales Return | `sales_return` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Purchase Order | `purchase_order` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Purchase Return | `purchase_return` | `write_transaction_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Receipt / Payment / Expense / Journal | voucher mode | `write_voucher_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Stock Entry / Transfer / Adjustment | mode-specific report rows | `write_report_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Stock Out / Load Challan | `stock_out` | `write_report_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Dispatch Return | `dispatch_return` | `write_report_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Route Settlement | `route_settlement` | `write_report_pdf()` | `show_print_preview()` plus shared PDF/WhatsApp/Email helpers |
| Report Center list reports | selected report key | `write_report_pdf()` | report print preview / export PDF |
| Report Center Profit & Loss / Balance Sheet | statement data | `write_statement_pdf()` | report print preview / export PDF |
| Document Center selected/bulk print | selected `PRINT_DOC_META` document type | `write_transaction_pdf()` | selected or merged bulk print preview |

The mapping guard is intentionally centralized: pages should feed correct
document metadata into these writers rather than introducing page-local print
engines.

### 2026-07-10 mapping guard update

- Known transaction/voucher document types now have deterministic fallback
  print metadata in the shared resolver. This prevents a live mapping such as
  `sales_return` from resolving with a blank template key when the database
  does not contain an active template row.
- `test_document_center_print_meta_resolves_configured_templates` protects
  Document Center mappings by requiring non-empty template code/name, supported
  paper size and valid orientation for every `PRINT_DOC_META` entry.
