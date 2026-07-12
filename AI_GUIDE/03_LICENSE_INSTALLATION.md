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
- Each client may receive a separately named export such as `lakshmi.prmlic` or
  `sairam.prmlic`. The installer Browse page accepts any readable `.prmlic`
  filename whose exported content is valid; it is not bound to one pre-existing
  filename.
- Setup copies the selected client export to `<app>\license\client.prmlic` only
  as a stable internal runtime name. This does not make the installer specific
  to the source basename.
- Installer, uninstaller, executable, Start Menu shortcut and product UI use
  PRM Software branding. Client branding is loaded from the licensed company
  profile after installation and must not be hardcoded into setup resources.

## Safe guidance
- Any license-related changes must remain backward-compatible.
- New releases should continue to recognize and validate existing .prmlic files.
- If installation logic changes, preserve support for current license files and installation patterns.
