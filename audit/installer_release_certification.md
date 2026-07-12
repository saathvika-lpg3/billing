# Installer Release Certification

## Official PRM BILLING INVENTORY V1.0 - 2026-07-12

**PASSED** - official production baseline. Active runtime, Windows executable
and setup metadata use technical version `1.0.0`; compact user-facing branding
uses `V1.0`. Historical internal 1.7.x identifiers remain compatibility and
upgrade evidence only.

### Certified artifacts

- Setup: `installer_output/PRM_Billing_Inventory_V1.0_Setup.exe`
- Setup size/SHA-256: 43,187,187 bytes / `04505DBEC75642B6345D547F4FC1536E3D901AE79DA3F6A0D0E2CAEF7CFBA584`
- Frozen executable size/SHA-256: 9,842,776 bytes / `0C521954DE709E1B1FA6CE5EBBD25CBBE9E9188F63D883ECEE9F8429F7748550`
- Sanitized seed size/SHA-256: 933,888 bytes / `E5EB868871F1F8AC120F8BF56CAD03AF3AB4D3D1505302D581FEE1B6AAB332CC`
- Payload: 238 files / 132,500,207 bytes; forbidden-content findings: zero.
- Authenticode: not signed because no organization certificate was supplied.

### Certification results

- Complete regression: 226 passed in 212.30 seconds; compile gate passed.
- Live all-route audit: 59/59 at 1366x768, 1440x900 and 1920x1080.
- Isolated clean install and exact responsive V1.0 login title: passed.
- Authenticated installed-resource smoke on a disposable database: passed.
- Preserving uninstall: database, licence, settings and uploads byte-identical;
  executable, uninstaller and Start Menu shortcut removed.
- Real local in-place upgrade: installed executable matched the certified hash;
  existing client database and licence were byte-identical across setup.
- Final real installed process reached the responsive
  `PRM BILLING INVENTORY V1.0 Login` window without a script-error dialog.

`RELEASE_LOCK.md` and `release_validation/2026-07-12_v1.0/` hold the permanent
behavior contract and safe evidence. The annotated `v1.0.0` tag identifies the
immutable release commit; the H-drive distribution copy carries its own
post-tag file/hash verification manifest.

## Installer 1.7.8 - 2026-07-12

**PASSED** - current certified, upgrade-safe release. The setup was rebuilt with
an explicit correction for obsolete runtime packages left by earlier installed
versions, applied over the reproduced affected installation, launched as the
actual frozen executable, and exercised with authenticated installed resources.

### Certified artifact and payload

- Setup: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 43,187,727 bytes
- SHA-256: `0C57293DECCC94ED6FDE2CD6177DBA3D6DB55DFF638A02B98CA2C1D5B5E6B1A2`
- Frozen executable SHA-256:
  `F721794BDED7023C84C6667C3707BE288BC9494BDC5F19338F86F140061EE1FB`
- Sanitized seed SHA-256:
  `E5EB868871F1F8AC120F8BF56CAD03AF3AB4D3D1505302D581FEE1B6AAB332CC`
- Setup version metadata: PRM Billing Inventory 1.7.8 / PRM Software Solutions.
- Authenticode: unsigned because no organization certificate was supplied.

### Corrective upgrade behavior

- A real upgrade from an older payload exposed that Inno Setup does not remove
  files merely because they are omitted from a newer payload. Stale `numpy`,
  `numpy.libs`, `numpy-*.dist-info`, `lxml`, `lxml-*.dist-info`, packaged `docs`
  and `requirements.txt` paths therefore survived the 1.7.7 installation.
- The stale, incomplete NumPy package was imported by `openpyxl` during startup
  and raised `AttributeError: module 'numpy' has no attribute 'short'` before
  the login window could open.
- Installer 1.7.8 adds a narrowly scoped Inno Setup `[InstallDelete]` section
  for only those immutable, rebuildable runtime paths. It does not target the
  client database, licence, uploads, user settings or other mutable client data.
- The corrected setup was applied over the actual reproduced broken 1.7.7
  installation. All targeted stale paths were absent afterward, while the
  database and client licence remained byte-identical across the installer run.

### Startup and installed smoke

- The corrected installed executable opened `PRM BILLING INVENTORY Login`,
  remained alive and responsive, and produced empty standard error. Startup
  logging confirmed PRM icon loading, valid licence, successful database
  initialization and LoginDialog creation.
- Authenticated installed-resource smoke passed SQLite integrity, administrator
  authentication, two-pack Product Master save/reload, Sales and Purchase Grand
  Totals, horizontal list actions, PRM-only top branding, client Dashboard logo,
  canonical Dispatch Summary, and light/dark themes.
