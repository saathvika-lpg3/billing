# PRM_GST_DESKTOP Development Principles

## 1. Purpose
This document defines the permanent development principles for PRM_GST_DESKTOP.

These principles are binding for future implementation, refactoring, feature work, testing, documentation, and release preparation. They are meant to protect customer data, preserve desktop stability, and keep the product consistent with its current architecture and business model.

Locked project rules:
- Python + PyQt6 + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve existing .prmlic licensing
- Preserve valid customer data during updates
- Keep all development work documentation-first and backward-compatible

## 2. Core development principles

### 2.1 Customer data is more valuable than code
Customer data is the most valuable asset in the product.

Development decisions must always prioritize:
- data safety
- data integrity
- data recoverability
- business continuity

If a change improves code elegance but risks customer data, it is not acceptable.

### 2.2 Never break existing customer installations
Every change must preserve compatibility with existing customer deployments.

This includes:
- existing database files
- existing .prmlic licenses
- existing print workflows
- existing master and transaction data
- existing installer and update scenarios

No change should assume that all customers will reinstall or reconfigure the system.

### 2.3 Always create backup before destructive changes
Before any destructive, migration, or high-risk change:
- create a backup
- verify the backup is readable
- confirm the scope of the change
- ensure rollback is possible

No destructive change should proceed without this safeguard.

### 2.4 One engine for GST
GST behavior must be implemented through a single, shared engine or service layer.

This means:
- GST logic must not be duplicated across modules
- invoice, report, and document logic must reuse the same GST core
- rules must remain consistent across billing, reporting, and print workflows

### 2.5 One engine for Printing
Printing must be implemented through one shared print engine or print service.

This means:
- document layout logic must be centralized
- A4 Portrait and A2 Landscape behavior must be consistent
- bulk print behavior must be handled centrally
- loading sheet and dispatch summary formatting must share the same base rules

### 2.6 One engine for Inventory
Inventory logic must be implemented through one shared engine.

This means:
- stock update logic must not be duplicated across sales, purchase, return, and adjustment modules
- stock movement rules must be centralized
- reports and transaction screens must rely on the same inventory logic

### 2.7 One engine for Accounts
Accounts logic must be implemented through one shared engine.

This means:
- ledger posting, balances, and account effects must be centralized
- sales, purchase, payment, receipt, and journal workflows must share the same accounts rules
- reports must reflect the same accounting logic

### 2.8 One engine for Security
Security logic must be implemented through one shared security layer.

This means:
- permissions, audit logging, role checks, and data protection must be centralized where possible
- security behavior must not be scattered across unrelated screens
- database protection and license-related enforcement must follow the same platform rules

### 2.9 One engine for Licensing
Licensing logic must be implemented through one shared licensing engine.

This means:
- .prmlic validation must stay centralized
- feature gating and license checks must not be duplicated in multiple unrelated modules
- licensing behavior must remain compatible with existing customer installations

### 2.10 Never duplicate business logic
Business logic must live in one place.

This includes:
- tax logic
- stock logic
- ledger logic
- approval logic
- print logic
- validation logic
- backup/restore safeguards

If the same logic appears in more than one module, it must be refactored into a single shared implementation.

### 2.11 Never duplicate UI
The UI should not be duplicated across similar workflows.

This means:
- repeated forms and dialogs should be standardized
- common entry patterns should be reused
- operator workflow should remain consistent across similar modules
- future changes must update shared UI patterns rather than create parallel screens

### 2.12 Keep everything configurable where possible
Configuration is preferred over hard-coding.

This includes:
- business type behavior
- print settings
- report settings
- role and permission behavior
- document defaults
- tax and item handling where appropriate

Configuration should be flexible enough for different industries without breaking the base product.

### 2.13 Every feature must support keyboard workflow
Every feature must support keyboard-first or keyboard-friendly operation.

This includes:
- quick navigation
- form entry
- search
- save and cancel
- report access
- print and export actions

Operator speed is a core requirement, not a nice-to-have.

### 2.14 Every feature must support audit logging
Every feature that changes business data or configuration must support audit logging.

Required audit information:
- user identity
- role
- timestamp
- action type
- affected module
- affected record where available

