"""Shipping: connect carrier accounts and see the status of every shipment in one list."""

import csv
import io
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.platform.services import record_change

from . import crypto
from .carriers import CARRIERS, detect_carrier, normalize_number, track, verify
from .http import ProviderError
from .models import CarrierAccount, TrackedShipment

router = APIRouter(prefix="/api/v1/shipping", tags=["shipping"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]

STATUSES = (
    "pending",
    "label_created",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "exception",
    "unknown",
)


class CarrierAccountCreate(BaseModel):
    carrier: str = Field(pattern="^(fedex|ups|usps|dhl)$")
    label: str | None = Field(default=None, max_length=120)
    credentials: dict[str, str] = Field(default_factory=dict)


class ShipmentAdd(BaseModel):
    tracking_number: str = Field(min_length=6, max_length=60)
    carrier: str | None = Field(default=None, pattern="^(fedex|ups|usps|dhl|demo)$")
    reference: str | None = Field(default=None, max_length=200)
    direction: str = Field(default="outbound", pattern="^(outbound|inbound|return)$")


def _account_public(a: CarrierAccount) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "carrier": a.carrier,
        "carrier_name": CARRIERS[a.carrier].name,
        "label": a.label,
        "account_number": a.account_number_mask,
        "status": a.status,
        "last_checked_at": a.last_checked_at.isoformat() if a.last_checked_at else None,
        "last_error": a.last_error,
    }


def _shipment_public(s: TrackedShipment) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "carrier": s.carrier,
        "carrier_name": CARRIERS.get(s.carrier, CARRIERS["demo"]).name,
        "tracking_number": s.tracking_number,
        "reference": s.reference,
        "direction": s.direction,
        "status": s.status,
        "status_detail": s.status_detail,
        "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
        "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None,
        "last_location": s.last_location,
        "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
        "last_refreshed_at": s.last_refreshed_at.isoformat() if s.last_refreshed_at else None,
        "last_error": s.last_error,
        "events": s.events or [],
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


