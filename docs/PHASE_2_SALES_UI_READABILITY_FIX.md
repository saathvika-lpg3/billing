# Sales UI Readability Fix

## Issue

The first PyQt Sales Bill draft used raw grid rows. On real screen size, Qt compressed labels and controls so field values were difficult to read.

## Fix

- Rebuilt Sales Bill fields as proper `fieldBox` containers.
- Added readable minimum heights for line edits, combo boxes, date edits, and buttons.
- Converted header form into proportional 4-column desktop field groups.
- Reworked item entry into a cleaner operator strip with a wide product search and readable numeric controls.
- Increased transaction table minimum height and set fixed useful column widths.
- Improved light/dark QSS so labels are transparent, controls have readable foreground colors, and text is not clipped.
- Relaunched the app with `pythonw.exe` to avoid the black console window.

## Verified

- Compile passed.
- Sales calculator tests passed.
- Offscreen app startup passed.
- Sales Bill source data loads: 13 customers, 68 packs.
