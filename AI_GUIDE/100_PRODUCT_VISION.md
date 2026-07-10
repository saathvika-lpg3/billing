# PRM_GST_DESKTOP Product Vision / ERP Constitution

## 1. Product purpose
PRM_GST_DESKTOP is a desktop-first ERP platform for small and mid-sized businesses that need reliable billing, inventory, accounts, dispatch, reporting, and print workflows without depending on a web backend.

The product exists to help operators work quickly, accurately, and confidently in a local environment where data ownership, licensing control, and offline usability matter.

The product is not a generic web application. It is a focused desktop ERP made for real business operations.

## 2. Target customers
The primary customers are:
- distributors and wholesalers
- retail and supermarket businesses
- pharmacy and medical trade businesses
- manufacturing and trading concerns
- restaurants and food businesses
- service businesses with billing and accounts needs
- businesses requiring strong print, dispatch, and reporting workflows

The product is especially suited to businesses that value:
- local data control
- fast daily operation
- strong desktop usability
- printable business documents
- simple deployment and maintenance

## 3. Desktop-first philosophy
PRM_GST_DESKTOP is a desktop application first and foremost.

This means:
- the user experience is designed around local desktop operators
- the product should feel fast, responsive, and dependable
- the application should work reliably without requiring a browser-based front end
- the system should be practical for everyday business use in a local environment

The desktop-first philosophy is a product promise, not an implementation accident.

## 4. Customer data first rule
Customer data is the most important asset in the system.

This means:
- customer records must be complete, searchable, and usable across billing, dispatch, reports, and print workflows
- customer data must remain protected and must not be lost during updates or migrations
- customer records must be treated as a trusted business foundation, not as disposable transaction metadata

If a feature improves speed but harms customer data quality, safety, or traceability, it is not acceptable.

## 5. Single source of truth rule
Every core business entity must have one authoritative source of truth in the system.

Examples include:
- customer master
- supplier master
- product master
- party ledger
- stock movement records
- invoice and document state
- print settings and document configuration

The system must avoid duplicate, conflicting, or fragmented records where possible.

If a piece of data can be created in more than one place, the product must enforce a clear ownership pattern and avoid ambiguity.

## 6. Operator speed rule
The product must be optimized for business operators, not just developers.

This means:
- common actions should take fewer clicks
- forms should support keyboard-friendly entry
- search and lookup must be fast and intuitive
- document creation should be smooth and predictable
- the UI should feel efficient for daily commercial work

The user experience must be stylish, modern, and operator-friendly while staying practical for long working hours.

## 7. Configuration over hard-coding rule
Business behavior should be configurable where possible rather than hard-coded.

This includes:
- business-type-specific behavior
- print layout and paper-size behavior
- document rules and defaults
- role-based access behavior
- reporting and summary preferences

The product should allow configuration for different industries without requiring a separate codebase for each business type.

## 8. Universal print engine rule
Printing is a core product capability, not an optional add-on.

The product must support:
- A4 Portrait
- A2 Landscape
- bulk print workflows
- document-specific print behavior
- print preview and export where applicable

The print engine must be universal across documents and business types so that invoices, dispatch summaries, loading sheets, reports, and other documents remain consistent and reliable.

The print engine must also support the business rule that Loading Sheet / Dispatch Summary show GSTIN, HSN, and FSSAI if available and hide missing fields gracefully.

## 9. Security and .prmlic rule
Security is a first-class product requirement.

The product must preserve the existing .prmlic licensing model and ensure that:
- protected workflows remain linked to valid licensing
- unauthorized local access is limited
- customer and business data are protected
- copied database files are not directly usable without the proper application protection context
- updates do not break valid customer data

The application must be designed to protect the business even when the local machine is shared, copied, or partially exposed.

## 10. SQLite desktop rule
The product is built around SQLite in a local desktop deployment model.

This means:
- the application remains desktop-only
- SQLite is the primary local database model
- the product does not rely on SQLite for this release
- local data ownership remains a core advantage
- future enhancements must respect the SQLite desktop architecture

The system must remain practical and robust in a single-user or small-workgroup desktop environment.

## 11. Future-ready platform rule
The product must be built in a way that allows future growth without breaking the core desktop experience.

Future readiness means:
- modular architecture where workflows can evolve independently
- a stable core for billing, inventory, accounts, print, and reporting
- room for stronger security, better diagnostics, and richer UI features
- compatibility with future desktop package and installer improvements

The platform should be able to grow into a deeper ERP over time without losing its current identity.

## 12. Smart diagnostics vision
The future product should include smart diagnostics that help operators and developers understand problems quickly.

Examples include:
- clear validation errors during document entry
- guided troubleshooting for printing issues
- license diagnostics and state reports
- database health checks
- backup integrity and restore status reporting
- workflow-specific warnings and recovery guidance

The goal is not just to show errors, but to help the operator recover or understand the issue without confusion.

## 13. ERP dashboard philosophy
The ERP dashboard should act as the operator’s command center.

It should provide:
- business status summaries
- quick access to common tasks
- sales, purchase, stock, and account indicators
- recent activity and alerts
- document and print readiness views
- shortcuts to high-value workflows

The dashboard should be visually clear, not overloaded, and should help the operator focus on what matters most.

## 14. Command palette vision
The product should eventually include a command palette-style experience for power users.

This would allow operators to:
- quickly jump to modules
- open recent documents
- run reports
- perform common tasks
- access print workflows
- search masters and transactions efficiently

The command palette should feel fast, contextual, and natural for a desktop ERP.

## 15. Search engine vision
Search should be a first-class product experience.

The system should support:
- fast search across customers, suppliers, products, transactions, and reports
- fuzzy and contextual lookup where helpful
- search that respects the current module and workflow
- quick navigation from search results into the relevant document or master record

The search experience should feel like a business tool, not just a basic filter.

## 16. One-year roadmap
Within one year, the product should focus on:
- stronger core module stability
- better print engine consistency across A4 Portrait and A2 Landscape
- improved bulk print workflows
- better dispatch and loading sheet output quality
- stronger role-based access controls
- better database protection and backup safety
- improved reporting quality and consistency
- polished desktop UI and operator workflows

## 17. Three-year roadmap
Within three years, the product should evolve toward:
- a richer ERP experience with stronger analytics and workflow automation
- more configurable business-type behavior
- advanced diagnostics and health monitoring
- improved security and machine-bound protection where feasible
- better cross-module reporting and and document lifecycle tracking
- a more powerful desktop command and search experience

## 18. Five-year roadmap
Within five years, PRM_GST_DESKTOP should become a durable, highly capable desktop ERP platform that:
- remains desktop-first and operator-focused
- supports a wide range of business types without becoming fragmented
- offers deep reporting, strong diagnostics, and secure data handling
- provides a polished, stylish, and modern operator experience
- preserves strong local data ownership and licensing control
- remains compatible with the product’s core constitution: desktop-only, secure, printable, and business-driven
