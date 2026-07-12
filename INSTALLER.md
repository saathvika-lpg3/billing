# Installer Runtime Certification

## Official PRM BILLING INVENTORY V1.0 - certified 2026-07-12

- Artifact: `installer_output/PRM_Billing_Inventory_V1.0_Setup.exe`
- Product/display version: `1.0.0` / `V1.0`
- Size: 43,187,187 bytes
- SHA-256: `04505DBEC75642B6345D547F4FC1536E3D901AE79DA3F6A0D0E2CAEF7CFBA584`
- Frozen executable: 9,842,776 bytes, SHA-256
  `0C521954DE709E1B1FA6CE5EBBD25CBBE9E9188F63D883ECEE9F8429F7748550`
- Sanitized seed: 933,888 bytes, SHA-256
  `E5EB868871F1F8AC120F8BF56CAD03AF3AB4D3D1505302D581FEE1B6AAB332CC`
- Build: PyInstaller 6.21.0 / Python 3.13.7 / Inno Setup 6.7.3.
- Stable upgrade identity: unchanged AppId, executable name and install path;
  exact seven-entry 1.7.8 cleanup allowlist retained.
- Clean install and responsive frozen launch: **PASSED** with exact title
  `PRM BILLING INVENTORY V1.0 Login`.
- Authenticated installed-resource smoke: **PASSED** using a disposable copy;
  Product Master save/reload, Sales/Purchase Grand Total, routing, branding,
  themes and SQLite integrity all passed without changing the installed seed.
- Preserving uninstall: **PASSED**. Executable, uninstaller and shortcut were
  removed; database, licence, settings and uploads markers remained
  byte-identical.
- Real internal-pre-release-to-V1.0 upgrade: **PASSED**. Installed executable
  matched the certified frozen hash, and the real client database and licence
  were byte-identical across setup.
- Payload privacy: 238 files / 132,500,207 bytes with zero private `.prmlic`,
  PowerShell, logs, uploads, tests, audit, backups, NumPy or lxml findings.
- Authenticode: unsigned because no organization code-signing certificate was
  supplied. Signing is an external distribution gate, not a runtime failure.

## Release 1.7.8 - certified 2026-07-12

- Artifact: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 43,187,727 bytes (8,686,079 bytes / 16.74% smaller than 1.7.6)
- SHA-256: `0C57293DECCC94ED6FDE2CD6177DBA3D6DB55DFF638A02B98CA2C1D5B5E6B1A2`
- Frozen executable: 9,839,737 bytes, SHA-256
  `F721794BDED7023C84C6667C3707BE288BC9494BDC5F19338F86F140061EE1FB`
- Sanitized seed SHA-256:
  `E5EB868871F1F8AC120F8BF56CAD03AF3AB4D3D1505302D581FEE1B6AAB332CC`
- Build: PyInstaller 6.21.0 / Python 3.13.7 / Inno Setup 6.7.3.
- Corrective real upgrade: **PASSED**. Database and licence were byte-identical;
  stale runtime packages were removed; frozen PRM login opened responsive with
  empty stderr; authenticated installed-resource smoke passed.

### Required optimized-upgrade cleanup

Inno Setup does not remove files merely because a newer payload omits them.
Release 1.7.7 therefore left partial `numpy`/`lxml` trees from 1.7.6 in a real
upgrade. `openpyxl` found stale `numpy` and failed before `app.main()` with
`AttributeError: module 'numpy' has no attribute 'short'`.

Release 1.7.8 adds a narrow `[InstallDelete]` list for:

- `_internal\numpy`, `_internal\numpy.libs`, `numpy-*.dist-info`;
- `_internal\lxml`, `lxml-*.dist-info`;
- old `_internal\docs` and `_internal\requirements.txt`.

These are proven immutable/rebuildable runtime paths. The deletion list never
targets `_internal\database`, `license`, uploads, settings, themes, print
templates, user documents, prints, reports, archives or backups.

The real broken 1.7.7 installation was used as the upgrade fixture. After 1.7.8
all stale-path checks were false, while database SHA-256 remained
`B294CE95487DD31CB22C3B842AD522267DFD8DEFA0EE6F909E36C4B4C6CEDDA4`
across installation and the licence hash was unchanged. Normal application
startup subsequently updated routine licence-check timestamps as designed.

## Release 1.7.7 - superseded for upgrades 2026-07-12

- Artifact: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 43,193,577 bytes (8,680,229 bytes / 16.73% smaller than 1.7.6)
- SHA-256: `E4ADC9CCCF76E2E1C38ACD042F42C6C9FF44A20329DC5E353A3EA8B83A6EE54C`
- Frozen executable: 9,839,737 bytes, SHA-256
  `FC98A4E26C206D1D70AA1EB80F81751E1DA8902F091667E21C5E41FF280A42BF`
- Build: PyInstaller 6.21.0 / Python 3.13.7 / Inno Setup 6.7.3
- Product metadata: PRM Billing Inventory 1.7.7, PRM Software Solutions;
  PRM setup/uninstall/application icon.
