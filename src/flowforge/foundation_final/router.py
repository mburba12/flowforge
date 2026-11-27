import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.foundation_completion.models import (
    AccessReview,
    DataQualityIssue,
    StewardshipTask,
    SupportGrant,
)
from flowforge.phase1a.tenancy import TenantContext

from .models import *
from .schemas import *
from .service import FinalFoundationService

router = APIRouter(prefix="/api/v2/foundation-final", tags=["foundation-final"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D):
    return FinalFoundationService(db, TenantContext(p.tenant_id, p.user_id))


def fail(e):
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/requirements/dependencies", status_code=201)
async def dependency(b: DependencyCreate, s: Annotated[FinalFoundationService, Depends(svc)]):
    if b.requirement_id == b.depends_on_id:
        raise HTTPException(422, "Self-dependency forbidden")
    o = RequirementDependency(requirement_id=b.requirement_id, depends_on_id=b.depends_on_id)
    s.db.add(o)
    await s.db.commit()
    return o


@router.post("/artifacts/classify", status_code=201)
async def classify(b: ArtifactClassify, s: Annotated[FinalFoundationService, Depends(svc)]):
    o = ArtifactClassification(
        artifact_path=b.artifact_path,
        classification=b.classification,
        requirement_id=b.requirement_id,
        reviewed=True,
    )
    s.db.add(o)
    await s.db.commit()
    return o


@router.post("/delegations", status_code=201)
async def delegation(b: DelegationCreate, s: Annotated[FinalFoundationService, Depends(svc)]):
    if b.grantor_id == b.delegate_id or b.expires_at <= b.starts_at:
        raise HTTPException(422, "Invalid delegation")
    return await s.save(
        DelegatedAccess(
            tenant_id=s.ctx.tenant_id,
            grantor_id=b.grantor_id,
            delegate_id=b.delegate_id,
            scope_json=json.dumps(b.scope),
            starts_at=b.starts_at,
            expires_at=b.expires_at,
        ),
        "delegated_access",
    )


@router.post("/approval-limits", status_code=201)
async def limit(b: ApprovalLimitCreate, s: Annotated[FinalFoundationService, Depends(svc)]):
    return await s.save(
        ApprovalLimit(tenant_id=s.ctx.tenant_id, **b.model_dump()), "approval_limit"
    )


@router.post("/sod-rules", status_code=201)
async def sod(b: SodCreate, s: Annotated[FinalFoundationService, Depends(svc)]):
    if b.permission_a == b.permission_b:
        raise HTTPException(422, "Permissions must differ")
    return await s.save(SodRule(tenant_id=s.ctx.tenant_id, **b.model_dump()), "sod_rule")


@router.post("/access-reviews/{id}/decide")
async def review(id: UUID, b: Decision, s: Annotated[FinalFoundationService, Depends(svc)]):
    try:
        return await s.decide(AccessReview, id, b.decision, b.reason)
    except Exception as e:
        raise fail(e) from e


@router.post("/support-grants/{id}/revoke")
async def revoke(id: UUID, b: Decision, s: Annotated[FinalFoundationService, Depends(svc)]):
    return await s.decide(SupportGrant, id, "revoke", b.reason)


@router.post("/stewardship/{id}/decide")
async def stewardship(id: UUID, b: Decision, s: Annotated[FinalFoundationService, Depends(svc)]):
    return await s.decide(StewardshipTask, id, b.decision, b.reason)


@router.post("/quality-issues/{id}/resolve")
async def issue(id: UUID, b: Decision, s: Annotated[FinalFoundationService, Depends(svc)]):
    return await s.decide(DataQualityIssue, id, "remediate", b.reason)


@router.post("/imports", status_code=201)
async def imp(b: ImportCreate, s: Annotated[FinalFoundationService, Depends(svc)]):
    return await s.import_job(b)


@router.post("/lineage", status_code=201)
async def lineage(b: LineageCreate, s: Annotated[FinalFoundationService, Depends(svc)]):
    return await s.save(LineageEdge(tenant_id=s.ctx.tenant_id, **b.model_dump()), "lineage_edge")


@router.post("/search/index", status_code=201)
async def index(b: IndexCreate, s: Annotated[FinalFoundationService, Depends(svc)]):
    return await s.index(b)


@router.post("/organization-units/{unit_id}/parent/{parent_id}")
async def reparent(
    unit_id: UUID, parent_id: UUID, s: Annotated[FinalFoundationService, Depends(svc)]
):
    try:
        return await s.hierarchy_reparent(unit_id, parent_id)
    except Exception as e:
        raise fail(e) from e
