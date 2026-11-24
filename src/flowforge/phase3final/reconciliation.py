from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase2b.models import (
    JournalEntry,
    JournalLine,
)
from flowforge.phase3a.models import APOpenItem
from flowforge.phase3b.models import (
    AROpenItem,
    InventoryBalance,
    Product,
)


class Phase3ReconciliationService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def open_ap(self) -> Decimal:
        statement = select(APOpenItem).where(APOpenItem.tenant_id == self.tenant_id)
        items = list((await self.db.scalars(statement)).all())

        return sum(
            (item.open_amount for item in items),
            Decimal("0"),
        )

    async def open_ar(self) -> Decimal:
        statement = select(AROpenItem).where(AROpenItem.tenant_id == self.tenant_id)
        items = list((await self.db.scalars(statement)).all())

        return sum(
            (item.open_amount for item in items),
            Decimal("0"),
        )

    async def inventory_value(self) -> Decimal:
        statement = select(InventoryBalance).where(InventoryBalance.tenant_id == self.tenant_id)
        balances = list((await self.db.scalars(statement)).all())

        total = Decimal("0")

        for balance in balances:
            product = await self.db.get(
                Product,
                balance.product_id,
            )

            if product is None:
                raise ValueError("Inventory product is missing")

            total += balance.on_hand * product.standard_cost

        return total

    async def gl_balance(
        self,
        account_id: UUID,
    ) -> Decimal:
        statement = (
            select(JournalLine)
            .join(
                JournalEntry,
                JournalEntry.id == JournalLine.journal_id,
            )
            .where(
                JournalEntry.tenant_id == self.tenant_id,
                JournalLine.account_id == account_id,
            )
        )
        lines = list((await self.db.scalars(statement)).all())

        return sum(
            (line.debit - line.credit for line in lines),
            Decimal("0"),
        )

    async def summary(
        self,
        ap_account_id: UUID,
        ar_account_id: UUID,
        inventory_account_id: UUID,
    ) -> dict[str, str]:
        ap_subledger = await self.open_ap()
        ar_subledger = await self.open_ar()
        inventory_subledger = await self.inventory_value()

        ap_gl = -(await self.gl_balance(ap_account_id))
        ar_gl = await self.gl_balance(ar_account_id)
        inventory_gl = await self.gl_balance(inventory_account_id)

        reconciled = (
            ap_subledger == ap_gl and ar_subledger == ar_gl and inventory_subledger == inventory_gl
        )

        return {
            "status": ("reconciled" if reconciled else "exception"),
            "ap_subledger": str(ap_subledger),
            "ap_gl": str(ap_gl),
            "ar_subledger": str(ar_subledger),
            "ar_gl": str(ar_gl),
            "inventory_subledger": str(inventory_subledger),
            "inventory_gl": str(inventory_gl),
        }
