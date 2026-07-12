# V1.0 Release-Lock Verification

The official baseline was checked against [`RELEASE_LOCK.md`](../../RELEASE_LOCK.md).

| Locked area | Result | Evidence |
|---|---:|---|
| Identity and version | Passed | Central `config/product_version.py`; Qt, header, windows and setup use 1.0.0/V1.0 |
| Historical compatibility IDs | Passed | 1.7.x history and schema/migration/licence-format IDs retained |
| Database and licensing | Passed | Sanitized unbound seed; per-client Browse selection; real DB/licence preserved |
| Stable installer identity | Passed | AppId, installed path and executable unchanged |
| Seven-rule cleanup allowlist | Passed | Exact-set regression; no client-data target |
| Product/client branding boundary | Passed | Fixed PRM header plus separate client-company contexts |
| Layout and shared UI frameworks | Passed | 59/59 routes at three resolutions and complete regression |
| Keyboard, smart dropdown and action feedback | Passed | Complete shared-control regression suite |
| Navigation and Dispatch Summary | Passed | Canonical route exercised in installed smoke |
| Transactions, posting, GST and integrity | Passed | Complete regression suite |
| Print/PDF/report mapping | Passed | Automated suite plus rendered Sales Invoice and Profit & Loss evidence |
| Communication behavior | Passed in code | Automated attachment/fallback coverage; live accounts remain external |
| Clean install/upgrade/uninstall | Passed | Frozen launch, installed smoke, byte-preservation and real upgrade |
| Package privacy | Passed | Zero forbidden packaged findings |

The annotated `v1.0.0` tag is the immutable commit authority. The distribution
copy is produced only from that tag and carries a post-copy SHA-256 manifest.
