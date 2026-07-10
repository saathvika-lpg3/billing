# UI Standard for PRM_GST_DESKTOP

## 1. Global UI direction
The UI for PRM_GST_DESKTOP must remain a modern, stylish desktop ERP experience built with Python and PyQt6.

Core goals:
- Keep the interface polished and professional
- Preserve fast operator workflow
- Keep the experience keyboard-first and efficient
- Avoid visual clutter and layout instability
- Support desktop screens comfortably on standard business hardware

Locked project rules:
- Python + PyQt6 + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve .prmlic licensing
- UI must be stylish but should not reduce speed
- Operator speed is more important than animation
- Forms must support keyboard-first workflow

## 1.1 Layout and page structure
- Pages must use a stable, clean layout with clear grouping of fields.
- Labels and controls must not overlap or visually collide.
- Controls must be placed in a predictable row/column structure.
- Vertical scrolling is acceptable when needed.
- Horizontal scrolling must be avoided on normal pages.
- Long forms should break into logical sections with clear spacing.
- Use cards, grouped panels, and section headers where appropriate.
- The layout must remain readable at common desktop resolutions.

## 1.2 Visual style
- The interface should feel modern, business-ready, and professional.
- Use clean spacing, consistent alignment, and clear hierarchy.
- Avoid excessive animation and decorative effects that slow users down.
- Prioritize clarity and speed over visual complexity.
- The UI should feel fast and responsive even on modest machines.

## 2. Operator-friendly data entry
The UI should be optimized for business operators who enter data quickly.

Rules:
- Keep commonly used fields visible and near the top of the form.
- Group related fields together.
- Pre-fill logical defaults when appropriate.
- Minimize clicks needed for common actions.
- Reduce unnecessary modal interruptions.
- Keep forms easy to scan while entering data at speed.

## 3. Mandatory field highlighting
Mandatory fields must be clearly indicated.

Rules:
- Required fields must be visually marked.
- Use a consistent requirement style such as bold label text, a required marker, or a colored indicator.
- The required marker must be clear but not visually noisy.
- The UI should make it easy to understand what must be completed before save.

## 4. Cursor and focus behavior
- When a form opens, the cursor/focus must start on the first mandatory control.
- If there is no mandatory field, focus should go to the first logical input field.
- After a field is completed and accepted, focus should move naturally to the next logical input.
- Focus must remain predictable during validation errors.

## 5. Enter key behavior
- Enter key should move to the next logical control in a form where appropriate.
- In grids and lists, Enter should move to the next row or next relevant field rather than triggering unexpected actions.
- Enter should not unexpectedly submit the form when a user is simply navigating fields.
- In dialogs, Enter should act consistently with the current focused control.

## 6. Esc key behavior
- Esc should safely cancel or close the current action where appropriate.
- If a form has unsaved changes, Esc should prompt the user before closing.
- Esc should not silently destroy data.
- Esc should close dialogs, search popups, or temporary overlays cleanly.

## 7. History and back navigation
- The application should support simple history/back navigation for pages and workflows.
- Users should be able to return to the previous screen without losing necessary context.
- Back navigation should behave predictably and not break the current workflow.
- For multi-step data entry, the user should be able to return safely without accidental data loss.

## 8. Hotkeys for common actions
Common actions should have keyboard shortcuts.

Recommended shortcuts:
- Ctrl+S: Save
- Ctrl+N: New document / new record
- Ctrl+F: Find / search
- F4: Add line / add row
- Esc: Cancel / close / back
- Ctrl+P: Print / preview
- Ctrl+Shift+P: Bulk print where supported
- Ctrl+L: Clear or focus search

Rules:
- Shortcuts must not conflict with system-level shortcuts unnecessarily.
- Shortcut behavior must be consistent across similar screens.
- If a shortcut is unavailable in a given context, it should do nothing or show a clear message.

## 9. Tooltips for fields and buttons
- Important fields and buttons should have tooltips.
- Tooltips should be short, practical, and helpful.
- Tooltips should explain purpose, expected format, or important behavior.
- Tooltips must not be used for obvious labels only.
- Forms should include placeholder/sample text where helpful for operators and demo/testing.

Examples:
- Date field: explain expected format or business meaning
- Print button: explain preview/export action
- Save button: explain validation before save
- Search field: explain the expected search terms or filters

## 10. Fast keyboard-only operation
The UI must be usable without a mouse where possible.

Rules:
- All major fields and actions should be reachable by keyboard.
- Tab order must be logical and consistent.
- Focus order must follow the visual flow of the form.
- Users should be able to complete standard transactions without needing to click repeatedly.
- Keyboard-first workflow is preferred over click-heavy interactions.

## 11. Data grid behavior
Data grids and tables must support fast entry and review.

