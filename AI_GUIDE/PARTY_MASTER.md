# Party Master Validation Notes

Principles:
- Preserve legacy database compatibility: existing records and import paths must still work.
- Enforce stronger validation for new records where safe (e.g., numeric fields, GST/PAN format when provided).
- Do not break unit tests; any change must ensure tests continue to pass or tests updated accordingly.

Validation behavior:
- `code`: optional for legacy records, but when provided must be unique per table.
- `name`: required.
- `city/state/address`: optional for legacy records, but recommended to be provided for new records.
- `gstin` and `pan`: validate format only when non-empty.
- `email`: basic `@` presence check only.
- Numeric fields (`balance`, `credit_limit`): must be numeric and non-negative when provided.

UI guidance:
- Party Master UI should indicate which fields are required for new records (e.g., `name`) and which are optional for legacy compatibility (e.g., `code`).
- If user leaves optional fields empty, show a non-blocking informational tooltip recommending completion.
