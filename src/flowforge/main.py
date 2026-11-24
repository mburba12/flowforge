from fastapi import FastAPI

from flowforge.api.router import api_router
from flowforge.integration.router import router as phase1_router
from flowforge.phase2a.router import router as phase2a_router
from flowforge.phase2b.router import router as phase2b_router
from flowforge.phase3a.router import router as phase3a_router
from flowforge.phase3b.router import router as phase3b_router
from flowforge.phase3final.router import router as phase3_final_router

app = FastAPI(
    title="FlowForge API",
    version="1.0.0-phase1",
    description="Complete Phase 1 platform foundation",
)
app.include_router(api_router)

app.include_router(phase1_router)

app.include_router(phase2a_router)

app.include_router(phase2b_router)

app.include_router(phase3a_router)

app.include_router(phase3b_router)

app.include_router(phase3_final_router)