Rules:
- Use clear headers and predictable column order.
- Keep rows easy to scan.
- Allow selection, editing, and navigation without ambiguity.
- Support keyboard navigation where appropriate.
- Use consistent alignment for numeric and text values.
- Avoid excessive column width changes that make the grid hard to read.
- If rows are long, keep the important columns visible and allow the grid to scroll vertically.

## 12. Search and filter behavior
Search should be fast and visible.

Rules:
- Search boxes should be easy to find.
- Search should work immediately as the user types where appropriate.
- Filter behavior must be responsive and predictable.
- Search should be case-insensitive where practical.
- If no results are found, show a clear empty-state message.
- The user should be able to clear filters quickly.

## 13. Save/cancel/delete confirmation behavior
- Save should validate data before writing.
- If validation fails, the user should stay on the form and see clear messages.
- Cancel should ask for confirmation when there are unsaved changes.
- Delete should require explicit confirmation.
- Destructive actions should not happen accidentally.
- Confirmation dialogs should be concise and clear.

## 14. Error, warning, and success message style
Messages should be consistent and easy to understand.

Rules:
- Error messages must explain what went wrong and what the user should do next.
- Warning messages should highlight risky actions before confirmation.
- Success messages should confirm completion without being overly verbose.
- Use a consistent message style across the app.
- Avoid generic messages such as "Failed" without explanation.

## 15. Light/dark theme readiness
The UI should be ready for light and dark themes.

Rules:
- Colors and contrast should remain readable in both themes.
- Theme changes should not break layout or controls.
- Important actions and status states must remain clear in both modes.
- The theme system should not remove the core readability of forms and tables.

## 16. Accessibility and readability
The UI should be readable and usable for a wide variety of users.

Rules:
- Use legible fonts and clear contrast.
- Avoid tiny text and cramped controls.
- Keep labels meaningful and readable.
- Ensure keyboard focus is visible.
- Avoid color-only meaning where text or icons are also needed.
- Keep the interface comfortable for long business sessions.

## 17. Billing screen special rules
Billing screens are the highest-speed operational screens and need extra care.

Rules:
- The first usable input should receive focus immediately.
- Mandatory fields must be obvious.
- Line-item entry should support fast movement between columns and rows.
- Totals and tax values must be visible and updated clearly.
- Save, print, clear, and add-row actions must be easy to access.
- The screen should not feel visually heavy or slow.
- Validation should happen before save, not after a long delay.
- The operator should be able to work quickly without losing context.

## 18. Report screen special rules
Report screens should be clear and focused on results.

Rules:
- Filters should be easy to adjust.
- Large result sets should remain readable and navigable.
- Report screens should not force the user into slow or confusing interactions.
- Export and print actions should be obvious.
- Empty results should show a clear message rather than a blank area.

## 19. Print preview UI rules
Print preview must be clean, predictable, and aligned with actual output.

Rules:
- Preview should show the same document content that the print/PDF output will produce.
- Paper size must be visibly reflected in the preview behavior where appropriate.
- A4 Portrait and A2 Landscape must both be supported and clearly handled.
- Loading Sheet / Dispatch Summary preview must show GSTIN, HSN, and FSSAI when available.
- Missing print values must be hidden gracefully.
- No blank labels should appear in preview.
- Preview must support the same document-wise paper-size selection used in the main print workflow.

## 20. Testing checklist
- Check layout on standard desktop resolutions.
- Verify no overlapping labels or controls.
- Verify vertical scrolling works and horizontal scrolling is not needed on standard pages.
- Verify focus begins on the first mandatory field.
- Verify Enter key moves to the next logical control.
- Verify Esc cancels or closes safely.
- Verify hotkeys work for common actions.
- Verify tooltips appear where expected.
- Verify keyboard-only operation works for core flows.
- Verify data grids are navigable and readable.
- Verify search/filter behavior is responsive.
- Verify save/cancel/delete confirmation is consistent.
- Verify error, warning, and success messages are clear.
- Verify light and dark themes remain readable.
- Verify billing screens remain fast and operator-friendly.
- Verify report screens remain clear and usable.
- Verify print preview and PDF output honor the selected paper settings and available metadata.

## 21. Future roadmap
- Standardize common form patterns across the desktop modules.
- Improve keyboard flow and shortcut consistency across screens.
- Expand reusable UI components for cards, tables, and validation states.
- Improve theme support and accessibility readiness.
- Keep the interface modern and fast while staying within the desktop Python + PyQt6 architecture.

## 22. Phase 1 transaction rollout status
- Reusable transaction shell components now live in widgets/erp_components.py.
- The first shared rollout has been applied to sales billing, purchase entry, sales document entry, and inventory entry pages.
- The rollout preserves business logic and database behavior while standardizing page headers, field wrappers, and toolbar placement.
