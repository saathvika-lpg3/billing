# Database shutdown safety note

## Summary
Added a guarded shutdown path so the desktop app closes registered SQLite/SQLite connections when the main window is closed, including forced window-close scenarios.

## What changed
- Added connection registration and cleanup methods to the shared SQLiteSource service.
- Hooked the main window close event to call the cleanup routine before the window exits.
- Added a regression test covering registered connection shutdown.

## Verification
Verified with:
- python -m pytest -q tests/test_sqlite_source_shutdown.py

Result:
- 1 passed in 0.35s

## Runtime note
The application was launched successfully with:
- d:/PRM_GST_DESKTOP/.venv/Scripts/python.exe app.py
