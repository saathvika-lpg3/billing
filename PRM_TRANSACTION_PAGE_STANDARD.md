# PRM Transaction Page Standard

## Standard Shell
1. Page header with title and short guidance.
2. Action toolbar with New, Save, Preview, Print, PDF, WhatsApp, Duplicate, Cancel.
3. Header card for document metadata and party context.
4. Item entry card for product search and quick entry.
5. Data grid occupying the main workspace.
6. Summary panel showing totals and document status.

## Interaction Principles
- Keyboard-first input and shortcuts.
- Single-click focused form interaction.
- Clear visual hierarchy for critical fields.
- Consistent button group placement.
- No scattered or duplicated controls.

## Progress
- Phase 1: Apply the master template to transaction pages — in progress.
- Focused UI regression tests executed: 21 passed.
- Recent files updated: `sales_bill_view.py`, `sales_document_view.py`, `purchase_entry_view.py`, `inventory_entry_view.py`, `stock_out_view.py`, `dispatch_return_view.py`, `account_entry_view.py`, plus master pages updated earlier.

Next steps:
- Finish any remaining transaction pages that still use legacy headers/field boxes.
- Standardize grid keyboard navigation and single-click editing.
- Run full regression suite and document results.
