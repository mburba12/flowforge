import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError

from flowforge.api.router import api_router
from flowforge.catalog.router import router as catalog_router
from flowforge.integration.router import router as phase1_router
from flowforge.part2a.resource_router import router as part2a_resource_router
from flowforge.part2b.router import router as part2b_router
from flowforge.phase2a.router import router as phase2a_router
from flowforge.phase2b.posting import PostingError
from flowforge.phase2b.router import router as phase2b_router
from flowforge.phase3a.router import router as phase3a_router
from flowforge.phase3b.router import router as phase3b_router
from flowforge.phase3final.router import router as phase3_final_router
from flowforge.phase4a.router import router as phase4a_router
from flowforge.phase4a_stage2.router import router as phase4a_stage2_router
from flowforge.phase4a_stage3.router import router as phase4a_stage3_router
from flowforge.phase4b.router import router as phase4b_router
from flowforge.phase4b_stage2.router import router as phase4b_stage2_router
from flowforge.phase4c.router import router as phase4c_router
from flowforge.phase4c_stage2.router import router as phase4c_stage2_router
from flowforge.phase4c_stage3.router import router as phase4c_stage3_router
from flowforge.phase4c_stage4.router import router as phase4c_stage4_router
from flowforge.phase4c_stage5.router import router as phase4c_stage5_router
from flowforge.phase4c_stage6.router import router as phase4c_stage6_router
from flowforge.phase4c_stage7.router import router as phase4c_stage7_router
from flowforge.phase4d.router import router as phase4d_router
from flowforge.phase4e.router import router as phase4e_router
from flowforge.phase4f.router import router as phase4f_router
from flowforge.phase4g.router import router as phase4g_router
from flowforge.phase4h.router import router as phase4h_router
from flowforge.phase4i.router import router as phase4i_router
from flowforge.phase4j.router import router as phase4j_router
from flowforge.phase5a.router import router as phase5a_router
from flowforge.phase5b.router import router as phase5b_router
from flowforge.platform.authorization import enforce, sync_standard_roles
from flowforge.release.admin_routes import router as release_admin_router
from flowforge.release.read_routes import router as release_read_router
from flowforge.resource_contracts.router import router as resource_contract_router
from flowforge.support_feedback import router as support_feedback_router

logger = logging.getLogger("flowforge")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Bring every tenant's standard roles up to the current permission catalog.
    try:
        added = await sync_standard_roles()
        logger.info("RBAC standard roles synchronised: %s", added)
    except Exception:  # noqa: BLE001 - never block startup; health checks report the database
        logger.exception("RBAC standard role synchronisation failed")
    yield


app = FastAPI(
    lifespan=lifespan,
    title="FlowForge API",
    version="1.0.0-phase1",
    description="Complete Phase 1 platform foundation",
    # Role-based access control for every release-scope endpoint (deny by default).
    dependencies=[Depends(enforce)],
)


@app.exception_handler(PostingError)
async def posting_error_handler(_: Request, exc: PostingError) -> JSONResponse:
    # Ledger rule violations (closed period, unbalanced, unpostable account) are
    # client-correctable conflicts, never server errors.
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    # Constraint violations (unknown reference, duplicate key) are reported as
    # conflicts without exposing database internals.
    logger.warning("Integrity constraint violation: %s", type(exc.orig).__name__)
    return JSONResponse(
        status_code=409,
        content={"detail": "The request conflicts with existing or missing reference data"},
    )


@app.exception_handler(LookupError)
async def lookup_error_handler(_: Request, exc: LookupError) -> JSONResponse:
    # Services raise plain LookupError for "record not found". Subclasses such as
    # KeyError/IndexError are programming errors and stay server errors.
    if type(exc) is not LookupError:
        raise exc
    return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    # Services raise plain ValueError for business-rule violations (invalid state change,
    # insufficient stock, ...). Library subclasses stay server errors.
    if type(exc) is not ValueError:
        raise exc
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(DBAPIError)
async def data_error_handler(_: Request, exc: DBAPIError) -> JSONResponse:
    # SQLSTATE class 22 = data exception (value too long, invalid number/date format).
    sqlstate = str(
        getattr(exc.orig, "sqlstate", "")
        or getattr(getattr(exc.orig, "__cause__", None), "sqlstate", "")
        or ""
    )
    if not sqlstate.startswith("22"):
        raise exc
    logger.warning("Data exception %s: %s", sqlstate, type(exc.orig).__name__)
    return JSONResponse(
        status_code=422,
        content={"detail": "A value is too long or has an invalid format for its field"},
    )


async def domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    # Business-rule errors defined by FlowForge modules are client-correctable conflicts.
    name = type(exc).__name__
    status = 404 if "NotFound" in name else 409
    return JSONResponse(status_code=status, content={"detail": str(exc)})


def register_domain_errors(application: FastAPI) -> list[str]:
    """Map every exception class defined in a loaded flowforge module to 404/409."""
    registered: list[str] = []
    for module_name, module in list(sys.modules.items()):
        if not module_name.startswith("flowforge.") or module is None:
            continue
        for obj in list(vars(module).values()):
            if (
                isinstance(obj, type)
                and issubclass(obj, Exception)
                and obj.__module__ == module_name
                and not issubclass(obj, HTTPException)
                and obj is not PostingError
            ):
                application.add_exception_handler(obj, domain_error_handler)
                registered.append(f"{module_name}.{obj.__name__}")
    return registered


# Release-scope completion routes first, so their GET paths take precedence.
app.include_router(release_admin_router)
app.include_router(release_read_router)
app.include_router(api_router)
app.include_router(phase1_router)
app.include_router(phase2a_router)
app.include_router(phase2b_router)
app.include_router(phase3a_router)
app.include_router(phase3b_router)
app.include_router(phase3_final_router)
app.include_router(phase4a_router)
app.include_router(phase4a_stage2_router)
app.include_router(phase4a_stage3_router)
app.include_router(phase4b_router)
app.include_router(phase4b_stage2_router)
app.include_router(phase4c_router)
app.include_router(phase4c_stage2_router)
app.include_router(phase4c_stage3_router)
app.include_router(phase4c_stage4_router)
app.include_router(phase4c_stage5_router)
app.include_router(phase4c_stage6_router)
app.include_router(phase4c_stage7_router)
app.include_router(phase4d_router)
app.include_router(phase4e_router)
app.include_router(phase4f_router)
app.include_router(phase4g_router)
app.include_router(phase4h_router)
app.include_router(phase4i_router)
app.include_router(phase4j_router)
app.include_router(phase5a_router)
app.include_router(phase5b_router)

app.include_router(support_feedback_router)
app.include_router(catalog_router)

app.include_router(part2a_resource_router)

app.include_router(part2b_router)

app.include_router(resource_contract_router)

DOMAIN_ERRORS = register_domain_errors(app)
