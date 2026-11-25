from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .catalog import PROVIDERS
from .models import FinanceConnection, FinanceDocument, FinanceSyncRun, FinanceWebhookEvent
from .providers import SandboxFinanceProvider
from .schemas import FinanceConnectionCreate, FinanceWebhookIngest


class FinanceIntegrationError(Exception):
    pass


class FinanceIntegrationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def provider(self, code: str) -> SandboxFinanceProvider:
        if code not in PROVIDERS:
            raise FinanceIntegrationError("Unsupported finance provider")
        return SandboxFinanceProvider(code)

    async def connect(self, data: FinanceConnectionCreate) -> FinanceConnection:
        definition = PROVIDERS.get(data.provider)
        if definition is None:
            raise FinanceIntegrationError("Unsupported finance provider")
        org_id, name = await self.provider(data.provider).connect(data.authorization_code)
        row = FinanceConnection(
            tenant_id=self.tenant_id,
            provider=data.provider,
            provider_family=definition.family,
            external_organization_id=org_id,
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
            select(FinanceConnection).where(
                FinanceConnection.id == connection_id, FinanceConnection.tenant_id == self.tenant_id
            )
        )
        if connection is None:
            raise FinanceIntegrationError("Finance connection not found")
        run = FinanceSyncRun(
            tenant_id=self.tenant_id,
            connection_id=connection.id,
            sync_type="incremental",
            status="running",
        )
        self.db.add(run)
        await self.db.flush()
        documents, cursor = await self.provider(connection.provider).documents(
            connection.external_organization_id, connection.cursor
        )
        created = 0
        for doc in documents:
            existing = await self.db.scalar(
                select(FinanceDocument).where(
                    FinanceDocument.tenant_id == self.tenant_id,
                    FinanceDocument.connection_id == connection.id,
                    FinanceDocument.document_type == doc.document_type,
                    FinanceDocument.external_document_id == doc.document_id,
                )
            )
            if existing is None:
                self.db.add(
                    FinanceDocument(
                        tenant_id=self.tenant_id,
                        connection_id=connection.id,
                        document_type=doc.document_type,
                        external_document_id=doc.document_id,
                        document_number=doc.number,
                        status=doc.status,
                        subtotal=doc.total,
                        tax_total=0,
                        total=doc.total,
                        balance=doc.total,
                        currency_code=doc.currency,
                        document_date=datetime.fromisoformat(doc.document_date),
                        summary={"sandbox": True},
                    )
                )
                created += 1
        connection.cursor = cursor
        connection.last_sync_at = datetime.now(UTC)
        run.documents_created = created
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        await self.db.commit()
        return {"documents_created": created}

    async def webhook(self, connection_id: UUID, data: FinanceWebhookIngest) -> FinanceWebhookEvent:
        connection = await self.db.scalar(
            select(FinanceConnection).where(
                FinanceConnection.id == connection_id, FinanceConnection.tenant_id == self.tenant_id
            )
        )
        if connection is None:
            raise FinanceIntegrationError("Finance connection not found")
        if not await self.provider(connection.provider).verify_webhook(
            data.payload.encode(), data.signature
        ):
            raise FinanceIntegrationError("Invalid webhook signature")
        existing = await self.db.scalar(
            select(FinanceWebhookEvent).where(
                FinanceWebhookEvent.provider == connection.provider,
                FinanceWebhookEvent.provider_event_id == data.provider_event_id,
            )
        )
        if existing is not None:
            if existing.tenant_id != self.tenant_id:
                raise FinanceIntegrationError("Webhook event tenant mismatch")
            return existing
        event = FinanceWebhookEvent(
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
