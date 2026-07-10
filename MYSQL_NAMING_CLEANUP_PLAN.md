# MySQL Naming Cleanup Plan

## Current state
- The runtime data source implementation in services/mysql_source.py is SQLite-based.
- The module uses sqlite3 directly, resolves a SQLite database path, creates/ensures SQLite schema, and reads from a local database file under the project database folder.
- The class name MySqlSource is historical and misleading, but it is still used as the application-facing data-source entry point.
- The project does not currently use MySQL client libraries in production runtime code.
- SQLAlchemy is present and is used in database/connection.py for SQLite-backed database access rather than MySQL.

## Audit findings
- SQLite only: Yes.
- Real MySQL dependency in runtime code: No.
- MySQL packages in requirements.txt: No.
- Production runtime imports of pymysql/mysql.connector/MySQLdb: None found in the runtime codebase.
- Compatibility module status: services/mysql_source.py can remain as a compatibility module for now.

## Risk of renaming
- Renaming the module or class now would be a broad, cross-cutting change because many services, views, and tests import MySqlSource directly.
- The risk is moderate to high for a maintenance release because it can create import churn, regressions, and needless noise without functional benefit.
- The current runtime behavior is already stable, so there is no urgent need to rename it during the current release window.

## Safe phased migration plan
1. Keep the current runtime unchanged for now.
2. Treat services/mysql_source.py as the compatibility entry point.
3. Document the intent that the project is SQLite-first and desktop-local.
4. In a future release, introduce a clearer runtime module name such as sqlite_source.py or data_source.py.
5. Make the old module a thin compatibility wrapper that re-exports the new implementation.
6. Update imports gradually and only after regression tests are green.
7. Remove the compatibility layer only in a later major cleanup phase.

## Compatibility wrapper approach
- Preserve the existing public import surface during the transition.
- Keep the current file and class names available so existing code and tests continue to work.
- Introduce a new canonical module in a later step, then route the old module to it rather than changing every importer immediately.
- This reduces churn and makes the rename low-risk.

## Files that would need change later
- services/mysql_source.py
- All modules that import MySqlSource, including services/*.py and views/*.py
- Test files that reference MySqlSource directly
- Any documentation that explains the old name as the primary runtime abstraction

## Tests required before and after
Before any future change:
- Run the full suite to confirm the current baseline.
- Keep the existing regression coverage for sales bill add-item, document/module UI, and backup/transaction flows.

After any future compatibility or rename change:
- Re-run the full suite.
- Verify import smoke tests for the affected services and views.
- Confirm no UI or runtime regression appears in the desktop flow.

## Recommendation
- Defer the rename until the next release.
- Keep services/mysql_source.py in place as a compatibility module for now.
- Focus future cleanup on documentation and a staged migration rather than a risky global rename.
