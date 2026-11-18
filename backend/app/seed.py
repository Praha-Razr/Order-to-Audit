from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.models import (
    User, UserRole, Item, ItemCategory, BOM, BOMItem,
    Customer, MovementType, StockMovement, AuditLog
)
from app.services.ledger_service import LedgerService

def seed_master_data(db: Session = None):
    """
    Seeds the exact Section 5 master data and opening stock:
    - Flour: 100 kg @ ₹42
    - Cooking oil: 30 L @ ₹140
    - Spice mix: 5 kg @ ₹200
    - 200g pouch: 500 pieces @ ₹2.50
    - Carton: 30 pieces @ ₹15
    - Murukku 200g: 50 packets @ ₹50 selling price
    - Customers: Retailer A (TN) and Distributor B (KA)
    - Standard Users for each of the roles
    """
    close_db = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db = True

    try:
        # Check if already seeded
        if db.query(Item).count() > 0:
            print("Master data already seeded.")
            return

        print("Seeding Users...")
        users = [
            User(username="salesman_a", full_name="Salesman A (Tamil Nadu)", role=UserRole.SALESMAN),
            User(username="salesman_b", full_name="Salesman B (Karnataka)", role=UserRole.SALESMAN),
            User(username="admin", full_name="Factory Admin Desk", role=UserRole.ADMIN),
            User(username="supervisor", full_name="Production Floor Supervisor", role=UserRole.PRODUCTION_SUPERVISOR),
            User(username="auditor", full_name="External Auditor / Accountant", role=UserRole.AUDITOR),
            User(username="owner", full_name="Factory Owner / MD", role=UserRole.OWNER),
        ]
        db.add_all(users)
        db.flush()

        print("Seeding Customers...")
        cust_a = Customer(
            name="Retailer A",
            type="RETAILER",
            state="Tamil Nadu",
            state_code="33",
            gstin="33AABCR1234A1Z1",
            address="Gandhi Bazaar, Tiruchirappalli, Tamil Nadu"
        )
        cust_b = Customer(
            name="Distributor B",
            type="DISTRIBUTOR",
            state="Karnataka",
            state_code="29",
            gstin="29XYZPK9876K1Z9",
            address="APMC Yard, Bengaluru, Karnataka"
        )
        db.add_all([cust_a, cust_b])
        db.flush()

        print("Seeding Items...")
        flour = Item(
            code="RM-FLOUR",
            name="Flour (Raw Material)",
            category=ItemCategory.RAW_MATERIAL,
            unit="kg",
            hsn_code="1101",
            gst_rate=Decimal("0.0500"),
            standard_cost=Decimal("42.00")
        )
        oil = Item(
            code="RM-OIL",
            name="Cooking Oil (Raw Material)",
            category=ItemCategory.RAW_MATERIAL,
            unit="litre",
            hsn_code="1512",
            gst_rate=Decimal("0.0500"),
            standard_cost=Decimal("140.00")
        )
        spice = Item(
            code="RM-SPICE",
            name="Salt and Spice Mix (Raw Material)",
            category=ItemCategory.RAW_MATERIAL,
            unit="kg",
            hsn_code="0910",
            gst_rate=Decimal("0.0500"),
            standard_cost=Decimal("200.00")
        )
        pouch = Item(
            code="PM-POUCH-200",
            name="200 g Printed Pouch (Packaging)",
            category=ItemCategory.PACKAGING,
            unit="piece",
            hsn_code="3923",
            gst_rate=Decimal("0.1800"),
            standard_cost=Decimal("2.50")
        )
        carton = Item(
            code="PM-CARTON-20",
            name="Carton (holds 20 pkts) (Packaging)",
            category=ItemCategory.PACKAGING,
            unit="piece",
            hsn_code="4819",
            gst_rate=Decimal("0.1200"),
            standard_cost=Decimal("15.00")
        )
        murukku = Item(
            code="FG-MURUKKU-200",
            name="Murukku 200 g",
            category=ItemCategory.FINISHED_GOOD,
            unit="packet",
            pack_size_grams=Decimal("200.00"),
            hsn_code="1905",
            gst_rate=Decimal("0.0500"),
            selling_price=Decimal("50.00"),
            standard_cost=Decimal("31.14")
        )
        db.add_all([flour, oil, spice, pouch, carton, murukku])
        db.flush()

        print("Seeding BOM for Murukku 200 g (1 batch = 200 packets)...")
        bom = BOM(
            product_id=murukku.id,
            name="Standard BOM - Murukku 200g (Batch = 200 pkts)",
            batch_output_qty=Decimal("200.00"),
            output_unit="packet"
        )
        db.add(bom)
        db.flush()

        bom_lines = [
            BOMItem(bom_id=bom.id, item_id=flour.id, quantity=Decimal("40.00"), unit="kg"),
            BOMItem(bom_id=bom.id, item_id=oil.id, quantity=Decimal("10.00"), unit="litre"),
            BOMItem(bom_id=bom.id, item_id=spice.id, quantity=Decimal("1.20"), unit="kg"),
            BOMItem(bom_id=bom.id, item_id=pouch.id, quantity=Decimal("200.00"), unit="piece"),
            BOMItem(bom_id=bom.id, item_id=carton.id, quantity=Decimal("10.00"), unit="piece"),
        ]
        db.add_all(bom_lines)
        db.flush()

        print("Recording Section 5 Opening Stock Balances in Ledger...")
        opening_stocks = [
            (flour.id, Decimal("100.00"), Decimal("42.00"), "Opening stock: 100 kg flour @ ₹42"),
            (oil.id, Decimal("30.00"), Decimal("140.00"), "Opening stock: 30 L cooking oil @ ₹140"),
            (spice.id, Decimal("5.00"), Decimal("200.00"), "Opening stock: 5 kg spice mix @ ₹200"),
            (pouch.id, Decimal("500.00"), Decimal("2.50"), "Opening stock: 500 pouches @ ₹2.50"),
            (carton.id, Decimal("30.00"), Decimal("15.00"), "Opening stock: 30 cartons @ ₹15"),
            (murukku.id, Decimal("50.00"), Decimal("31.14"), "Opening stock: 50 packets Murukku 200g"),
        ]

        for item_id, qty, cost, note in opening_stocks:
            LedgerService.record_movement(
                db=db,
                item_id=item_id,
                quantity=qty,
                unit_cost=cost,
                movement_type=MovementType.OPENING_BALANCE,
                reference_type="OPENING",
                reference_id="OPENING-2026",
                notes=note,
                user="admin"
            )

        db.add(AuditLog(
            entity_name="SYSTEM",
            entity_id="SEED",
            action="INITIALIZE",
            performed_by="system",
            details="Section 5 benchmark master data and opening stock initialized successfully"
        ))

        db.commit()
        print("Master data and opening stocks seeded successfully!")
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_master_data()
