from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    BankAccountGLMapping,
    BankBalanceSnapshot,
    BankConnection,
    BankSyncRun,
    BankTransaction,
    ConnectedBankAccount,
)
from .providers import SandboxBankingProvider
from .schemas import GLMappingCreate, ManualTransactionCreate, TokenExchange


class BankingError(Exception):
    pass


class BankingService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def provider(self, name: str) -> SandboxBankingProvider:
        if name != "sandbox":
            raise BankingError("Provider is not configured")
        return SandboxBankingProvider()

    async def link_session(self, name: str) -> str:
        return await self.provider(name).create_link_session(str(self.tenant_id))

    async def exchange(self, data: TokenExchange) -> BankConnection:
        provider = self.provider(data.provider)
        access, item_id = await provider.exchange_token(data.public_token)
        connection = BankConnection(
            tenant_id=self.tenant_id,
            provider=data.provider,
            provider_item_id=item_id,
            institution_id=data.institution_id,
            institution_name=data.institution_name,
            encrypted_access_token="SANDBOX_TOKEN_NOT_PERSISTED",
            status="connected",
            connected_by=self.user_id,
        )
        self.db.add(connection)
        await self.db.flush()
        for account in await provider.list_accounts(access):
            record = ConnectedBankAccount(
                tenant_id=self.tenant_id,
                connection_id=connection.id,
                provider_account_id=account.account_id,
                name=account.name,
                account_mask=account.mask,
                account_type=account.account_type,
                account_subtype=account.subtype,
                currency_code=account.currency,
                current_balance=account.current,
                available_balance=account.available,
            )
            self.db.add(record)
            await self.db.flush()
            self.db.add(
                BankBalanceSnapshot(
                    tenant_id=self.tenant_id,
                    connected_bank_account_id=record.id,
                    current_balance=account.current,
                    available_balance=account.available,
                    currency_code=account.currency,
                )
            )
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def map_account(self, account_id: UUID, data: GLMappingCreate) -> BankAccountGLMapping:
        account = await self.db.scalar(
            select(ConnectedBankAccount).where(
                ConnectedBankAccount.id == account_id,
                ConnectedBankAccount.tenant_id == self.tenant_id,
            )
        )
        if account is None:
            raise BankingError("Connected account not found")
        mapping = BankAccountGLMapping(
            tenant_id=self.tenant_id,
            connected_bank_account_id=account.id,
            gl_account_id=data.gl_account_id,
            mapping_type=data.mapping_type,
            created_by=self.user_id,
        )
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def manual_transaction(self, data: ManualTransactionCreate) -> BankTransaction:
        account = await self.db.scalar(
            select(ConnectedBankAccount).where(
                ConnectedBankAccount.id == data.connected_bank_account_id,
                ConnectedBankAccount.tenant_id == self.tenant_id,
            )
        )
        if account is None:
            raise BankingError("Connected account not found")
        existing = await self.db.scalar(
            select(BankTransaction).where(
                BankTransaction.tenant_id == self.tenant_id,
                BankTransaction.provider == "manual",
                BankTransaction.provider_transaction_id == data.provider_transaction_id,
            )
        )
        if existing is not None:
            return existing
        item = BankTransaction(
            tenant_id=self.tenant_id,
            connected_bank_account_id=account.id,
            provider="manual",
            provider_transaction_id=data.provider_transaction_id,
            posted_at=datetime.fromisoformat(data.posted_at),
            amount=Decimal(data.amount),
            currency_code=data.currency_code,
            direction=data.direction,
            original_description=data.description,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def sync(
        self,
        connection_id: UUID,
    ) -> BankSyncRun:
        connection_statement = select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.tenant_id == self.tenant_id,
        )
        connection = await self.db.scalar(connection_statement)

        if connection is None:
            raise BankingError("Bank connection was not found")

        if connection.provider != "sandbox":
            raise BankingError(
                "Production banking providers require Key Vault-backed token encryption"
            )

        if connection.encrypted_access_token != "SANDBOX_TOKEN_NOT_PERSISTED":
            raise BankingError("Sandbox connection token state is invalid")

        sync_run = BankSyncRun(
            tenant_id=self.tenant_id,
            connection_id=connection.id,
            sync_type="incremental",
        )
        self.db.add(sync_run)
        await self.db.flush()

        provider = self.provider(connection.provider)
        transactions, cursor = await provider.sync_transactions(
            "sandbox-ephemeral-session",
            connection.cursor,
        )

        created = 0

        for transaction in transactions:
            account_statement = select(ConnectedBankAccount).where(
                ConnectedBankAccount.connection_id == connection.id,
                ConnectedBankAccount.provider_account_id == transaction.account_id,
                ConnectedBankAccount.tenant_id == self.tenant_id,
            )
            account = await self.db.scalar(account_statement)

            if account is None:
                continue

            transaction_statement = select(BankTransaction).where(
                BankTransaction.tenant_id == self.tenant_id,
                BankTransaction.provider == connection.provider,
                BankTransaction.provider_transaction_id == transaction.transaction_id,
            )
            existing = await self.db.scalar(transaction_statement)

            if existing is not None:
                existing.pending = transaction.pending
                existing.removed = transaction.removed
                existing.amount = transaction.amount
                existing.original_description = transaction.description
                sync_run.transactions_updated += 1
                continue

            bank_transaction = BankTransaction(
                tenant_id=self.tenant_id,
                connected_bank_account_id=account.id,
                provider=connection.provider,
                provider_transaction_id=(transaction.transaction_id),
                posted_at=datetime.fromisoformat(transaction.posted_at),
                amount=transaction.amount,
                currency_code=transaction.currency,
                direction=("debit" if transaction.amount > 0 else "credit"),
                original_description=(transaction.description),
                pending=transaction.pending,
                removed=transaction.removed,
            )
            self.db.add(bank_transaction)
            created += 1

        connection.cursor = cursor
        connection.last_successful_sync_at = datetime.now(UTC)

        sync_run.transactions_created = created
        sync_run.status = "completed"
        sync_run.completed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(sync_run)

        return sync_run