- The installed-resource smoke used a disposable database copy; the installed
  database remained unchanged during that exercise.

### Supporting gates

- Focused installer packaging regression: 7 passed.
- Corrected real-install startup diagnostic: passed with no traceback or script
  error dialog.
- Installed-resource functional and branding smoke: passed.

## Installer 1.7.7 - 2026-07-12 (superseded for upgrades)

**SUPERSEDED FOR UPGRADES** - its optimized payload, clean installation,
branding/navigation, data-preservation and test-harness gates passed, but the
upgrade model did not account for obsolete files retained from larger earlier
payloads. A subsequent real installed launch exposed stale `numpy`/`lxml`
runtime residue. Installer 1.7.8 is the corrected and certified replacement.

### Certified artifact and payload

- Setup: `installer_output/PRM_Billing_Inventory_Setup.exe`
- Size: 43,193,577 bytes
- SHA-256: `E4ADC9CCCF76E2E1C38ACD042F42C6C9FF44A20329DC5E353A3EA8B83A6EE54C`
- Frozen executable: 9,839,737 bytes; SHA-256
  `FC98A4E26C206D1D70AA1EB80F81751E1DA8902F091667E21C5E41FF280A42BF`
- Sanitized seed: 933,888 bytes; SHA-256
  `848DB97732B44CBDEB08066AEF28FE78A0C28E0BF50E8420ADF860B1BB08134B`
- Builder: PyInstaller 6.21.0, Python 3.13.7, Inno Setup 6.7.3.
- Setup version metadata: PRM Billing Inventory 1.7.7 / PRM Software Solutions.
- Runtime payload: 132,497,168 bytes / 238 files before Inno compression.
- Privacy scan: zero private `.prmlic`, `.ps1`, log, upload, test, audit or
  backup files; no `numpy` or `lxml` package directory.
- Authenticode: unsigned because no organization certificate was supplied.

### Clean install, startup and installed smoke

- Silent clean installation with source basename `sairam.prmlic`: passed.
  Executable, sanitized database, normalized installed licence, PRM assets,
  themes, shortcut and uninstaller were present.
- Actual frozen process remained alive/responding at licensed login. Startup
  logging confirmed PRM `.ico` loading, valid licence, database initialization
  and LoginDialog creation without traceback/import/resource failure.
- Authenticated installed-resource smoke: SQLite `ok`; Product Master saved and
  reloaded one two-pack synthetic product in a disposable database; Sales and
  Purchase Grand Totals were visible; Sales toolbar was horizontal; light/dark
  themes loaded; PRM header/logo loaded with no client identity in the top bar;
  Dashboard client logo area was 144x96; canonical Dispatch Summary opened.
- Installed database stayed byte-identical during the disposable-copy smoke.

### Historical upgrade evidence and later correction

- Upgrade with source basename `lakshmi.prmlic`: passed.
- That upgrade began from a clean optimized installation, so it proved licence
  replacement and mutable-data preservation but did not model omitted runtime
  files surviving from the larger 1.7.6 payload.
- Test database SHA-256 remained byte-identical at
  `89A8863137F3EE714B5B651AB34777221796746BC89EF48B5D6EDAE28AAB1100`.
  Installed licence and client-logo hashes remained unchanged; print/user
  marker settings remained present.
- Silent uninstall removed executable, uninstaller and Start Menu shortcut while
  preserving database, licence, upload and user-settings marker.
- Real local upgrade installed the same frozen SHA-256 and its existing database
  stayed byte-identical at
  `B294CE95487DD31CB22C3B842AD522267DFD8DEFA0EE6F909E36C4B4C6CEDDA4`;
  licence SHA-256 remained
  `CDC7C6BC5A136DD473E6F9C7C17E4B0A8E4CD21201F7B92E00A8255268A3C1F6`.
- Those preservation checks did not establish a healthy post-upgrade startup.
  The later launch reproduced the stale NumPy import failure documented in the
  1.7.8 certification above.

### Supporting gates

- Full source suite: 220 passed in 369.44 seconds.
- Focused branding/navigation/installer/print parity: 44 passed.
- Post-build packaging/branding/navigation: 14 passed.
- New live-database isolation gate: 7 passed with identical before/after hash.
- Live UI audit: 59/59 routes passed at 1366x768, 1440x900 and 1920x1080.
- Visual evidence: PRM header, client Dashboard card, Company Profile, Dispatch
  Summary, client-branded Sales Invoice and Profit & Loss with PRM footer.

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
