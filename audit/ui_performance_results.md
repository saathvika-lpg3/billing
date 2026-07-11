# UI Performance Smoke Results

Measured on 2026-07-12 using a temporary copy of the local database; thresholds are regression smoke limits, not hardware benchmarks.

| Operation | Seconds | Threshold | Status |
|---|---:|---:|---|
| product_master_open | 0.1402 | 5.00 | PASS |
| add_20_pack_rows | 0.0146 | 2.00 | PASS |
| product_filter | 0.0128 | 1.00 | PASS |
| product_save_reload | 0.1070 | 5.00 | PASS |
| product_refresh | 0.0554 | 5.00 | PASS |
| new_button_response | 0.0012 | 0.25 | PASS |
| sales_bill_open | 0.0683 | 5.00 | PASS |
| purchase_entry_open | 0.0530 | 5.00 | PASS |
