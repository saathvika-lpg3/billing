# PRM_GST Source Gap Analysis

Generated from the live source folder `D:\PRM_GST_DESKTOP` on 2026-07-02.

## Source Scan

- Main portal file: `index.php`
- Portal routes found: 212
- PHP functions found: 968
- Layout calls found: 106
- Menu/link route references found: 286
- SQLite tables found: 94
- SQLite columns found: 1500

## Default Business Type

- Active company business type: `distributor_wholesale`
- Active company plan: `premium`
- Active invoice template code: `wholesale_tax_invoice`
- Active license row also confirms `distributor_wholesale`.

## Desktop Coverage Result

- Distributor/wholesale top-menu options: no missing labels.
- Client-facing desktop menu keeps only the active distributor/wholesale ERP modules.
- Optional business families from PRM_GST remain in the audit data for future migration review, but the Industry menu is not exposed in the client build.
- Feature access is now driven from the client `.prmlic` plan and role/security flow.

## Remaining Deep Migration Work

These are retained in the source audit only and still need full entry forms and posting engines if a future client license switches away from distributor/wholesale:

- Restaurant/KOT/table billing workflows.
- Pharmacy prescription, doctor, patient history and batch/expiry-focused billing workflows.
- Real estate lead, booking, agreement, installment, refund, commission and document workflows.
- Manufacturing BOM, work order, production run, job work and QC posting workflows.
- Service/warranty serial number, complaint, repair, job card, warranty claim and reminder workflows.

## Current Decision

The client handover build keeps distributor/wholesale as the default operator workflow, removes the Industry menu from the client UI, and uses `.prmlic` security for install, login, developer access, plan, expiry and feature gating.
