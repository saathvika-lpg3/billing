# Installer Runtime Certification

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
- Version 1.7.5 requires the client `.prmlic` in interactive and silent installs.
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

## Certification status
- Installer seed integrity/privacy tests and license activation/machine-binding
  regressions are part of the automated suite.
- Runtime paths now resolve from the installed application context instead of developer-specific hardcoded locations.
- Release 1.7.5 is built with PyInstaller and Inno Setup 6.7.3. Certification
  separates the actual frozen-executable startup check from an authenticated
  source-harness UI check using a disposable copy of the installed database plus
  the installed license and resources. The latter covers Product Master
  multi-pack save/reload, sales and purchase Grand Total visibility, both themes
  and SQLite integrity without modifying a client database. Silent uninstall
  then verifies database/license preservation.
- Test and audit folders, logs, backups, and private development licenses are
  excluded from the client payload. The complete evidence is recorded in
  `audit/installer_release_certification.md`.
- The certified 1.7.5 setup and desktop executable are not Authenticode-signed
  because no commercial code-signing certificate was supplied. Functional
  certification is complete; sign the binaries before public distribution when
  a trusted Windows publisher identity is required.
