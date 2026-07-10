# Developer Dashboard Rules

1. Access Control
- Developer Dashboard access must be controlled exclusively by developer `.prmlic` credentials (developer license context). Normal users must not be able to access developer features.
- The UI entry for Developer Dashboard must only be visible when `LicenseService` returns a developer license context.
- Attempted access without a developer license must show an explicit denial dialog and record the attempt in an audit table `developer_login_attempts`.

2. Authentication and Logging
- Successful developer login is granted only when a valid developer `.prmlic` is present and validated by `LicenseService.require_license()`.
- Failed attempts (missing/invalid developer .prmlic or invalid passphrase) must be logged with timestamp, attempted identity, machine id (if available), and reason.

3. Developer vs Normal Users
- Normal users must never see Developer Dashboard menu items or developer-only controls.
- Developer-only settings must not be stored in a separate company table; use permission gating on the shared `company` table.

4. Audit Table Suggestion
- Create `developer_login_attempts` table with columns: id, username, attempted_at, machine_fingerprint, ip (null for desktop), success (0/1), reason.
