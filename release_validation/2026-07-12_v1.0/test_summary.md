# PRM BILLING INVENTORY V1.0 Test Summary

Release date: 2026-07-12
Technical/display version: `1.0.0` / `V1.0`

## Passed gates

- Python compile/import gate: passed.
- Complete pytest suite: **226 passed in 212.30 seconds**.
- Live UI route/layout audit: **59/59 routes passed** at 1366x768,
  1440x900 and 1920x1080.
- Frozen payload privacy: 238 files / 132,500,207 bytes; zero private
  licence, PowerShell, log, upload, test, audit, backup, NumPy or lxml findings.
- Isolated clean install: passed with a separately named synthetic `.prmlic`.
- Actual frozen login: responsive with exact title
  `PRM BILLING INVENTORY V1.0 Login`.
- Authenticated installed UI/resource smoke: passed on a disposable database
  copy; the installed seed stayed unchanged.
- Preserving uninstall: database, licence, settings and upload markers stayed
  byte-identical; executable, uninstaller and shortcut were removed.
- Real local upgrade: passed; database and licence stayed byte-identical, and
  the installed executable matched the certified frozen build.
- Final installed application: open and responsive at the V1.0 login for
  manual operator acceptance.

## External acceptance gates

- Organization Authenticode certificate/signing.
- Physical printer output on target printer/driver combinations.
- Live SMTP credentials, logged-in WhatsApp session and government GST
  credentials/endpoints.

These external items do not change the code-controlled pass result and must not
be represented as completed until the corresponding production services or
hardware are supplied.
