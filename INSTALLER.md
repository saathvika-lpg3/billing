# Installer Runtime Certification

## Runtime assumptions
- The desktop runtime is a Python + PyQt6 application backed by SQLite.
- The runtime resolves its database, license file, backup directory, archive directory, print templates, and logs from the installed application context.
- No XAMPP, SQLite, web server, offscreen Qt, or test-harness dependency is required in production runtime.

## Installation layout
- Application root: `%LOCALAPPDATA%\Programs\PRM Billing Inventory`
- Database: `<app_root>\_internal\database\prm_billing_inventory.db`
- License file: <app_root>\license\client.prmlic or an explicit PRM_CLIENT_LICENSE_FILE override
- Backups: <app_root>\backups
- Archive: <app_root>\documents\archive
- Logs: <app_root>\logs

## License-safe packaging
- Version 1.7.4 requires the client `.prmlic` in interactive and silent installs.
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
