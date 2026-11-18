from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import StockMovement, Item, MovementType, AuditLog, utc_now

class LedgerService:
    @staticmethod
    def get_stock_balance(db: Session, item_id: int) -> Decimal:
        """
        Derives current stock balance exclusively by summing the immutable ledger of movements.
        """
        result = db.query(func.coalesce(func.sum(StockMovement.quantity), Decimal("0.0000")))\
                   .filter(StockMovement.item_id == item_id)\
                   .scalar()
        return Decimal(str(result))

    @staticmethod
    def get_all_stock_balances(db: Session) -> Dict[int, Decimal]:
        """
        Returns a dictionary of item_id -> current stock balance.
        """
        results = db.query(StockMovement.item_id, func.coalesce(func.sum(StockMovement.quantity), Decimal("0.0000")))\
                    .group_by(StockMovement.item_id)\
                    .all()
        return {r[0]: Decimal(str(r[1])) for r in results}

    @staticmethod
    def record_movement(
        db: Session,
        item_id: int,
        quantity: Decimal,
        unit_cost: Decimal,
        movement_type: MovementType,
        reference_type: str,
        reference_id: str,
        batch_number: Optional[str] = None,
        notes: Optional[str] = None,
        user: str = "system",
        timestamp: Optional[datetime] = None
    ) -> StockMovement:
        """
        Appends an immutable movement to the stock ledger.
        """
        movement = StockMovement(
            timestamp=timestamp or utc_now(),
            item_id=item_id,
            quantity=quantity,
            unit_cost=unit_cost,
            movement_type=movement_type,
            reference_type=reference_type,
            reference_id=str(reference_id),
            batch_number=batch_number,
            notes=notes,
            created_by=user
        )
        db.add(movement)
        return movement

    @staticmethod
    def get_stock_ledger(
        db: Session,
        item_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns the stock ledger with running balance for an item or all items.
        """
        query = db.query(StockMovement).join(Item)
        if item_id:
            query = query.filter(StockMovement.item_id == item_id)
        if from_date:
            query = query.filter(StockMovement.timestamp >= from_date)
        if to_date:
            query = query.filter(StockMovement.timestamp <= to_date)
        
        movements = query.order_by(StockMovement.item_id, StockMovement.timestamp.asc()).all()
        
        ledger_entries = []
        running_balances: Dict[int, Decimal] = {}
        
        for m in movements:
            current_bal = running_balances.get(m.item_id, Decimal("0.0000"))
            new_bal = current_bal + Decimal(str(m.quantity))
            running_balances[m.item_id] = new_bal
            
            ledger_entries.append({
                "id": m.id,
                "timestamp": m.timestamp.isoformat(),
                "item_id": m.item_id,
                "item_code": m.item.code,
                "item_name": m.item.name,
                "category": m.item.category.value,
                "unit": m.item.unit,
                "movement_type": m.movement_type.value,
                "reference_type": m.reference_type,
                "reference_id": m.reference_id,
                "quantity": float(m.quantity),
                "unit_cost": float(m.unit_cost),
                "running_balance": float(new_bal),
                "notes": m.notes,
                "created_by": m.created_by
            })
            
        return ledger_entries

    @staticmethod
    def get_stock_summary(db: Session) -> List[Dict[str, Any]]:
        """
        Computes Opening + Receipts - Issues = Closing balance for all items.
        """
        items = db.query(Item).order_by(Item.category, Item.name).all()
        summary = []
        
        for item in items:
            movements = db.query(StockMovement).filter(StockMovement.item_id == item.id).all()
            
            opening = Decimal("0.0000")
            receipts = Decimal("0.0000")
            issues = Decimal("0.0000")
            
            for m in movements:
                qty = Decimal(str(m.quantity))
                if m.movement_type == MovementType.OPENING_BALANCE:
                    opening += qty
                elif qty > 0:
                    receipts += qty
                else:
                    issues += abs(qty)
                    
            closing = opening + receipts - issues
            
            summary.append({
                "item_id": item.id,
                "code": item.code,
                "name": item.name,
                "category": item.category.value,
                "unit": item.unit,
                "opening_stock": float(opening),
                "receipts": float(receipts),
                "issues": float(issues),
                "closing_stock": float(closing)
            })
            
        return summary
