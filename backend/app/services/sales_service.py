from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models import (
    SalesOrder, SalesOrderItem, OrderStatus,
    Invoice, InvoiceItem, InvoiceStatus,
    Payment, CreditNote, Customer, Item, User,
    StockMovement, MovementType, AuditLog, utc_now
)
from app.services.ledger_service import LedgerService
from app.config import settings

class SalesService:
    @staticmethod
    def create_sales_order(
        db: Session,
        salesman_id: int,
        customer_id: int,
        items_data: List[Dict[str, Any]],
        user: str = "salesman"
    ) -> SalesOrder:
        """
        Creates a sales order, checks finished goods availability, and flags shortage if any.
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        now = utc_now()
        count = db.query(SalesOrder).count() + 1
        order_number = f"SO-{now.year}-{count:03d}"

        total_taxable = Decimal("0.00")
        total_gst = Decimal("0.00")
        has_shortage = False
        total_shortage_qty = Decimal("0.00")
        shortage_notes = []

        order_items = []
        for item_data in items_data:
            item_id = item_data["item_id"]
            qty = Decimal(str(item_data["quantity"]))
            item = db.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise ValueError(f"Item {item_id} not found")

            # Check stock availability
            current_stock = LedgerService.get_stock_balance(db, item_id)
            if current_stock < qty:
                shortage = qty - current_stock
                has_shortage = True
                total_shortage_qty += shortage
                shortage_notes.append(
                    f"Shortage of {shortage} {item.unit} for {item.name} (Available: {current_stock}, Requested: {qty})"
                )

            unit_price = Decimal(str(item_data.get("unit_price", item.selling_price or Decimal("0.00"))))
            taxable = (qty * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            gst_rate = Decimal(str(item.gst_rate))
            gst_amount = (taxable * gst_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            item_total = taxable + gst_amount

            total_taxable += taxable
            total_gst += gst_amount

            order_items.append(SalesOrderItem(
                item_id=item_id,
                ordered_qty=qty,
                approved_qty=qty,
                unit_price=unit_price,
                taxable_amount=taxable,
                gst_rate=gst_rate,
                gst_amount=gst_amount,
                total_amount=item_total
            ))

        sales_order = SalesOrder(
            order_number=order_number,
            salesman_id=salesman_id,
            customer_id=customer_id,
            order_date=utc_now(),
            status=OrderStatus.SUBMITTED,
            shortage_flag=has_shortage,
            shortage_qty=total_shortage_qty,
            shortage_notes="; ".join(shortage_notes) if shortage_notes else None,
            total_taxable_amount=total_taxable,
            total_gst_amount=total_gst,
            total_amount=total_taxable + total_gst,
            items=order_items
        )

        db.add(sales_order)
        db.commit()
        db.refresh(sales_order)

        db.add(AuditLog(
            entity_name="SALES_ORDER",
            entity_id=str(sales_order.id),
            action="CREATE",
            performed_by=user,
            details=f"Order {order_number} submitted for customer {customer.name}. Shortage: {has_shortage}"
        ))
        db.commit()

        return sales_order

    @staticmethod
    def approve_order(db: Session, order_id: int, user: str = "admin") -> SalesOrder:
        order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        order.status = OrderStatus.APPROVED
        db.add(AuditLog(
            entity_name="SALES_ORDER",
            entity_id=str(order.id),
            action="APPROVE",
            performed_by=user,
            details=f"Order {order.order_number} approved by {user}"
        ))
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def generate_gst_invoice(db: Session, order_id: int, user: str = "admin") -> Invoice:
        """
        Converts an approved order into a GST tax invoice:
        - Determines CGST+SGST (Intra-state) vs IGST (Inter-state)
        - Uses FY invoice numbering (e.g. INV/2026-27/001)
        """
        order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
            
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        
        # Check place of supply
        is_inter_state = (customer.state.strip().lower() != settings.FACTORY_STATE.strip().lower())

        count = db.query(Invoice).count() + 1
        fy = "2026-27"
        invoice_number = f"INV/{fy}/{count:03d}"

        total_taxable = Decimal("0.00")
        total_cgst = Decimal("0.00")
        total_sgst = Decimal("0.00")
        total_igst = Decimal("0.00")

        invoice_items = []
        for o_item in order.items:
            item = db.query(Item).filter(Item.id == o_item.item_id).first()
            taxable = o_item.taxable_amount
            total_taxable += taxable
            rate = Decimal(str(item.gst_rate)) # e.g. 0.05

            if is_inter_state:
                cgst_amt = Decimal("0.00")
                sgst_amt = Decimal("0.00")
                igst_amt = (taxable * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_igst += igst_amt
            else:
                half_rate = rate / Decimal("2")
                cgst_amt = (taxable * half_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                sgst_amt = (taxable * half_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                igst_amt = Decimal("0.00")
                total_cgst += cgst_amt
                total_sgst += sgst_amt

            line_total = taxable + cgst_amt + sgst_amt + igst_amt

            invoice_items.append(InvoiceItem(
                item_id=item.id,
                hsn_code=item.hsn_code,
                quantity=o_item.approved_qty,
                unit=item.unit,
                unit_price=o_item.unit_price,
                taxable_amount=taxable,
                cgst_amount=cgst_amt,
                sgst_amount=sgst_amt,
                igst_amount=igst_amt,
                total_amount=line_total
            ))

        total_invoice = total_taxable + total_cgst + total_sgst + total_igst

        invoice = Invoice(
            invoice_number=invoice_number,
            financial_year=fy,
            sales_order_id=order.id,
            customer_id=customer.id,
            invoice_date=utc_now(),
            place_of_supply=customer.state,
            is_inter_state=is_inter_state,
            taxable_amount=total_taxable,
            cgst_rate=Decimal("0.0250") if not is_inter_state else Decimal("0.0000"),
            cgst_amount=total_cgst,
            sgst_rate=Decimal("0.0250") if not is_inter_state else Decimal("0.0000"),
            sgst_amount=total_sgst,
            igst_rate=Decimal("0.0500") if is_inter_state else Decimal("0.0000"),
            igst_amount=total_igst,
            total_amount=total_invoice,
            status=InvoiceStatus.POSTED,
            is_dispatched=False,
            items=invoice_items
        )

        order.status = OrderStatus.INVOICED
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        db.add(AuditLog(
            entity_name="INVOICE",
            entity_id=str(invoice.id),
            action="CREATE",
            performed_by=user,
            details=f"Invoice {invoice_number} generated for Order {order.order_number}. Taxable: ₹{total_taxable}, Total: ₹{total_invoice}"
        ))
        db.commit()

        return invoice

    @staticmethod
    def record_dispatch(db: Session, invoice_id: int, user: str = "admin") -> Invoice:
        """
        Dispatches an invoice, automatically reducing Finished Goods stock in the ledger.
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError("Invoice not found")
            
        if invoice.is_dispatched:
            raise ValueError("Invoice has already been dispatched")

        # Check stock and create negative movement in ledger
        for inv_item in invoice.items:
            qty = Decimal(str(inv_item.quantity))
            current_stock = LedgerService.get_stock_balance(db, inv_item.item_id)
            if current_stock < qty:
                raise ValueError(
                    f"Insufficient stock for dispatch of {inv_item.item.name}. Available: {current_stock}, Required: {qty}"
                )

            LedgerService.record_movement(
                db=db,
                item_id=inv_item.item_id,
                quantity=-qty, # Negative movement
                unit_cost=inv_item.unit_price,
                movement_type=MovementType.SALES_DISPATCH,
                reference_type="SALES_INVOICE",
                reference_id=str(invoice.invoice_number),
                notes=f"Dispatched against invoice {invoice.invoice_number} for customer {invoice.customer.name}",
                user=user
            )

        invoice.is_dispatched = True
        invoice.dispatched_at = utc_now()
        invoice.status = InvoiceStatus.DISPATCHED
        if invoice.order:
            invoice.order.status = OrderStatus.DISPATCHED

        db.add(AuditLog(
            entity_name="INVOICE",
            entity_id=str(invoice.id),
            action="DISPATCH",
            performed_by=user,
            details=f"Invoice {invoice.invoice_number} dispatched. Finished goods stock deducted."
        ))
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def record_payment(
        db: Session,
        customer_id: int,
        amount: Decimal,
        invoice_id: Optional[int] = None,
        payment_mode: str = "Bank Transfer",
        reference: Optional[str] = None,
        notes: Optional[str] = None,
        user: str = "admin"
    ) -> Payment:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError("Customer not found")

        now = utc_now()
        count = db.query(Payment).count() + 1
        payment_number = f"PAY-{now.year}-{count:03d}"

        payment = Payment(
            payment_number=payment_number,
            customer_id=customer_id,
            invoice_id=invoice_id,
            payment_date=now,
            amount=amount,
            payment_mode=payment_mode,
            reference=reference,
            notes=notes
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        db.add(AuditLog(
            entity_name="PAYMENT",
            entity_id=str(payment.id),
            action="CREATE",
            performed_by=user,
            details=f"Payment of ₹{amount} recorded for {customer.name}"
        ))
        db.commit()
        return payment

    @staticmethod
    def get_customer_outstanding(db: Session, customer_id: int) -> Dict[str, Any]:
        """
        Computes Total Invoiced - Total Payments = Outstanding Balance.
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError("Customer not found")

        invoices = db.query(Invoice).filter(
            Invoice.customer_id == customer_id,
            Invoice.status != InvoiceStatus.CANCELLED_VIA_CREDIT_NOTE
        ).all()
        
        payments = db.query(Payment).filter(Payment.customer_id == customer_id).all()

        total_invoiced = sum([Decimal(str(inv.total_amount)) for inv in invoices], Decimal("0.00"))
        total_paid = sum([Decimal(str(p.amount)) for p in payments], Decimal("0.00"))
        outstanding = total_invoiced - total_paid

        return {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "total_invoiced": float(total_invoiced),
            "total_paid": float(total_paid),
            "outstanding": float(outstanding)
        }

    @staticmethod
    def cancel_invoice_with_credit_note(
        db: Session,
        invoice_id: int,
        reason: str,
        user: str = "admin"
    ) -> CreditNote:
        """
        Auditing expectation: 'posted invoices are cancelled with a credit note, not deleted.'
        Reverses stock movement if previously dispatched.
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError("Invoice not found")

        now = utc_now()
        count = db.query(CreditNote).count() + 1
        cn_number = f"CN-{now.year}-{count:03d}"

        # If already dispatched, restore stock in the ledger with a credit movement
        if invoice.is_dispatched:
            for inv_item in invoice.items:
                LedgerService.record_movement(
                    db=db,
                    item_id=inv_item.item_id,
                    quantity=Decimal(str(inv_item.quantity)), # Positive reversal
                    unit_cost=inv_item.unit_price,
                    movement_type=MovementType.SALES_RETURN,
                    reference_type="CREDIT_NOTE",
                    reference_id=cn_number,
                    notes=f"Reversal for cancelled invoice {invoice.invoice_number}",
                    user=user
                )

        credit_note = CreditNote(
            credit_note_number=cn_number,
            invoice_id=invoice.id,
            date=now,
            reason=reason,
            taxable_amount=invoice.taxable_amount,
            gst_amount=invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount,
            total_amount=invoice.total_amount
        )
        invoice.status = InvoiceStatus.CANCELLED_VIA_CREDIT_NOTE

        db.add(credit_note)
        db.add(AuditLog(
            entity_name="INVOICE",
            entity_id=str(invoice.id),
            action="CANCEL",
            performed_by=user,
            details=f"Invoice {invoice.invoice_number} cancelled via Credit Note {cn_number}. Reason: {reason}"
        ))
        db.commit()
        db.refresh(credit_note)
        return credit_note
