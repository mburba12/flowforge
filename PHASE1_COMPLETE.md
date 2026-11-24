# FlowForge Phase 1 Complete
Implements the platform foundation: tenant bootstrap, login/JWT, users/RBAC data model, tenant-scoped protected APIs, audit and domain events, workflows, document metadata, notifications, integrations, search and analytics schemas.
## Apply to verified scaffold
Back up the existing repository. Copy this package over the repository root, preserving `.env`. Run `scripts\Complete-Phase1.ps1`. If an initial migration already exists, autogenerate creates the incremental Phase 1 completion migration.
## Acceptance
The final verifier must pass. Then start `python -m uvicorn flowforge.main:app --reload` and use `/api/v1/auth/bootstrap` to create the first tenant owner.
