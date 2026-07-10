# Universal Numbering Series Engine

## Purpose
The Universal Numbering Series Engine centralizes document number generation for all future transaction and master flows. It eliminates duplicate numbering logic and provides consistent numbering rules across Sales, Purchase, Receipt, Payment, Journal, Credit Note, Debit Note, Transfer, and manufacturing documents.

## Supported document types
- Sales Invoice
- Purchase Invoice
- Sales Order
- Purchase Order
- Quotation
- Delivery Challan
- Receipt
- Payment
- Contra
- Journal
- Credit Note
- Debit Note
- Stock Transfer
- Stock Adjustment
- Manufacturing
- Any future document

## Data model
- `numbering_series`
  - `id`
  - `document_type`
  - `prefix`
  - `suffix`
  - `separator`
  - `financial_year_label`
  - `branch_code`
  - `warehouse_code`
  - `business_type_code`
  - `running_number`
  - `padding_length`
  - `start_number`
  - `current_number`
  - `reset_rule`
  - `last_reset_at`
  - `is_active`
  - `created_at`
  - `updated_at`

- `numbering_series_reservations`
  - `id`
  - `numbering_series_id`
  - `reserved_number`
  - `reserved_at`
  - `reserved_by`
  - `status`
  - `cancelled_at`
  - `created_at`

## Number format
The engine supports:
- `Prefix`
- `Suffix`
- `Separator`
- `Financial Year`
- `Branch`
- `Warehouse`
- `Business Type`
- `Running Number`
- `Padding Length`
- `Starting Number`
- `Reset Rule` (`never`, `yearly`, `monthly`)

Example output:
- `SI-2026-27-000001`
- `PI-2026-27-000001`
- `PO-2026-27-000001`

## Rules
- Numbers are unique per configured series.
- Generation is transaction-safe and serial within SQLite transactions.
- No duplicate numbers are allowed.
- Number preview is supported via `preview=True`.
- Number reservation is supported.
- Cancelled reserved numbers are recorded and never reused.

## Implementation
- `services/numbering_series_service.py`
- `MasterRepository.ensure_schema()` now creates numbering engine schema.

## Usage
- `NumberingSeriesService.create_series(...)`
- `NumberingSeriesService.generate_next(document_type, scope, preview=False, reserved_by=None)`
- `NumberingSeriesService.reserve_number(series_id, number, reserved_by)`
- `NumberingSeriesService.cancel_reserved_number(reservation_id)`

## Notes
- Future transaction flows must use this service to generate document numbers instead of inline logic.
- Document type and scope should match a configured numbering series exactly.
- The engine can be extended for branch/warehouse/business type filtering without changing per-document logic.
