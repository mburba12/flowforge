from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .catalog import PROVIDERS
from .models import (
    EngagementConnection,
    EngagementOpportunity,
    EngagementSyncRun,
    EngagementWebhookEvent,
)
from .providers import SandboxEngagementProvider
from .schemas import (
    EngagementConnectionCreate,
    EngagementWebhookIngest,
)


class EngagementIntegrationError(Exception):
    pass


class EngagementIntegrationService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def provider(
        self,
        code: str,
    ) -> SandboxEngagementProvider:
        if code not in PROVIDERS:
            raise EngagementIntegrationError("Unsupported engagement provider")

        return SandboxEngagementProvider(code)

    async def connect(
        self,
        data: EngagementConnectionCreate,
    ) -> EngagementConnection:
        definition = PROVIDERS.get(data.provider)

        if definition is None:
            raise EngagementIntegrationError("Unsupported engagement provider")

        organization_id, name = await self.provider(data.provider).connect(data.authorization_code)

        existing = await self.db.scalar(
            select(EngagementConnection).where(
                EngagementConnection.tenant_id == self.tenant_id,
                EngagementConnection.provider == data.provider,
                EngagementConnection.external_organization_id == organization_id,
            )
        )

        if existing is not None:
            return existing

        connection = EngagementConnection(
            tenant_id=self.tenant_id,
            provider=data.provider,
            provider_family=definition.family,
            external_organization_id=organization_id,
            organization_name=name,
            credential_state=("SANDBOX_CREDENTIAL_NOT_PERSISTED"),
            environment="sandbox",
            status="connected",
            connected_by=self.user_id,
        )

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)

        return connection

    async def sync(
        self,
        connection_id: UUID,
    ) -> dict[str, int]:
        connection = await self.db.scalar(
            select(EngagementConnection).where(
                EngagementConnection.id == connection_id,
                EngagementConnection.tenant_id == self.tenant_id,
            )
        )

        if connection is None:
            raise EngagementIntegrationError("Engagement connection not found")

        sync_run = EngagementSyncRun(
            tenant_id=self.tenant_id,
            connection_id=connection.id,
            sync_type="incremental",
            status="running",
        )

        self.db.add(sync_run)
        await self.db.flush()

        opportunities, cursor = await self.provider(connection.provider).opportunities(
            connection.external_organization_id,
            connection.cursor,
        )

        opportunities_created = 0

        for opportunity in opportunities:
            existing = await self.db.scalar(
                select(EngagementOpportunity).where(
                    EngagementOpportunity.tenant_id == self.tenant_id,
                    EngagementOpportunity.connection_id == connection.id,
                    EngagementOpportunity.external_opportunity_id == opportunity.opportunity_id,
                )
            )

            if existing is not None:
                continue

            self.db.add(
                EngagementOpportunity(
                    tenant_id=self.tenant_id,
                    connection_id=connection.id,
                    external_opportunity_id=(opportunity.opportunity_id),
                    name=opportunity.name,
                    stage=opportunity.stage,
                    amount=opportunity.amount,
                    currency_code=opportunity.currency,
                )
            )

            opportunities_created += 1

        connection.cursor = cursor
        connection.last_sync_at = datetime.now(UTC)

        sync_run.opportunities_created = opportunities_created
        sync_run.status = "completed"
        sync_run.completed_at = datetime.now(UTC)

        await self.db.commit()

        return {"opportunities_created": opportunities_created}

    async def webhook(
        self,
        connection_id: UUID,
        data: EngagementWebhookIngest,
    ) -> EngagementWebhookEvent:
        connection = await self.db.scalar(
            select(EngagementConnection).where(
                EngagementConnection.id == connection_id,
                EngagementConnection.tenant_id == self.tenant_id,
            )
        )

        if connection is None:
            raise EngagementIntegrationError("Engagement connection not found")

        signature_valid = await self.provider(connection.provider).verify_webhook(
            data.payload.encode(),
            data.signature,
        )

        if not signature_valid:
            raise EngagementIntegrationError("Invalid webhook signature")

        existing = await self.db.scalar(
            select(EngagementWebhookEvent).where(
                EngagementWebhookEvent.provider == connection.provider,
                EngagementWebhookEvent.provider_event_id == data.provider_event_id,
            )
        )

        if existing is not None:
            if existing.tenant_id != self.tenant_id:
                raise EngagementIntegrationError("Webhook event tenant mismatch")

            return existing

        event = EngagementWebhookEvent(
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
