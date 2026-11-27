from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import WorkforceService

router = APIRouter(prefix="/api/v2/workforce/final", tags=["workforce-final"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D):
    return WorkforceService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e):
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/positions", status_code=201)
async def position(b: PositionCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(Position(tenant_id=s.ctx.tenant_id, **b.model_dump()), "position")


@router.post("/candidates", status_code=201)
async def candidate(b: CandidateCreate, s: Annotated[WorkforceService, Depends(svc)]):
    try:
        return await s.candidate(b)
    except Exception as e:
        raise fail(e) from e


@router.post("/applications", status_code=201)
async def application(b: ApplicationCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(Application(tenant_id=s.ctx.tenant_id, **b.model_dump()), "application")


@router.post("/applications/{id}/transition")
async def app_action(id: UUID, b: StageAction, s: Annotated[WorkforceService, Depends(svc)]):
    try:
        return await s.application_action(id, b.target, b.reason)
    except Exception as e:
        raise fail(e) from e


@router.post("/offers", status_code=201)
async def offer(b: OfferCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(Offer(tenant_id=s.ctx.tenant_id, **b.model_dump()), "offer")


@router.post("/offers/{id}/transition")
async def offer_action(id: UUID, b: StageAction, s: Annotated[WorkforceService, Depends(svc)]):
    try:
        return await s.offer_action(id, b.target)
    except Exception as e:
        raise fail(e) from e


@router.post("/reviews", status_code=201)
async def review(b: ReviewCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(
        PerformanceReview(tenant_id=s.ctx.tenant_id, **b.model_dump()), "performance_review"
    )


@router.post("/reviews/{id}/transition")
async def review_action(id: UUID, b: StageAction, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.review_action(id, b.target)


@router.post("/goals", status_code=201)
async def goal(b: GoalCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(Goal(tenant_id=s.ctx.tenant_id, **b.model_dump()), "goal")


@router.post("/goals/{id}/progress")
async def progress(id: UUID, b: GoalProgress, s: Annotated[WorkforceService, Depends(svc)]):
    x = await s.get(Goal, id)
    x.progress = b.progress
    x.status = "completed" if b.progress == 100 else "active"
    await s.db.commit()
    return x


@router.post("/courses", status_code=201)
async def course(b: CourseCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(Course(tenant_id=s.ctx.tenant_id, **b.model_dump()), "course")


@router.post("/enrollments", status_code=201)
async def enrollment(b: EnrollmentCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(Enrollment(tenant_id=s.ctx.tenant_id, **b.model_dump()), "enrollment")


@router.post("/enrollments/{id}/complete")
async def complete(id: UUID, score: int, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.complete_enrollment(id, score)


@router.post("/benefit-plans", status_code=201)
async def plan(b: BenefitPlanCreate, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(BenefitPlan(tenant_id=s.ctx.tenant_id, **b.model_dump()), "benefit_plan")


@router.post("/benefit-enrollments", status_code=201)
async def benroll(b: BenefitEnroll, s: Annotated[WorkforceService, Depends(svc)]):
    return await s.save(
        BenefitEnrollment(tenant_id=s.ctx.tenant_id, **b.model_dump()), "benefit_enrollment"
    )


@router.get("/dashboard")
async def dashboard(s: Annotated[WorkforceService, Depends(svc)]):
    return await s.dashboard()
