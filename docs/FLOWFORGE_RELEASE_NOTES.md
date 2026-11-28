# FlowForge release notes (release scope: GL, AP, AR & orders, inventory, payroll, tax, administration)

Sign in at **http://127.0.0.1:3000**. Every workspace is under the left-hand menu
(`/modules/<name>`). Buttons you are not permitted to use are disabled and say which
permission they need; every business rule is enforced by the server, so the UI can
never bypass it.

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
return cannot approve it.

Extended workspaces follow the same pattern: every role can read; Clerks prepare
(create and update); Approvers decide (approve, post, close, release, reverse, and moving a
record to a decided state such as approved, won or paid). Governance & controls and
Integrations are changed only by Owners and Managers.

## Known limitations

* Extended workspaces use generated forms: identifiers (for example a vendor or worker)
  are entered as record ids, which you can copy from the Records tab. Purpose-built
  screens exist for the release areas above.
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
