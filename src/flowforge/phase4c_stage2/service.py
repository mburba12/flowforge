from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    PaymentConnection,
    PaymentWebhookEvent,
    ProcessorFee,
    ProcessorPayment,
    ProcessorPayout,
)
from .provider import PaymentProvider
from .providers import SandboxSquareProvider, SandboxStripeProvider
from .schemas import PaymentConnectionCreate, WebhookIngest


class PaymentIntegrationError(Exception):
    pass


class PaymentIntegrationService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def provider(self, name: str) -> PaymentProvider:
        if name == "stripe_sandbox":
            return SandboxStripeProvider()
        if name == "square_sandbox":
            return SandboxSquareProvider()
        raise PaymentIntegrationError("Production payment providers require Key Vault credentials")

    async def connect(self, data: PaymentConnectionCreate) -> PaymentConnection:
        provider = self.provider(data.provider)
        account_id, merchant_id = await provider.connect(data.authorization_code)
        item = PaymentConnection(
            tenant_id=self.tenant_id,
            provider=data.provider,
            provider_account_id=account_id,
            provider_merchant_id=merchant_id,
            credential_state="SANDBOX_CREDENTIAL_NOT_PERSISTED",
            environment="sandbox",
            status="connected",
            connected_by=self.user_id,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def sync(self, connection_id: UUID) -> dict[str, int]:
        connection = await self.db.scalar(
            select(PaymentConnection).where(
                PaymentConnection.id == connection_id, PaymentConnection.tenant_id == self.tenant_id
            )
        )
        if connection is None:
            raise PaymentIntegrationError("Payment connection not found")
        if connection.credential_state != "SANDBOX_CREDENTIAL_NOT_PERSISTED":
            raise PaymentIntegrationError("Invalid sandbox credential state")
        provider = self.provider(connection.provider)
        created_payments = created_payouts = 0
        for payment in await provider.list_payments(connection.provider_account_id):
            existing = await self.db.scalar(
                select(ProcessorPayment).where(
                    ProcessorPayment.tenant_id == self.tenant_id,
                    ProcessorPayment.provider == connection.provider,
                    ProcessorPayment.provider_payment_id == payment.payment_id,
                )
            )
            if existing is None:
                row = ProcessorPayment(
                    tenant_id=self.tenant_id,
                    payment_connection_id=connection.id,
                    provider=connection.provider,
                    provider_payment_id=payment.payment_id,
                    amount=payment.amount,
                    currency_code=payment.currency,
                    status=payment.status,
                    payment_method_type=payment.method_type,
                    card_brand=payment.card_brand,
                    card_last4=payment.card_last4,
                    payment_date=datetime.fromisoformat(payment.occurred_at),
                    livemode=False,
                )
                self.db.add(row)
                await self.db.flush()
                self.db.add(
                    ProcessorFee(
                        tenant_id=self.tenant_id,
                        processor_payment_id=row.id,
                        provider_fee_id=f"fee_{payment.payment_id}",
                        fee_type="processing",
                        amount=__import__("decimal").Decimal("3.00"),
                        currency_code=payment.currency,
                        assessed_at=datetime.fromisoformat(payment.occurred_at),
                    )
                )
                created_payments += 1
        for payout in await provider.list_payouts(connection.provider_account_id):
            existing = await self.db.scalar(
                select(ProcessorPayout).where(
                    ProcessorPayout.tenant_id == self.tenant_id,
                    ProcessorPayout.provider == connection.provider,
                    ProcessorPayout.provider_payout_id == payout.payout_id,
                )
            )
            if existing is None:
                self.db.add(
                    ProcessorPayout(
                        tenant_id=self.tenant_id,
                        payment_connection_id=connection.id,
                        provider=connection.provider,
                        provider_payout_id=payout.payout_id,
                        gross_amount=payout.gross,
                        fee_amount=payout.fees,
                        net_amount=payout.net,
                        currency_code=payout.currency,
                        arrival_date=datetime.fromisoformat(payout.arrival_at),
                        status=payout.status,
                    )
                )
                created_payouts += 1
        await self.db.commit()
        return {"payments_created": created_payments, "payouts_created": created_payouts}

    async def webhook(self, connection_id: UUID, data: WebhookIngest) -> PaymentWebhookEvent:
        connection = await self.db.scalar(
            select(PaymentConnection).where(
                PaymentConnection.id == connection_id, PaymentConnection.tenant_id == self.tenant_id
            )
        )
        if connection is None:
            raise PaymentIntegrationError("Payment connection not found")
        valid = await self.provider(connection.provider).verify_webhook(
            data.payload.encode(), data.signature
        )
        if not valid:
            raise PaymentIntegrationError("Invalid webhook signature")
        existing = await self.db.scalar(
            select(PaymentWebhookEvent).where(
                PaymentWebhookEvent.provider == connection.provider,
                PaymentWebhookEvent.provider_event_id == data.provider_event_id,
            )
        )
        if existing is not None:
            if existing.tenant_id != self.tenant_id:
                raise PaymentIntegrationError("Webhook event tenant mismatch")
            return existing
        event = PaymentWebhookEvent(
            tenant_id=self.tenant_id,
            payment_connection_id=connection.id,
            provider=connection.provider,
            provider_event_id=data.provider_event_id,
            event_type=data.event_type,
            signature_valid=True,
            processed=True,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event
