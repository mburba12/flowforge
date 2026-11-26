# Unified Implementation Plan

## Baseline
- Alembic: `ff_all_apis_delta_001`
- Public tables: 561
- Tenant tables: 556
- Forced-RLS tables: 557
- New-table tenant isolation: 289/289
- Backend tests: 280

## Architecture
Every request follows:

`Entra identity -> session membership -> server tenant -> entitlement -> permission -> transaction-local RLS -> domain service -> audit -> outbox -> response`

The browser never controls tenant IDs, approval state, permissions, audit columns, execution state, or provider activation.

## Workstreams

### A. Secure runtime
- Async SQLAlchemy and `flowforge_app`
- server tenant context
- Entra OIDC with PKCE
- token signature, issuer, audience, expiry checks
- MFA and step-up claims
- permission and entitlement dependencies
- idempotency, optimistic locking, common problem details

### B. Shared services
- immutable audit
- workflows and approvals
- task/work queues
- notifications
- files, quarantine, and jobs
- transactional outbox with Azure Service Bus adapter

### C. Financial core
- GL, journal validation/posting/reversal
- AP vendor/requisition/PO/receipt/bill/match/payment proposal
- AR customer/quote/order/invoice/cash application/dispute
- reconciliations and close

### D. Operations
- item/warehouse/bin/lot/serial
- inventory movements, availability, history, counts, valuation
- BOM, MRP, work orders, yield and scrap
- shipping rates, labels, tracking, returns and claims

### E. People and payroll
- workforce lifecycle, time, leave, training
- payroll configuration and gross-to-net adapter
- validation, approval, release, reversal and reconciliation
- benefits and retirement
- read-only provider learning, code mapping, parallel runs and cutover

### F. Banking and tax
- bank connectivity, transactions and reconciliation
- payment proposals, dual approval, release and reversal
- tax obligations, filings, notices and reconciliation

### G. Documents and intelligence
- upload, malware scan, OCR, classify, extract, versions and retention
- permission-aware global and semantic search
- reports, exports, dashboards and forecasts
- FlowForge AI with tenant grounding, citations and read-only default

### H. Enterprise expansion
- QMS, CAPA, nonconformance, complaints, supplier quality
- ISO 13485, ISO 14971 and 21 CFR Part 11 controls
- projects, job costing and fixed assets
- customer, vendor, worker and auditor portals
- SaaS billing and support tickets

### I. Frontend completion
For every module: list -> details -> draft -> edit -> submit -> approve -> execute -> reconcile -> history.
A button is complete only when it reaches the API, persists, audits, survives refresh, handles errors, and passes Playwright.

### J. Local and Azure deployment
Local substitutes:
- PostgreSQL 16
- Redis 7
- Azurite
- Mailpit
- local worker

Azure promotion:
- Container Apps
- PostgreSQL Flexible Server
- Service Bus
- Blob Storage
- Key Vault
- Application Insights
- Log Analytics
- ACR
- Entra ID
- GitHub Actions OIDC

## Build sequence
1. Runtime authentication and tenancy
2. Audit/outbox/workflow/tasks/files/jobs
3. GL/AP/AR/orders/reconciliation
4. Inventory/manufacturing/shipping
5. Workforce/payroll/benefits/provider learning
6. Banking/tax
7. Documents/search/reporting/AI
8. QMS/projects/assets/portals/billing/support
9. Full frontend wiring
10. Recovery/security/capacity/pilot and Azure activation

## Acceptance gates for every workstream
- Ruff, formatting, MyPy and compile
- pytest and API integration
- migration upgrade and disposable downgrade
- forced-RLS inventory and two-tenant campaign
- permission, audit, idempotency and stale-version tests
- TypeScript, unit tests, Next build and Playwright
- clean working tree, commit and annotated tag
