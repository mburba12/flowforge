# FlowForge Phase 1 Completion Boundary

This source package preserves the existing FlowForge architecture and completes the verified Phase 1 bootstrap and acceptance defects found during live recovery.

## Included corrections

- Tenant-scoped `user_roles` bootstrap association.
- Tenant-scoped `role_permissions` bootstrap association.
- Duplicate bootstrap conflicts return HTTP 409 after rollback.
- Unique acceptance tenant and email for every run.
- Acceptance restricted to development, test, or local environments.
- Backend, frontend, build, and Playwright gates use real native exit codes.
- Marked acceptance tenant cleanup and zero-record verification.

## Acceptance command

From the repository root, with the API and frontend running:

```powershell
$env:FLOWFORGE_ENV = "development"
$env:FLOWFORGE_TEST_PASSWORD = "<strong test password>"
.\scripts\acceptance\Invoke-FlowForgeAcceptance.ps1
```

The success line is authoritative only when the script emits it after every required gate passes.

## Deliberately disabled

Real payment execution, payroll release, tax filing, shipping-label purchase, provider writes, and high-risk AI actions remain disabled until their own credentials and acceptance gates exist.
