# FlowForge release notes (release scope: GL, AP, AR & orders, inventory, payroll, tax, administration)

Sign in at **http://127.0.0.1:3000**. Every workspace is under the left-hand menu
(`/modules/<name>`). Buttons you are not permitted to use are disabled and say which
permission they need; every business rule is enforced by the server, so the UI can
never bypass it.

## New: Krov WorkAgent, sign up from the website, pay for what you use

**Krov WorkAgent.** The product is now called Krov WorkAgent, with the Krov logo.

**Sign in with email and password only.** There is no Workspace box any more: Krov
WorkAgent finds your workspace from your email. If one email belongs to several workspaces,
you choose which one after your password is checked. The website's **Log in** button asks
for your email and opens the app's sign-in page with it filled in; passwords are only ever
typed in the app.

**Sign up.** Anyone can create an account from the website or at `/signup`: business name,
name, email and password. They get their own workspace, every feature included, and are
its administrator. Sign-in and sign-up attempts are limited per address to stop guessing.

**Billing & usage** (sidebar, next to Settings). Customers pay only for what they use:
storage and activity. Moving data in and keeping banks, payroll and carriers in sync are
free. The page shows this month's estimated bill, a **cost calculator**, the card on file and
past invoices. On the 1st of each month every customer is emailed an invoice for the month
before; the card on file is charged automatically 3 business days later, and the email says
which card, how much and on what day. Cards are saved on Stripe's secure page, after the
owner agrees to automatic monthly charges. Prices are set at a 70% margin after card fees
(see `docs/KROV_PRICING.md`). Your own workspace is never billed.

**Customize your screen** (Settings). Each person can hide any sidebar section, Home page
part or Home figure they do not use, and show it again any time. It is saved to their
account, so it follows them to any computer. Settings itself always stays visible.

## New: approving your own work, full audit export, record drop-downs

**Approving your own work.** The two-person rule still applies by default: whoever creates
a journal, purchase order, payroll run, tax return, close run or merge proposal cannot
approve it. **Owners** (the account administrator) may approve their own work. To let
someone else do the same, open **Settings → Users**, select the person and choose **Let
them approve their own work** (the "Approves own work" column shows who may). **Require a
second approver** turns it off again. They still need the normal permission to create and
to approve. A custom role can also include the permission `approvals.self_approve`.

**Audit trail export.** The Audit trail page shows the latest 100 changes with when and
who. **Export all changes** downloads every change ever recorded as a CSV spreadsheet
(time, user, action, record type, record, details). Each export is itself recorded.

