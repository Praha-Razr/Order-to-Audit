from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

from app.database import get_db
from app.models import BOM, ProductionRun
from app.schemas import BOMResponse, BOMItemResponse, ProductionRunCreate
from app.services.production_service import ProductionService

router = APIRouter(prefix="/production", tags=["BOM & Production"])

@router.get("/boms", response_model=List[BOMResponse])
def list_boms(db: Session = Depends(get_db)):
    boms = db.query(BOM).all()
    res = []
    for b in boms:
        items = []
        for i in b.items:
            items.append(BOMItemResponse(
                id=i.id,
                item_id=i.item_id,
                item_name=i.item.name,
                item_code=i.item.code,
                quantity=float(i.quantity),
                unit=i.unit
            ))
        res.append(BOMResponse(
            id=b.id,
            name=b.name,
            batch_output_qty=float(b.batch_output_qty),
            output_unit=b.output_unit,
            items=items
        ))
    return res

@router.post("/run")
def record_production_run(payload: ProductionRunCreate, db: Session = Depends(get_db)):
    """
    Records a production batch:
    - Calculates planned vs actual consumption and yield
    - Updates raw material, packaging, and finished goods stock in ledger
    - Calculates cost per packet and margins
    """
    try:
        materials = [
            {
                "item_id": m.item_id,
                "actual_qty": Decimal(str(m.actual_qty)),
                "unit_rate": Decimal(str(m.unit_rate)) if m.unit_rate is not None else None
            }
            for m in payload.materials_issued
        ]
        
        run = ProductionService.record_production_run(
            db=db,
            bom_id=payload.bom_id,
            actual_output_qty=Decimal(str(payload.actual_output_qty)),
            materials_issued=materials,
            labour_cost=Decimal(str(payload.labour_cost)),
            power_gas_cost=Decimal(str(payload.power_gas_cost)),
            damaged_pouches_qty=Decimal(str(payload.damaged_pouches_qty)),
            notes=payload.notes,
            user=payload.user
        )
        
        return {
            "message": "Production run recorded successfully",
            "run_number": run.run_number,
            "planned_output": float(run.planned_output_qty),
            "actual_output": float(run.actual_output_qty),
            "yield_variance_percent": float(run.yield_variance_percent),
            "total_material_cost": float(run.total_material_cost),
            "total_production_cost": float(run.total_production_cost),
            "cost_per_packet": float(run.cost_per_packet),
            "margin_percent": float(run.margin_percent)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/runs")
def list_production_runs(db: Session = Depends(get_db)):
    runs = db.query(ProductionRun).order_by(ProductionRun.run_date.desc()).all()
    res = []
    for r in runs:
        items = []
        for it in r.items:
            items.append({
                "item_name": it.item.name,
                "standard_qty": float(it.standard_qty),
                "actual_qty": float(it.actual_qty),
                "unit": it.unit,
                "variance_percent": float(it.consumption_variance_percent),
                "is_damaged_scrap": it.is_damaged_scrap,
                "unit_cost": float(it.unit_cost),
                "total_cost": float(it.total_cost)
            })
        res.append({
            "id": r.id,
            "run_number": r.run_number,
            "product_name": r.product.name,
            "run_date": r.run_date.isoformat(),
            "planned_output": float(r.planned_output_qty),
            "actual_output": float(r.actual_output_qty),
            "yield_variance_percent": float(r.yield_variance_percent),
            "labour_cost": float(r.labour_cost),
            "power_gas_cost": float(r.power_gas_cost),
            "total_production_cost": float(r.total_production_cost),
            "cost_per_packet": float(r.cost_per_packet),
            "margin_percent": float(r.margin_percent),
            "items": items
        })
    return res
