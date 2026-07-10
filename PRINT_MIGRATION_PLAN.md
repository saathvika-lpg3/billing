# PRM Billing and Inventory - Phase 7A
# Print Engine Migration Plan

## Scope

This document is a controlled migration plan for the print engine from the existing PRM Billing Inventory reference project. The goal is to reuse proven layout behavior and business logic where appropriate, while preserving the current desktop architecture and avoiding a redesign.

## Reference Source

- Reference project: D:\PRM_BILLING_INVENTORY
- Current desktop project: D:\PRM_GST_DESKTOP
- Central print service: services/pdf_print.py
- Primary UI entry points: views/sales_bill_view.py, views/purchase_entry_view.py, views/account_entry_view.py, views/report_center_view.py

## Analysis Summary

### Files analyzed

- services/pdf_print.py
- tests/test_print_and_report_parity.py
- views/sales_bill_view.py
- views/purchase_entry_view.py
- views/account_entry_view.py
- views/report_center_view.py
- docs/DESKTOP_UI_SYSTEM.md
- docs/PRM_GST_PARITY_AUDIT_20260702.md
- docs/DESKTOP_MIGRATION_PLAN.md
- D:\PRM_BILLING_INVENTORY\docs\DESKTOP_MIGRATION_PLAN.md
- D:\PRM_BILLING_INVENTORY\docs\PRM_GST_PARITY_AUDIT_20260702.md

### Documents found

The reference project does not expose a full legacy print source tree under src; the available evidence is primarily documentation, packaging output, and the current desktop print engine implementation. The migration target remains the business behavior and layout patterns that are already reflected in the current architecture.

## Current implementation

The current project already has a central print engine in services/pdf_print.py with:

- a shared transaction writer for sales and purchase invoices
- a shared voucher writer for receipt/payment-style documents
- a shared report writer for tabular reports
- paper-size and orientation resolution based on company/business type and template settings
- automatic page numbering for PDF exports
- support for A2 landscape output for distributor-style invoices and vouchers

## Existing implementation

The legacy/reference project appears to be a prior PRM Billing Inventory release that emphasized:

- invoice and voucher print output
- GST-aware document layout
- report export and print workflows
- business-type-specific template selection

The exact legacy print source files were not found in the checked reference tree, so the migration should rely on documented behavior and the current implementation patterns rather than direct code copying.

## Reuse opportunities

### Reusable code

- GST and totals calculations already flow through the desktop transaction and report workflows.
- The current shared writer functions already centralize document layout and PDF generation.
- Business-type-aware template selection is already present in the print service.
- Page numbering and report pagination are already implemented in the central engine.

### Reusable layouts

- Sales and purchase invoices share the same structural logic and line-item layout.
- Receipt and payment vouchers share the same voucher template family.
- Tabular reports share a common header/body/footer pattern.

### Reusable calculations

- Taxable, GST, round-off, and grand-total calculations already exist in the transaction view layer.
- These should remain in the existing calculator layer instead of being duplicated in the print engine.

### Reusable headers and footers

- Company header blocks, party header blocks, and page-foot metadata are already handled in the current PDF service.
- The migration should preserve these patterns and extend them only when the reference layout showed stronger structure.

### Reusable GST summary

- The current invoice payload already supplies GST breakdown per line and totals summary.
- This is a strong candidate for reuse without rewriting the calculation path.

### Reusable page numbering

- Already present in the current engine and should remain the default behavior for all generated PDFs.

## Document-by-document migration plan

