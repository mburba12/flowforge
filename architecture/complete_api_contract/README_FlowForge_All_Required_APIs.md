# FlowForge Complete Required API Package

Generated operations: **1,756**

Contents:
- `FlowForge_All_Required_APIs.openapi.json`: complete target OpenAPI contract
- `FlowForge_All_Required_APIs_Manifest.csv`: endpoint inventory
- `flowforge_all_required_apis.py`: runnable FastAPI contract server and generic tenant-scoped dispatcher

This package is the complete API **contract and implementation scaffold** for every FlowForge feature area. It is not a claim that regulated calculations, provider credentials, payment rails, tax filing, payroll filing, QMS validation, or production authentication can be safely completed by generic handlers. Those operations still require domain services, third-party credentials, legal validation, controls, migrations, tests, and deployment evidence.

Mandatory production controls for every mutation: validated Entra identity, server-derived tenant context, permission checks, forced PostgreSQL RLS, idempotency, audit events, state-machine validation, step-up authentication for consequential actions, and provider confirmation/reconciliation.

## Database schemas and migration

This package adds 307 SQLAlchemy tenant tables, Pydantic schemas, PostgreSQL DDL, forced RLS policies, and Alembic revision `ff_all_apis_001` after `f174aad30e21`.
