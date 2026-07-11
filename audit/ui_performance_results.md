# UI Performance Smoke Results

Measured on a temporary copy of the local database; thresholds are regression smoke limits, not hardware benchmarks.

| Operation | Seconds | Threshold | Status |
|---|---:|---:|---|
| product_master_open | 0.1626 | 5.00 | PASS |
| add_20_pack_rows | 0.1080 | 2.00 | PASS |
| product_filter | 0.0067 | 1.00 | PASS |
| product_save_reload | 0.3277 | 5.00 | PASS |
| product_refresh | 0.2900 | 5.00 | PASS |
| new_button_response | 0.0151 | 0.25 | PASS |
| sales_bill_open | 0.1283 | 5.00 | PASS |
| purchase_entry_open | 0.0853 | 5.00 | PASS |
