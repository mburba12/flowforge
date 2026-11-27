from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase1a.tenancy import TenantContext

from .models import *  # noqa: F403, F405
from .schemas import *  # noqa: F403, F405
from .service import BG08Service

router = APIRouter(prefix="/api/v2/bg08/final", tags=["bg08-final"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def svc(p: P, db: D):
    return BG08Service(db, TenantContext(p.tenant_id, p.user_id))


def fail(e):
    return HTTPException(404 if isinstance(e, LookupError) else 409, str(e))


@router.post("/plans", status_code=201)
async def plan(b: PlanCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(Plan(tenant_id=s.ctx.tenant_id, **b.model_dump()), "billing_plan")


@router.post("/subscriptions", status_code=201)
async def sub(b: SubscriptionCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.subscription(b)


@router.post("/subscriptions/{id}/action")
async def sub_action(id: UUID, b: Action, s: Annotated[BG08Service, Depends(svc)]):
    return await s.subscription_action(id, b.target, b.reason)


@router.post("/subscriptions/{id}/entitlements", status_code=201)
async def entitlement(id: UUID, b: EntitlementCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(
        Entitlement(tenant_id=s.ctx.tenant_id, subscription_id=id, **b.model_dump()), "entitlement"
    )


@router.post("/usage", status_code=201)
async def usage(b: UsageCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.usage(b)


@router.post("/billing-runs", status_code=201)
async def billing(b: BillingRunCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.billing_run(b)


@router.post("/projects", status_code=201)
async def project(b: ProjectCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(Project(tenant_id=s.ctx.tenant_id, **b.model_dump()), "project")


@router.post("/projects/{id}/tasks", status_code=201)
async def task(id: UUID, b: TaskCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(
        ProjectTask(tenant_id=s.ctx.tenant_id, project_id=id, **b.model_dump()), "project_task"
    )


@router.post("/projects/{id}/time", status_code=201)
async def time(id: UUID, b: TimeCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(
        ProjectTime(tenant_id=s.ctx.tenant_id, project_id=id, **b.model_dump()), "project_time"
    )


@router.post("/projects/{id}/expenses", status_code=201)
async def expense(id: UUID, b: ExpenseCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(
        ProjectExpense(tenant_id=s.ctx.tenant_id, project_id=id, **b.model_dump()),
        "project_expense",
    )


@router.post("/projects/{id}/change-orders", status_code=201)
async def change(id: UUID, b: ChangeCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(
        ChangeOrder(tenant_id=s.ctx.tenant_id, project_id=id, **b.model_dump()), "change_order"
    )


@router.get("/projects/{id}/profitability")
async def profitability(id: UUID, s: Annotated[BG08Service, Depends(svc)]):
    return await s.project_profitability(id)


@router.post("/asset-books", status_code=201)
async def book(b: BookCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(AssetBook(tenant_id=s.ctx.tenant_id, **b.model_dump()), "asset_book")


@router.post("/asset-books/{id}/depreciate")
async def depreciate(id: UUID, s: Annotated[BG08Service, Depends(svc)]):
    return await s.depreciation(id)


@router.post("/asset-transactions", status_code=201)
async def asset_txn(b: AssetTxnCreate, s: Annotated[BG08Service, Depends(svc)]):
    return await s.save(
        AssetTransaction(tenant_id=s.ctx.tenant_id, **b.model_dump()), "asset_transaction"
    )
