# PRM UI Design System

This document records the approved Quotation Entry page as the MASTER TEMPLATE and the global component library derived from it.

## Master Rules
- Use the Quotation Entry screen as the single visual reference.
- Preserve all business logic, database, print, report, GST and inventory behavior.
- Replace only the UI controls with reusable, styled components.

## Core Components
- `ERPMainWindow` — application chrome and header
- `ERPHeader` / `ERPPageHeader` — page title, subtitle, status label and action area
- `ERPTopNavigation` — horizontal top navigation bar (no left nav)
- `ERPSectionCard` — white card with padding, title and body
- `ERPFieldBox` — labeled compact field container with consistent spacing
- `ERPToolbar`, `ERPGridToolbar` — consistent action groups and ordering
- `ERPGrid` — standardized editable grid with keyboard-first navigation
- `ERPLineEdit`, `ERPComboBox`, `ERPDateEdit`, `ERPAmountEdit` — styled form inputs
- `ERPTotalCard`, `ERPTaxSummaryCard` — totals and tax summary panels
- `ERPStatusBadge`, `ERPMessageBar`, `ERPDialog`, `ERPFooter`, `ERPKeyboardHintBar`

## Transaction Page Standard (summary)
- Header: `ERPPageHeader` + `ERPToolbar` (actions always in same order: New, Save, Preview, Print, PDF, WhatsApp, Email, Close)
- Cards: Header card, Item entry card, Grid card, Summary card (totals & tax)
- Grid: single-click editing, Enter/Tab navigation, sticky header, alternating rows

## Accessibility & Scaling
- Support Windows DPI scaling and common desktop resolutions.
- Keyboard shortcuts preserved and globally consistent.

## Rollout Phases
- Phase 1: Apply to all transaction entry pages (in progress).
- Phase 2: Apply to all masters (partial completed).
- Phase 3+: Reports, Administration, Developer Dashboard (planned).

## Current Status
- Phase 1: Several transaction pages updated; focused UI tests passing.
- Next: complete the remaining transaction pages, standardize grid behavior, then run full regression tests.
