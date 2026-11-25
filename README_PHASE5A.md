# FlowForge Phase 5A Product and Platform Integration
One dependency-safe overlay containing the production web shell, 23 module workspaces, Entra/MSAL configuration, tenant-safe API client, onboarding, entitlements, Copilot/document/reconciliation/approval workspaces, billing and tenant lifecycle foundations, 12 tenant-owned backend tables, tests, and verification scripts.

External production credentials and irreversible execution remain disabled. Run backend gates first, then `npm ci`, `npm run typecheck`, `npm test`, `npm run build`, and Playwright in `web`.
