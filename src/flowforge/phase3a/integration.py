from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.phase2b.posting import PostingError, PostingLine, post_system_journal

from .matching import MatchInput, MatchPolicy, evaluate
from .models import (
    APOpenItem,
    InvoiceMatch,
    PurchaseOrderLine,
    VendorInvoice,
    VendorInvoiceLine,
)


class APIntegrationService:
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def match_invoice(
        self,
        invoice_id: UUID,
    ) -> InvoiceMatch:
        invoice_statement = select(VendorInvoice).where(
            VendorInvoice.id == invoice_id,
            VendorInvoice.tenant_id == self.tenant_id,
        )
        invoice = await self.db.scalar(invoice_statement)

        if invoice is None:
            raise ValueError("Invoice not found")

        line_statement = select(VendorInvoiceLine).where(VendorInvoiceLine.invoice_id == invoice.id)
        lines = list((await self.db.scalars(line_statement)).all())

        reasons: list[str] = []

        for line in lines:
            if line.po_line_id is None:
                reasons.append("missing_po_line")
                continue

            po_line_statement = select(PurchaseOrderLine).where(
                PurchaseOrderLine.id == line.po_line_id,
                PurchaseOrderLine.tenant_id == self.tenant_id,
            )
            po_line = await self.db.scalar(po_line_statement)

            if po_line is None:
                reasons.append("missing_po_line")
                continue

            match_input = MatchInput(
                ordered=po_line.quantity,
                received=po_line.received_quantity,
                invoiced=line.quantity,
                po_unit_price=po_line.unit_price,
                invoice_unit_price=line.unit_price,
            )

            _, found_reasons = evaluate(
                match_input,
                MatchPolicy(),
            )
            reasons.extend(found_reasons)

        match_status = "matched" if not reasons else "exception"

        result = InvoiceMatch(
            tenant_id=self.tenant_id,
            invoice_id=invoice.id,
            status=match_status,
            exception_count=len(reasons),
            details=",".join(sorted(set(reasons))),
        )
        self.db.add(result)

        invoice.status = match_status

        await self.db.commit()
        await self.db.refresh(result)

        return result

    async def post_invoice(
        self,
        invoice_id: UUID,
        ledger_id: UUID,
        period_id: UUID,
        ap_account_id: UUID,
    ) -> VendorInvoice:
        invoice_statement = select(VendorInvoice).where(
            VendorInvoice.id == invoice_id,
            VendorInvoice.tenant_id == self.tenant_id,
        )
        invoice = await self.db.scalar(invoice_statement)

        if invoice is None or invoice.status not in {"matched", "approved"}:
            raise ValueError("Invoice is not ready to post")

        line_statement = select(VendorInvoiceLine).where(VendorInvoiceLine.invoice_id == invoice.id)
        lines = list((await self.db.scalars(line_statement)).all())

        try:
            journal = await post_system_journal(
                self.db,
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                ledger_id=ledger_id,
                period_id=period_id,
                journal_number=f"AP-{str(invoice.id)[:8]}",
                journal_date=invoice.invoice_date,
                description=f"Vendor invoice {invoice.invoice_number}",
                currency_code=invoice.currency_code,
                lines=[
                    *(
                        PostingLine(
                            account_id=line.account_id,
                            debit=line.quantity * line.unit_price,
                            credit=Decimal("0"),
                            description=line.description,
                        )
                        for line in lines
                    ),
                    PostingLine(
                        account_id=ap_account_id,
                        debit=Decimal("0"),
                        credit=invoice.total_amount,
                        description="Accounts payable",
                    ),
                ],
            )
        except PostingError as exc:
            raise ValueError(str(exc)) from exc

        self.db.add(
            APOpenItem(
                tenant_id=self.tenant_id,
                vendor_id=invoice.vendor_id,
                invoice_id=invoice.id,
                original_amount=invoice.total_amount,
                open_amount=invoice.total_amount,
                due_date=invoice.due_date,
            )
        )

        invoice.status = "posted"
        invoice.posted_journal_id = journal.id

        await self.db.commit()
        await self.db.refresh(invoice)

        return invoice