- Historical result: clean install and an upgrade over the same optimized
  payload passed. The later real 1.7.6-to-1.7.7 upgrade exposed stale omitted
  packages and failed before startup. Do not distribute 1.7.7 for upgrades;
  use 1.7.8.

### Per-client licence selection

- The Browse page accepts any valid export whose filename ends in `.prmlic`.
  Certification used `sairam.prmlic` for clean install and `lakshmi.prmlic` for
  upgrade, proving setup is not bound to the repository's `client.prmlic`.
- Setup validates the selected content and copies it to
  `<app>\license\client.prmlic` as the stable internal runtime path.
- The packaged payload contains no private `.prmlic`; each client installation
  receives its own file exported from PRM Client Management.

### Payload and preservation

- Runtime documentation, tests, audit output, backups, logs, uploads,
  PowerShell files, `numpy` and `lxml` are excluded. Assets, themes, print
  templates, the public verification key and the sanitized database seed remain.
- The clean seed contains zero licence, activation, user or transaction rows and
  passes SQLite integrity checks.
- Reinstall uses `onlyifdoesntexist` for the mutable database. The certified
  test preserved database, licence, uploaded client logo, print settings and
  user settings. Uninstall removed binaries/shortcut while retaining those
  client-owned files.
- The real local installation under `%LOCALAPPDATA%\Programs\PRM Billing
  Inventory` was upgraded to the certified executable; its existing database
  and licence hashes remained byte-identical.
- The repository's PowerShell scripts are build-time helpers only. No
  PowerShell file or runtime dependency is installed.
- Authenticode remains the only external distribution limitation: no commercial
  signing certificate was supplied.

## Release 1.7.6 - certified 2026-07-12

- Artifact: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 51,873,806 bytes
- SHA-256: `E769D2216540AE04632ACA0E419D013A3D1020C67DD5ED12B865BDDF985FA8E7`
- Build: PyInstaller 6.21.0 / Python 3.13.7 / Inno Setup 6.7.3
- Result: clean install, frozen startup, authenticated installed-resource UI
  smoke, byte-identical upgrade preservation and uninstall preservation passed.

## Runtime assumptions
- The desktop runtime is a Python + PyQt6 application backed by SQLite.
- The runtime resolves its database, license file, backup directory, archive directory, print templates, and logs from the installed application context.
- No XAMPP, SQLite, web server, offscreen Qt, or test-harness dependency is required in production runtime.

## Installation layout
- Application root: `%LOCALAPPDATA%\Programs\PRM Billing Inventory`
- Database: `<app_root>\_internal\database\prm_billing_inventory.db`
- License file: `<app_root>\license\client.prmlic` or an explicit `PRM_CLIENT_LICENSE_FILE` override
- Backups: `<app_root>\backups`
- Archive: `<app_root>\documents\archive`
- Logs: `<app_root>\logs`

## License-safe packaging
- Version 1.7.6 requires a valid client `.prmlic` in interactive and silent
  installs. The Browse page accepts **any valid filename ending in `.prmlic`**,
  including per-client names such as `lakshmi.prmlic` and `sairam.prmlic`.
  Validation is based on the extension and signed/exported license content, not
  on one hard-coded basename. Setup copies the selected file internally to
  `<app_root>\license\client.prmlic` so the runtime uses one stable path.
- The build creates a separate sanitized SQLite seed. It contains application
  templates/reference rows but no activation, client license, user, customer,
  supplier, item, transaction, ledger, GST, setting, or communication-log rows.
- First startup validates the selected `.prmlic` and binds the new database to
  the target machine through the existing `LicenseService` checks.
- Upgrade/reinstall packaging excludes the mutable database from the general
  application payload. The seed uses `onlyifdoesntexist` and
  `uninsneveruninstall`, so an existing client database is neither overwritten
  nor removed by the application file refresh.
- Runtime/client upload files are not included in the desktop build.
- An upgrade refreshes application binaries/resources while preserving the
  existing database, license, settings, templates, configuration and user data.

## Certification status
- Installer seed integrity/privacy tests and license activation/machine-binding
  regressions are part of the automated suite.
- Runtime paths now resolve from the installed application context instead of developer-specific hardcoded locations.
- Release 1.7.6 is built with PyInstaller 6.21.0 and Inno Setup 6.7.3. Certification
  separates the actual frozen-executable startup check from an authenticated
  source-harness UI check using a disposable copy of the installed database plus
  the installed license and resources. The latter covers Product Master
  multi-pack save/reload, sales and purchase Grand Total visibility, both themes
  and SQLite integrity without modifying a client database. Silent uninstall
  then verifies database/license preservation.
- Test and audit folders, logs, backups, and private development licenses are
  excluded from the client payload. The complete evidence is recorded in
  `audit/installer_release_certification.md`.
- The installed runtime contains no `.ps1` files and does not launch or depend
  on PowerShell. The repository's `.ps1` files are developer-only build helpers
  and are not shipped as runtime dependencies.
- The certified 1.7.6 setup and desktop executable are not Authenticode-signed
  because no commercial code-signing certificate was supplied. Functional
  certification is complete; sign the binaries before public distribution when
  a trusted Windows publisher identity is required.