class Shipping:
    def __init__(self, db: AsyncSession, p: Principal):
        self.db, self.p = db, p

    def _context(self, account_id: UUID) -> str:
        return f"{self.p.tenant_id}:carrier:{account_id}"

    async def connect(self, data: CarrierAccountCreate) -> CarrierAccount:
        creds = {k: v.strip() for k, v in data.credentials.items() if isinstance(v, str)}
        allowed = {f.name for f in CARRIERS[data.carrier].fields}
        creds = {k: v for k, v in creds.items() if k in allowed and v}
        if creds.get("environment") not in (None, "production", "sandbox"):
            raise ValueError("Environment must be production or sandbox")
        await verify(data.carrier, creds)
        account = CarrierAccount(
            tenant_id=self.p.tenant_id,
            carrier=data.carrier,
            label=(data.label or CARRIERS[data.carrier].name).strip()[:120],
            account_number_mask=crypto.mask(creds.get("account_number", "")) or None,
            encrypted_credentials="pending",
            status="connected",
            last_checked_at=datetime.now(UTC),
            connected_by=self.p.user_id,
        )
        self.db.add(account)
        await self.db.flush()
        account.encrypted_credentials = crypto.encrypt_json(creds, self._context(account.id))
        await record_change(
            self.db,
            self.p.tenant_id,
            self.p.user_id,
            "connected",
            "carrier_account",
            str(account.id),
            {"carrier": data.carrier},
        )
        await self.db.commit()
        return account

    async def disconnect(self, account_id: UUID) -> None:
        account = await self.db.scalar(
            select(CarrierAccount).where(
                CarrierAccount.id == account_id, CarrierAccount.tenant_id == self.p.tenant_id
            )
        )
        if account is None:
            raise LookupError("Carrier account not found")
        await record_change(
            self.db,
            self.p.tenant_id,
            self.p.user_id,
            "disconnected",
            "carrier_account",
            str(account.id),
            {"carrier": account.carrier},
        )
        await self.db.delete(account)
        await self.db.commit()

    async def _account_for(self, carrier: str) -> CarrierAccount | None:
        return await self.db.scalar(
            select(CarrierAccount)
            .where(
                CarrierAccount.tenant_id == self.p.tenant_id,
                CarrierAccount.carrier == carrier,
                CarrierAccount.status == "connected",
            )
            .order_by(CarrierAccount.created_at)
        )

    async def add(self, data: ShipmentAdd, refresh: bool = True) -> TrackedShipment:
        number = normalize_number(data.tracking_number)
        carrier = data.carrier or detect_carrier(number)
        if carrier is None:
            raise ValueError(
                "Could not tell the carrier from this tracking number; choose the carrier"
            )
        existing = await self.db.scalar(
            select(TrackedShipment).where(
                TrackedShipment.tenant_id == self.p.tenant_id,
                TrackedShipment.carrier == carrier,
                TrackedShipment.tracking_number == number,
            )
        )
        if existing is not None:
            if data.reference and not existing.reference:
                existing.reference = data.reference
            shipment = existing
        else:
            shipment = TrackedShipment(
                tenant_id=self.p.tenant_id,
                carrier=carrier,
                tracking_number=number,
                reference=data.reference,
                direction=data.direction,
                added_by=self.p.user_id,
                created_at=datetime.now(UTC),
                events=[],
            )
            self.db.add(shipment)
            await self.db.flush()
        if refresh:
            await self._refresh(shipment)
        await self.db.commit()
        return shipment

    async def _refresh(self, shipment: TrackedShipment) -> None:
        creds: dict[str, str] = {}
        if shipment.carrier != "demo":
            account = await self._account_for(shipment.carrier)
            if account is None:
                shipment.last_error = (
                    f"Connect your {CARRIERS[shipment.carrier].name} account to see tracking"
                )
                return
            shipment.carrier_account_id = account.id
            creds = {
                k: str(v)
                for k, v in crypto.decrypt_json(
                    account.encrypted_credentials, self._context(account.id)
                ).items()
            }
        try:
            result = await track(
                shipment.carrier, creds, shipment.tracking_number, shipment.created_at
            )
        except (ProviderError, ValueError) as exc:
            shipment.last_error = str(exc)[:500]
            shipment.last_refreshed_at = datetime.now(UTC)
            return
        shipment.status = result.status
        shipment.status_detail = (result.detail or "")[:300] or None
        shipment.estimated_delivery = result.estimated_delivery
        shipment.delivered_at = result.delivered_at
        shipment.last_location = (result.location or "")[:200] or None
        shipment.last_event_at = result.last_event_at
        shipment.events = [
            {k: (str(v) if v is not None else None) for k, v in e.items()} for e in result.events
        ]
        shipment.last_refreshed_at = datetime.now(UTC)
        shipment.last_error = None

    async def shipment(self, shipment_id: UUID) -> TrackedShipment:
        s = await self.db.scalar(
            select(TrackedShipment).where(
                TrackedShipment.id == shipment_id, TrackedShipment.tenant_id == self.p.tenant_id
            )
        )
        if s is None:
            raise LookupError("Shipment not found")
        return s

    async def refresh_one(self, shipment_id: UUID) -> TrackedShipment:
        s = await self.shipment(shipment_id)
        await self._refresh(s)
        await self.db.commit()
        return s

    async def refresh_all(self) -> dict[str, int]:
        rows = list(
            await self.db.scalars(
                select(TrackedShipment)
                .where(
                    TrackedShipment.tenant_id == self.p.tenant_id,
                    TrackedShipment.status != "delivered",
                )
                .order_by(TrackedShipment.last_refreshed_at.asc().nulls_first())
                .limit(100)
            )
        )
        failed = 0
        for s in rows:
            await self._refresh(s)
            failed += 1 if s.last_error else 0
        await self.db.commit()
        return {"refreshed": len(rows) - failed, "failed": failed}


@router.get("/carriers")
async def shipping_carriers(db: D, p: P) -> dict[str, Any]:
    accounts = await db.scalars(
        select(CarrierAccount)
        .where(CarrierAccount.tenant_id == p.tenant_id)
        .order_by(CarrierAccount.created_at)
    )
    return {
        "carriers": [
            {
                "code": c.code,
                "name": c.name,
                "signup_url": c.signup_url,
                "instructions": c.instructions,
                "fields": [
                    {
                        "name": f.name,
                        "label": f.label,
                        "secret": f.secret,
                        "required": f.required,
                        "help": f.help,
                    }
                    for f in c.fields
                ],
            }
            for c in CARRIERS.values()
            if c.code != "demo"
        ],
        "accounts": [_account_public(a) for a in accounts],
    }


