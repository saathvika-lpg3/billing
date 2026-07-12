# ERP Business Flow Completion Matrix

> **Official V1.0 release context:** [`RELEASE_LOCK.md`](../RELEASE_LOCK.md)
> locks only the accepted, tested behaviors identified as functional in this
> matrix. Explicit limitations remain accurate scope disclosures; the V1.0
> label does not silently convert incomplete operations into passed workflows.
> Historical checkpoint identifiers below remain evidence, not active product
> versions.

Audit cycle: 2026-07-11
Starting checkpoint: `71a4aab` on `business-flow-audit-20260710`
Intermediate safety commit: `acfb396`

This matrix traces the live desktop path. A route or table by itself is not treated as proof of completion. `Fully functional` means the route reads live SQLite data and its applicable save, posting, reversal, report, and output path is exercised. Limitations are listed explicitly.

## Core transaction lifecycle

| Flow | Live route / view | Save and validation path | Tables and effects | Edit / cancel / output | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Quotation | `quotation_entry` / `SalesDocumentView` | `save_order_document`; document/party/item/totals/date/unique-number validation | `order_documents`, `order_document_items`; no stock or ledger posting by design | Conversion through `OrderConversionService`; PDF/share use the same computed payload | Existing conversion and output tests | Fully functional |
| Sales Order | `sales_order_entry` / `SalesDocumentView` | Same order framework | Order tables; non-posting until conversion | Converts once to Sales; converted source status retained | Conversion regression | Fully functional |
| Delivery Challan | `delivery_challan_entry` / `SalesDocumentView` | Same order framework | Order tables; dispatch lifecycle only | PDF/share and dispatch-return source path | Dispatch-return regression | Fully functional with no accounting effect by design |
| Cash Sale | `sales_bill` / `SalesBillView` | `save_sales`; atomic SQLite transaction | `sales`, `sales_items`, `stock_log`, item/pack/warehouse stock, `gst_postings`, voucher and ledger; Cash debited | List opens editor; edit reverses/reposts; cancel restores stock and deactivates GST/ledger; PDF/share use one document | Lifecycle and existing print tests | Fully functional |
| Credit Sale | `sales_bill` / `SalesBillView` | Same; party balance updated by Grand Total | Customer debit, Sales/output GST credit, round-off balancing row, outstanding increase | Edit/cancel protected against duplicate active posting | Lifecycle diagnostics pass on clean fixture | Fully functional |
| Sales Return / Credit Note | `sales_return_entry` / `SalesDocumentView` | Source quantity/free-quantity limits; atomic save | Return header/items, accepted stock in, negative output GST, Sales Return ledger, outstanding reduction | Return List supports cancellation and correct reversal | Return and dispatch-return tests | Fully functional |
| Receipt / partial receipt / advance | `receipt_entry` / `AccountEntryView` | Positive amount/date/party/unique-number/locked-year validation | Receipt, voucher, Cash/Bank debit, customer credit, party balance reduction; overpayment becomes credit balance | Draft is non-posting; cancellation restores balance; voucher PDF/share path | Partial receipt, draft, and cancellation tests | Fully functional at party-account level |
| Purchase Order | `purchase_order_entry` / `PurchaseDocumentView` | Order validation and unique number | Order tables; non-posting until conversion | Converts once to Purchase; PDF/share | Conversion regression | Fully functional |
| Cash Purchase | `purchase_entry` / `PurchaseEntryView` | `save_purchase`; atomic validation | Purchase/items, stock in, input GST, Purchases debit, Cash credit | List-to-edit and cancellation lifecycle | Purchase lifecycle regression | Fully functional |
| Credit Purchase | `purchase_entry` / `PurchaseEntryView` | Same; live warehouse ID is persisted | Supplier credit, outstanding increase, global and warehouse stock increase | Edit reverses/reposts once; cancellation restores stock/outstanding | Purchase edit test | Fully functional |
| Purchase Return / Debit Note | `purchase_return_entry` / `PurchaseDocumentView` | Source limits plus available-stock validation | Stock out, negative input GST, Purchase Return credit, supplier debit | Debit Notes supports cancellation/reversal | Return lifecycle test | Fully functional |
| Payment / partial payment / advance | `payment_entry` / `AccountEntryView` | Account validation | Supplier debit, Cash/Bank credit, payable reduction; overpayment becomes supplier debit balance | Draft non-posting; cancellation restores balance | Payment lifecycle test | Fully functional at party-account level |
| Expense | `expense_entry` / `AccountEntryView` | Positive amount/date/ledger/number validation | Expense debit and Cash/Bank credit | Cancel marks voucher and ledger rows inactive | Account posting framework | Fully functional |
| Journal / Contra | `journal_entry` / `AccountEntryView` | Different debit/credit ledgers required; amount/date/number validation | Balanced two-line voucher | Draft non-posting; cancellation deactivates both lines | Contra regression | Fully functional |
| Stock Entry | `stock_entry_entry` / `InventoryEntryView` | Item/quantity/date/reference/warehouse validation | Item/pack/warehouse stock plus `stock_log` | PDF/share available | Stock-entry regression | Functional; saved entries do not yet have a cancellable header |
| Stock Transfer | `stock_transfer_entry` / `InventoryEntryView` | Both warehouses required and different; source availability checked | Equal transfer-out and transfer-in log; global stock unchanged; warehouse balances move | Transfer List cancellation moves stock back and retains audit rows | Transfer lifecycle test | Fully functional |
| Stock Adjustment | `stock_adjustment_entry` / `InventoryEntryView` | Count/difference validation; negative stock rejected atomically | `stock_adjustments`, item/pack/warehouse balance and movement | PDF/share available | Negative rollback test | Functional; adjustment cancellation is not yet exposed |
| GST | Sales/Purchase/Return services and Report Center | Line/document reconciliation within one paisa | Active input/output GST postings; return rows are negative | GST report, HSN Summary, annual summary exclude cancelled/superseded rows | Interstate multi-rate test | Fully functional for local calculation/reporting |
| Financial statements | Accounts Hub / Report Center | Active ledger rows only | Trial Balance, P&L and Balance Sheet derive from ledger and stock valuation | Date filters, PDF/CSV and statement preview | Existing statement tests plus performance smoke | Fully functional for code-created balanced data |
| Print and communication | Transaction views, Document Center | One calculated header/line/totals payload | Accepted A4/A2 portrait/landscape templates retained | Preview/PDF path returned to WhatsApp/email preparation as the same attachment | Existing print/communication regressions | Fully functional |

