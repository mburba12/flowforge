from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_db

from .schemas import JurisdictionCreate, TaxCalculate, TaxElectionCreate, TaxRuleCreate
from .service import TaxEngineError, TaxEngineService

router = APIRouter(prefix="/api/v4b", tags=["phase4b-tax"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_db)]


def service(p: P, db: D) -> TaxEngineService:
    return TaxEngineService(db, p.tenant_id)


S = Annotated[TaxEngineService, Depends(service)]


@router.post("/jurisdictions", status_code=201)
async def jurisdiction(b: JurisdictionCreate, s: S) -> dict[str, str]:
    x = await s.jurisdiction(b)
    return {"id": str(x.id), "code": x.code}


@router.post("/tax-rules", status_code=201)
async def rule(b: TaxRuleCreate, s: S) -> dict[str, str]:
    try:
        x = await s.rule(b)
    except TaxEngineError as e:
        raise HTTPException(404, str(e)) from e
    return {"id": str(x.id), "code": x.code, "version": str(x.version)}


@router.post("/worker-elections", status_code=201)
async def election(b: TaxElectionCreate, s: S) -> dict[str, str]:
    x = await s.election(b)
    return {"id": str(x.id), "filing_status": x.filing_status}


@router.post("/calculate", status_code=201)
async def calculate(b: TaxCalculate, s: S) -> dict[str, str]:
    try:
        x = await s.calculate(b)
    except TaxEngineError as e:
        raise HTTPException(409, str(e)) from e
    return {
        "id": str(x.id),
        "employee_amount": str(x.employee_amount),
        "employer_amount": str(x.employer_amount),
        "explanation": x.explanation,
    }
