from fastapi import FastAPI

from flowforge.api.router import api_router
from flowforge.integration.router import router as phase1_router

app = FastAPI(
    title="FlowForge API",
    version="1.0.0-phase1",
    description="Complete Phase 1 platform foundation",
)
app.include_router(api_router)

app.include_router(phase1_router)
