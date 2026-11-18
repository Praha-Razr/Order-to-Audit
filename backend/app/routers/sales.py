from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

from app.database import get_db
from app.models import Customer, SalesOrder, Invoice, Payment, CreditNote, OrderStatus, InvoiceStatus
from app.schemas import CustomerResponse, OrderCreate, PaymentCreate, InvoiceCancelInput
from app.services.sales_service import SalesService

router = APIRouter(prefix="/sales", tags=["Sales & Invoicing"])

@router.get("/customers", response_model=List[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).all()

@router.post("/orders")
def create_sales_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """
    Salesman places order (from mobile UI).
    Automatically validates finished goods stock and flags shortage if insufficient.
    """
    try:
        items_data = [
            {
                "item_id": i.item_id,
                "quantity": Decimal(str(i.quantity)),
                "unit_price": Decimal(str(i.unit_price)) if i.unit_price is not None else None
            }
            for i in payload.items
        ]
        order = SalesService.create_sales_order(
            db=db,
            salesman_id=payload.salesman_id,
            customer_id=payload.customer_id,
            items_data=items_data,
            user=payload.user
        )
        return {
            "message": "Order placed successfully",
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "shortage_flag": order.shortage_flag,
            "shortage_qty": float(order.shortage_qty),
            "shortage_notes": order.shortage_notes,
            "total_taxable_amount": float(order.total_taxable_amount),
            "total_gst_amount": float(order.total_gst_amount),
            "total_amount": float(order.total_amount)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(SalesOrder).order_by(SalesOrder.order_date.desc()).all()
    res = []
    for o in orders:
        items = []
        for it in o.items:
            items.append({
                "item_name": it.item.name,
                "ordered_qty": float(it.ordered_qty),
                "unit_price": float(it.unit_price),
                "taxable_amount": float(it.taxable_amount),
                "total_amount": float(it.total_amount)
            })
        res.append({
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": o.customer.name,
            "customer_state": o.customer.state,
            "salesman_name": o.salesman.full_name,
            "order_date": o.order_date.isoformat(),
            "status": o.status.value,
            "shortage_flag": o.shortage_flag,
            "shortage_qty": float(o.shortage_qty),
            "shortage_notes": o.shortage_notes,
            "total_amount": float(o.total_amount),
            "items": items
        })
    return res

@router.post("/orders/{order_id}/approve")
def approve_order(order_id: int, user: str = "admin", db: Session = Depends(get_db)):
    try:
        order = SalesService.approve_order(db=db, order_id=order_id, user=user)
        return {"message": f"Order {order.order_number} approved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders/{order_id}/invoice")
def generate_gst_invoice(order_id: int, user: str = "admin", db: Session = Depends(get_db)):
    """
    Raises GST Tax Invoice:
    - Automatically calculates CGST + SGST (Intra-state) vs IGST (Inter-state)
    - Financial year sequence numbering
    """
    try:
        inv = SalesService.generate_gst_invoice(db=db, order_id=order_id, user=user)
        return {
            "message": "GST Tax invoice generated",
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "taxable_amount": float(inv.taxable_amount),
            "cgst_amount": float(inv.cgst_amount),
            "sgst_amount": float(inv.sgst_amount),
            "igst_amount": float(inv.igst_amount),
            "total_amount": float(inv.total_amount),
            "place_of_supply": inv.place_of_supply,
            "is_inter_state": inv.is_inter_state
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/invoices/{invoice_id}/dispatch")
def dispatch_invoice(invoice_id: int, user: str = "admin", db: Session = Depends(get_db)):
    """
    Records dispatch, reducing Finished Goods stock in the ledger.
    """
    try:
        inv = SalesService.record_dispatch(db=db, invoice_id=invoice_id, user=user)
        return {"message": f"Invoice {inv.invoice_number} dispatched successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/invoices")
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
    res = []
    for inv in invoices:
        res.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "customer_name": inv.customer.name,
            "customer_state": inv.customer.state,
            "date": inv.invoice_date.strftime("%Y-%m-%d"),
            "taxable_amount": float(inv.taxable_amount),
            "cgst_amount": float(inv.cgst_amount),
            "sgst_amount": float(inv.sgst_amount),
            "igst_amount": float(inv.igst_amount),
            "total_amount": float(inv.total_amount),
            "status": inv.status.value,
            "is_dispatched": inv.is_dispatched
        })
    return res

@router.post("/invoices/{invoice_id}/cancel")
def cancel_invoice(invoice_id: int, payload: InvoiceCancelInput, db: Session = Depends(get_db)):
    """
    Cancels posted invoice with a Credit Note and logs audit trail.
    """
    try:
        cn = SalesService.cancel_invoice_with_credit_note(
            db=db, invoice_id=invoice_id, reason=payload.reason, user=payload.user
        )
        return {
            "message": "Invoice cancelled via Credit Note",
            "credit_note_number": cn.credit_note_number,
            "reversal_total": float(cn.total_amount)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payments")
def record_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    try:
        payment = SalesService.record_payment(
            db=db,
            customer_id=payload.customer_id,
            amount=Decimal(str(payload.amount)),
            invoice_id=payload.invoice_id,
            payment_mode=payload.payment_mode,
            reference=payload.reference,
            notes=payload.notes,
            user=payload.user
        )
        outstanding = SalesService.get_customer_outstanding(db, payload.customer_id)
        return {
            "message": f"Payment of ₹{payload.amount} recorded",
            "payment_number": payment.payment_number,
            "customer_outstanding": outstanding
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/receivables")
def get_receivables(db: Session = Depends(get_db)):
    return [SalesService.get_customer_outstanding(db, c.id) for c in db.query(Customer).all()]
