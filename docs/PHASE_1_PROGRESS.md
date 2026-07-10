# Phase 1 Progress

## Confirmed Direction

- New desktop project location: `D:\PRM_GST_DESKTOP`
- Source PHP/XAMPP project: `D:\PRM_GST_DESKTOP`
- XAMPP is source reference only. The new application is a pure Python desktop app.
- UI target is modern desktop ERP design, not copied web visuals.

## Completed

- Created D-drive desktop workspace.
- Added PyQt6 project shell.
- Added light/dark QSS themes.
- Added route/function/source-file audit tools.
- Added SQLite schema audit tool.
- Generated audit outputs in `D:\PRM_GST_DESKTOP\audit`.
- Built migration phase map from current PHP routes.

## Source Scale

- PHP routes: 212
- PHP functions: 968
- Layout calls: 106
- SQLite tables: 94
- SQLite columns: 1500

## Next Gate

Before building the Sales Bill workflow, create a verified SQLite backup and
start the SQLite-to-SQLite/SQLCipher migration design.
