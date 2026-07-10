# SQLite Database Rules

## Database platform rules
- This release uses SQLite as the primary database.
- Do not switch to SQLite for this release.
- Keep the database local to the desktop installation and project runtime context.
- Production runtime resolves the database, license files, backups, archive folders, and logs from the installed application runtime rather than developer-specific paths.

## Safe database guidelines
- Preserve existing SQLite tables, columns, and data where possible.
- Avoid destructive schema changes without a clear migration plan.
- Prefer additive changes and backward-compatible updates.
- Ensure new features do not break existing local database files.

## Data integrity expectations
- Master data, transaction data, inventory data, and accounting data should remain consistent.
- Printing and licensing features must continue to function with existing SQLite-backed records.
- Any future database work should preserve valid existing data and support current desktop workflows.

## Practical guidance
- Keep SQLite as the source of truth for this release.
- Do not assume SQLite compatibility or SQLite migration as part of this release scope.
- If schema changes are needed, keep them minimal and carefully documented.
- The desktop data source class previously named SQLiteSource remains a SQLite-only compatibility wrapper for runtime use and is not a SQLite connector.
- Add Item reads product options from the local SQLite tables items, suppliers, and product_packs through this wrapper.
