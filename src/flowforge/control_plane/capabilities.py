from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import StrEnum
from importlib.util import find_spec
from typing import Final
class Status(StrEnum): IMPLEMENTED='implemented'; PARTIAL='partial'; BLOCKED='blocked'
@dataclass(frozen=True,slots=True)
class Capability:
 code:str; implementation:str; status:Status=Status.IMPLEMENTED; tenant_scoped:bool=True; audit_required:bool=True; write_enabled:bool=True
 def available(self)->bool:return find_spec(self.implementation) is not None
 def to_dict(self)->dict[str,object]:return {**asdict(self),'available':self.available()}
CAPABILITIES:Final= (
 Capability('tenancy','flowforge.phase1.tenancy'),Capability('identity','flowforge.phase1.identity'),Capability('sessions','flowforge.phase1a.sessions'),Capability('mfa','flowforge.phase1a.mfa'),Capability('authorization','flowforge.phase1.authorization'),Capability('rbac','flowforge.phase1a.rbac'),Capability('workflow','flowforge.phase1.workflow'),Capability('audit','flowforge.phase1a.audit'),Capability('documents','flowforge.phase1.documents'),Capability('events','flowforge.phase1.events'),Capability('outbox','flowforge.phase1a.outbox'),Capability('notifications','flowforge.phase1.notifications'),Capability('integrations','flowforge.phase1.integrations',write_enabled=False),Capability('search','flowforge.phase1.search'),Capability('analytics','flowforge.phase1.analytics'),Capability('operations','flowforge.phase1.operations'),Capability('support','flowforge.phase4c_stage7',Status.PARTIAL),)
def registry()->dict[str,Capability]:return {x.code:x for x in CAPABILITIES}