**Drop-downs in More tools.** Forms under More tools now let you choose customers,
workers, accounts, ledgers, periods, products, warehouses, orders and other records by
name from a list instead of typing record ids (**Enter an id** is still available).
References to outside systems (for example a provider's event id) stay as text.

## Earlier in this release: simpler to use, uploads everywhere, banks, payroll switch, shipments

**A simpler menu.** Everyday work is in five groups: **Money** (Bank accounts, Bills to
pay, Invoices & payments, Accounting, Taxes), **Sales** (Orders, Customers & deals,
Shipments), **Products** (Inventory, Purchasing & warehouse), **People** (Employees,
Payroll), then **Files** and **Settings**. Specialist tools (close and budgets,
reconciliation, reports, payroll filings, HR, manufacturing, governance, audit trail and
more) are folded under **More tools** at the bottom. Each page's raw API actions are
folded under **Advanced** at the bottom of the page.

**Home** shows a setup checklist (connect your bank, move your payroll, connect a
carrier, upload a first file), one-click shortcuts, cash in the bank, what customers owe
you, bills to pay, packages on the way, and payroll and journals waiting on you.

**Upload in every section.** Every page has **Files** and **Upload** at the top right.
Drop invoices, receipts, contracts, statements or photos (PDF, images, spreadsheets,
documents, CSV, OFX/QFX; up to 20 MB each). Files stay with the section they were
uploaded in and are all listed in **Files**. HTML, SVG and scripts are refused.

**Bank accounts.** Three ways to bring a bank in:
* **Connect a bank** — live balances and transactions through Plaid (needs the Plaid keys
  on the server; see the runbook). Use **Refresh** to fetch new transactions.
* **Import a statement** — works with every bank: download the activity as CSV, OFX or
  QFX from the bank's website and import it. Importing the same file twice never
  duplicates anything; the file is kept in Files.
* **Try with demo data** — sample accounts you can disconnect any time.

**Payroll → Move from another provider.** Choose your provider (ADP RUN, ADP Workforce
Now, Paychex Flex, Gusto, QuickBooks Payroll, Rippling, Paylocity, Paycom, Square, OnPay,
Justworks or a spreadsheet), upload its employee export (with year-to-date totals if you
have them), check the preview and import. FlowForge creates the employees with their pay
rates, pay frequency, state and filing status, and carries this year's totals over so
year-end forms stay right. Re-importing updates the same people (a raise becomes a new
pay rate from today). Gusto can also be connected directly when the Gusto keys are set
on the server. Salaried employees are paid salary ÷ pay periods per year.

**Shipments.** Paste any FedEx, UPS, USPS or DHL tracking number (the carrier is detected
automatically) or upload a CSV of tracking numbers. Each business connects its own
carrier account in **Carrier accounts** (API keys from the carrier's developer portal;
FlowForge checks them with the carrier before saving and stores them encrypted). The list
shows what is on the way, out for delivery, delivered or needs attention, with each
package's scan history. Tracking numbers starting with DEMO use sample data.

## Using the workspaces

| Workspace | What you can do |
|---|---|
| Dashboard | Live totals: receivables and payables open, journals and payroll runs awaiting action, open periods, latest orders. |
| Finance & ledger | Create journals (debits must equal credits), approve and post them (a different user must approve), create/close/reopen accounting periods (reopen needs a reason), trial balance with per-account balances, ledgers, chart of accounts, fiscal calendars. |
| Accounts payable | Vendors; purchase orders (create, submit, approve by another user, receive, invoice from the PO); invoices (three-way match, post); open items and payments; reconciliation of AP to the ledger; aging. |
| Accounts receivable / Orders | Customers with credit limits; sales orders with full status history (over-limit orders are put on credit hold); reserve stock; ship and invoice; open items and receipts; aging. |
| Inventory | Products, warehouses, locations, stock on hand and reserved; adjustments, optionally posted to the ledger against an offset account. |
| Payroll / Workforce | Workers with hourly rates; pay groups and pay periods; payroll runs: calculate gross to net, approve (another user), post to the ledger, pay each worker (limited to their net pay), reconcile. |
| Tax | Jurisdictions and versioned rules with effective dates; authorities; liabilities created from a posted payroll run; returns (create, approve by another user, remit and post); reconciliation; calculator. |
| Administration | Invite users with a role, activate/deactivate (takes effect on their next request), assign/remove roles; create custom roles and choose their permissions. |
| Audit | The latest 100 audited changes. |

**Posting to:** workspaces that post to the ledger show a blue bar where you choose the
ledger, the open period and the accounts to use (for example the AP control and cash
accounts). Choose these once per screen before posting, paying or receiving.

## Extended workspaces

Every other part of FlowForge has its own workspace in the menu. Each one lists all of
its operations; choose one to get a form for it (required fields are marked `*`), run
it, and see the server's answer. The **Records** tab lists the workspace's records.

| Workspace | Covers |
|---|---|
| CRM & sales | Leads, conversion, opportunities and stages, quotes and revisions, activities, campaigns and members, price lists, pricing, credit profiles, customer portal users |
| Procurement & logistics | Requisitions (convert to PO), reservations, transfers, inventory counts, landed costs, receiving, fulfilment, shipping rates, labels, manifests, tracking, returns and claims |
| Close, budgets & assets | Close runs, accruals, allocations, recurring journals, budgets, consolidations, reconciliations, payment batches and matching, fixed assets and depreciation, statements and certification |
| Payroll & tax operations | Adjustments, retro pay, garnishments, imports, parallel runs, filings and submissions, tax amendments, payment batches, year-end forms |
| HR & talent | Positions, candidates, applications, offers, interviews and feedback, onboarding, assignments, compensation, benefits and dependants, retirement plans, courses and enrolments, goals and reviews, schedules, timecards, clock events, leave and policies, lifecycle tasks, documents |
| Master data | Parties, contacts, addresses, identifiers, external references, roles, relationships, payment terms, duplicate candidates and merges |
| Subscriptions & projects | Plans, subscriptions, amendments, entitlements and usage, billing runs, projects, tasks, time, expenses, change orders, project billing, asset books |
| Manufacturing & quality | Manufacturing and quality records, their approval/release/closure, lot genealogy |
| Knowledge & copilot | Knowledge records and search, copilot proposals (approve, reject, execute), upload inspection |
| Governance & controls | Entitlements, access reviews, support grants, delegations, approval limits, SoD rules, requirements and lineage, data quality and stewardship, exports and imports |
| Integrations | Banking, payments, commerce, logistics, finance, workforce and engagement provider connections, sync and webhooks |
| Entities, Operations runs | Entity records, relationships, lineage, matching and merges; operational runs |

The finance, payables, receivables, inventory, payroll, workforce, tax and administration
workspaces also have an **All operations** section at the bottom with every operation of
that area, including ones without a purpose-built screen.

## Roles

| Role | Intended for |
|---|---|
| Owner | Full access including users and roles. |
| Manager | Everything except user and role administration. |
| Approver | Read everything; approve POs, journals, payroll runs, tax returns, time; post journals. |
| Clerk | Read everything; create documents (journals, POs, receipts, invoices, orders, receipts, payroll runs, tax liabilities and returns). |
| Viewer | Read only. |

Segregation of duties: the person who creates a journal, purchase order, payroll run or tax
return cannot approve it, unless they are an Owner or were allowed to approve their own
work in Settings → Users.

Extended workspaces follow the same pattern: every role can read; Clerks prepare
(create and update); Approvers decide (approve, post, close, release, reverse, and moving a
record to a decided state such as approved, won or paid). Governance & controls and
Integrations are changed only by Owners and Managers.

## Known limitations

* Extended workspaces use generated forms. Most record fields are drop-downs; a few
  generic ones (for example a parent record that could be of several kinds) are still
  typed as record ids, which you can copy from the Records tab.
* Banking, reconciliation, documents, approvals, work queue, reports and support remain
  read-only record browsers plus their operations.
* Segregation of duties (creator cannot approve) is enforced by the release documents;
  extended areas separate duties by role (Clerk vs Approver), not per document.
* Problem reports are queued in the support outbox unless support email is configured
  (see the runbook).
* Tax reconciliation compares an authority's open liabilities with one payable account;
  liabilities do not record which account they belong to, so reconcile per account.
* Inventory adjustments without ledger details are accepted and do not post (policy
  decision pending).
* Subledger postings (AP, AR, payroll, tax) are approved through their own documents;
  invoice posting and receipts do not require a separate approval step.
* The specification PDFs contain chapter titles only; there are no testable requirements
  beyond the release scope above.
