# PRM BILLING INVENTORY V1.0 Safe Release Manifest

This folder contains only synthetic/product-owned validation evidence. It does
not contain a client database, client `.prmlic`, credentials, sessions, logs,
uploads or private business documents.

## Distributable product

| File | Bytes | SHA-256 |
|---|---:|---|
| `PRM_Billing_Inventory_V1.0_Setup.exe` | 43,187,187 | `04505DBEC75642B6345D547F4FC1536E3D901AE79DA3F6A0D0E2CAEF7CFBA584` |
| `PRM_Billing_Inventory.exe` | 9,842,776 | `0C521954DE709E1B1FA6CE5EBBD25CBBE9E9188F63D883ECEE9F8429F7748550` |
| `prm_billing_inventory_seed.db` | 933,888 | `E5EB868871F1F8AC120F8BF56CAD03AF3AB4D3D1505302D581FEE1B6AAB332CC` |

Only the setup is intended for normal client distribution. Each client must
receive their own valid `.prmlic` exported from PRM Client Management and select
it using the installer Browse page.

## Synthetic visual/functional evidence

| File | Bytes | SHA-256 |
|---|---:|---|
| `v1_clean_install_smoke.json` | 1,404 | `C2471EFE00CFCCC0F056EF30B6EFACB319DFC604BF12D51B21E806A0A456F4B7` |
| `v1_dashboard_1366x768.png` | 109,280 | `2B8874050A1D216CF53E0ECA100E43C961E2240CA97179BB92205A610CACC045` |
| `v1_login_version.png` | 30,131 | `C01C3F28E83ECBABBC8063996ECACDEBC8CFAFF5C4E406B0FFAE7449950EEAF5` |
| `v1_product_version_header.png` | 17,423 | `BBBCDABB1E7CB6C42C080756B00DCF8B400E94882FBA8DA155175E26305315FF` |
| `v1_profit_loss_sample.pdf` | 20,118 | `D692C5FFD6F8AFFCECC0AE4C33C7B1CE4460B25B323C3DDDEB4E7EB6E3322E9E` |
| `v1_sales_invoice_sample.pdf` | 22,263 | `B69E7E94C58027F6F67977B73016F4566D0DDB1CAC094861D14B5A12BA812F76` |

The H-drive bundle is created after the release commit/tag. It contains the
versioned setup, a source archive produced from tag `v1.0.0`, this safe evidence
folder, the release lock and an independently generated copy-verification
manifest. No runtime/client data is copied.
