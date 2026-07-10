# Report Engine Guide

## Future report requirements

- The report engine must support A2 Landscape for reports, previews, exports, and bulk printing.
- Reports must be built with page-aware layout so headers, footers, page numbers, and totals render correctly across page breaks.
- Support large report pagination and ensure:
  - repeated header rows on every page
  - repeated footer rows on every page as needed
  - visible current page / total pages
  - final totals on the last page
- Use `D:\PRM_BILLING_INVENTORY` as a reference implementation for report layout and data structure where the existing code is stable.
- Profit & Loss and Balance Sheet layout/format should follow the existing project and must not be changed unless safety improvements are obvious.
- Provide a QA checklist for report testing that includes 1-page, 2-page, 5-page, 20-page, and large reports.
- Keep report generation separate from view rendering so the same output can be used in preview, export, and print.

## 2026-07-10 Report Center audit

- `views.report_center_view.ReportCenterView` is the live Report Center route.
- Profit & Loss is opened with `open_report("erp_profit_loss")`; Balance Sheet
  is opened with `open_report("balance_sheet")`.
- Statement reports render in the statement-tree panel rather than the generic
  flat table. The UI test `test_accounting_reports_use_statement_tree` protects
  this route and verifies left/right statement tree rows.
- Report PDF output continues through `write_report_pdf()` so preview, PDF and
  export paths use the same centralized renderer.
- The UI test `test_accounting_statement_reports_open_print_preview` protects
  the Profit & Loss and Balance Sheet print-preview handoff. Each statement
  report must generate a non-empty PDF before invoking the shared preview
  layer.
- Exact visual comparison against the latest attached Profit & Loss and Balance
  Sheet screenshots is blocked in runs where those image files are not provided
  as readable workspace attachments.
- Account Closing exposes the CA Export panel inside Report Center. That panel
  requires the filter card to expand while visible, then return to the compact
  report-filter height for normal reports. This hidden state is protected by
  `test_report_center_account_closing_ca_export_panel_fits_target_width`.
