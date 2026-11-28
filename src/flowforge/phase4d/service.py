from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.platform.approval import blocks_self_approval

from .matching import score_match
from .models import (
    CanonicalEntity,
    EntityMatchCandidate,
    EntityMergeEvent,
    EntityMergeMember,
    EntityMergeProposal,
    EntityRelationship,
    ExternalEntityReference,
)
from .normalization import normalize_name
from .schemas import (
    EntityCreate,
    MatchRequest,
    MergeProposalCreate,
    ReferenceCreate,
    RelationshipCreate,
)


class Phase4DError(Exception):
    pass


class Phase4DService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def create_entity(self, data: EntityCreate) -> CanonicalEntity:
        row = CanonicalEntity(
            tenant_id=self.tenant_id,
            entity_type=data.entity_type,
            display_name=data.display_name,
            normalized_name=normalize_name(data.display_name),
            legal_name=data.legal_name,
            status="active",
            confidence_band="low",
            source_count=0,
            canonical_version=1,
            created_by=self.user_id,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_entity(self, entity_id: UUID) -> CanonicalEntity:
        row = await self.db.scalar(
            select(CanonicalEntity).where(
                CanonicalEntity.id == entity_id,
                CanonicalEntity.tenant_id == self.tenant_id,
            )
        )
        if row is None:
            raise Phase4DError("Entity not found")
        return row

    async def add_reference(
        self, entity_id: UUID, data: ReferenceCreate
    ) -> ExternalEntityReference:
        entity = await self.get_entity(entity_id)
        row = ExternalEntityReference(
            tenant_id=self.tenant_id,
            canonical_entity_id=entity.id,
            source_system=data.source_system,
            source_table=data.source_table,
            source_record_id=data.source_record_id,
            external_identifier=data.external_identifier,
            identity_fingerprint=data.identity_fingerprint,
            link_method=data.link_method,
            link_confidence=data.link_confidence,
            linked_by=self.user_id,
        )
        self.db.add(row)
        entity.source_count += 1
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def match(self, data: MatchRequest) -> EntityMatchCandidate | None:
        if data.left_reference_id == data.right_reference_id:
            raise Phase4DError("A reference cannot match itself")
        refs = list(
            (
                await self.db.scalars(
                    select(ExternalEntityReference).where(
                        ExternalEntityReference.tenant_id == self.tenant_id,
                        ExternalEntityReference.id.in_(
                            [data.left_reference_id, data.right_reference_id]
                        ),
                    )
                )
            ).all()
        )
        if len(refs) != 2:
            raise Phase4DError("Reference not found")
        result = score_match(data.signals)
        if result.decision == "none":
            return None
        row = EntityMatchCandidate(
            tenant_id=self.tenant_id,
            left_reference_id=data.left_reference_id,
            right_reference_id=data.right_reference_id,
            score=result.score,
            confidence_band=result.confidence_band,
            matching_signals={name: True for name in result.signals},
            status="pending",
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def create_merge_proposal(self, data: MergeProposalCreate) -> EntityMergeProposal:
        existing = await self.db.scalar(
            select(EntityMergeProposal).where(
                EntityMergeProposal.tenant_id == self.tenant_id,
                EntityMergeProposal.idempotency_key == data.idempotency_key,
            )
        )
        if existing is not None:
            return existing
        ids = set(data.member_entity_ids)
        if data.target_entity_id not in ids:
            raise Phase4DError("Target must be a merge member")
        entities = list(
            (
                await self.db.scalars(
                    select(CanonicalEntity).where(
                        CanonicalEntity.tenant_id == self.tenant_id,
                        CanonicalEntity.id.in_(ids),
                    )
                )
            ).all()
        )
        if len(entities) != len(ids):
            raise Phase4DError("Merge member not found")
        proposal = EntityMergeProposal(
            tenant_id=self.tenant_id,
            target_entity_id=data.target_entity_id,
            status="draft",
            idempotency_key=data.idempotency_key,
            conflict_summary={},
            dry_run_result={"member_count": len(ids)},
            created_by=self.user_id,
        )
        self.db.add(proposal)
        await self.db.flush()
        for entity in entities:
            self.db.add(
                EntityMergeMember(
                    tenant_id=self.tenant_id,
                    proposal_id=proposal.id,
                    entity_id=entity.id,
                    member_role="target" if entity.id == data.target_entity_id else "source",
                    original_status=entity.status,
                )
            )
        self.db.add(
            EntityMergeEvent(
                tenant_id=self.tenant_id,
                proposal_id=proposal.id,
                event_type="created",
                event_payload={"members": len(ids)},
                actor_id=self.user_id,
            )
        )
        await self.db.commit()
        await self.db.refresh(proposal)
        return proposal

    async def approve(self, proposal_id: UUID) -> EntityMergeProposal:
        proposal = await self._proposal(proposal_id)
        if blocks_self_approval(proposal.created_by, self.user_id):
            raise Phase4DError("Creator cannot approve own proposal")
        proposal.status = "approved"
        proposal.approved_by = self.user_id
        proposal.decided_at = datetime.now(UTC)
        self.db.add(
            EntityMergeEvent(
                tenant_id=self.tenant_id,
                proposal_id=proposal.id,
                event_type="approved",
                event_payload={},
                actor_id=self.user_id,
            )
        )
        await self.db.commit()
        return proposal

    async def _proposal(self, proposal_id: UUID) -> EntityMergeProposal:
        row = await self.db.scalar(
            select(EntityMergeProposal).where(
                EntityMergeProposal.id == proposal_id,
                EntityMergeProposal.tenant_id == self.tenant_id,
            )
        )
        if row is None:
            raise Phase4DError("Merge proposal not found")
        return row

    async def create_relationship(self, data: RelationshipCreate) -> EntityRelationship:
        if data.source_entity_id == data.target_entity_id:
            raise Phase4DError("Self relationships are not allowed")
        entities = list(
            (
                await self.db.scalars(
                    select(CanonicalEntity).where(
                        CanonicalEntity.tenant_id == self.tenant_id,
                        CanonicalEntity.id.in_([data.source_entity_id, data.target_entity_id]),
                    )
                )
            ).all()
        )
        if len(entities) != 2:
            raise Phase4DError("Relationship entity not found")
        row = EntityRelationship(
            tenant_id=self.tenant_id,
            source_entity_id=data.source_entity_id,
            target_entity_id=data.target_entity_id,
            relationship_type=data.relationship_type,
            status="active",
            evidence=data.evidence,
            created_by=self.user_id,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row
