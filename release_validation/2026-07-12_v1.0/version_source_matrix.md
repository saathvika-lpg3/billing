# PRM BILLING INVENTORY V1.0 Version-Source Matrix

Audit date: 2026-07-12

Policy: active product/runtime/package/installer identity uses technical version
`1.0.0`, compact display `V1.0`, release name `PRM BILLING INVENTORY V1.0` and
annotated tag `v1.0.0`. Historical, schema, migration, protocol and file-format
versions retain their original ordering and meaning.

| File / surface | Symbol or field | Pre-lock value | V1.0 value / action | Change required | Compatibility risk | Regression evidence |
|---|---|---|---|---|---|---|
| `config/product_version.py` | product constants / `__version__` | no authority module | `1.0.0`, `V1.0`, release name | Yes | Low; removes drift | runtime-version tests |
| `app.py` | Qt application identity | name only | product name, display name and application version from authority module | Yes | Low | startup/runtime-version tests |
| `widgets/product_branding.py` | fixed product header | product name/tagline only | retain PRM identity and add compact `V1.0` | Yes | UI geometry/readability | branding + live three-size audit |
| `views/login_dialog.py` | login product identity | no release version | shared product header displays `V1.0` | Via shared component | UI geometry | login branding test |
| `views/main_window.py` | window title | product name only | `PRM BILLING INVENTORY V1.0` | Yes | automation/window-title expectations | runtime-version + frozen launch |
| `services/dashboard_service.py` | Application Version dataset | schema release row presented as app version | prepend canonical Desktop Runtime `V1.0`; retain schema rows as components/history | Yes | avoids relabelling migrations | dashboard/runtime-version test |
| Developer Console / diagnostics | version record | database diagnostic only | canonical runtime record available without changing schema IDs | Yes | low | developer/runtime tests |
| `PRM_Billing_Inventory.spec` | Windows EXE version resource | none | numeric `1.0.0.0`, text `1.0.0`/`V1.0`, PRM product/company metadata | Yes | high shell/file-property visibility | spec test + post-build property audit |
| `installer/prm_billing_inventory.iss` | `MyAppVersion` | internal pre-release `1.7.8` | `1.0.0` | Yes | official semantic reset; stable AppId preserves upgrade | packaging + real 1.7.8 upgrade |
| `installer/prm_billing_inventory.iss` | display/ARP/setup file properties | internal pre-release identity | `V1.0`, Windows `1.0.0.0`, PRM publisher/product | Yes | shell/ARP identity | post-build metadata audit |
| `installer/prm_billing_inventory.iss` | output filename | generic setup name | `PRM_Billing_Inventory_V1.0_Setup.exe` | Yes | build consumers must change together | build-script/packaging tests |
| `installer/prm_billing_inventory.iss` | AppId/executable/install path | existing stable values | unchanged | No | critical upgrade contract | packaging + real upgrade |
| `installer/prm_billing_inventory.iss` | `[InstallDelete]` | seven-rule 1.7.8 allowlist | exact same seven rules | No broadening | critical client-data safety | exact-set regression |
| `tools/build_installer.ps1` | expected artifact | generic setup filename | V1.0 versioned filename | Yes | stale/missing artifact false result | packaging + clean build |
| `tools/build_desktop.ps1` / seed preparation | installer DB source | sanitized from development DB | product-owned sanitized/unbound seed path | Reviewed | must never package client rows | seed privacy tests |
| `tests/test_installer_packaging.py` | active installer expectation | `1.7.8` / generic filename | `1.0.0`, `V1.0`, versioned filename, exact cleanup rules | Yes | release drift prevention | focused installer gate |
| `README.md` | current release | 1.7.8 | V1.0 / technical 1.0.0 | Yes | documentation | release-lock test |
| `CURRENT_STATUS.md` / `PRM_CURRENT_STATUS.md` | current release status | 1.7.8 | new V1.0 section; retain 1.7.8 history | Yes | historical accuracy | doc review |
| `INSTALLER.md` / installer certification | current artifact | certified internal 1.7.8 hash | add V1.0 size/hash/clean+upgrade results after build | Yes | must not invent artifact data | final artifact audit |
| `TEST_REPORT.md` | latest gate | 1.7.8 correction | add exact V1.0 compile/regression/install results | Yes | evidence accuracy | final test manifests |
| `CHANGELOG.md` | latest entry | internal 1.7.8 correction | add official V1.0 entry above history | Yes | history preserved | doc review |
| `RELEASE_LOCK.md` | permanent contract | absent | V1.0 identity, locked behavior, gates, change control and rollback | Yes | release governance | release-lock test |
| `release_validation/2026-07-12_v1.0` | safe release evidence | absent | version matrix, hashes, test summary, screenshots/PDF and verification | Yes | privacy scan required | release manifest audit |

## Intentionally unchanged compatibility and historical versions

| Source | Value | Reason unchanged |
|---|---|---|
| SQLite `PRAGMA user_version`, migrations and `app_release_versions.schema_version` | existing ordered identifiers such as `20260701_pdf_archive_speed_cache` | database compatibility/migration history, not product marketing |
| `.prmlic` payload format date | `2026-06-28` where used in synthetic tests | licence format compatibility |
| `services/gst_payload_service.py` | GST payload `1.1` | external payload schema |
| CA export schema | `inventory` | export schema identifier |
| backup envelope version | existing numeric format | restore compatibility |
| PDF header | `%PDF-1.4` | document file format |
| XML declarations | `1.0` | XML standard version |
| dependency/Python versions | installed tool versions | dependency identity, recorded separately |
| historical 1.7.5/1.7.6/1.7.7/1.7.8 changelog, hashes and certification | original values | immutable internal pre-release evidence and rollback diagnosis |
| tag `v1.0.0-production-baseline` | existing historical tag | separate earlier baseline; never move or overwrite |

The official tag `v1.0.0` did not exist at inventory time and must be created
only after the V1.0 candidate passes all release gates.
