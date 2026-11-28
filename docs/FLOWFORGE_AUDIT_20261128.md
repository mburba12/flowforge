# FlowForge end-to-end audit — 2026-11-28

An audit of every API operation, every workspace and every role, run against the
isolated test stack, then rehearsed on a copy of production before release.
Every finding below was fixed and is covered by a regression test.

## What was audited, and how

| Audit | Method | Result |
|---|---|---|
| No server errors | `tests/extended/test_no_server_errors.py`: every operation, 3 rounds, schema-generated input, restricted DB role | 400 operations, 1,194 calls, **0 server errors** |
| Every operation works | `tests/extended/functional_audit.py` (valid input from real records, ids resolved through the database's foreign keys, second user for approvals) + workflow scenario suites, measured by `tests/extended/operation_coverage.py` | **400 of 401 operations answered successfully**; the one remaining, *create tenant*, is a platform-operator action by design and its refusal is tested |
| Tenant isolation | `tests/extended/isolation_audit.py`: a second tenant calls every operation using the first tenant's real record ids | **No data disclosed**; cross-tenant references now refused by the database |
| Roles | same audit: a Viewer calls every permission-mapped mutating operation | **Refused on all 294** |
| User interface | `web/e2e/ui-audit.spec.ts`: every sidebar workspace as owner, approver and viewer; all 368 operation forms opened | **0 page errors, 0 console errors, 0 error notices** |
| Regression | backend suite, browser suite | **403 backend tests, 62 browser tests passing** |

## Defects found and fixed

| # | Area | Defect | Fix |
|---|---|---|---|
| 1 | Security | Another tenant could store references to your records (quotes on your parties, liabilities on your tax authority, timecards on your workers): PostgreSQL foreign-key checks bypass row-level security. 465 references on 272 tables. | Database trigger on every tenant table refuses references to another tenant's records (migration `ff_security_001`); a test fails if a future table misses it. Production had no such references. |
| 2 | Security | 44 handlers returned raw database error text (table and constraint names) to users. | Database errors go through the global handlers (generic message). |
| 3 | Shipping | Manifests accepted any shipment ids. | Only the tenant's own existing shipments. |
| 4 | CRM | Converting a lead to a customer always failed. | Creates an organization or person, numbered, with the customer role. |
| 5 | CRM | Converting an accepted quote to a sales order always failed. | Goes through the order service: numbered, credit-checked, status history. |
| 6 | Procurement | Requisition → purchase order always failed (no order date, no expense account). | Conversion takes the expense account; PO numbered and dated. |
| 7 | Inventory | Completing a transfer failed when the destination warehouse had no stock yet. | Opens the destination balance at its first location. |
| 8 | Finance | Recurring journals, accruals, allocations and asset postings created unnumbered journals and lines (always failed). | Journal and line numbers assigned. |
| 9 | Finance | Payment batches could never be released (no way to approve them). | New *approve* step (approver permission; items must match the total). |
| 10 | Workforce | Open-ended assignments and compensation (no end date — the normal case) always failed. | Overlap check fixed. |
| 11 | Governance | Data-quality issues could never be raised or resolved (no route). | New *run quality rule* operation. |
| 12 | Knowledge, providers, operations | Creating knowledge records, copilot proposals, provider connections and operations runs failed after saving. | Responses return plain values. |
| 13 | Platform | Business-rule refusals (entitlement limits, locked budgets, creator approving own close run, ...) surfaced as server errors. | Reported as 409 / 403 with the reason. |
| 14 | Web | Every page raised a React hydration error (flash and extra render on load). | Sign-in gate renders identically on server and browser. |
| 15 | Web | Approvers and viewers saw raw "Missing permission" errors in Administration and Audit. | The page explains which permission is needed. |

## By design (not defects)

* **Create tenant** — only platform operators; no tenant role can create tenants.
* **Production payment providers** — need Key Vault credentials; sandbox providers work.
* **Provider webhooks** — accepted only with a valid signature (sandbox: `sandbox-valid-signature`).
* **Free-form record references** — CRM activities and the search index refer to records of any type by id
  (`entity_type` + `entity_id`); storing an id discloses nothing about the record.

## How to re-run

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```powershell
.\.venv\Scripts\python.exe tests\extended\functional_audit.py
```

```powershell
.\.venv\Scripts\python.exe tests\extended\isolation_audit.py
```

(with `FLOWFORGE_DATABASE_URL` pointing at the isolated test database), and the browser
suite from `web` with `npx playwright test`.
