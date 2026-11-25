# FlowForge Phase 4D-4J Master Build

This package contains seven dependency-ordered waves. Production writes remain disabled throughout the scaffold. The master runner defaults to validation-only. Use `-ApplyMigrations` only after integrating router/model imports and reviewing generated migrations. Use `-CreateCheckpoints` only with a clean branch and after live acceptance has been added for the local project.

## Waves
- 4D canonical identity and lineage
- 4E reconciliation and scorecards
- 4F Copilot/document governance
- 4G proposals, approvals, workflows
- 4H controls, observability, recovery
- 4I production activation controls
- 4J release candidate gates

## Safety
The orchestrator stops on the first failure. It does not enable provider writes, payments, payroll submissions, journal posting, messaging, or production credentials.
