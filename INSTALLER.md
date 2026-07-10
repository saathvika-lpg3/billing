# Installer Runtime Certification

## Runtime assumptions
- The desktop runtime is a Python + PyQt6 application backed by SQLite.
- The runtime resolves its database, license file, backup directory, archive directory, print templates, and logs from the installed application context.
- No XAMPP, SQLite, web server, offscreen Qt, or test-harness dependency is required in production runtime.

## Installation layout
- Application root: C:\Program Files\PRM Billing and Inventory
- Database: <app_root>\database\prm_billing_inventory.db
- License file: <app_root>\license\client.prmlic or an explicit PRM_CLIENT_LICENSE_FILE override
- Backups: <app_root>\backups
- Archive: <app_root>\documents\archive
- Logs: <app_root>\logs

## Certification status
- Verified by the full pytest suite: 117 passed in 63.57s.
- Runtime paths now resolve from the installed application context instead of developer-specific hardcoded locations.
