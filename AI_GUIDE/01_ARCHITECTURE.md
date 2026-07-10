# Architecture Guide

## High-level architecture
The application is a desktop ERP-style Python system with:
- PyQt6-based UI views
- SQLite as the local database engine
- service-layer business logic
- modular desktop screens for masters, transactions, inventory, accounting, reporting, and printing

## Architectural constraints
- Keep the current desktop architecture intact.
- Preserve the existing view/service/module boundaries.
- Avoid introducing web frameworks, remote services, or SQLite in this release.
- Continue to support local-first workflows and file-based licensing.

## Suggested architecture understanding
- UI layer: desktop views and windows
- Service layer: business logic, printing, licensing, import/export, backup, reporting helpers
- Data layer: SQLite database and local files
- Configuration and assets: project-local config, templates, assets, theme, logs, prints

## Safe extension approach
- Add documentation and implementation notes only where requested.
- When changing behavior, keep the same screens and module names.
- Prefer additive changes that maintain compatibility with current SQLite data and existing .prmlic licenses.