### 2.15 Every feature must support backup/restore
Every feature that changes persistent data must preserve backup and restore compatibility.

This means:
- changes must not silently break restore workflows
- migrations must be reversible where possible
- backup safety must be considered before deployment

### 2.16 Every feature must support permissions
Every feature must respect the role-based permission model.

This includes:
- view/edit/delete/cancel restrictions where appropriate
- license-sensitive restrictions
- security-sensitive workflows
- print and export restrictions where applicable

### 2.17 Every feature must be tested
Every change must be tested before release.

Testing should include:
- functional correctness
- UI behavior
- permission behavior
- print and export behavior where relevant
- backup/restore compatibility where relevant
- regression checks for existing workflows

### 2.18 Every change must update documentation
Every meaningful change must be reflected in the relevant documentation.

This includes:
- product specification documents in AI_GUIDE
- module-specific workflow documentation
- release notes where relevant
- print and security rules where affected

No feature should be considered complete without the related documentation update.

### 2.19 Every module must preserve operator speed
Every module must remain fast and usable for real business operators.

This means:
- no unnecessary delay in form entry
- no freezing UI during search or document load
- no heavy blocking operations in transaction workflows
- no design that sacrifices speed for visual complexity

### 2.20 Future AI must read AI_GUIDE before changing code
All future AI-assisted or human-assisted implementation work must start by consulting AI_GUIDE.

This is a permanent rule.

Before changing code, the implementer must review:
- the relevant product-spec documents
- the locked rules
- the architecture guidance
- the current task queue and roadmap guidance

AI-guided work must respect the documented product constitution rather than inventing new behavior.

### 2.21 If project status is unclear, do not guess
If the current project status is unclear, do NOT guess.

First scan code, docs, database, and AI_GUIDE.
Then report the actual status before changing code.

## 3. Code Review Checklist
Before approving any change, confirm the following:
- The change respects the locked product rules.
- The change does not break existing customer installations.
- The change preserves .prmlic behavior and security expectations.
- The change uses existing shared engines instead of duplicating logic.
- The change does not duplicate UI patterns unnecessarily.
- The change supports keyboard-friendly operation.
- The change includes audit logging where applicable.
- The change is compatible with backup/restore and data safety expectations.
- The change respects permissions.
- The change is documented in AI_GUIDE where relevant.
- The change includes or updates testing evidence.

## 4. Pull Request Checklist
Before submitting a pull request or change set, confirm:
- The change is scoped and clearly described.
- The change does not modify unrelated application code.
- The change is compatible with the current desktop-only architecture.
- The change has been tested in a realistic desktop workflow.
- The change preserves SQLite compatibility and customer data safety.
- Any migration or database change has a safe plan and rollback path.
- Print behavior and report behavior were checked where relevant.
- Documentation was updated.
- Permissions and auditing were considered.
- The change does not introduce a new hard-coded business rule without review.

## 5. Release Checklist
Before each release, confirm:
- Existing customer data remains intact.
- Backup creation and restore validation are working.
- .prmlic licensing still behaves correctly.
- Print workflows support A4 Portrait and A2 Landscape where applicable.
- Bulk print and loading sheet / dispatch summary behavior remain correct.
- Security protections remain intact.
- Role-based permissions are still enforced.
- Core modules still work end-to-end.
- Documentation is current.
- Release notes and migration notes are prepared.

## 6. Definition of Done
A feature or change is done only when all of the following are true:
- The requirement is implemented in the desktop application.
- The change works in the intended business workflow.
- The change preserves existing customer installations and data.
- The change is documented.
- The change is tested.
- The change respects permissions, audit logging, and security expectations.
- The change preserves operator speed and usability.
- The change does not break printing, reporting, or backup/restore behavior.

## 7. Future roadmap
- Strengthen shared engines for GST, printing, inventory, accounts, licensing, and security.
- Improve documentation discipline and product-spec traceability.
- Add more automated testing for UI, print, and workflow scenarios.
- Improve backup validation, restore confidence, and migration safety.
- Keep all future development aligned with the desktop-first architecture and .prmlic-based licensing model.
- Continue using AI_GUIDE as the authoritative source for product behavior and implementation guidance.
