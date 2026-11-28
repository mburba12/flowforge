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

## Known limitations

* Extended modules (banking, reconciliation workbench, documents, entities, approvals,
  reports, CRM and other enterprise areas) are available as read-only record browsers;
  their write APIs are not permission-mapped yet.
* Tax reconciliation compares an authority's open liabilities with one payable account;
  liabilities do not record which account they belong to, so reconcile per account.
* Inventory adjustments without ledger details are accepted and do not post (policy
  decision pending).
* Subledger postings (AP, AR, payroll, tax) are approved through their own documents;
  invoice posting and receipts do not require a separate approval step.
* The specification PDFs contain chapter titles only; there are no testable requirements
  beyond the release scope above.
