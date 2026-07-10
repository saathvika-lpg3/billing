# License and Installation Rules

## Licensing rules
- Installation and licensing must continue to use .prmlic files.
- Existing valid .prmlic files must remain valid after updates.
- Do not break compatibility with previously issued valid licenses.

## Installation rules
- Preserve existing desktop installation flow and packaging assumptions.
- Keep the application usable as a local desktop install.
- Avoid introducing new license mechanisms that would invalidate current valid .prmlic files.
- Production runtime must resolve the license file from the installed application folder or an explicit environment override, and the installer should place the database, backups, logs, and archive folders under the installation runtime.

## Safe guidance
- Any license-related changes must remain backward-compatible.
- New releases should continue to recognize and validate existing .prmlic files.
- If installation logic changes, preserve support for current license files and installation patterns.
