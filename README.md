# PRM Billing Inventory Desktop

This project is the Python desktop ERP for PRM Billing Inventory.
It runs from its own application folder with a local SQLite database, without
requiring XAMPP on client machines.

Official product release: **PRM BILLING INVENTORY V1.0** (technical version
`1.0.0`). The release contract is [`RELEASE_LOCK.md`](RELEASE_LOCK.md). The
installer uses fixed PRM product branding and accepts a separately exported
`.prmlic` file for each client through its Browse page.

Official Windows setup: `installer_output/PRM_Billing_Inventory_V1.0_Setup.exe`.
The setup stores the selected client file internally as `license/client.prmlic`;
it is not bound to a particular exported filename or client.

## Target

- Python desktop ERP application
- PyQt6 UI
- SQLAlchemy data layer
- SQLite / SQLCipher local database
- Modern desktop ERP layout, not a visual copy of the web portal
- Data import and verification tools for existing PRM business data

## Verification

1. Verify menu and database parity.
2. Verify local desktop data and backup flow.
3. Verify operator screens, reports, print templates and installer output.

## Git Status

- Official origin: `https://github.com/saathvika-lpg3/billing.git`
- Active release branch: `business-flow-audit-20260710`.
- Do not commit local databases, `.prmlic` files, uploads, generated PDFs,
  screenshots, logs, backups, sessions/cookies, SMTP/WhatsApp secrets or build
  output.
