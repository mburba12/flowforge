from fastapi import FastAPI

from flowforge.api.router import api_router

app = FastAPI(
    title="FlowForge API",
    version="1.0.0-phase1",
    description="Complete Phase 1 platform foundation",
)
app.include_router(api_router)
