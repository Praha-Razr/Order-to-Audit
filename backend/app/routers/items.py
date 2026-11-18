from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

from app.database import get_db
from app.models import Item, MovementType
from app.schemas import ItemResponse, ItemCreate, PurchaseCreate
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/items", tags=["Inventory & Items"])

@router.get("", response_model=List[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    """
    Lists all master items with current stock derived from the ledger.
    """
    items = db.query(Item).all()
    balances = LedgerService.get_all_stock_balances(db)
    
    result = []
    for item in items:
        item_dict = {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "category": item.category.value,
            "unit": item.unit,
            "pack_size_grams": float(item.pack_size_grams) if item.pack_size_grams else None,
            "hsn_code": item.hsn_code,
            "gst_rate": float(item.gst_rate),
            "selling_price": float(item.selling_price) if item.selling_price else None,
            "standard_cost": float(item.standard_cost) if item.standard_cost else None,
            "current_stock": float(balances.get(item.id, Decimal("0.00")))
        }
        result.append(ItemResponse(**item_dict))
    return result

@router.post("", response_model=ItemResponse)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    """
    Create a new item (e.g. during live interview: adding a second pack size of 500 g).
    """
    existing = db.query(Item).filter(Item.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Item with code {payload.code} already exists")
        
    item = Item(
        code=payload.code,
        name=payload.name,
        category=payload.category,
        unit=payload.unit,
        pack_size_grams=Decimal(str(payload.pack_size_grams)) if payload.pack_size_grams else None,
        hsn_code=payload.hsn_code,
        gst_rate=Decimal(str(payload.gst_rate)),
        selling_price=Decimal(str(payload.selling_price)) if payload.selling_price else None,
        standard_cost=Decimal(str(payload.standard_cost)) if payload.standard_cost else None
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.post("/purchase")
def record_purchase(payload: PurchaseCreate, db: Session = Depends(get_db)):
    """
    Records raw material purchase (Step 1 of benchmark).
    """
    item = db.query(Item).filter(Item.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    movement = LedgerService.record_movement(
        db=db,
        item_id=payload.item_id,
        quantity=Decimal(str(payload.quantity)),
        unit_cost=Decimal(str(payload.unit_cost)),
        movement_type=MovementType.PURCHASE_RECEIPT,
        reference_type="PURCHASE",
        reference_id=payload.reference_id,
        notes=payload.notes,
        user=payload.user
    )
    db.commit()
    new_balance = LedgerService.get_stock_balance(db, payload.item_id)
    return {
        "message": f"Recorded purchase of {payload.quantity} {item.unit} {item.name}",
        "item_id": payload.item_id,
        "quantity_purchased": payload.quantity,
        "unit_cost": payload.unit_cost,
        "new_stock_balance": float(new_balance)
    }

@router.get("/stock-summary")
def get_stock_summary(db: Session = Depends(get_db)):
    """
    Opening + Receipts - Issues = Closing stock table for all items.
    """
    return LedgerService.get_stock_summary(db)

@router.get("/ledger")
def get_stock_ledger(item_id: int = None, db: Session = Depends(get_db)):
    """
    Immutable audit ledger of every single movement.
    """
    return LedgerService.get_stock_ledger(db, item_id=item_id)
