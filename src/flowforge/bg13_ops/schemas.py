from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    run_type: str = Field(
        pattern="^(migration|backup|restore|rollback|dr_rehearsal|sast|dast|dependency_scan|container_scan|secret_scan|incident_drill)$"
    )
    evidence: dict = {}


class RunComplete(BaseModel):
    status: str = Field(pattern="^(passed|failed|blocked)$")
    result: dict = {}
