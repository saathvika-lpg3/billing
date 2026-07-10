# PRM_GST to PRM Billing Inventory Desktop Parity Matrix

Generated: 2026-07-02

This matrix tracks PRM_GST web options against the desktop migration. The target is not to copy the old web look; the target is the same business capability with a faster desktop ERP design.

## Status Legend

| Status | Meaning |
|---|---|
| Done | Desktop page exists, opens from menu/search, uses migrated local data, and supports the operator workflow for this phase. |
| Posted | Core transaction saves into the local database with GST, stock, ledger, and audit JSON copy. |
| Partial | Page/list exists, but deeper PRM_GST behavior such as final posting, advanced validation, designer detail, or API integration still needs a completion pass. |
| Planned | Known PRM_GST feature; desktop route or detailed workflow is still queued. |

## Masters

| PRM_GST option | Desktop target | Status | Notes |
|---|---|---|---|
| Categories | Category Master | Done | Desktop master screen and live migrated rows. |
| Products | Product Master | Done | FMCG-style packs, barcode, GST, pricing, batch/expiry flags and stock fields are present. |
| Customers | Customer Master | Done | Party master with migrated customer list. |
| Suppliers | Supplier Master | Done | Party master with migrated supplier list. |
| Brands | Brand Master | Done | Brand/manufacturer list and master workflow. |
| Schemes / Offers | Scheme Master | Done | Scheme draft workflow and live product choices. |
| Units | Unit Master | Done | Unit master screen. |
| GST Rates | GST Rate Master | Done | Tax slab master screen. |
| Excel Import | Excel Import | Posted | CSV/XLSX preview plus direct posting for products, packs, customers, suppliers, opening stock and schemes. |
| Product Labels | Label Print | Done | Label batch preparation and export. |
| Employees | Employee/User Master | Done | User list and master workflow. |

## Sales

| PRM_GST option | Desktop target | Status | Notes |
|---|---|---|---|
| Quotation | Quotation Entry | Posted | Saves to `order_documents`; open documents can convert to sales bill from Document Center. |
| Quotation List | Sales Hub | Done | Live migrated `order_documents` rows. |
| Sales Order | Sales Order Entry | Posted | Saves to `order_documents`; open orders can convert to posted sales bill from Document Center. |
| Order List | Sales Hub | Done | Live migrated order rows. |
| Sales Bill | Sales Bill | Posted | Saves bill, item rows, stock movement, GST postings, voucher header, and ledger rows in local SQLite. |
| Sales List | Sales Hub / Reports | Done | Live migrated sales rows. |
| Delivery Challan | Delivery Challan Entry | Posted | Saves to `order_documents`; open challans can convert to posted sales bill from Document Center. |
| DC List | Sales Hub | Done | Live migrated DC rows. |
| Sales Return | Sales Return Entry | Posted | Source-bill selection, editable remaining return quantities, original bill linkage, stock input, reverse GST postings, voucher header, and ledger rows. |
| Return List | Sales Hub | Done | Live migrated return rows. |

## Purchase

| PRM_GST option | Desktop target | Status | Notes |
|---|---|---|---|
| Purchase Order | Purchase Order Entry | Posted | Saves to `order_documents`; open POs can convert to posted purchase invoice from Document Center. |
| PO List | Purchase Hub | Done | Live migrated PO rows. |
| Buy Stock / Purchase Bill | Purchase Entry | Posted | Saves purchase, item rows, stock input, GST postings, voucher header, and ledger rows in local SQLite. |
| Purchase List | Purchase Hub / Reports | Done | Live migrated purchase rows. |
| Purchase Return | Purchase Return Entry | Posted | Source-purchase selection, editable remaining return quantities, original purchase linkage, stock output, reverse GST postings, voucher header, and ledger rows. |
| Debit Notes | Purchase Hub | Done | Live migrated purchase-return rows. |
| Supplier Ledger | Purchase Hub / Accounts | Done | Live migrated supplier ledger rows. |

## Inventory

| PRM_GST option | Desktop target | Status | Notes |
|---|---|---|---|
| Stock | Stock Dashboard | Done | Stock cards and live item rows. |
| Stock Entry | Inventory Entry | Posted | Saves stock log and updates item/pack stock. |
| Stock Transfer | Transfer Entry | Posted | Saves transfer header, transfer items, and stock movement log. |
| Transfer List | Inventory Hub | Done | Live migrated transfer rows. |
| Stock Adjustment | Adjustment Entry | Posted | Saves adjustment rows, updates item/pack stock by difference, and logs movement. |
| Stock Alerts | Stock Dashboard | Done | Low-stock list. |
| Negative Stock | Stock Dashboard | Done | Negative-stock list. |
| Expiry / Wastage | Inventory Hub | Done | Batch expiry/wastage rows. |
| Vehicle Stock Out | Stock Out | Done | Route load workflow. |
| Load Challans | Inventory Hub | Done | Live stock-out rows. |
| Route Settlement | Route Settlement | Done | Settlement workflow. |
| Warehouses | Warehouse Master | Done | Warehouse master screen. |
| Stock Movement | Inventory / Reports | Done | Live stock log rows. |

## Accounts

