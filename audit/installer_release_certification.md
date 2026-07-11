# Installer Release Certification

## Installer 1.7.6 - 2026-07-12

**PASSED** - the release was rebuilt from current source, installed, launched,
exercised, upgraded with a differently named valid client license, and
uninstalled without bypassing license validation or authentication.

### Certified artifact

- File: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 51,873,806 bytes
- SHA-256: `E769D2216540AE04632ACA0E419D013A3D1020C67DD5ED12B865BDDF985FA8E7`
- Build timestamp: 2026-07-12 01:13:02.094 local time
- Builder: PyInstaller 6.21.0, Python 3.13.7 and Inno Setup 6.7.3
- Frozen desktop SHA-256:
  `A8736A8DF144775370E5019DF865454DBAA1C4C0D6EABA22BEC48EB8CB897E81`
- Authenticode: not signed; no commercial certificate was supplied

### Build and privacy checks

- Sanitized seed integrity returned `ok` with zero license, activation, user or
  transaction rows. Reference masters/templates were retained.
- Client payload contains zero `.prmlic` files and zero `.ps1` files.
- Application source contains zero PowerShell/`.ps1` runtime references.
- Audit/test output, logs, backups and private development/client licenses are
  excluded from the client payload.

### Installation, license and UI checks

- Clean silent install exit code: 0; executable, sanitized database, installed
  license, both themes and uninstaller were present.
- Actual frozen executable remained healthy after 12 seconds at login and its
  startup log contained zero traceback/critical/unhandled/failure markers.
- Authenticated installed-resource smoke opened Product Master, Sales Bill,
  Purchase Entry, Sales and Reports; saved and reloaded one synthetic product
  with two packs in a disposable database; verified both Grand Totals,
  horizontal list actions and light/dark themes; SQLite integrity returned
  `ok`; the installed database stayed byte-identical.
- Upgrade used the valid source basename `lakshmi.prmlic`, proving setup is not
  bound to `client.prmlic` or any one client filename. Setup validates the
  `.prmlic` content/extension and copies it to
  `<app>\license\client.prmlic`.
- Upgrade exit code: 0. The activated database SHA-256 remained byte-identical:
  `FBA4518F35F32AA134566ECE1929413DF0D4E4586476A67FDE45837C12B8CEC1`.
- Uninstall exit code: 0; binaries were removed while the client database and
  license were preserved byte-identically. Preserved database integrity was
  `ok` with one activation and one administrator row.

### Supporting gates

- Installer/license regression: 7 passed.
- Final full native suite: 213 passed in 183.75 seconds.
- Live UI audit: 59/59 routes passed at 1366x768, 1440x900 and 1920x1080.
- Typed widget audit: 35 files, zero unsafe calls.
- Performance smoke: 8/8 scenarios passed.

## Historical Installer 1.7.5 Release Certification

Date: 2026-07-11
Application: PRM Billing Inventory
Release: 1.7.5

## Result

**PASSED** - the installer was built, installed, launched, exercised, and
uninstalled without bypassing license validation or authentication. Frozen and
source-harness checks are identified separately below.

## Certified artifact

- File: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 51,836,487 bytes
- SHA-256: `C54E99B4B714E20D5D7DE2958415ED6FEDA35D9E39D2C694B927F965AF41BFFA`
- Builder: PyInstaller plus Inno Setup 6.7.3
- Build timestamp: 2026-07-11 18:30:07.931 local time
- Authenticode: not signed; no commercial certificate was supplied

## Build and privacy checks

- The sanitized SQLite seed returned `PRAGMA integrity_check = ok`.
- The seed contained zero licenses, activations, users, customers, suppliers,
  items, transactions, ledgers, GST rows, settings, and communication logs.
- The packaged payload excluded audit output, runtime logs, backups, and private
  development license files.
- Themes, application documentation, assets, and the 139 database-backed print
  templates were present through the supported runtime sources.

## Installed-runtime smoke checks

- Silent installer exit code: 0.
- Installed executable, database, selected client license, and both themes were
  present.
- The actual frozen executable stayed alive at the login screen and wrote only
  success startup markers during the observation window. Its log contained no
  full client license key.
- The installed-resource UI harness uses the current source UI modules with a
  disposable copy of the installed database plus the installed license, themes
  and paths; it neither changes a client database nor represents direct
  automation of widgets embedded inside the frozen executable.
- Normal `LicenseService` validation and administrator authentication passed in
  that harness; no activation or authentication bypass was used.
- Product Master opened, created and explicitly reloaded a synthetic QA product
  with two package rows.
- Sales Bill, Purchase Entry, Sales, Reports, and the shared module hub opened.
- Sales and purchase Grand Total panels were visible and the primary action bar
  was horizontal.
- Dark and light themes loaded successfully.
- Disposable-copy SQLite integrity returned `ok`; the installed database hash
  remained byte-for-byte unchanged during the UI harness.
- Reinstall over the activated test path returned exit code 0 and preserved the
  database SHA-256 byte-for-byte.

## Uninstall and data preservation

- Silent uninstaller exit code: 0.
- Application binaries were removed.
- The mutable database and client license were preserved.
- The preserved installed database returned `PRAGMA integrity_check = ok` with
  one activation row and one user in a final read-only verification. Synthetic
  product/package rows existed only in the disposable smoke copy.

## Supporting release gates

- Full automated suite: 190 passed in 182.32 seconds.
- UI stabilization suite: 8 passed in 10.02 seconds.
- Five-size page-fit gate: passed at 1366x768, 1440x900, 1920x1080,
  1093x614, and 911x512.
- Live UI inventory: 59/59 routes with no detected issues.
- Widget API audit: 33 UI files, zero findings.
- Performance smoke: 8/8 scenarios passed.

## External distribution consideration

The setup and desktop executable are functionally certified but are not
Authenticode-signed because no commercial certificate was supplied. This is not
a code-controlled defect; apply organization-owned signing before public
distribution if Windows publisher trust is required.
