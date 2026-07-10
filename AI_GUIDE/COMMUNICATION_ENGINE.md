# Communication Engine Guide

## Future communication requirements

- Add support for WhatsApp sharing as part of the Communication Engine.
- The Communication Engine must support sending:
  - invoices
  - receipts
  - payment reminders
  - outstanding statements
  - ledgers
  - reports
  - purchase orders
  - PDFs
- WhatsApp integration should be planned as a future external channel that consumes generated document output.
- Keep communication behavior separate from core save/print workflows to preserve desktop architecture.
- The engine should handle share metadata, contact resolution, and message templates safely.
