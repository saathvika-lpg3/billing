# Security Standard for PRM_GST_DESKTOP

## 1. Security purpose
This document defines the security specification for PRM_GST_DESKTOP in its current Python + PyQt6 + SQLite desktop form.

The purpose is to protect business data, license integrity, customer records, print/export outputs, and installer/update workflows while preserving the existing desktop-only architecture and .prmlic licensing model.

Locked project rules:
- Python + PyQt6 + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve existing .prmlic licensing
- Preserve existing valid customer data during updates
- Keep all security measures additive and backward-compatible

## 2. Local desktop threat model
The primary threat model is local desktop usage with possible risks such as:
- copying the SQLite database file
- unauthorized local access to the application folder
- reinstalling or moving the application to another machine
- using an old or copied backup without authorization
- tampering with installer or update files
- unauthorized user access from a shared workstation
- export or print leakage of sensitive business data

The application must assume that the local machine may be accessible to an authorized but untrusted operator, a copied deployment, or a stolen device.

## 3. SQLite database protection
The SQLite database is a core asset and must be protected against direct misuse.

Required rules:
- The database must not be usable simply by copying the file and opening it outside the authorized application context.
- Database access must be protected using encryption or an application-level encryption strategy.
- Encryption must be implemented without storing the master key directly in plain text inside the project source.
- The application should validate access using the current .prmlic context and/or machine identity where feasible.
- Database access should be denied or fail closed if the application cannot validate the expected protected context.

## 4. Protection if database file is copied
If someone copies the SQLite database file, they should not be able to open or use it directly.

Required behavior:
- The copied database must be unreadable or unusable without the correct application context.
- A copied database should not be opened by a generic SQLite tool or by a simple local file access path.
- The application should use encrypted storage or an equivalent secure application-layer protection strategy.
- Any copied database should be treated as an unauthorized access attempt unless the correct runtime context is present.

Implementation expectation:
- Encryption or app-level protection must be part of the data-access layer.
- The encryption design must not rely on plain-text keys embedded in the repository.
- Key handling must use a protected local mechanism such as machine-bound storage, OS-protected storage, or a derived key tied to license and device identity where feasible.

## 5. .prmlic license binding
The existing .prmlic licensing model remains the primary trust boundary for authorized use.

Required rules:
- Database access and protected application workflows must remain linked to valid .prmlic state.
- Invalid or missing licenses must block protected operations.
- The security model must not allow a copied database to operate with a simple license bypass.
- License validation must remain compatible with the existing desktop deployment model.

## 6. Machine/device binding
Where feasible, protected data access should be tied to machine or device identity.

Required rules:
- The application should support device-bound access patterns where practical.
- The application must not rely purely on a copied license file or copied database file for trust.
- If a device binding strategy is implemented, it must be compatible with the current desktop packaging and installer workflow.
- A device-bound strategy must not silently break valid deployments during updates.

## 7. Database encryption requirement
Database encryption is required for protecting local business data.

Required rules:
- Database content must be protected at rest.
- Encryption must be implemented in a way that is compatible with the current desktop-only architecture.
- The encryption strategy must support safe upgrades and future changes.
- Encryption keys must not be stored directly in plain text inside the project.
- Any change to the encryption approach must include a migration plan and rollback plan.

Security expectation:
- The database should remain unreadable to casual file copy or basic local inspection.
- A valid application runtime should be able to decrypt and use the database only when the correct secure context is present.

## 8. Backup encryption requirement
Backups must also be protected.

Required rules:
- Backup files must be encrypted or otherwise protected.
- A backup should not be restorable by simple file copy or casual local access.
- Backup protection must be compatible with existing backup workflows and desktop deployment.
- Backup encryption should use a protected key strategy rather than embedded plain-text secrets.

## 9. Restore validation
Restore operations must be safe and validated.

Required rules:
- Restore must not silently overwrite current customer data without confirmation.
- Restore should confirm the backup source, version compatibility, and integrity before applying changes.
- Restore must verify that the backup is valid and matches the expected application context.
- Restore must be blocked if the backup cannot be authenticated or validated.
- Any restore operation must preserve current data unless explicitly confirmed by an authorized operator.

## 10. User role security
User roles must be enforced so that only authorized users can access sensitive functions.