| PRM_GST option | Desktop target | Status | Notes |
|---|---|---|---|
| Receipts | Receipt Entry | Posted | Saves receipt, voucher header, and ledger rows. |
| Payments | Payment Entry | Posted | Saves payment, voucher header, and ledger rows. |
| Expenses | Expense Entry | Posted | Saves expense, voucher header, and ledger rows. |
| Cash/Bank Book | Accounts Hub | Done | Live cash/bank ledger rows. |
| Journal Entry | Journal Entry | Posted | Saves journal entry, voucher header, and ledger rows. |
| Ledger Heads | Ledger Master | Done | Ledger master screen. |
| Outstanding | Accounts Hub | Done | Live customer/supplier outstanding rows. |
| Aging Report | Accounts Hub | Done | Live aging rows. |
| Customer Ledger | Accounts Hub | Done | Live customer ledger rows. |
| Ledger Groups | Accounts Hub | Done | Live ledger group rows. |
| Trial Balance | Accounts / Reports | Done | Live ledger totals. |
| Voucher Register | Accounts Hub | Done | Live voucher rows. |
| Voucher Review | Accounts Hub | Done | Live voucher review rows. |
| Bank Reconciliation | Accounts Hub | Done | Live bank reconciliation rows. |
| Cash Flow | Accounts Hub | Done | Live cash flow rows. |
| Fund Flow | Accounts Hub | Done | Live fund flow rows. |
| ERP Ledger | Accounts Hub | Done | Live ledger postings. |
| ERP Day Book | Accounts Hub | Done | Live day-book rows. |
| Account Closing | Accounts / Reports | Done | Live closing periods. |
| Control Check | Accounts Hub | Done | Ledger/stock control rows. |
| Branches | Branch Master | Done | Branch master screen. |
| Cost Centers | Cost Center Master | Done | Cost center master screen. |
| ERP Profit & Loss | Accounts / Reports | Done | Live P&L rows. |
| Balance Sheet | Accounts / Reports | Done | Live balance rows. |
| Stock Ledger Adj. | Accounts Hub | Done | Live stock valuation adjustment rows. |

## Reports

| PRM_GST option | Desktop target | Status | Notes |
|---|---|---|---|
| Sales List / Reports | Report Center | Done | Live rows with CSV and PDF export. |
| Purchase Reports | Report Center | Done | Live rows with CSV and PDF export. |
| Stock Reports | Report Center | Done | Live stock rows with PDF export. |
| Item Movement | Report Center | Done | Live stock movement rows. |
| GST Reports | Report Center | Done | Live GST postings. |
| GST Return | Report Center | Done | Live filing rows. |
| E-Invoice | Report Center | Partial | Live rows plus offline JSON preparation; government/API submission needs client credentials. |
| E-Way Bill | Report Center | Partial | Live rows plus offline JSON preparation; government/API submission needs client credentials. |
| Profit & Loss | Report Center | Done | Live ledger summary. |
| Day Book | Report Center | Done | Live voucher day book. |
| Audit Log | Report Center | Done | Live audit rows. |
| Daily Dispatch Summary | Report Center | Done | Live stock-out summary. |
| Item Loading Sheet | Report Center | Done | Live item loading rows. |
| Route Loading Sheet | Report Center | Done | Live grouped route rows. |
| Pending Dispatch | Report Center | Done | Live pending dispatch rows. |
| Loading Sheet | Report Center | Done | Live loading rows. |
| Customer Loading Sheet | Report Center | Done | Live customer dispatch rows. |
| Dispatch Return Summary | Report Center | Done | Live dispatch-return rows. |
| Account Closing | Report Center | Done | Live closing rows. |
| Balance Sheet | Report Center | Done | Live balance rows. |
| Trial Balance | Report Center | Done | Live trial balance rows. |
| GST Postings | Report Center | Done | Live GST posting rows. |
| Stock Postings | Report Center | Done | Live stock posting rows. |
| Inventory Valuation | Report Center | Done | Live valuation rows. |
| GST Adjustment | Report Center | Done | Live GST adjustment rows. |
| ITC Reconciliation | Report Center | Done | Live ITC rows. |
| GSTR-9 Annual | Report Center | Done | Financial-year basis rows. |

## Administration / Developer

| PRM_GST option | Desktop target | Status | Notes |
|---|---|---|---|
| Developer Dashboard | Developer Console | Done | Desktop dashboard, companies, licenses, profiles, templates, permissions, backup and settings tabs. |
| Company | Company Settings | Done | Company settings screen and live company rows. |
| Users | Employee/User Master | Done | User master/list. |
| Role Permissions | Developer Console | Done | Role permission editor posts to `role_permissions`. |
| Financial Years | Administration Hub | Done | Live financial-year rows. |
| Print Settings | Developer Console | Done | Print-template editor, PDF preview, HTML/CSS export and print defaults. |
| Backup | Developer Console | Done | JSON backup, encrypted `.pgst`, restore with typed confirmation and pre-restore safety backup. |
| LAN Setup | Developer Console | Done | Desktop mode removes XAMPP/LAN dependency; setup values remain visible. |
| Dashboard Settings | Developer Console | Done | Settings editor for app/dashboard values. |

## Conversion Workflows

| PRM_GST route | Desktop target | Status | Notes |
|---|---|---|---|
| order_doc_convert_sale | Document Center / Order Conversions | Posted | Converts quotation, sales order, or delivery challan to posted sales bill, marks source document converted, and posts stock/GST/ledger rows. |
| order_doc_convert_purchase | Document Center / Order Conversions | Posted | Converts purchase order to posted purchase invoice with supplier invoice number, marks source PO converted, and posts stock/GST/ledger rows. |

## Current Remaining Completion Passes

| Area | Remaining work |
|---|---|
| Sales/Purchase Returns | Source-bill selection and one-click return loading are done; next optional refinement is separate item-wise return authorization workflow. |
| Document Templates | Visual preview/export is now done; advanced drag/drop column designer is still optional future enhancement. |
| GST Integrations | Offline E-Invoice/E-Way JSON preparation is done; live government API submission requires client API credentials. |
| Full Report Printouts | CSV and PDF export are done for Report Center; specialized statutory layouts can be refined per client format. |
