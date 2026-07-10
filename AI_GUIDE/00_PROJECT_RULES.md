# Project Rules

## Core platform rules
- This project is a Python desktop application using SQLite.
- Do not convert the product to a web application.
- Do not introduce SQLite for this release.
- Preserve the existing desktop UI, modules, navigation, and workflows.
- Keep the application focused on local desktop usage and offline/near-offline business operations.

## Product and business rules
- Installation and licensing must continue to use .prmlic files.
- Existing valid .prmlic files must remain valid after updates.
- The distributor business type must support both A4 Portrait and A2 Landscape.
- Client/Admin users must be able to choose paper size per document type.
- Bulk print must support A4 Portrait and A2 Landscape.
- Bulk print must respect the selected paper settings.
- Do not hard-code A2 only.
- Do not hard-code A4 only.

## Documentation and implementation rules
- Only create or update documentation files unless explicitly requested otherwise.
- Do not modify existing application code.
- Any future implementation work should preserve current behavior and UI structure.
- New features must be backward-compatible with existing valid licenses and current SQLite data.
- Before starting implementation, create or update PRM_CURRENT_STATUS.md.
- PRM_CURRENT_STATUS.md must clearly mention:
  - Last completed module
  - Current working module
  - Pending modules
  - Known issues
  - Files already modified
  - Next safe implementation step
