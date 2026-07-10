# Search Engine Specification for PRM_GST_DESKTOP

## 1. Purpose
This document defines the product specification for the PRM_GST_DESKTOP Search Engine.

The Search Engine is a core productivity layer for the desktop ERP. It must allow operators to quickly find customers, suppliers, products, invoices, documents, tax identifiers, barcodes, routes, and other business data without slowing down the application.

Locked project rules:
- Python + PyQt6 + SQLite desktop only
- No web conversion
- No SQLite for this release
- Preserve existing .prmlic licensing
- Operator speed is very important
- Search must not freeze the UI
- Search must respect user permissions

## 2. Global search bar
The application must provide a global search experience that is available from a prominent desktop entry point.

Required behavior:
- A global search box should be visible or quickly accessible from the main desktop workflow.
- The search bar must support quick entry of text and immediately return likely matches.
- The global search should work across major business entities such as customers, suppliers, products, invoices, documents, and routes.
- The search should remain responsive and should not block the UI thread.
- Results should be grouped clearly by category.

## 3. Command palette search
The product should support a command palette-style search experience for power users.

Required behavior:
- Operators should be able to open a command palette quickly from keyboard input.
- The command palette should support both commands and data search.
- Example commands may include: open sales bill, open customer master, open reports, open product master, open search.
- Search results should be filtered as the operator types.
- Command palette results should be fast, keyboard-friendly, and non-blocking.

## 4. Module-wise search
Each major module should expose its own focused search experience.

Required modules:
- Sales module search
- Purchase module search
- Inventory module search
- Accounts module search
- Reports module search
- Dispatch / loading module search
- Master data search

Required behavior:
- Module-wise search should use the same overall search patterns but tailor results to the current module context.
- The current module should influence the default result ordering.
- Returning to the same module should feel fast and consistent.

## 5. Customer search
Customer search is a core requirement.

Required behavior:
- Search by customer name, code, mobile number, GSTIN, city, state, or route.
- Search results should show customer name, code, city, mobile, GSTIN, status, and route where available.
- Selecting a customer should open the customer record or allow immediate use in a transaction.
- Search should be available in sales, dispatch, billing, and report workflows.
- Permission filtering must ensure that unauthorized users cannot view restricted customer data.

## 6. Supplier search
Supplier search is required for purchase and accounts workflows.

Required behavior:
- Search by supplier name, code, mobile number, GSTIN, city, state, or remarks.
- Results should include supplier identity and status.
- Selecting a supplier should open the supplier record or allow immediate use in a transaction.
- Supplier search must be available in purchase, accounts, and reporting contexts.
- Permission filtering must ensure unauthorized users cannot access restricted supplier data.

## 7. Product search
Product search is essential for billing, inventory, stock, and purchase workflows.

Required behavior:
- Search by product name, code, HSN, barcode, alias, or category.
- Results should include product name, code, stock availability, HSN, barcode, and status where available.
- Search should support quick selection in transaction entry screens.
- The product search experience should stay responsive even when many products exist.
- Product search must respect permissions and business visibility rules.

## 8. Invoice/document search
Invoice and document search must support business document retrieval.

Required behavior:
- Search by invoice number, document number, customer, supplier, date, amount, or status.
- Results should include document type, number, party name, date, amount, and status.
- Search should allow quick access to the original document view or print preview.
- The system should support both open and historical document lookup.
- Permission filtering must control what a user can open or view.

## 9. GSTIN search
GSTIN search is required for tax-related lookups and compliance workflows.

Required behavior:
- Search by GSTIN value.
- Results should show the matching customer or supplier record where available.
- Search should support quick navigation to the related party record.
- The UI should not freeze while processing GSTIN search.
- If no match exists, the search should return a clear empty state.

## 10. HSN search
HSN search should support item classification and tax-related navigation.

Required behavior:
- Search by HSN code or partial HSN values.
- Results should return matching products or classification-based items.
- The results should be useful in invoice, billing, and reporting workflows.
- Search should remain fast even with a larger item catalog.

## 11. Barcode search
Barcode search is important for inventory, retail, and dispatch workflows.

Required behavior:
- Search by barcode or QR value.
- Results should return the matching product or document reference where relevant.
- The search experience should be fast enough for real-time retail or inventory usage.
- The system should support barcode lookup from the desktop workflow without freezing the UI.

## 12. Mobile number search
Mobile number search is required for party lookup and quick contact-based access.

Required behavior:
- Search by mobile number or partial mobile number.
- Results should return matching customer or supplier records.
- The search should be available in both master and transaction contexts.
- The UI should avoid expensive blocking operations while searching.

