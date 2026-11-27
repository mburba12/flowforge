from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase1a.tenancy import TenantContext
from flowforge.platform.services import record_change

from .models import *  # noqa: F403, F405


class WorkforceService:
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

    async def get(self, m, id):
        x = await self.db.scalar(select(m).where(m.id == id, m.tenant_id == self.ctx.tenant_id))
        if not x:
            raise LookupError("Record not found")
        return x

    async def candidate(self, b):
        if not b.consent:
            raise ValueError("Candidate consent required")
        return await self.save(
            Candidate(
                tenant_id=self.ctx.tenant_id,
                consent_at=datetime.now(UTC),
                **b.model_dump(exclude={"consent"}),
            ),
            "candidate",
        )

    async def application_action(self, id, target, reason):
        x = await self.get(Application, id)
        allowed = {
            "applied": {"screening", "rejected"},
            "screening": {"interview", "rejected"},
            "interview": {"offer", "rejected"},
            "offer": {"hired", "rejected"},
        }
        if target not in allowed.get(x.stage, set()):
            raise ValueError("Invalid application transition")
        if target == "rejected" and not reason:
            raise ValueError("Rejection reason required")
        x.stage = target
        x.rejection_reason = reason if target == "rejected" else None
        await self._event("application.stage_changed", "application", x.id, {"stage": target})
        await self.db.commit()
        return x

    async def offer_action(self, id, target):
        x = await self.get(Offer, id)
        allowed = {
            "draft": {"submitted", "cancelled"},
            "submitted": {"approved", "rejected"},
            "approved": {"accepted", "declined"},
        }
        if target not in allowed.get(x.status, set()):
            raise ValueError("Invalid offer transition")
        if target == "approved":
            x.approved_by = self.ctx.user_id
        if target == "accepted":
            x.accepted_at = datetime.now(UTC)
        x.status = target
        await self.db.commit()
        return x

    async def review_action(self, id, target):
        x = await self.get(PerformanceReview, id)
        allowed = {
            "draft": {"submitted"},
            "submitted": {"acknowledged", "returned"},
            "returned": {"draft"},
            "acknowledged": {"completed"},
        }
        if target not in allowed.get(x.status, set()):
            raise ValueError("Invalid review transition")
        x.status = target
        await self.db.commit()
        return x

    async def complete_enrollment(self, id, score):
        x = await self.get(Enrollment, id)
        course = await self.get(Course, x.course_id)
        x.status = "completed"
        x.score = score
        x.completed_at = datetime.now(UTC)
        x.expires_on = (
            (datetime.now(UTC) + timedelta(days=course.validity_days)).date()
            if course.validity_days
            else None
        )
        await self.db.commit()
        return x

    async def dashboard(self):
        async def c(m, *conds):
            return int(
                (
                    await self.db.scalar(
                        select(func.count())
                        .select_from(m)
                        .where(m.tenant_id == self.ctx.tenant_id, *conds)
                    )
                )
                or 0
            )

        return {
            "open_positions": await c(Position, Position.status == "open"),
            "active_candidates": await c(Candidate, Candidate.status == "active"),
            "open_applications": await c(
                Application, Application.stage.notin_(["hired", "rejected"])
            ),
            "pending_reviews": await c(PerformanceReview, PerformanceReview.status != "completed"),
            "training_due": await c(Enrollment, Enrollment.status != "completed"),
            "active_benefits": await c(BenefitEnrollment, BenefitEnrollment.status == "active"),
        }

    async def _event(self, t, a, id, p):
        self.db.add(
            WorkforceEvent(
                tenant_id=self.ctx.tenant_id,
                event_type=t,
                aggregate_type=a,
                aggregate_id=id,
                payload_json=json.dumps(p, default=str),
            )
        )

    async def list(self, m):
        return list(
            (await self.db.scalars(select(m).where(m.tenant_id == self.ctx.tenant_id))).all()
        )