## Posting invariants enforced

- All document, line, stock, GST, voucher, ledger, and party-balance mutations execute in one SQLite transaction.
- Free quantity is a free portion of physical `qty`; it reduces billable quantity and is not added a second time to stock movement.
- Round-off creates a balancing ledger row. Voucher header debit/credit totals reflect the actual balanced posting total; party outstanding reflects Grand Total.
- One active voucher version is permitted after edit. Old voucher, ledger, and GST rows become `Superseded`; stock and outstanding effects are reversed before reposting.
- Cancellation requires a reason, retains the source document, reserves its number, creates auditable stock reversal movements, and excludes inactive postings from financial/GST reports.
- Draft/Hold account vouchers and draft transfers are saved without financial or stock posting.
- Closed financial-year dates, duplicate numbers, invalid totals, invalid quantities, missing referenced items/packs/warehouses, same-warehouse transfers, and insufficient stock fail before commit.

## Original 59 preview/list/report operations

| # | Operation | Route key | Classification | Verified behavior / limitation |
| ---: | --- | --- | --- | --- |
| 1 | Quotation List | `quotation_list` | Missing drill-down | Live rows, filter, print/PDF/CSV; conversion remains in Document Center. |
| 2 | Order List | `order_list` | Missing drill-down | Live rows and outputs; conversion is separate. |
| 3 | Sales List | `sales_list` | Fully functional | Auditable all-status list; double-click/Edit opens saved bill; cancel reverses effects. |
| 4 | DC List | `dc_list` | Missing drill-down | Live rows and outputs; dispatch-return workflow is separate. |
| 5 | Return List | `return_list` | Fully functional | Live return rows and cancellation/reversal. |
| 6 | Print Batches | `print_batches` | Fully functional | Live batch audit rows, filter and export. |
| 7 | Print Templates | `print_templates` | Fully functional | Live templates; editor/preview remains in Document Center/Developer Admin. |
| 8 | Print Logs | `print_logs` | Fully functional | Live immutable print audit rows. |
| 9 | PO List | `po_list` | Missing drill-down | Live rows and output; conversion remains in Document Center. |
| 10 | Purchase List | `purchase_list` | Fully functional | Auditable all-status list; double-click/Edit and cancel supported. |
| 11 | Debit Notes | `debit_notes` | Fully functional | Live purchase returns and cancellation/reversal. |
| 12 | Supplier Ledger | `supplier_ledger` | Fully functional | Live ledger rows retain status for audit; print/export available. |
| 13 | Transfer List | `transfer_list` | Fully functional | Live transfers and cancellation with equal reverse movement. |
| 14 | Expiry / Wastage | `expiry_wastage` | Missing drill-down | Live batch/expiry rows; no batch adjustment editor from this list. |
| 15 | Load Challans | `load_challans` | Missing drill-down | Live challan headers; detailed dispatch-return route is separate. |
| 16 | Stock Movement | `stock_entry` | Fully functional | Live `stock_log` movement, date filter and export. |
| 17 | Cash / Bank Book | `cash_bank` | Fully functional | Active Cash/Bank rows only; cancelled/superseded entries excluded. |
| 18 | Outstanding | `outstanding` | Fully functional | Current customer/supplier balances including advances. |
| 19 | Aging Report | `aging_report` | Route exists but data incomplete | Separates receivable/payable/advance, but no invoice-age buckets without allocation data. |
| 20 | Customer Ledger | `customer_ledger` | Fully functional | Live rows with posting status retained for audit. |
| 21 | Ledger Groups | `ledger_groups` | Fully functional | Live group hierarchy rows. |
| 22 | Trial Balance | `trial_balance` | Fully functional | Active postings only; debit/credit totals are not concealed when legacy data differs. |
| 23 | Voucher Register | `vouchers` | Fully functional | Auditable all-status voucher headers. |
| 24 | Voucher Review | `voucher_review` | Missing drill-down | Live approval/status ordering; no approval action on the list itself. |
| 25 | Bank Reconciliation | `bank_reconciliation` | Route exists but data incomplete | Live rows; matching/clearance editor is not exposed here. |
| 26 | Cash Flow | `cash_flow` | Fully functional | Active Cash/Bank movements with date filter. |
| 27 | Fund Flow | `fund_flow` | Fully functional | Active ledger net movement by ledger. |
| 28 | ERP Ledger | `erp_ledger` | Fully functional | Full auditable ledger list with statuses. |
| 29 | ERP Day Book | `erp_day_book` | Fully functional | Full auditable voucher day book. |
| 30 | Control Check | `control_check` | Fully functional | Surfaces ledger imbalance and stock-value movement; does not hide differences. |
| 31 | ERP Profit & Loss | `erp_profit_loss` | Fully functional | Active date-filtered statement and print layout. |
| 32 | Balance Sheet | `balance_sheet` | Fully functional | Active as-on statement plus explicit stock adjustment control. |
| 33 | Stock Ledger Adj. | `stock_ledger_adj` | Route exists but data incomplete | Live adjustment audit rows; posting editor is not exposed from this list. |
| 34 | Sales Reports | `sales_register` | Fully functional | Active date-filtered Sales Register; cancelled rows remain only in Sales List. |
| 35 | Purchase Reports | `purchase_register` | Fully functional | Active date-filtered Purchase Register. |
| 36 | Stock Reports | `stock` | Fully functional | Current stock snapshot; date range is not applicable to a snapshot. |
| 37 | Item Movement | `item_movement` | Fully functional | Live movement source with date filtering. |
| 38 | GST Reports | `gst_reports` | Fully functional | Active input/output postings with date filtering. |
| 39 | GST Return | `gst_return` | Route exists but data incomplete | Shows local filing records; statutory submission requires external credentials. |
| 40 | E-Invoice | `einvoice` | Route exists but data incomplete | Offline JSON preparation works; government acknowledgement requires credentials. |
| 41 | E-Way Bill | `eway_bill` | Route exists but data incomplete | Offline JSON preparation works; government acknowledgement requires credentials. |
| 42 | Profit & Loss | `erp_profit_loss` | Fully functional | Same reconciled statement source as Accounts. |
| 43 | Day Book | `day_book` | Fully functional | Active, date-filtered vouchers only. |
| 44 | Audit Log | `audit_log` | Fully functional | Live audit rows with date filter and export. |
| 45 | Daily Dispatch Summary | `daily_dispatch_summary` | Fully functional | Live, date-filtered dispatch headers. |
| 46 | Item Loading Sheet | `item_loading_sheet` | Fully functional | Active challan items with date filter. |
| 47 | Route Loading Sheet | `route_loading_sheet` | Fully functional | Active, date/item/route aggregation. |
| 48 | Pending Dispatch | `pending_dispatch` | Fully functional | Active incomplete dispatches only. |
| 49 | Loading Sheet | `loading_sheet` | Fully functional | Active loading headers with date filter. |
| 50 | Customer Loading Sheet | `customer_loading_sheet` | Fully functional | Active sales/dispatch rows only. |
| 51 | Dispatch Return Summary | `dispatch_return_summary` | Fully functional | Live dispatch-return values/statuses and export. |
| 52 | Balance Sheet | `balance_sheet` | Fully functional | Same reconciled statement source as Accounts. |
| 53 | Trial Balance | `trial_balance` | Fully functional | Same active ledger aggregation as Accounts. |
| 54 | GST Postings | `gst_reports` | Fully functional | Active posting detail; cancelled/superseded rows excluded. |
| 55 | Stock Postings | `stock_postings_report` | Fully functional | Rewired from stale legacy value rows to live `stock_log`. |
| 56 | Inventory Valuation | `inventory_valuation` | Fully functional | Current item quantity multiplied by standard cost. |
| 57 | GST Adjustment | `gst_adjustment` | Route exists but data incomplete | Live audit rows; adjustment entry workflow is not exposed in Report Center. |
| 58 | ITC Reconciliation | `itc_reconciliation` | Route exists but data incomplete | Live imported/matched rows; external GSTR-2B acquisition is credential-dependent. |
| 59 | GSTR-9 Annual | `gstr9_annual` | Fully functional local summary | Rewired to active GST postings grouped by financial year; statutory filing remains external. |

