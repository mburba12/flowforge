from datetime import UTC, date, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .catalog import PROVIDERS
from .models import (
    PayrollRun,
    WorkforceConnection,
    WorkforceSyncRun,
    WorkforceWebhookEvent,
)
from .providers import SandboxWorkforceProvider
from .schemas import WorkforceConnectionCreate, WorkforceWebhookIngest


class WorkforceIntegrationError(Exception):
    pass


class WorkforceIntegrationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def provider(self, code: str) -> SandboxWorkforceProvider:
        if code not in PROVIDERS:
            raise WorkforceIntegrationError("Unsupported workforce provider")
        return SandboxWorkforceProvider(code)

    async def connect(self, data: WorkforceConnectionCreate) -> WorkforceConnection:
        definition = PROVIDERS.get(data.provider)
        if definition is None:
            raise WorkforceIntegrationError("Unsupported workforce provider")
        organization_id, name = await self.provider(data.provider).connect(data.authorization_code)
        row = WorkforceConnection(
            tenant_id=self.tenant_id,
            provider=data.provider,
            provider_family=definition.family,
            external_organization_id=organization_id,
            organization_name=name,
            credential_state="SANDBOX_CREDENTIAL_NOT_PERSISTED",
            environment="sandbox",
            status="connected",
            connected_by=self.user_id,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def sync(self, connection_id: UUID) -> dict[str, int]:
        connection = await self.db.scalar(
            select(WorkforceConnection).where(
                WorkforceConnection.id == connection_id,
                WorkforceConnection.tenant_id == self.tenant_id,
            )
        )
        if connection is None:
            raise WorkforceIntegrationError("Workforce connection not found")
        run = WorkforceSyncRun(
            tenant_id=self.tenant_id,
            connection_id=connection.id,
            sync_type="incremental",
            status="running",
        )
        self.db.add(run)
        await self.db.flush()
        payroll_runs, cursor = await self.provider(connection.provider).payroll_runs(
            connection.external_organization_id,
            connection.cursor,
        )
        created = 0
        for payroll in payroll_runs:
            existing = await self.db.scalar(
                select(PayrollRun).where(
                    PayrollRun.tenant_id == self.tenant_id,
                    PayrollRun.connection_id == connection.id,
                    PayrollRun.external_payroll_run_id == payroll.run_id,
                )
            )
            if existing is None:
                self.db.add(
                    PayrollRun(
                        tenant_id=self.tenant_id,
                        connection_id=connection.id,
                        external_payroll_run_id=payroll.run_id,
                        period_start=date.fromisoformat(payroll.pay_date),
                        period_end=date.fromisoformat(payroll.pay_date),
                        pay_date=date.fromisoformat(payroll.pay_date),
                        status=payroll.status,
                        gross_pay=payroll.gross_pay,
                        employee_taxes=0,
                        employer_taxes=0,
                        deductions=payroll.gross_pay - payroll.net_pay,
                        net_pay=payroll.net_pay,
                        currency_code=payroll.currency,
                    )
                )
                created += 1
        connection.cursor = cursor
        connection.last_sync_at = datetime.now(UTC)
        run.payroll_runs_created = created
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        await self.db.commit()
        return {"payroll_runs_created": created}

    async def webhook(
        self, connection_id: UUID, data: WorkforceWebhookIngest
    ) -> WorkforceWebhookEvent:
        connection = await self.db.scalar(
            select(WorkforceConnection).where(
                WorkforceConnection.id == connection_id,
                WorkforceConnection.tenant_id == self.tenant_id,
            )
        )
        if connection is None:
            raise WorkforceIntegrationError("Workforce connection not found")
        valid = await self.provider(connection.provider).verify_webhook(
            data.payload.encode(),
            data.signature,
        )
        if not valid:
            raise WorkforceIntegrationError("Invalid webhook signature")
        existing = await self.db.scalar(
            select(WorkforceWebhookEvent).where(
                WorkforceWebhookEvent.provider == connection.provider,
                WorkforceWebhookEvent.provider_event_id == data.provider_event_id,
            )
        )
        if existing is not None:
            if existing.tenant_id != self.tenant_id:
                raise WorkforceIntegrationError("Webhook event tenant mismatch")
            return existing
        event = WorkforceWebhookEvent(
            tenant_id=self.tenant_id,
            connection_id=connection.id,
            provider=connection.provider,
            provider_event_id=data.provider_event_id,
            event_type=data.event_type,
            signature_valid=True,
            processed=True,
            payload_digest=sha256(data.payload.encode()).hexdigest(),
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event