| Document / Report | Current implementation | Existing implementation | Reuse % | Changes required | Risk level | Recommendation |
|---|---|---|---|---|---|---|
| Sales Invoice | Central transaction PDF writer with line-item and GST totals rendering | Legacy wholesale/distributor invoice layout with A2 landscape support | 95% | Preserve current layout contract, add stronger header/footer fidelity and optional legacy field mapping; refactored shared header/title into reusable sections. | Medium | Completed. |
| Purchase Invoice | Central transaction PDF writer reused from sales invoice flow | Similar invoice layout with supplier context | 80% | Completed: reuse the same shared transaction print path, preserve existing layout/rendering, and add safe supplier-style header compatibility mapping only. | Low | Completed. Continue with Receipt Voucher next. |
| Receipt Voucher | Central voucher PDF writer | Legacy receipt voucher style | 100% | Completed: voucher normalization helper added; layout rendering preserved via shared `_draw_voucher` function; header/title refactored to sections. | Low | Completed. |
| Payment Voucher | Central voucher PDF writer | Legacy payment voucher style | 100% | Completed: voucher normalization helper added; layout rendering preserved via shared `_draw_voucher` function; header/title refactored to sections. | Low | Completed. |

## Recent implementation update

- Added `_section_party_block` and `_section_document_details` helpers in `services/pdf_print.py`.
- Wired party and voucher metadata rendering through these helpers in `_draw_transaction_header` and `_draw_voucher`.
- Preserved existing A2/A4 layout logic, QR image placement, and page numbering behavior.
| Delivery Challan | Not yet specialized; current architecture can reuse generic transaction layout | Legacy challan/document layout | 60% | Add document-type-specific metadata and line summary fields | Medium | Migrate after voucher flows. |
| Loading Sheet | Report-style document | Legacy dispatch/loading style | 55% | Adapt report-table layout and repeated header/footer behavior | Medium | Migrate after basic transaction documents. |
| Dispatch Summary | Report-style document | Legacy dispatch summary view | 60% | Reuse report writer and add grouped totals/summary rows | Medium | Migrate after loading sheet. |
| Ledger | Report-style document | Legacy ledger listing | 70% | Reuse report writer and ensure date/amount columns and running balance display | Low | Migrate once the report writer is stable. |
| Outstanding | Report-style document | Legacy outstanding summary | 70% | Reuse report writer and add balance grouping fields | Low | Migrate after ledger. |
| Day Book | Report-style document | Legacy day-book register | 70% | Reuse report writer and adjust account/date/amount columns | Low | Migrate after outstanding. |
| Cash Book | Report-style document | Legacy cash-book register | 70% | Reuse report writer with cash-specific grouping | Low | Migrate after day book. |
| Bank Book | Report-style document | Legacy bank-book register | 70% | Reuse report writer with bank-specific grouping | Low | Migrate after cash book. |
| Trial Balance | Report-style document | Legacy trial balance output | 75% | Reuse report writer and add debit/credit columns | Low | Migrate after book reports. |
| Balance Sheet | Report-style document | Legacy balance sheet layout | 50% | Reuse report writer but likely needs a specialized layout, not plain tabular export | High | Migrate only after the generic report engine is stabilized. |
| Profit & Loss | Report-style document | Legacy P&L layout | 50% | Reuse report writer but likely needs a specialized layout and grouped totals | High | Migrate only after balance sheet. |

## Technical debt found

- The legacy source tree is not available in the checked reference project, so migration must be based on behavior and documentation rather than direct source reuse.
- The current print engine is centralized, but some document-specific formatting remains implicit rather than explicitly parameterized.
- The report writer is generic and will need document-specific formatting extension for complex reports such as balance sheet and P&L.
- Some field names and labels still need explicit alignment with legacy document vocabulary.

## Migration risks

- Layout mismatch between the current desktop print engine and the legacy printed output.
- Business-type-specific templates may not fully match the old wide-format distributor invoice expectations.
- Complex financial statements may require a custom layout rather than a generic table export.
- Over-copying the legacy behavior could break the current architecture and test coverage.

## Recommended migration order

1. Sales Invoice
2. Purchase Invoice
3. Receipt Voucher
4. Payment Voucher
5. Delivery Challan
6. Loading Sheet
7. Dispatch Summary
8. Ledger
9. Outstanding
10. Day Book
11. Cash Book
12. Bank Book
13. Trial Balance
14. Balance Sheet
15. Profit & Loss

## Immediate next step

Begin migration one document at a time, starting with Sales Invoice. The current implementation already exposes a transaction print path that is suitable for this first migration pass.