Required rules:
- Developer or administrator-level actions must be restricted to authorized users.
- Ordinary users must not be able to change license state, installer behavior, or core security settings.
- Access to Company Master, backup/restore, and print-policy configuration must follow role rules.
- The application must support role-based restrictions without introducing a web backend.

## 11. Developer/admin permissions
Developer and administrator access must be tightly controlled.

Required rules:
- Developer/admin actions must be limited to approved workflows.
- Sensitive operations such as license inspection, security configuration, backup/restore, and installer-related actions must require higher-level authorization.
- Developer/admin accounts must not bypass .prmlic or security protections without explicit authorized design.
- Permission changes must be logged and auditable.

## 12. Audit log protection
Audit logs are part of the security posture.

Required rules:
- Critical actions must be logged with user identity, role, timestamp, action type, and affected record where applicable.
- Audit logs must be protected from casual tampering.
- Logs must remain compatible with the local desktop architecture and SQLite storage model.
- Sensitive audit events should not be exposed in a way that leaks data to unauthorized users.

## 13. Print/export data protection
Print and export outputs may contain business-sensitive information and must be protected.

Required rules:
- Printed or exported data should not expose hidden or unauthorized record content.
- Print/export workflows must respect role-based access and customer data visibility.
- Sensitive print fields such as GSTIN, HSN, FSSAI, and customer details must be handled carefully.
- Loading Sheet / Dispatch Summary must show GSTIN, HSN, and FSSAI if available and hide missing fields gracefully.
- Output files should not contain unnecessary sensitive information beyond the intended business document.

## 14. Installer/update security
Installer and update workflows must preserve data and integrity.

Required rules:
- Updates must not break existing customer data.
- Installer and update actions must validate integrity before applying changes.
- Update logic must preserve current database, backups, and license state where feasible.
- Any security-related change must include a safe migration and rollback plan.
- No destructive changes should occur without backup and confirmation.

## 15. Uninstall safety
Uninstall actions must be safe and predictable.

Required rules:
- Uninstall should not silently delete valid customer data unless explicitly intended by a confirmed workflow.
- If uninstall includes data removal, the action must require confirmation and should preserve backups when possible.
- The uninstall flow must not corrupt the existing database or license state.

## 16. Password policy
The desktop application should use a simple but safe access model for local user accounts where applicable.

Required rules:
- Passwords, if used, should be stored using a strong salted hash strategy.
- Passwords must not be stored in plain text.
- Default or weak passwords must be avoided.
- Local login should not be the only protection if database encryption and .prmlic binding are available.
- Password policy should remain practical for desktop users and not block normal business use.

## 17. Sensitive data handling
Sensitive data such as customer details, financial summaries, GST information, and license-related data must be handled carefully.

Required rules:
- Sensitive data should be available only to authorized roles and workflows.
- Sensitive fields should not be exposed unnecessarily in logs, exports, or UI messages.
- Local file access to sensitive data must remain protected by the application context.
- Any temporary working files should be removed safely after use where appropriate.

## 18. Error/log safety
Error and log handling must not leak sensitive data.

Required rules:
- Error messages should avoid exposing raw database contents, encryption details, or license secrets.
- Logs should contain enough operational context for debugging without revealing sensitive business values.
- Log files should be stored safely and not be easily exposed to unauthorized users.
- The application should handle failures gracefully without exposing internal security state.

## 19. Testing checklist
- Verify that a copied SQLite database cannot be used directly without the protected application context.
- Verify that database encryption or app-level protection is active for local data storage.
- Verify that backup files are protected and not easily usable without the correct context.
- Verify that restore operations require validation and confirmation.
- Verify that .prmlic validation remains intact.
- Verify that role-based access blocks unauthorized users from sensitive actions.
- Verify that audit logs capture critical security-related actions.
- Verify that print/export output respects role and data visibility requirements.
- Verify that updates preserve existing customer data and do not break the database.
- Verify that uninstall actions are safe and do not silently destroy data.
- Verify that error and log handling does not expose sensitive information.

## 20. Future roadmap
- Implement a stronger encrypted local database strategy with safe migration support.
- Add more granular role-based access for sensitive modules and reports.
- Improve backup integrity verification and restore authentication.
- Add stronger machine/device binding where feasible without breaking supported desktop deployments.
- Improve log protection and restricted error reporting.
- Keep all future security work aligned with the current Python + PyQt6 + SQLite desktop architecture and .prmlic licensing model.
