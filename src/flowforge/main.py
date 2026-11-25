from fastapi import FastAPI

from flowforge.api.router import api_router
from flowforge.integration.router import router as phase1_router
from flowforge.phase2a.router import router as phase2a_router
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
from flowforge.support_feedback import router as support_feedback_router

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
