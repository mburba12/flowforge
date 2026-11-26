# Local-first and Azure deployment

Local services use PostgreSQL 16, Redis 7, Azurite, Mailpit, FastAPI and Next.js. Start with `scripts/Start-FlowForgeLocal.ps1`; stop with `scripts/Stop-FlowForgeLocal.ps1`.

Azure promotion uses the existing Bicep modules under `infra/bicep`: Azure Container Apps, Azure Database for PostgreSQL Flexible Server, Azure Service Bus, Azure Blob Storage, Azure Key Vault, Azure Container Registry, Application Insights, Log Analytics and Microsoft Entra ID. Domain code must depend on adapters, not Azure SDKs directly.

External writes remain disabled until sandbox credentials and acceptance gates exist. This includes payroll release, bank payments, tax filing, shipping-label purchase, electronic signatures and high-risk AI actions.
