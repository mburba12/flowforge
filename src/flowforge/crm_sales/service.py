from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.phase2a.enums import PartyKind
from flowforge.phase2a.models import Organization, Party, PartyRoleAssignment, Person
from flowforge.phase2a.normalization import normalize_name
from flowforge.phase3b.models import SalesOrder
from flowforge.platform.numbering import next_number
from flowforge.platform.services import record_change

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405


class CRMService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx

    async def save(self, o, e):
        self.db.add(o)
        await self.db.flush()
        await record_change(self.db, self.ctx.tenant_id, self.ctx.user_id, "created", e, str(o.id))
        await self.db.commit()
        await self.db.refresh(o)
        return o

    async def lead(self, b):
        return await self.save(Lead(tenant_id=self.ctx.tenant_id, **b.model_dump()), "crm_lead")

    async def opportunity(self, b):
        return await self.save(
            Opportunity(tenant_id=self.ctx.tenant_id, **b.model_dump()), "crm_opportunity"
        )

    async def quote(self, b):
        subtotal = Decimal("0")
        discount = Decimal("0")
        q = Quote(
            tenant_id=self.ctx.tenant_id,
            quote_number=b.quote_number,
            party_id=b.party_id,
            opportunity_id=b.opportunity_id,
            currency_code=b.currency_code,
            valid_until=b.valid_until,
        )
        self.db.add(q)
        await self.db.flush()
        for line in b.lines:
            gross = line.quantity * line.unit_price
            disc = (gross * Decimal(line.discount_bps) / Decimal(10000)).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )
            total = gross - disc
            subtotal += gross
            discount += disc
            self.db.add(
                QuoteLine(
                    tenant_id=self.ctx.tenant_id,
                    quote_id=q.id,
                    line_total=total,
                    **line.model_dump(),
                )
            )
        q.subtotal = subtotal
        q.discount_total = discount
        q.total = subtotal - discount
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, "created", "crm_quote", str(q.id)
        )
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def transition_quote(self, qid, target, reason=None):
        q = await self.db.scalar(
            select(Quote).where(Quote.id == qid, Quote.tenant_id == self.ctx.tenant_id)
        )
        if not q:
            raise LookupError("Quote not found")
        allowed = {
            "draft": {"submitted", "cancelled"},
            "submitted": {"approved", "rejected"},
            "approved": {"accepted", "expired"},
            "accepted": {"converted"},
        }
        if target not in allowed.get(q.status, set()):
            raise ValueError(f"Invalid quote transition {q.status}->{target}")
        if target == "approved":
            q.approved_by = self.ctx.user_id
        q.status = target
        await record_change(
            self.db, self.ctx.tenant_id, self.ctx.user_id, target, "crm_quote", str(q.id)
        )
        await self.db.commit()
        return q

    async def convert_lead(self, lid):
        lead = await self.db.scalar(
            select(Lead).where(Lead.id == lid, Lead.tenant_id == self.ctx.tenant_id)
        )
        if not lead or lead.status == "converted":
            raise ValueError("Lead unavailable for conversion")
        # The customer becomes a master-data party: an organization when the lead names a
        # company, otherwise a person; numbered from the tenant's party sequence.
        name = lead.company_name or lead.contact_name
        p = Party(
            tenant_id=self.ctx.tenant_id,
            party_number=await next_number(self.db, self.ctx.tenant_id, "party"),
            kind=PartyKind.ORGANIZATION if lead.company_name else PartyKind.PERSON,
            display_name=name,
            normalized_name=normalize_name(name),
            status="active",
        )
        self.db.add(p)
        await self.db.flush()
        if lead.company_name:
            self.db.add(
                Organization(
                    tenant_id=self.ctx.tenant_id, party_id=p.id, legal_name=lead.company_name
                )
            )
        else:
            given, _, family = lead.contact_name.strip().partition(" ")
            self.db.add(
                Person(
                    tenant_id=self.ctx.tenant_id,
                    party_id=p.id,
                    given_name=given or lead.contact_name,
                    family_name=family or given or lead.contact_name,
                )
            )
        self.db.add(
            PartyRoleAssignment(tenant_id=self.ctx.tenant_id, party_id=p.id, role="customer")
        )
        lead.status = "converted"
        lead.converted_party_id = p.id
        await self.db.commit()
        return {"lead_id": str(lead.id), "party_id": str(p.id)}

    async def credit_check(self, party_id, amount):
        c = await self.db.scalar(
            select(CreditProfile).where(
                CreditProfile.party_id == party_id, CreditProfile.tenant_id == self.ctx.tenant_id
            )
        )
        if not c:
            return {"approved": False, "reason": "No credit profile"}
        approved = c.status == "active" and c.current_exposure + amount <= c.credit_limit
        return {
            "approved": approved,
            "available": c.credit_limit - c.current_exposure,
            "reason": None if approved else c.hold_reason or "Credit limit exceeded",
        }

    async def dashboard(self):
        async def count(m, *c):
            return int(
                (
                    await self.db.scalar(
                        select(func.count())
                        .select_from(m)
                        .where(m.tenant_id == self.ctx.tenant_id, *c)
                    )
                )
                or 0
            )

        pipeline = await self.db.scalar(
            select(
                func.coalesce(func.sum(Opportunity.amount * Opportunity.probability / 100), 0)
            ).where(
                Opportunity.tenant_id == self.ctx.tenant_id,
                Opportunity.stage.notin_(["won", "lost"]),
            )
        )
        return {
            "leads": await count(Lead, Lead.status != "converted"),
            "open_opportunities": await count(
                Opportunity, Opportunity.stage.notin_(["won", "lost"])
            ),
            "pipeline_weighted": pipeline or 0,
            "draft_quotes": await count(Quote, Quote.status == "draft"),
            "active_campaigns": await count(Campaign, Campaign.status == "active"),
        }

    async def order_status(self, party_id):
        rows = list(
            (
                await self.db.scalars(
                    select(SalesOrder)
                    .where(
                        SalesOrder.tenant_id == self.ctx.tenant_id,
                        SalesOrder.customer_id == party_id,
                    )
                    .order_by(SalesOrder.order_date.desc())
                )
            ).all()
        )
        return [
            {
                "order_id": str(x.id),
                "order_number": x.order_number,
                "status": x.status,
                "total_amount": x.total_amount,
                "order_date": x.order_date,
            }
            for x in rows
        ]
