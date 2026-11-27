# Backend live workflow coverage

The current repository already contains domain contract and workflow tests for finance, reconciliation, CRM, commerce, workforce, payroll/tax, authorization, documents, search, events, integration, and security. Phase B composes these under one runner rather than duplicating business logic.

Required regression suites: full `tests/`, API tenant isolation, four-tenant RLS, backup/restore, migration rehearsal, and controlled failure recovery. External-provider sandbox workflows remain Phase I.
