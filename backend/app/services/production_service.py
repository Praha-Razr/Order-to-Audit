from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    BOM, BOMItem, Item, ProductionRun, ProductionRunItem, 
    ProductionStatus, StockMovement, MovementType, AuditLog, utc_now
)
from app.services.ledger_service import LedgerService
from app.config import settings

class ProductionService:
    @staticmethod
    def get_weighted_average_cost(db: Session, item_id: int) -> Decimal:
        """
        Calculates moving weighted average cost of an item from opening stock and purchases.
        """
        inflow_movements = db.query(StockMovement).filter(
            StockMovement.item_id == item_id,
            StockMovement.quantity > 0,
            StockMovement.movement_type.in_([MovementType.OPENING_BALANCE, MovementType.PURCHASE_RECEIPT])
        ).all()
        
        total_qty = Decimal("0.0000")
        total_val = Decimal("0.0000")
        
        for m in inflow_movements:
            qty = Decimal(str(m.quantity))
            cost = Decimal(str(m.unit_cost))
            total_qty += qty
            total_val += (qty * cost)
            
        if total_qty > 0:
            return (total_val / total_qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            
        # Fallback to standard cost or 0
        item = db.query(Item).filter(Item.id == item_id).first()
        return Decimal(str(item.standard_cost or "0.00"))

    @staticmethod
    def calculate_cost_per_packet(
        material_cost: Decimal,
        labour_cost: Decimal,
        power_gas_cost: Decimal,
        actual_output_qty: Decimal,
        selling_price: Decimal
    ) -> Dict[str, Decimal]:
        """
        Computes total production cost, cost per packet, and profit margin.
        """
        total_cost = material_cost + labour_cost + power_gas_cost
        if actual_output_qty > 0:
            cost_per_pkt = (total_cost / actual_output_qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            cost_per_pkt = Decimal("0.00")
            
        if selling_price > 0 and cost_per_pkt > 0:
            margin_pct = (((selling_price - cost_per_pkt) / selling_price) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            margin_pct = Decimal("0.00")
            
        return {
            "total_material_cost": material_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "total_production_cost": total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "cost_per_packet": cost_per_pkt,
            "margin_percent": margin_pct
        }

    @staticmethod
    def record_production_run(
        db: Session,
        bom_id: int,
        actual_output_qty: Decimal,
        materials_issued: List[Dict[str, Any]],
        labour_cost: Decimal = Decimal("0.00"),
        power_gas_cost: Decimal = Decimal("0.00"),
        damaged_pouches_qty: Decimal = Decimal("0.00"),
        run_number: Optional[str] = None,
        notes: Optional[str] = None,
        user: str = "supervisor"
    ) -> ProductionRun:
        """
        Executes a production run atomically:
        - Validates BOM and inputs
        - Computes planned vs actual yield & consumption variances
        - Decrements raw and packaging materials in the stock ledger
        - Increments finished goods in the stock ledger
        - Computes batch cost and cost per packet
        """
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise ValueError(f"BOM with ID {bom_id} not found")

        finished_item = db.query(Item).filter(Item.id == bom.product_id).first()
        if not finished_item:
            raise ValueError(f"Finished product with ID {bom.product_id} not found")

        planned_output_qty = Decimal(str(bom.batch_output_qty))
        
        # Calculate Yield Variance % = ((Actual - Planned) / Planned) * 100
        yield_var_pct = (((actual_output_qty - planned_output_qty) / planned_output_qty) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if not run_number:
            now = utc_now()
            count = db.query(ProductionRun).count() + 1
            run_number = f"PR-{now.year}-{count:03d}"

        total_material_cost = Decimal("0.00")
        run_items = []

        # Map BOM items for standard comparison
        bom_items_map = {b.item_id: b for b in bom.items}

        # Process each material issue
        for mat in materials_issued:
            item_id = mat["item_id"]
            actual_qty = Decimal(str(mat["actual_qty"]))
            item = db.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise ValueError(f"Item {item_id} not found")

            # Standard quantity from BOM
            standard_qty = Decimal(str(bom_items_map[item_id].quantity)) if item_id in bom_items_map else actual_qty

            # Consumption variance % = ((Actual - Standard) / Standard) * 100
            if standard_qty > 0:
                cons_var_pct = (((actual_qty - standard_qty) / standard_qty) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                cons_var_pct = Decimal("0.00")

            # Unit valuation (weighted average)
            unit_rate = mat.get("unit_rate")
            if unit_rate is None:
                unit_cost = ProductionService.get_weighted_average_cost(db, item_id)
            else:
                unit_cost = Decimal(str(unit_rate))

            line_cost = (actual_qty * unit_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_material_cost += line_cost

            run_item = ProductionRunItem(
                item_id=item_id,
                standard_qty=standard_qty,
                actual_qty=actual_qty,
                unit=item.unit,
                consumption_variance_percent=cons_var_pct,
                is_damaged_scrap=False,
                unit_cost=unit_cost,
                total_cost=line_cost
            )
            run_items.append(run_item)

        # Handle damaged pouches if any
        if damaged_pouches_qty > 0:
            # Find pouch item
            pouch_item = db.query(Item).filter(Item.code.like("%POUCH%")).first()
            if pouch_item:
                pouch_cost = ProductionService.get_weighted_average_cost(db, pouch_item.id)
                damaged_cost = (damaged_pouches_qty * pouch_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_material_cost += damaged_cost

                run_items.append(ProductionRunItem(
                    item_id=pouch_item.id,
                    standard_qty=Decimal("0.00"),
                    actual_qty=damaged_pouches_qty,
                    unit=pouch_item.unit,
                    consumption_variance_percent=Decimal("0.00"),
                    is_damaged_scrap=True,
                    unit_cost=pouch_cost,
                    total_cost=damaged_cost
                ))

        # Costing calculations
        selling_price = Decimal(str(finished_item.selling_price or "0.00"))
        costing_res = ProductionService.calculate_cost_per_packet(
            material_cost=total_material_cost,
            labour_cost=labour_cost,
            power_gas_cost=power_gas_cost,
            actual_output_qty=actual_output_qty,
            selling_price=selling_price
        )

        production_run = ProductionRun(
            run_number=run_number,
            bom_id=bom_id,
            product_id=finished_item.id,
            run_date=utc_now(),
            planned_output_qty=planned_output_qty,
            actual_output_qty=actual_output_qty,
            yield_variance_percent=yield_var_pct,
            labour_cost=labour_cost,
            power_gas_cost=power_gas_cost,
            total_material_cost=costing_res["total_material_cost"],
            total_production_cost=costing_res["total_production_cost"],
            cost_per_packet=costing_res["cost_per_packet"],
            margin_percent=costing_res["margin_percent"],
            status=ProductionStatus.COMPLETED,
            notes=notes,
            created_by=user,
            items=run_items
        )
        db.add(production_run)
        db.flush() # Populate production_run.id

        # Update Stock Ledger Atomically
        # 1. Deduct raw materials issued
        for mat in materials_issued:
            item_id = mat["item_id"]
            actual_qty = Decimal(str(mat["actual_qty"]))
            unit_rate = mat.get("unit_rate")
            if unit_rate is None:
                unit_cost = ProductionService.get_weighted_average_cost(db, item_id)
            else:
                unit_cost = Decimal(str(unit_rate))
                
            LedgerService.record_movement(
                db=db,
                item_id=item_id,
                quantity=-actual_qty, # Negative = Stock Out
                unit_cost=unit_cost,
                movement_type=MovementType.PRODUCTION_ISSUE,
                reference_type="PRODUCTION_RUN",
                reference_id=str(production_run.run_number),
                notes=f"Issued for production run {production_run.run_number}",
                user=user
            )

        # 2. Deduct damaged packaging if any
        if damaged_pouches_qty > 0 and pouch_item:
            LedgerService.record_movement(
                db=db,
                item_id=pouch_item.id,
                quantity=-damaged_pouches_qty,
                unit_cost=pouch_cost,
                movement_type=MovementType.SCRAP_DAMAGE,
                reference_type="PRODUCTION_RUN",
                reference_id=str(production_run.run_number),
                notes=f"Damaged during production run {production_run.run_number}",
                user=user
            )

        # 3. Add Finished Goods produced
        LedgerService.record_movement(
            db=db,
            item_id=finished_item.id,
            quantity=actual_output_qty, # Positive = Stock In
            unit_cost=costing_res["cost_per_packet"],
            movement_type=MovementType.PRODUCTION_YIELD,
            reference_type="PRODUCTION_RUN",
            reference_id=str(production_run.run_number),
            notes=f"Production yield from run {production_run.run_number}",
            user=user
        )

        # Audit Log
        db.add(AuditLog(
            entity_name="PRODUCTION_RUN",
            entity_id=str(production_run.id),
            action="CREATE",
            performed_by=user,
            details=f"Production run {run_number} created with actual yield {actual_output_qty} pkts, yield variance {yield_var_pct}%"
        ))

        db.commit()
        db.refresh(production_run)
        return production_run