## 13. Vehicle/route search
Vehicle and route search is important for dispatch, loading, transport, or delivery workflows.

Required behavior:
- Search by vehicle number, route, area, or dispatch-related identifier.
- Results should show available dispatch or route references where applicable.
- The search should be usable in loading sheet and dispatch summary workflows.
- The search should remain responsive and not delay document creation.

## 14. Date/range search
Date-based search is required for transaction and document review.

Required behavior:
- Support single-date search and date-range search.
- The search engine should allow date filtering for invoices, bills, returns, reports, payments, and stock movement.
- Date search should work with clear UI controls and predictable result ordering.
- Date-range search must remain responsive even when the database grows.

## 15. Fuzzy search for typing mistakes
The search engine must support fuzzy search to tolerate minor typing mistakes.

Required behavior:
- Typing errors should not prevent useful results.
- Examples include missing characters, transposed letters, or small spelling differences.
- Fuzzy matching should be used on names, codes, and other free-text fields where appropriate.
- The search should remain fast and should not degrade the desktop experience.
- Fuzzy behavior must be practical and not overly noisy.

## 16. Keyboard shortcuts
The search experience must be keyboard-friendly and fast.

Required shortcuts:
- Ctrl+F or a dedicated global search shortcut to open search
- Esc to close or cancel search UI
- Enter to confirm the selected result
- Arrow keys to navigate results
- Ctrl+Shift+P or equivalent for command palette if implemented
- Shortcuts should work without making the UI feel crowded or confusing

## 17. Search result UI
The search result UI must be clear and operator-friendly.

Required behavior:
- Results should be grouped by category such as Customer, Supplier, Product, Invoice, Report, and Command.
- Each result should show a short descriptive label and relevant metadata.
- The selected result should be easy to identify visually.
- The UI should support quick preview or navigation to the underlying record.
- The result list should stay readable even when many matches are returned.

## 18. Security/permission filtering
Search results must respect user permissions.

Required behavior:
- Users should only see records they are allowed to access.
- Sensitive data should not appear in search results for unauthorized roles.
- Permissions should be applied at both search and result-display levels.
- The search experience must remain functional for read-only and restricted users without exposing protected data.
- .prmlic-based access and role-based filtering must both be respected.

## 19. SQLite indexing expectations
Search must be efficient in the SQLite desktop model.

Required expectations:
- Indexed columns should include common search keys such as code, name, GSTIN, mobile number, barcode, invoice number, date, status, and route.
- Full-text search may be used where beneficial, but it must remain lightweight and compatible with the desktop environment.
- Search should be designed to work efficiently with the local SQLite database size expected for this product.
- Index choices should preserve a balance between speed and update cost.

## 20. Performance rules
The search engine must not freeze the UI.

Required rules:
- Search should be asynchronous or otherwise non-blocking.
- Typing should not create long UI freezes or repeated full-table scans in the main thread.
- The system should support a reasonable amount of data without major lag.
- If a search is expensive, the UI should show a lightweight loading state rather than freeze.
- Search should remain responsive during document entry, report opening, and master-data work.

## 21. Audit/logging
Search activity should be auditable where required by policy.

Required behavior:
- Sensitive searches may be logged where appropriate.
- Audit logging should capture the action type, user identity, timestamp, and target context where relevant.
- Search logging must not expose protected data unnecessarily.
- Logging should remain compatible with the current desktop + SQLite model.

## 22. Testing checklist
- Verify global search returns the expected categories and results.
- Verify command palette search opens quickly and returns useful results.
- Verify customer, supplier, product, invoice, GSTIN, HSN, barcode, and mobile searches work correctly.
- Verify date-range search returns the expected record set.
- Verify fuzzy search tolerates minor typing errors.
- Verify keyboard shortcuts work as expected.
- Verify search results respect user permissions.
- Verify the UI remains responsive while typing.
- Verify SQLite-backed search remains functional with typical desktop data volumes.
- Verify audit/logging rules are respected where applicable.

## 23. Done condition
The Search Engine is considered complete when:
- operators can quickly search across major master and transaction data from the desktop UI
- searches are fast, responsive, and keyboard-friendly
- results are relevant and grouped clearly
- permissions are enforced properly
- the feature works in the existing Python + PyQt6 + SQLite architecture without requiring SQLite or web services
- the UI does not freeze during search operations

## 24. Future roadmap
- Add richer ranking and contextual relevance rules
- Improve fuzzy matching and partial-token search
- Add more command palette actions and shortcuts
- Expand cross-module search intelligence for reports and documents
- Improve search performance and indexing as data volume grows
- Keep all future work aligned with the desktop-first product vision and .prmlic security model
