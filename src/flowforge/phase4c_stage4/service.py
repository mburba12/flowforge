from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .catalog import PROVIDERS
from .models import (
    LogisticsConnection,
    LogisticsSyncRun,
    LogisticsWebhookEvent,
    Shipment,
    TrackingEvent,
)
from .providers import SandboxLogisticsProvider
from .schemas import LogisticsConnectionCreate, LogisticsWebhookIngest


class LogisticsIntegrationError(Exception):
    pass


class LogisticsIntegrationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def provider(self, code: str) -> SandboxLogisticsProvider:
        if code not in PROVIDERS:
            raise LogisticsIntegrationError("Unsupported logistics provider")
        return SandboxLogisticsProvider(code)

    async def connect(self, data: LogisticsConnectionCreate) -> LogisticsConnection:
        definition = PROVIDERS.get(data.provider)
        if definition is None:
            raise LogisticsIntegrationError("Unsupported logistics provider")
        account_id, name = await self.provider(data.provider).connect(data.authorization_code)
        row = LogisticsConnection(
            tenant_id=self.tenant_id,
            provider=data.provider,
            provider_family=definition.family,
            external_account_id=account_id,
            account_name=name,
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
            select(LogisticsConnection).where(
                LogisticsConnection.id == connection_id,
                LogisticsConnection.tenant_id == self.tenant_id,
            )
        )
        if connection is None:
            raise LogisticsIntegrationError("Logistics connection not found")
        run = LogisticsSyncRun(
            tenant_id=self.tenant_id,
            connection_id=connection.id,
            sync_type="incremental",
            status="running",
        )
        self.db.add(run)
        await self.db.flush()
        shipment = await self.db.scalar(
            select(Shipment).where(
                Shipment.tenant_id == self.tenant_id,
                Shipment.connection_id == connection.id,
                Shipment.external_shipment_id == f"shipment_{connection.provider}_001",
            )
        )
        created = 0
        if shipment is None:
            shipment = Shipment(
                tenant_id=self.tenant_id,
                connection_id=connection.id,
                external_shipment_id=f"shipment_{connection.provider}_001",
                service_code="sandbox_ground",
                status="in_transit",
                tracking_number_mask="...1234",
                origin_country="US",
                destination_country="US",
                weight_grams=1000,
                shipped_at=datetime.now(UTC),
                metadata_summary={"sandbox": True},
            )
            self.db.add(shipment)
            await self.db.flush()
            created = 1
        events, _ = await self.provider(connection.provider).tracking(
            connection.external_account_id, None
        )
        event_created = 0
        for event in events:
            existing = await self.db.scalar(
                select(TrackingEvent).where(
                    TrackingEvent.tenant_id == self.tenant_id,
                    TrackingEvent.provider == connection.provider,
                    TrackingEvent.external_event_id == event.event_id,
                )
            )
            if existing is None:
                self.db.add(
                    TrackingEvent(
                        tenant_id=self.tenant_id,
                        shipment_id=shipment.id,
                        provider=connection.provider,
                        external_event_id=event.event_id,
                        status_code=event.status_code,
                        description=event.description,
                        occurred_at=datetime.fromisoformat(event.occurred_at),
                    )
                )
                event_created += 1
        run.shipments_created = created
        run.tracking_events_created = event_created
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        await self.db.commit()
        return {"shipments_created": created, "tracking_events_created": event_created}

    async def webhook(
        self, connection_id: UUID, data: LogisticsWebhookIngest
    ) -> LogisticsWebhookEvent:
        connection = await self.db.scalar(
            select(LogisticsConnection).where(
                LogisticsConnection.id == connection_id,
                LogisticsConnection.tenant_id == self.tenant_id,
            )
        )
        if connection is None:
            raise LogisticsIntegrationError("Logistics connection not found")
        if not await self.provider(connection.provider).verify_webhook(
            data.payload.encode(), data.signature
        ):
            raise LogisticsIntegrationError("Invalid webhook signature")
        existing = await self.db.scalar(
            select(LogisticsWebhookEvent).where(
                LogisticsWebhookEvent.provider == connection.provider,
                LogisticsWebhookEvent.provider_event_id == data.provider_event_id,
            )
        )
        if existing is not None:
            if existing.tenant_id != self.tenant_id:
                raise LogisticsIntegrationError("Webhook event tenant mismatch")
            return existing
        event = LogisticsWebhookEvent(
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
