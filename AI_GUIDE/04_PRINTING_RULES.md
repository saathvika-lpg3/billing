# Printing Rules

## Paper size rules
- The distributor business type must support both A4 Portrait and A2 Landscape.
- Client/Admin users must be able to choose paper size per document type.
- Bulk print must support A4 Portrait and A2 Landscape.
- Bulk print must respect the selected paper settings.
- Do not hard-code A2 only.
- Do not hard-code A4 only.

## Locked print requirement: Loading Sheet / Dispatch Summary
- Loading Sheet / Dispatch Summary print rules must show GSTIN if available.
- Loading Sheet / Dispatch Summary print rules must show HSN if available.
- Loading Sheet / Dispatch Summary print rules must show FSSAI number if available.
- These fields must appear in print preview, PDF export, and bulk print.
- If a field is not available, hide it gracefully.
- Do not show blank labels such as "GSTIN:" with no value.
- This requirement applies especially to the Distributor business type.
- The print workflow must support both A4 Portrait and A2 Landscape.

## Printing behavior expectations
- Paper selection should be configurable and document-aware.
- The same document type may need different paper settings depending on business context.
- Printing flow must honor the chosen settings in both single-document and bulk-print scenarios.

## Safe implementation guidance
- Keep existing print modules and UI structure intact.
- Add paper-size support in a backward-compatible way.
- Ensure any new print option defaults do not break current workflows.

## Current production-readiness status

- Distributor paper requirements are represented in the shared print engine by
  document-aware `PrintOptions` with A4/A2 and portrait/landscape support.
- Preview, PDF export and report generation must all continue to call the same
  centralized PDF writers so paper selection and template mapping stay
  consistent.
- The automated print/report parity suite is the required guard for repeated
  headers, page numbering, report paper overrides, transaction PDFs and voucher
  PDFs.
- Real printer-driver output and locked external PDF visual comparison remain
  operator/workstation tasks and must be marked blocked until those references
  and devices are available.