@router.post("/accounts", status_code=201)
async def connect_carrier(db: D, p: P, body: CarrierAccountCreate) -> dict[str, Any]:
    return _account_public(await Shipping(db, p).connect(body))


@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_carrier(db: D, p: P, account_id: UUID) -> None:
    await Shipping(db, p).disconnect(account_id)


@router.get("/shipments")
async def list_shipments(
    db: D,
    p: P,
    status: str | None = None,
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 300,
) -> dict[str, Any]:
    q = select(TrackedShipment).where(TrackedShipment.tenant_id == p.tenant_id)
    if status == "active":
        q = q.where(TrackedShipment.status != "delivered")
    elif status:
        q = q.where(TrackedShipment.status == status)
    if search:
        like = f"%{search[:60]}%"
        q = q.where(
            TrackedShipment.tracking_number.ilike(like) | TrackedShipment.reference.ilike(like)
        )
    rows = await db.scalars(q.order_by(TrackedShipment.created_at.desc()).limit(limit))
    counts = dict(
        (
            await db.execute(
                select(TrackedShipment.status, func.count())
                .where(TrackedShipment.tenant_id == p.tenant_id)
                .group_by(TrackedShipment.status)
            )
        ).all()
    )
    return {
        "shipments": [_shipment_public(s) for s in rows],
        "counts": {s: int(counts.get(s, 0)) for s in STATUSES},
    }


@router.post("/shipments", status_code=201)
async def add_shipment(db: D, p: P, body: ShipmentAdd) -> dict[str, Any]:
    return _shipment_public(await Shipping(db, p).add(body))


@router.post("/shipments/import", status_code=201)
async def import_shipments(
    db: D, p: P, file: Annotated[UploadFile, File(description="CSV with a tracking number column")]
) -> dict[str, Any]:
    """Add many shipments at once from a CSV (columns: tracking number, carrier, reference)."""
    text = (await file.read(2 * 1024 * 1024)).decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("The file is empty")
    header = [c.strip().lower().replace("_", " ") for c in rows[0]]
    tracking_col = next((i for i, c in enumerate(header) if "tracking" in c), None)
    if tracking_col is None:
        raise ValueError("The file needs a 'Tracking number' column")
    carrier_col = next((i for i, c in enumerate(header) if c in ("carrier", "carrier code")), None)
    reference_col = next(
        (
            i
            for i, c in enumerate(header)
            if c in ("reference", "order", "order number", "po", "description")
        ),
        None,
    )
    service = Shipping(db, p)
    added, skipped = 0, []
    for number, row in enumerate(rows[1:501], start=2):
        if tracking_col >= len(row) or not row[tracking_col].strip():
            continue
        carrier = (
            row[carrier_col].strip().lower()
            if carrier_col is not None and carrier_col < len(row)
            else None
        )
        try:
            await service.add(
                ShipmentAdd(
                    tracking_number=row[tracking_col],
                    carrier=carrier or None,
                    reference=row[reference_col][:200]
                    if reference_col is not None and reference_col < len(row)
                    else None,
                ),
                refresh=False,
            )
            added += 1
        except ValueError as exc:
            skipped.append(f"Row {number}: {exc}"[:200])
    result = await service.refresh_all()
    return {"added": added, "skipped": skipped[:50], **result}


@router.post("/shipments/{shipment_id}/refresh")
async def refresh_shipment(db: D, p: P, shipment_id: UUID) -> dict[str, Any]:
    return _shipment_public(await Shipping(db, p).refresh_one(shipment_id))


@router.post("/refresh")
async def refresh_all_shipments(db: D, p: P) -> dict[str, int]:
    return await Shipping(db, p).refresh_all()


@router.delete("/shipments/{shipment_id}", status_code=204)
async def remove_shipment(db: D, p: P, shipment_id: UUID) -> None:
    s = await Shipping(db, p).shipment(shipment_id)
    await db.delete(s)
    await db.commit()
