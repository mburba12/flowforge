from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.platform.services import record_change

from .models import (
    GoodsReceipt,
    GoodsReceiptLine,
    PurchaseOrder,
    PurchaseOrderLine,
    VendorInvoice,
    VendorInvoiceLine,
    VendorProfile,
)
from .schemas import InvoiceCreate, POCreate, ReceiptCreate, VendorCreate


class ProcurementService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def vendor(self, data: VendorCreate) -> VendorProfile:
        statement = (
            select(func.count())
            .select_from(VendorProfile)
            .where(VendorProfile.tenant_id == self.tenant_id)
        )
        count = await self.db.scalar(statement)

        vendor = VendorProfile(
            tenant_id=self.tenant_id,
            vendor_number=f"V-{int(count or 0) + 1:08d}",
            **data.model_dump(),
        )
        self.db.add(vendor)

        await self.db.commit()
        await self.db.refresh(vendor)

        return vendor

    async def purchase_order(self, data: POCreate) -> PurchaseOrder:
        statement = (
            select(func.count())
            .select_from(PurchaseOrder)
            .where(PurchaseOrder.tenant_id == self.tenant_id)
        )
        count = await self.db.scalar(statement)

        total = sum(
            (line.quantity * line.unit_price for line in data.lines),
            Decimal("0"),
        )

        purchase_order = PurchaseOrder(
            tenant_id=self.tenant_id,
            po_number=f"PO-{int(count or 0) + 1:08d}",
            vendor_id=data.vendor_id,
            currency_code=data.currency_code,
            order_date=data.order_date,
            total_amount=total,
            created_by=self.user_id,
        )
        self.db.add(purchase_order)
        await self.db.flush()

        for line_number, line in enumerate(data.lines, start=1):
            self.db.add(
                PurchaseOrderLine(
                    tenant_id=self.tenant_id,
                    purchase_order_id=purchase_order.id,
                    line_number=line_number,
                    **line.model_dump(),
                )
            )

        await record_change(
            self.db,
            self.tenant_id,
            self.user_id,
            "created",
            "purchase_order",
            str(purchase_order.id),
        )

        await self.db.commit()
        await self.db.refresh(purchase_order)

        return purchase_order

    async def receipt(self, data: ReceiptCreate) -> GoodsReceipt:
        po_statement = select(PurchaseOrder).where(
            PurchaseOrder.id == data.purchase_order_id,
            PurchaseOrder.tenant_id == self.tenant_id,
        )
        purchase_order = await self.db.scalar(po_statement)

        receivable_statuses = {
            "approved",
            "sent",
            "partially_received",
        }

        if purchase_order is None or purchase_order.status not in receivable_statuses:
            raise ValueError("Purchase order is not receivable")

        count_statement = (
            select(func.count())
            .select_from(GoodsReceipt)
            .where(GoodsReceipt.tenant_id == self.tenant_id)
        )
        count = await self.db.scalar(count_statement)

        receipt = GoodsReceipt(
            tenant_id=self.tenant_id,
            receipt_number=f"GR-{int(count or 0) + 1:08d}",
            purchase_order_id=purchase_order.id,
            receipt_date=data.receipt_date,
            received_by=self.user_id,
        )
        self.db.add(receipt)
        await self.db.flush()

        all_lines_fully_received = True

        for requested_line in data.lines:
            line_statement = select(PurchaseOrderLine).where(
                PurchaseOrderLine.id == requested_line.po_line_id,
                PurchaseOrderLine.purchase_order_id == purchase_order.id,
                PurchaseOrderLine.tenant_id == self.tenant_id,
            )
            purchase_order_line = await self.db.scalar(line_statement)

            if purchase_order_line is None:
                raise ValueError("Purchase order line was not found")

            new_received_quantity = purchase_order_line.received_quantity + requested_line.quantity

            if new_received_quantity > purchase_order_line.quantity:
                raise ValueError("Receipt exceeds ordered quantity")

            purchase_order_line.received_quantity = new_received_quantity

            if new_received_quantity < purchase_order_line.quantity:
                all_lines_fully_received = False

            self.db.add(
                GoodsReceiptLine(
                    tenant_id=self.tenant_id,
                    receipt_id=receipt.id,
                    po_line_id=purchase_order_line.id,
                    quantity=requested_line.quantity,
                )
            )

        purchase_order.status = "received" if all_lines_fully_received else "partially_received"

        await record_change(
            self.db,
            self.tenant_id,
            self.user_id,
            "created",
            "goods_receipt",
            str(receipt.id),
        )

        await self.db.commit()
        await self.db.refresh(receipt)

        return receipt

    async def invoice(self, data: InvoiceCreate) -> VendorInvoice:
        total = sum(
            (line.quantity * line.unit_price for line in data.lines),
            Decimal("0"),
        )

        invoice_data = data.model_dump(exclude={"lines"})

        invoice = VendorInvoice(
            tenant_id=self.tenant_id,
            total_amount=total,
            created_by=self.user_id,
            **invoice_data,
        )
        self.db.add(invoice)
        await self.db.flush()

        for line in data.lines:
            self.db.add(
                VendorInvoiceLine(
                    tenant_id=self.tenant_id,
                    invoice_id=invoice.id,
                    **line.model_dump(),
                )
            )

        await record_change(
            self.db,
            self.tenant_id,
            self.user_id,
            "created",
            "vendor_invoice",
            str(invoice.id),
        )

        await self.db.commit()
        await self.db.refresh(invoice)

        return invoice
