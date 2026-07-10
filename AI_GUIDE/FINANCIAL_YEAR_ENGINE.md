# Financial Year Engine

## Purpose
The Financial Year Engine provides reusable year management for all future ERP document and accounting flows. It is the single source of truth for open, closed, current, and locked financial years.

## Supported concepts
- Multiple financial year records
- Active current year
- Previous and future years
- Open and closed statuses
- Locked years
- Year switching and validation
- Migration-safe schema evolution
- Carry-forward/opening-balance hooks
- Audit-ready events table

## Data model
- `financial_years`
  - `id`
  - `label`
  - `start_date`
  - `end_date`
  - `status` (`Open`/`Closed`)
  - `is_current`
  - `is_locked`
  - `created_at`
  - `updated_at`
  - `closed_at`
  - `locked_at`

- `financial_year_events`
  - `id`
  - `financial_year_id`
  - `event_type`
  - `event_at`
  - `details`
  - `created_at`

## Rules
- Only one year may be marked current.
- Closed years may not be current.
- Locked years cannot be edited, opened, or closed.
- Year switch validates the target year is open and unlocked.
- Year close rejects future/active overlap and writes a closing event.
- Years with existing transactions cannot be deleted.

## Implementation
- `services/financial_year_service.py`
- `MasterRepository.ensure_schema()` now creates the financial year engine schema.

## Usage
- `FinancialYearService.create_year(label, start_date, end_date)`
- `FinancialYearService.set_current_year(year_id)`
- `FinancialYearService.close_year(year_id)`
- `FinancialYearService.lock_year(year_id)`
- `FinancialYearService.open_year(year_id)`
- `FinancialYearService.carry_forward_opening_balance(from_year_id, to_year_id)`

## Notes
- The engine is intentionally isolated from document flows; future document services must request the current financial year and numbering series from these services.
- No numbering or date logic should be duplicated outside these service APIs.
