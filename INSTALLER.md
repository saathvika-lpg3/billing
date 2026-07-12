# Installer Runtime Certification

## Release 1.7.7 - certified 2026-07-12

- Artifact: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 43,193,577 bytes (8,680,229 bytes / 16.73% smaller than 1.7.6)
- SHA-256: `E4ADC9CCCF76E2E1C38ACD042F42C6C9FF44A20329DC5E353A3EA8B83A6EE54C`
- Frozen executable: 9,839,737 bytes, SHA-256
  `FC98A4E26C206D1D70AA1EB80F81751E1DA8902F091667E21C5E41FF280A42BF`
- Build: PyInstaller 6.21.0 / Python 3.13.7 / Inno Setup 6.7.3
- Product metadata: PRM Billing Inventory 1.7.7, PRM Software Solutions;
  PRM setup/uninstall/application icon.
- Result: clean install, real frozen startup, authenticated installed-resource
  UI smoke, byte-identical upgrade preservation, preserving uninstall and real
  local upgrade all passed.

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
