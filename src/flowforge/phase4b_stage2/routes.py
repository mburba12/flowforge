from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import (
    Principal,
    current_principal,
)
from flowforge.db.session import get_tenant_db

from .schemas import (
    TaxLiabilityCreate,
    TaxNoticeCreate,
    TaxRemittanceCreate,
    TaxReturnCreate,
)
from .service import (
    TaxFilingError,
    TaxFilingService,
)

router = APIRouter(
    prefix="/api/v4b",
    tags=["phase4b-filing"],
)

PrincipalDependency = Annotated[
    Principal,
    Depends(current_principal),
]
DatabaseDependency = Annotated[
    AsyncSession,
    Depends(get_tenant_db),
]


def service(
    principal: PrincipalDependency,
    db: DatabaseDependency,
) -> TaxFilingService:
    return TaxFilingService(
        db,
        principal.tenant_id,
        principal.user_id,
    )


ServiceDependency = Annotated[
    TaxFilingService,
    Depends(service),
]


@router.post("/liabilities", status_code=201)
async def create_liability(
    body: TaxLiabilityCreate,
    filing: ServiceDependency,
) -> dict[str, str]:
    liability = await filing.liability(body)

    return {
        "id": str(liability.id),
        "status": liability.status,
        "open_amount": str(liability.open_amount),
    }


@router.post("/returns", status_code=201)
async def create_return(
    body: TaxReturnCreate,
    filing: ServiceDependency,
) -> dict[str, str]:
    tax_return = await filing.tax_return(body)

    return {
        "id": str(tax_return.id),
        "status": tax_return.status,
        "total_tax": str(tax_return.total_tax),
    }


@router.post("/returns/{return_id}/approve")
async def approve_return(
    return_id: UUID,
    filing: ServiceDependency,
) -> dict[str, str]:
    try:
        tax_return = await filing.approve_return(return_id)
    except TaxFilingError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(tax_return.id),
        "status": tax_return.status,
    }


@router.post(
    "/returns/{return_id}/remit",
    status_code=201,
)
async def remit_return(
    return_id: UUID,
    body: TaxRemittanceCreate,
    filing: ServiceDependency,
) -> dict[str, str]:
    try:
        remittance = await filing.remit(
            return_id,
            body,
        )
    except TaxFilingError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(remittance.id),
        "status": remittance.status,
        "amount": str(remittance.amount),
    }


@router.post("/notices", status_code=201)
async def create_notice(
    body: TaxNoticeCreate,
    filing: ServiceDependency,
) -> dict[str, str]:
    notice = await filing.notice(body)

    return {
        "id": str(notice.id),
        "status": notice.status,
    }


@router.post("/notices/{notice_id}/resolve")
async def resolve_notice(
    notice_id: UUID,
    filing: ServiceDependency,
    resolution: str = Query(min_length=1),
) -> dict[str, str]:
    try:
        notice = await filing.resolve_notice(
            notice_id,
            resolution,
        )
    except TaxFilingError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "id": str(notice.id),
        "status": notice.status,
    }


@router.post("/reconcile")
async def reconcile_tax(
    authority_id: UUID,
    tax_payable_account_id: UUID,
    filing: ServiceDependency,
) -> dict[str, str]:
    reconciliation = await filing.reconcile(
        authority_id,
        tax_payable_account_id,
    )

    return {
        "id": str(reconciliation.id),
        "status": reconciliation.status,
        "subledger_total": str(reconciliation.subledger_total),
        "gl_total": str(reconciliation.gl_total),
    }
