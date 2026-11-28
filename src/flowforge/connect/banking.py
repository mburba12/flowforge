"""Bank accounts: live feeds through Plaid, statement imports for any bank, and a demo bank.

* Plaid (FLOWFORGE_PLAID_CLIENT_ID / _SECRET / _ENV): the user signs in to their bank in
  Plaid Link; FlowForge stores only the encrypted access token and syncs balances and
  transactions (cursor-based /transactions/sync).
* Statement import: CSV, OFX or QFX downloaded from any bank's website.
* Demo bank: sample accounts and transactions, to try FlowForge without real data.

Amounts are stored with positive = money out (Plaid's convention); the API also returns
money_in / money_out so screens never have to interpret signs.
"""

import hashlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.accounts.service import require_verified_email
from flowforge.core.config import settings
from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase4c.models import (
    BankBalanceSnapshot,
    BankConnection,
    BankSyncRun,
    BankTransaction,
    ConnectedBankAccount,
)
from flowforge.platform.services import record_change

from . import crypto
from .files import store_file
from .http import ProviderError, request
from .statements import parse_statement

router = APIRouter(prefix="/api/v1/banking", tags=["banking"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]

PLAID_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


def plaid_configured() -> bool:
    return bool(settings.plaid_client_id and settings.plaid_secret)


# ------------------------------------------------------------------ providers
class Plaid:
    name = "plaid"

    def _url(self, path: str) -> str:
        return PLAID_HOSTS.get(settings.plaid_env, PLAID_HOSTS["sandbox"]) + path

    async def call(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if not plaid_configured():
            raise ProviderError(
                "Live bank connections are not set up yet. An administrator adds the Plaid "
                "keys (FLOWFORGE_PLAID_CLIENT_ID and FLOWFORGE_PLAID_SECRET) to the server."
            )
        payload = {"client_id": settings.plaid_client_id, "secret": settings.plaid_secret, **body}
        result = await request("POST", self._url(path), "Plaid", json=payload)
        return result if isinstance(result, dict) else {}

    async def link_token(self, tenant_id: UUID, user_id: UUID) -> str:
        result = await self.call(
            "/link/token/create",
            {
                "client_name": "Krov WorkAgent",
                "user": {
                    "client_user_id": hashlib.sha256(f"{tenant_id}:{user_id}".encode()).hexdigest()
                },
                "products": ["transactions"],
                "country_codes": ["US"],
                "language": "en",
            },
        )
        return str(result["link_token"])

    async def exchange(self, public_token: str) -> tuple[str, str]:
        result = await self.call("/item/public_token/exchange", {"public_token": public_token})
        return str(result["access_token"]), str(result["item_id"])

    async def accounts(self, access_token: str) -> list[dict[str, Any]]:
        result = await self.call("/accounts/get", {"access_token": access_token})
        out = []
        for a in result.get("accounts", []):
            balances = a.get("balances") or {}
            out.append(
                {
                    "id": a["account_id"],
                    "name": a.get("name") or "Account",
                    "official_name": a.get("official_name"),
                    "mask": a.get("mask"),
                    "type": a.get("type") or "depository",
                    "subtype": a.get("subtype"),
                    "currency": balances.get("iso_currency_code") or "USD",
                    "current": _dec(balances.get("current")),
                    "available": _dec(balances.get("available")),
                }
            )
        return out

    async def transactions(
        self, access_token: str, cursor: str | None
    ) -> tuple[list[dict[str, Any]], list[str], str | None]:
        changed: list[dict[str, Any]] = []
        removed: list[str] = []
        for _ in range(50):  # pages of 500; a generous bound for a first full sync
            body: dict[str, Any] = {"access_token": access_token, "count": 500}
            if cursor:
                body["cursor"] = cursor
            page = await self.call("/transactions/sync", body)
            for t in list(page.get("added", [])) + list(page.get("modified", [])):
                changed.append(
                    {
                        "id": t["transaction_id"],
                        "account_id": t["account_id"],
                        "date": t.get("authorized_date") or t["date"],
                        "posted": t["date"],
                        "amount": _dec(t["amount"]) or Decimal("0"),
                        "currency": t.get("iso_currency_code") or "USD",
                        "description": t.get("merchant_name") or t.get("name") or "Transaction",
                        "original": t.get("name") or "",
                        "pending": bool(t.get("pending")),
                    }
                )
            removed.extend(r["transaction_id"] for r in page.get("removed", []))
            cursor = page.get("next_cursor") or cursor
            if not page.get("has_more"):
                break
        return changed, removed, cursor

    async def remove(self, access_token: str) -> None:
        await self.call("/item/remove", {"access_token": access_token})


class DemoBank:
    """Sample data, clearly labelled, so a new user can see how the bank pages work."""

    name = "demo"

    async def exchange(self, public_token: str) -> tuple[str, str]:
        return "demo-access", f"demo-{uuid4().hex[:10]}"

    async def accounts(self, access_token: str) -> list[dict[str, Any]]:
        return [
            {
                "id": "demo-checking",
                "name": "Business Checking (demo)",
                "official_name": None,
                "mask": "4321",
                "type": "depository",
                "subtype": "checking",
                "currency": "USD",
                "current": Decimal("48250.17"),
                "available": Decimal("47100.17"),
            },
            {
                "id": "demo-savings",
                "name": "Business Savings (demo)",
                "official_name": None,
                "mask": "8765",
                "type": "depository",
                "subtype": "savings",
                "currency": "USD",
                "current": Decimal("125000.00"),
                "available": Decimal("125000.00"),
            },
            {
                "id": "demo-card",
                "name": "Business Credit Card (demo)",
                "official_name": None,
                "mask": "1111",
                "type": "credit",
                "subtype": "credit card",
                "currency": "USD",
                "current": Decimal("3210.45"),
                "available": Decimal("16789.55"),
            },
        ]

    async def transactions(
        self, access_token: str, cursor: str | None
    ) -> tuple[list[dict[str, Any]], list[str], str | None]:
        if cursor:
            return [], [], cursor
        today = date.today()
        sample = [
            ("demo-checking", 2, "-18450.00", "Customer payment — Acme Corp"),
            ("demo-checking", 3, "1250.00", "Office rent"),
            ("demo-checking", 5, "312.40", "Utilities — City Power"),
            ("demo-checking", 7, "-6200.00", "Customer payment — Globex"),
            ("demo-checking", 9, "14820.55", "Payroll"),
            ("demo-checking", 12, "89.99", "Software subscription"),
            ("demo-savings", 15, "-25.12", "Interest"),
            ("demo-card", 1, "42.18", "Fuel"),
            ("demo-card", 4, "615.00", "Shipping supplies"),
            ("demo-card", 8, "128.40", "Team lunch"),
        ]
        out = [
            {
                "id": f"demo-{i}-{(today - timedelta(days=d)).isoformat()}",
                "account_id": acct,
                "date": (today - timedelta(days=d)).isoformat(),
                "posted": (today - timedelta(days=d)).isoformat(),
                "amount": Decimal(amount),
                "currency": "USD",
                "description": text,
                "original": text,
                "pending": d <= 1,
            }
            for i, (acct, d, amount, text) in enumerate(sample)
        ]
        return out, [], "demo-cursor-1"

    async def remove(self, access_token: str) -> None:
        return None


PROVIDERS: dict[str, Plaid | DemoBank] = {"plaid": Plaid(), "demo": DemoBank()}


def _dec(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value)).quantize(Decimal("0.01"))


def _money(value: Decimal | None) -> str | None:
    return None if value is None else str(value.quantize(Decimal("0.01")))


# ------------------------------------------------------------------ service
class Banking:
    def __init__(self, db: AsyncSession, p: Principal):
        self.db, self.p = db, p

    def _context(self, connection_id: UUID) -> str:
        return f"{self.p.tenant_id}:bank:{connection_id}"

    async def connection(self, connection_id: UUID) -> BankConnection:
        c = await self.db.scalar(
            select(BankConnection).where(
                BankConnection.id == connection_id, BankConnection.tenant_id == self.p.tenant_id
            )
        )
        if c is None:
            raise LookupError("Bank connection not found")
        return c

    async def connect(
        self,
        provider_name: str,
        public_token: str,
        institution_id: str | None,
        institution_name: str | None,
    ) -> dict[str, Any]:
        provider = PROVIDERS.get(provider_name)
        if provider is None:
            raise ValueError("Unknown bank provider")
        access, item_id = await provider.exchange(public_token)
        connection = BankConnection(
            tenant_id=self.p.tenant_id,
            provider=provider_name,
            provider_item_id=item_id,
            institution_id=institution_id,
            institution_name=institution_name
            or ("Demo Bank" if provider_name == "demo" else "Bank"),
            status="connected",
            connected_by=self.p.user_id,
        )
        connection.id = uuid4()
        connection.encrypted_access_token = crypto.encrypt(access, self._context(connection.id))
        self.db.add(connection)
        await self.db.flush()
        await record_change(
            self.db,
            self.p.tenant_id,
            self.p.user_id,
            "connected",
            "bank_connection",
            str(connection.id),
            {"provider": provider_name},
        )
        result = await self._sync(connection, access, "initial")
        return {"connection_id": str(connection.id), **result}

    async def sync(self, connection_id: UUID) -> dict[str, Any]:
        connection = await self.connection(connection_id)
        if connection.provider not in PROVIDERS:
            raise ValueError("This account is updated by importing statements")
        if connection.status == "disconnected":
            raise ValueError("This bank connection was disconnected; connect it again")
        try:
            access = crypto.decrypt(
                connection.encrypted_access_token or "", self._context(connection.id)
            )
        except Exception as exc:
            raise ValueError(
                "The stored bank token is not readable; connect the bank again"
            ) from exc
        return await self._sync(connection, access, "incremental")

    async def _sync(self, connection: BankConnection, access: str, kind: str) -> dict[str, Any]:
        provider = PROVIDERS[connection.provider]
        run = BankSyncRun(tenant_id=self.p.tenant_id, connection_id=connection.id, sync_type=kind)
        self.db.add(run)
        await self.db.flush()
        try:
            accounts = await provider.accounts(access)
            changed, removed, cursor = await provider.transactions(access, connection.cursor)
        except ProviderError as exc:
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            if "ITEM_LOGIN_REQUIRED" in str(exc) or "login" in str(exc).lower():
                connection.status = "reauth_required"
            await self.db.commit()
            raise
        by_external: dict[str, ConnectedBankAccount] = {}
        existing = await self.db.scalars(
            select(ConnectedBankAccount).where(
                ConnectedBankAccount.tenant_id == self.p.tenant_id,
                ConnectedBankAccount.connection_id == connection.id,
            )
        )
        for row in existing:
            by_external[row.provider_account_id] = row
        for a in accounts:
            found = by_external.get(a["id"])
            if found is None:
                account = ConnectedBankAccount(
                    tenant_id=self.p.tenant_id,
                    connection_id=connection.id,
                    provider_account_id=a["id"],
                    name=a["name"],
                    account_type=a["type"],
                    currency_code=a["currency"],
                )
                self.db.add(account)
                by_external[a["id"]] = account
            else:
                account = found
            account.name = a["name"]
            account.official_name = a["official_name"]
            account.account_mask = a["mask"]
            account.account_type = a["type"]
            account.account_subtype = a["subtype"]
            account.currency_code = a["currency"]
            account.current_balance = a["current"]
            account.available_balance = a["available"]
            await self.db.flush()
            self.db.add(
                BankBalanceSnapshot(
                    tenant_id=self.p.tenant_id,
                    connected_bank_account_id=account.id,
                    current_balance=a["current"],
                    available_balance=a["available"],
                    currency_code=a["currency"],
                )
            )
        created = updated = 0
        for t in changed:
            target = by_external.get(t["account_id"])
            if target is None:
                continue
            if await self._upsert(
                target,
                connection.provider,
                t["id"],
                date.fromisoformat(t["posted"][:10]),
                t["amount"],
                t["currency"],
                t["description"],
                t["original"],
                t["pending"],
            ):
                created += 1
            else:
                updated += 1
        removed_count = 0
        for transaction_id in removed:
            row = await self.db.scalar(
                select(BankTransaction).where(
                    BankTransaction.tenant_id == self.p.tenant_id,
                    BankTransaction.provider == connection.provider,
                    BankTransaction.provider_transaction_id == transaction_id,
                )
            )
            if row is not None and not row.removed:
                row.removed = True
                removed_count += 1
        connection.cursor = cursor
        connection.status = "connected"
        connection.last_successful_sync_at = datetime.now(UTC)
        run.transactions_created, run.transactions_updated = created, updated
        run.transactions_removed = removed_count
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        await self.db.commit()
        return {
            "accounts": len(accounts),
            "transactions_added": created,
            "transactions_updated": updated,
            "transactions_removed": removed_count,
        }

    async def _upsert(
        self,
        account: ConnectedBankAccount,
        provider: str,
        external_id: str,
        posted: date,
        amount: Decimal,
        currency: str,
        description: str,
        original: str,
        pending: bool,
    ) -> bool:
        row = await self.db.scalar(
            select(BankTransaction).where(
                BankTransaction.tenant_id == self.p.tenant_id,
                BankTransaction.provider == provider,
                BankTransaction.provider_transaction_id == external_id,
            )
        )
        when = datetime(posted.year, posted.month, posted.day, 12, tzinfo=UTC)
        if row is None:
            self.db.add(
                BankTransaction(
                    tenant_id=self.p.tenant_id,
                    connected_bank_account_id=account.id,
                    provider=provider,
                    provider_transaction_id=external_id,
                    posted_at=when,
                    amount=amount,
                    currency_code=currency,
                    direction="debit" if amount > 0 else "credit",
                    original_description=(original or description)[:500],
                    normalized_description=description[:500],
                    pending=pending,
                )
            )
            return True
        row.posted_at, row.amount, row.pending, row.removed = when, amount, pending, False
        row.direction = "debit" if amount > 0 else "credit"
        row.normalized_description = description[:500]
        return False

    async def disconnect(self, connection_id: UUID) -> None:
        connection = await self.connection(connection_id)
        provider = PROVIDERS.get(connection.provider)
        if provider is not None and connection.encrypted_access_token:
            try:
                access = crypto.decrypt(
                    connection.encrypted_access_token, self._context(connection.id)
                )
                await provider.remove(access)
            except (ProviderError, ValueError):
                pass  # the bank side may already be gone; still forget the token here
        connection.encrypted_access_token = None
        connection.status = "disconnected"
        accounts = await self.db.scalars(
            select(ConnectedBankAccount).where(
                ConnectedBankAccount.tenant_id == self.p.tenant_id,
                ConnectedBankAccount.connection_id == connection.id,
            )
        )
        for account in accounts:
            account.import_enabled = False
        await record_change(
            self.db,
            self.p.tenant_id,
            self.p.user_id,
            "disconnected",
            "bank_connection",
            str(connection.id),
        )
        await self.db.commit()

    async def import_statement(
        self,
        filename: str,
        data: bytes,
        account_id: UUID | None,
        account_name: str | None,
        currency: str,
    ) -> dict[str, Any]:
        statement = parse_statement(filename, data)
        if account_id is not None:
            account = await self.db.scalar(
                select(ConnectedBankAccount).where(
                    ConnectedBankAccount.id == account_id,
                    ConnectedBankAccount.tenant_id == self.p.tenant_id,
                )
            )
            if account is None:
                raise LookupError("Bank account not found")
            connection = await self.connection(account.connection_id)
        else:
            name = (account_name or "").strip()
            if not name:
                raise ValueError("Choose an account, or name the new account this statement is for")
            mask = (statement.account_number or "")[-4:] or None
            connection = BankConnection(
                tenant_id=self.p.tenant_id,
                provider="statement",
                institution_name=name,
                status="connected",
                connected_by=self.p.user_id,
            )
            self.db.add(connection)
            await self.db.flush()
            account = ConnectedBankAccount(
                tenant_id=self.p.tenant_id,
                connection_id=connection.id,
                provider_account_id=f"statement-{uuid4().hex[:12]}",
                name=name[:200],
                account_mask=mask,
                account_type="depository",
                account_subtype="checking",
                currency_code=(statement.currency or currency or "USD").upper()[:3],
            )
            self.db.add(account)
            await self.db.flush()
        created = updated = 0
        for line in statement.lines:
            external = f"{account.id}:{line.external_id}"[:180]
            if await self._upsert(
                account,
                connection.provider,
                external,
                line.posted,
                line.amount,
                account.currency_code,
                line.description,
                line.description,
                False,
            ):
                created += 1
            else:
                updated += 1
        if statement.balance is not None:
            account.current_balance = statement.balance
            account.available_balance = statement.balance
            self.db.add(
                BankBalanceSnapshot(
                    tenant_id=self.p.tenant_id,
                    connected_bank_account_id=account.id,
                    current_balance=statement.balance,
                    available_balance=statement.balance,
                    currency_code=account.currency_code,
                )
            )
        connection.last_successful_sync_at = datetime.now(UTC)
        file = await store_file(
            self.db,
            self.p,
            section="banking",
            filename=filename,
            data=data,
            record_type="bank_account",
            record_id=str(account.id),
            note="Imported bank statement",
        )
        await self.db.commit()
        return {
            "account_id": str(account.id),
            "transactions_added": created,
            "transactions_already_imported": updated,
            "balance": _money(statement.balance),
            "file_id": str(file.id),
        }

    async def overview(self) -> dict[str, Any]:
        rows = (
            await self.db.execute(
                select(ConnectedBankAccount, BankConnection)
                .join(BankConnection, BankConnection.id == ConnectedBankAccount.connection_id)
                .where(
                    ConnectedBankAccount.tenant_id == self.p.tenant_id,
                    ConnectedBankAccount.active.is_(True),
                )
                .order_by(BankConnection.institution_name, ConnectedBankAccount.name)
            )
        ).all()
        counts = dict(
            (
                await self.db.execute(
                    select(BankTransaction.connected_bank_account_id, func.count())
                    .where(
                        BankTransaction.tenant_id == self.p.tenant_id,
                        BankTransaction.removed.is_(False),
                    )
                    .group_by(BankTransaction.connected_bank_account_id)
                )
            ).all()
        )
        accounts: list[dict[str, Any]] = []
        connections: dict[str, str] = {}
        totals: dict[str, dict[str, Decimal]] = {}
        for account, connection in rows:
            if connection.status == "disconnected":
                continue
            balance = account.current_balance or Decimal("0")
            # Cash = deposit accounts; card and loan balances are money owed.
            owed = account.account_type in ("credit", "loan")
            bucket = totals.setdefault(
                account.currency_code, {"cash": Decimal("0"), "owed": Decimal("0")}
            )
            bucket["owed" if owed else "cash"] += balance
            accounts.append(
                {
                    "id": str(account.id),
                    "name": account.name,
                    "mask": account.account_mask,
                    "type": account.account_type,
                    "subtype": account.account_subtype,
                    "currency": account.currency_code,
                    "current_balance": _money(account.current_balance),
                    "available_balance": _money(account.available_balance),
                    "owed": owed,
                    "connection_id": str(connection.id),
                    "institution": connection.institution_name,
                    "provider": connection.provider,
                    "status": connection.status,
                    "last_synced_at": connection.last_successful_sync_at.isoformat()
                    if connection.last_successful_sync_at
                    else None,
                    "transactions": int(counts.get(account.id, 0)),
                }
            )
            connections[str(connection.id)] = connection.status
        return {
            "accounts": accounts,
            "totals": [
                {"currency": c, "cash": _money(v["cash"]), "owed": _money(v["owed"])}
                for c, v in totals.items()
            ],
            "live_connections_available": plaid_configured(),
            "plaid_env": settings.plaid_env if plaid_configured() else None,
        }

    async def transactions(
        self, account_id: UUID | None, search: str | None, limit: int
    ) -> list[dict[str, Any]]:
        q = (
            select(BankTransaction, ConnectedBankAccount.name)
            .join(
                ConnectedBankAccount,
                ConnectedBankAccount.id == BankTransaction.connected_bank_account_id,
            )
            .where(
                BankTransaction.tenant_id == self.p.tenant_id, BankTransaction.removed.is_(False)
            )
        )
        if account_id is not None:
            q = q.where(BankTransaction.connected_bank_account_id == account_id)
        if search:
            q = q.where(
                func.coalesce(
                    BankTransaction.normalized_description, BankTransaction.original_description
                ).ilike(f"%{search[:80]}%")
            )
        rows = (
            await self.db.execute(q.order_by(BankTransaction.posted_at.desc()).limit(limit))
        ).all()
        return [
            {
                "id": str(t.id),
                "account_id": str(t.connected_bank_account_id),
                "account": name,
                "date": t.posted_at.date().isoformat(),
                "description": t.normalized_description or t.original_description,
                "money_in": _money(-t.amount) if t.amount < 0 else None,
                "money_out": _money(t.amount) if t.amount > 0 else None,
                "currency": t.currency_code,
                "pending": t.pending,
                "source": t.provider,
            }
            for t, name in rows
        ]


# ------------------------------------------------------------------ routes
class LinkRequest(BaseModel):
    provider: str = Field(default="plaid", pattern="^(plaid|demo)$")


class ConnectRequest(BaseModel):
    provider: str = Field(pattern="^(plaid|demo)$")
    public_token: str = Field(min_length=1, max_length=500)
    institution_id: str | None = Field(default=None, max_length=150)
    institution_name: str | None = Field(default=None, max_length=200)


@router.get("/overview")
async def banking_overview(db: D, p: P) -> dict[str, Any]:
    return await Banking(db, p).overview()


@router.get("/transactions")
async def bank_transactions(
    db: D,
    p: P,
    account_id: UUID | None = None,
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> list[dict[str, Any]]:
    return await Banking(db, p).transactions(account_id, search, limit)


@router.post("/link")
async def start_bank_link(db: D, p: P, body: LinkRequest) -> dict[str, Any]:
    """Start connecting a bank: returns the Plaid Link token (or a demo token)."""
    if body.provider == "demo":
        return {"provider": "demo", "link_token": "demo-link"}
    await require_verified_email(db, p.user_id)
    return {"provider": "plaid", "link_token": await Plaid().link_token(p.tenant_id, p.user_id)}


@router.post("/connections", status_code=201)
async def connect_bank(db: D, p: P, body: ConnectRequest) -> dict[str, Any]:
    return await Banking(db, p).connect(
        body.provider, body.public_token, body.institution_id, body.institution_name
    )


@router.post("/connections/{connection_id}/sync")
async def sync_bank(db: D, p: P, connection_id: UUID) -> dict[str, Any]:
    return await Banking(db, p).sync(connection_id)


@router.delete("/connections/{connection_id}", status_code=204)
async def disconnect_bank(db: D, p: P, connection_id: UUID) -> None:
    await Banking(db, p).disconnect(connection_id)


@router.post("/statements", status_code=201)
async def import_bank_statement(
    db: D,
    p: P,
    file: Annotated[UploadFile, File(description="CSV, OFX or QFX statement from your bank")],
    account_id: Annotated[UUID | None, Form()] = None,
    account_name: Annotated[str | None, Form(max_length=200)] = None,
    currency: Annotated[str, Form(min_length=3, max_length=3)] = "USD",
) -> dict[str, Any]:
    data = await file.read(settings.upload_max_bytes + 1)
    if len(data) > settings.upload_max_bytes:
        raise HTTPException(413, "The file is too large")
    return await Banking(db, p).import_statement(
        file.filename or "statement.csv", data, account_id, account_name, currency
    )
