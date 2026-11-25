from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .catalog import PROVIDERS
from .models import CommerceConnection, CommerceOrder, CommerceSyncRun, CommerceWebhookEvent
from .providers import SandboxCommerceProvider
from .schemas import CommerceConnectionCreate, CommerceWebhookIngest


class CommerceIntegrationError(Exception):
    pass


class CommerceIntegrationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def provider(self, code: str) -> SandboxCommerceProvider:
        if code not in PROVIDERS:
            raise CommerceIntegrationError("Unsupported commerce provider")
        return SandboxCommerceProvider(code)

    async def connect(self, data: CommerceConnectionCreate) -> CommerceConnection:
        definition = PROVIDERS.get(data.provider)
        if definition is None:
            raise CommerceIntegrationError("Unsupported commerce provider")
        store_id, store_name = await self.provider(data.provider).connect(data.authorization_code)
        row = CommerceConnection(
            tenant_id=self.tenant_id,
            provider=data.provider,
            provider_family=definition.family,
            external_store_id=store_id,
            store_name=store_name,
            store_domain=data.store_domain,
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
            select(CommerceConnection).where(
                CommerceConnection.id == connection_id,
                CommerceConnection.tenant_id == self.tenant_id,
            )
        )
        if connection is None:
            raise CommerceIntegrationError("Commerce connection not found")
        if connection.credential_state != "SANDBOX_CREDENTIAL_NOT_PERSISTED":
            raise CommerceIntegrationError("Invalid sandbox credential state")
        run = CommerceSyncRun(
            tenant_id=self.tenant_id, connection_id=connection.id, sync_type="incremental"
        )
        self.db.add(run)
        await self.db.flush()
        orders, cursor = await self.provider(connection.provider).orders(
            connection.external_store_id, connection.cursor
        )
        created = updated = 0
        for order in orders:
            existing = await self.db.scalar(
                select(CommerceOrder).where(
                    CommerceOrder.tenant_id == self.tenant_id,
                    CommerceOrder.connection_id == connection.id,
                    CommerceOrder.external_order_id == order.order_id,
                )
            )
            if existing is None:
                self.db.add(
                    CommerceOrder(
                        tenant_id=self.tenant_id,
                        connection_id=connection.id,
                        external_order_id=order.order_id,
                        order_number=order.order_number,
                        order_status=order.status,
                        financial_status="paid",
                        fulfillment_status="unfulfilled",
                        subtotal=order.total,
                        discount_total=0,
                        shipping_total=0,
                        tax_total=0,
                        fee_total=0,
                        grand_total=order.total,
                        currency_code=order.currency,
                        placed_at=datetime.fromisoformat(order.placed_at),
                        raw_summary={"sandbox": True},
                    )
                )
                created += 1
            else:
                updated += 1
        connection.cursor = cursor
        connection.last_sync_at = datetime.now(UTC)
        run.orders_created = created
        run.orders_updated = updated
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        await self.db.commit()
        return {"orders_created": created, "orders_updated": updated}

    async def webhook(
        self, connection_id: UUID, data: CommerceWebhookIngest
    ) -> CommerceWebhookEvent:
        connection = await self.db.scalar(
            select(CommerceConnection).where(
                CommerceConnection.id == connection_id,
                CommerceConnection.tenant_id == self.tenant_id,
            )
        )
        if connection is None:
            raise CommerceIntegrationError("Commerce connection not found")
        valid = await self.provider(connection.provider).verify_webhook(
            data.payload.encode(), data.signature
        )
        if not valid:
            raise CommerceIntegrationError("Invalid webhook signature")
        existing = await self.db.scalar(
            select(CommerceWebhookEvent).where(
                CommerceWebhookEvent.provider == connection.provider,
                CommerceWebhookEvent.provider_event_id == data.provider_event_id,
            )
        )
        if existing is not None:
            if existing.tenant_id != self.tenant_id:
                raise CommerceIntegrationError("Webhook event tenant mismatch")
            return existing
        event = CommerceWebhookEvent(
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