Additional operation added in this cycle: `HSN Summary` (`hsn_summary`), calculated from active GST postings by date, HSN, rate, and input/output type.

## Deterministic coverage

`tests/test_business_flow_lifecycle.py` uses an isolated copied database and covers:

- credit sale, free quantity, round-off, outstanding, cancellation and inactive report filtering;
- sales edit without duplicate active posting;
- partial receipt and receipt cancellation;
- transfer equality, global-stock preservation and transfer cancellation;
- credit purchase, purchase edit, purchase return/cancel, partial payment/cancel and purchase cancel;
- sales return/cancel;
- interstate multi-rate GST, discount, date-filtered registers, HSN and GST report agreement;
- insufficient stock, duplicate number and locked-year atomic rollback;
- non-posting draft receipt and balanced Journal/Contra cancellation;
- negative stock-adjustment rollback; and
- a clean deterministic database where all 12 integrity diagnostics pass.

## Genuine remaining limitations

1. Receipt/payment updates party outstanding but has no invoice-allocation table. Exact invoice aging, allocation validation, and invoice-by-invoice advance application remain future schema work.
2. Batch/expiry rows are visible, but sales/purchase entry does not yet capture a batch ID; batch-level FEFO movement cannot be claimed.
3. Pack snapshots and pack stock are retained, but conversion into a canonical base-UOM stock ledger is not implemented. Current quantities use the selected pack's stored quantity convention.
4. Stock Entry and Stock Adjustment lack a cancellable document-header lifecycle. Their saves are atomic and negative-safe, but reversal requires a new adjustment.
5. Landed-cost allocation is not implemented.
6. The inherited live/demo database contains legacy inconsistencies recorded in `audit/business_flow_audit.json`; this cycle does not rewrite customer data or fabricate balancing entries.

These limitations prevent an unconditional production-readiness claim for batch-controlled, invoice-allocation, or base-UOM conversion deployments. They do not invalidate the code-controlled lifecycle checks that pass on the deterministic fixture.
