from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.crm_sales.models import (
    Activity,
    Campaign,
    CreditProfile,
    Opportunity,
    PortalToken,
    Quote,
    QuoteLine,
)
from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase3b.models import SalesOrder, SalesOrderLine
from flowforge.platform.services import record_change


class CRMFinalService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def get(self, m, id):
        x = await self.db.scalar(select(m).where(m.id == id, m.tenant_id == self.ctx.tenant_id))
        if not x:
            raise LookupError("Record not found")
        return x

    async def list(self, m):
        return list(
            (await self.db.scalars(select(m).where(m.tenant_id == self.ctx.tenant_id))).all()
        )

    async def opportunity(self, id, b):
        x = await self.get(Opportunity, id)
        allowed = {
            "qualification": {"discovery", "lost"},
            "discovery": {"proposal", "lost"},
            "proposal": {"negotiation", "lost"},
            "negotiation": {"won", "lost"},
        }
        if b.stage not in allowed.get(x.stage, set()):
            raise ValueError(f"Invalid stage {x.stage}->{b.stage}")
        if b.stage == "lost" and not b.reason:
            raise ValueError("Lost reason required")
        x.stage = b.stage
        x.probability = 100 if b.stage == "won" else 0 if b.stage == "lost" else b.probability
        x.lost_reason = b.reason if b.stage == "lost" else None
        await self.db.commit()
        return x

    async def complete_activity(self, id):
        x = await self.get(Activity, id)
        x.completed_at = datetime.now(UTC)
        await self.db.commit()
        return x

    async def campaign(self, id, status):
        x = await self.get(Campaign, id)
        allowed = {
            "draft": {"active", "cancelled"},
            "active": {"paused", "completed", "cancelled"},
            "paused": {"active", "completed", "cancelled"},
        }
        if status not in allowed.get(x.status, set()):
            raise ValueError(f"Invalid campaign transition {x.status}->{status}")
        x.status = status
        await self.db.commit()
        return x

    async def quote_to_order(self, id, b):
        q = await self.get(Quote, id)
        if q.status != "accepted":
            raise ValueError("Only accepted quotes convert to orders")
        if q.converted_order_id:
            raise ValueError("Quote already converted")
        lines = await self.list_quote_lines(q.id)
        o = SalesOrder(
            tenant_id=self.ctx.tenant_id,
            order_number=f"SO-{q.quote_number}",
            customer_id=b.customer_id,
            ledger_id=b.ledger_id,
            period_id=b.period_id,
            order_date=b.order_date,
            status="draft",
            total_amount=q.total,
            created_by=self.ctx.user_id,
        )
        self.db.add(o)
        await self.db.flush()
        for quote_line in lines:
            if quote_line.product_id is None:
                raise ValueError("All converted quote lines require product_id")
            self.db.add(
                SalesOrderLine(
                    tenant_id=self.ctx.tenant_id,
                    order_id=o.id,
                    product_id=quote_line.product_id,
                    quantity=quote_line.quantity,
                    unit_price=quote_line.unit_price,
                    line_total=quote_line.line_total,
                )
            )
        q.status = "converted"
        q.converted_order_id = o.id
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "converted", "crm_quote", str(q.id)
        )
        await self.db.commit()
        return {"quote_id": str(q.id), "order_id": str(o.id)}

    async def list_quote_lines(self, qid):
        return list(
            (
                await self.db.scalars(
                    select(QuoteLine).where(
                        QuoteLine.quote_id == qid, QuoteLine.tenant_id == self.ctx.tenant_id
                    )
                )
            ).all()
        )

    async def exposure(self, party_id, delta, reason):
        c = await self.db.scalar(
            select(CreditProfile).where(
                CreditProfile.party_id == party_id, CreditProfile.tenant_id == self.ctx.tenant_id
            )
        )
        if not c:
            raise LookupError("Credit profile not found")
        new = c.current_exposure + delta
        if new < 0:
            raise ValueError("Credit exposure cannot be negative")
        c.current_exposure = new
        if new > c.credit_limit:
            c.status = "hold"
            c.hold_reason = reason or "Credit limit exceeded"
        await self.db.commit()
        return c

    async def issue_portal(self, party_id, minutes):
        token = secrets.token_urlsafe(32)
        h = hashlib.sha256(token.encode()).hexdigest()
        row = PortalToken(
            tenant_id=self.ctx.tenant_id,
            party_id=party_id,
            token_hash=h,
            expires_at=datetime.now(UTC) + timedelta(minutes=minutes),
        )
        self.db.add(row)
        await self.db.commit()
        return {"token": token, "expires_at": row.expires_at}

    async def validate_portal(self, token):
        h = hashlib.sha256(token.encode()).hexdigest()
        row = await self.db.scalar(
            select(PortalToken).where(
                PortalToken.token_hash == h, PortalToken.tenant_id == self.ctx.tenant_id
            )
        )
        if not row or row.revoked_at or row.expires_at <= datetime.now(UTC):
            raise PermissionError("Portal token invalid or expired")
        return {"party_id": str(row.party_id), "expires_at": row.expires_at}
