import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Item, Customer, BOM, User, MovementType
from app.seed import seed_master_data
from app.services.ledger_service import LedgerService
from app.services.production_service import ProductionService
from app.services.sales_service import SalesService

@pytest.fixture(scope="function")
def test_db():
    # Use isolated SQLite in-memory database with foreign keys enabled
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    # Seed Section 5 master data and opening stocks
    seed_master_data(db)
    
    yield db
    db.close()

def test_section_5_benchmark_scenario(test_db):
    """
    Executes the exact 9-step benchmark scenario from Section 5 of the problem statement
    and asserts every single result from the official evaluation check table.
    """
    db = test_db

    # Fetch seeded items
    flour = db.query(Item).filter(Item.code == "RM-FLOUR").first()
    oil = db.query(Item).filter(Item.code == "RM-OIL").first()
    spice = db.query(Item).filter(Item.code == "RM-SPICE").first()
    pouch = db.query(Item).filter(Item.code == "PM-POUCH-200").first()
    carton = db.query(Item).filter(Item.code == "PM-CARTON-20").first()
    murukku = db.query(Item).filter(Item.code == "FG-MURUKKU-200").first()
    bom = db.query(BOM).first()

    retailer_a = db.query(Customer).filter(Customer.name == "Retailer A").first()
    distributor_b = db.query(Customer).filter(Customer.name == "Distributor B").first()
    salesman_a = db.query(User).filter(User.username == "salesman_a").first()
    salesman_b = db.query(User).filter(User.username == "salesman_b").first()

    # Verify initial opening stock balances
    assert LedgerService.get_stock_balance(db, flour.id) == Decimal("100.0000")
    assert LedgerService.get_stock_balance(db, oil.id) == Decimal("30.0000")
    assert LedgerService.get_stock_balance(db, spice.id) == Decimal("5.0000")
    assert LedgerService.get_stock_balance(db, pouch.id) == Decimal("500.0000")
    assert LedgerService.get_stock_balance(db, carton.id) == Decimal("30.0000")
    assert LedgerService.get_stock_balance(db, murukku.id) == Decimal("50.0000")

    # -------------------------------------------------------------
    # Step 1: Record a purchase of 60 kg flour at ₹45/kg
    # -------------------------------------------------------------
    LedgerService.record_movement(
        db=db,
        item_id=flour.id,
        quantity=Decimal("60.00"),
        unit_cost=Decimal("45.00"),
        movement_type=MovementType.PURCHASE_RECEIPT,
        reference_type="PURCHASE",
        reference_id="PO-2026-001",
        notes="Purchase 60 kg flour @ ₹45/kg",
        user="admin"
    )
    db.commit()

    # Flour stock after purchase: 100 + 60 = 160 kg
    assert LedgerService.get_stock_balance(db, flour.id) == Decimal("160.0000")

    # -------------------------------------------------------------
    # Step 2 & 3 & 8: Start production run, issue materials, record output & overheads
    # Issues: 40 kg flour, 10.5 L oil (0.5 L over standard), 1.2 kg spice mix, 188 pouches + 6 damaged, 9 cartons used
    # Overheads: Labour ₹1,200, Gas/power ₹600
    # Output: 188 good packets
    # -------------------------------------------------------------
    materials_issued = [
        {"item_id": flour.id, "actual_qty": Decimal("40.00")},
        {"item_id": oil.id, "actual_qty": Decimal("10.50")},
        {"item_id": spice.id, "actual_qty": Decimal("1.20")},
        {"item_id": pouch.id, "actual_qty": Decimal("188.00")},
        {"item_id": carton.id, "actual_qty": Decimal("9.00")},
    ]

    prod_run = ProductionService.record_production_run(
        db=db,
        bom_id=bom.id,
        actual_output_qty=Decimal("188.00"),
        materials_issued=materials_issued,
        labour_cost=Decimal("1200.00"),
        power_gas_cost=Decimal("600.00"),
        damaged_pouches_qty=Decimal("6.00"),
        run_number="PR-2026-001",
        notes="Batch 1 Murukku 200g run",
        user="supervisor"
    )

    # -------------------------------------------------------------
    # Verify Checks After Production:
    # -------------------------------------------------------------
    # Check 1: Flour closing balance: 120 kg (100 + 60 - 40)
    assert LedgerService.get_stock_balance(db, flour.id) == Decimal("120.0000")

    # Check 2: Oil closing balance: 19.5 L (30 - 10.5)
    assert LedgerService.get_stock_balance(db, oil.id) == Decimal("19.5000")

    # Check 3: Pouches closing balance: 306 (500 - 188 used - 6 damaged)
    assert LedgerService.get_stock_balance(db, pouch.id) == Decimal("306.0000")

    # Check 4: Finished goods after run: 238 packets (50 opening + 188 produced)
    assert LedgerService.get_stock_balance(db, murukku.id) == Decimal("238.0000")

    # Check 5: Yield variance: 188 vs 200 expected = -6.00%, flagged (> 3%)
    assert prod_run.yield_variance_percent == Decimal("-6.00")
    assert abs(prod_run.yield_variance_percent) > Decimal("3.0")

    # Check 6: Oil consumption variance: +5.00%, flagged (> 3%)
    oil_run_item = [item for item in prod_run.items if item.item_id == oil.id][0]
    assert oil_run_item.consumption_variance_percent == Decimal("5.00")
    assert oil_run_item.consumption_variance_percent > Decimal("3.0")

    # Check Cost per packet: Total cost ₹5,855 / 188 = ₹31.14
    assert prod_run.cost_per_packet == Decimal("31.14")
    assert prod_run.margin_percent == Decimal("37.72")

    # -------------------------------------------------------------
    # Step 4: Salesman A places order for Retailer A (Tamil Nadu): 150 packets
    # -------------------------------------------------------------
    order_a = SalesService.create_sales_order(
        db=db,
        salesman_id=salesman_a.id,
        customer_id=retailer_a.id,
        items_data=[{"item_id": murukku.id, "quantity": Decimal("150.00")}],
        user="salesman_a"
    )
    assert order_a.shortage_flag is False

    # -------------------------------------------------------------
    # Step 5: Admin approves it, raises GST invoice (CGST + SGST), records dispatch
    # -------------------------------------------------------------
    SalesService.approve_order(db=db, order_id=order_a.id, user="admin")
    invoice_a = SalesService.generate_gst_invoice(db=db, order_id=order_a.id, user="admin")

    # Check 7: Retailer A invoice: ₹7,500 taxable + ₹187.50 CGST + ₹187.50 SGST = ₹7,875
    assert invoice_a.taxable_amount == Decimal("7500.00")
    assert invoice_a.cgst_amount == Decimal("187.50")
    assert invoice_a.sgst_amount == Decimal("187.50")
    assert invoice_a.igst_amount == Decimal("0.00")
    assert invoice_a.total_amount == Decimal("7875.00")

    # Record dispatch
    SalesService.record_dispatch(db=db, invoice_id=invoice_a.id, user="admin")

    # Check 8: Finished goods after Retailer A dispatch: 88 packets (238 - 150)
    assert LedgerService.get_stock_balance(db, murukku.id) == Decimal("88.0000")

    # -------------------------------------------------------------
    # Step 6: Salesman B places order for Distributor B (Karnataka): 120 packets
    # -------------------------------------------------------------
    order_b = SalesService.create_sales_order(
        db=db,
        salesman_id=salesman_b.id,
        customer_id=distributor_b.id,
        items_data=[{"item_id": murukku.id, "quantity": Decimal("120.00")}],
        user="salesman_b"
    )

    # Check 9: Distributor B order: Shortage of 32 packets flagged (120 requested - 88 available)
    assert order_b.shortage_flag is True
    assert order_b.shortage_qty == Decimal("32.00")
    assert "Shortage of 32.0000" in order_b.shortage_notes

    # Verify that if invoiced, IGST 5% applies (Inter-state: TN to KA)
    SalesService.approve_order(db=db, order_id=order_b.id, user="admin")
    invoice_b = SalesService.generate_gst_invoice(db=db, order_id=order_b.id, user="admin")
    assert invoice_b.is_inter_state is True
    assert invoice_b.igst_rate == Decimal("0.0500")
    assert invoice_b.cgst_amount == Decimal("0.00")
    assert invoice_b.sgst_amount == Decimal("0.00")
    assert invoice_b.igst_amount == Decimal("300.00") # 120 * 50 = 6000 * 5% = 300

    # -------------------------------------------------------------
    # Step 7: Record a payment of ₹4,000 from Retailer A
    # -------------------------------------------------------------
    SalesService.record_payment(
        db=db,
        customer_id=retailer_a.id,
        amount=Decimal("4000.00"),
        invoice_id=invoice_a.id,
        payment_mode="Bank Transfer",
        reference="NEFT-RET-A-001",
        user="admin"
    )

    # Check 10: Retailer A outstanding: ₹3,875 (₹7,875 - ₹4,000)
    outstanding_a = SalesService.get_customer_outstanding(db, retailer_a.id)
    assert Decimal(str(outstanding_a["outstanding"])) == Decimal("3875.00")

    print("\n ALL SECTION 5 BENCHMARK CHECKS PASSED WITH 100% PRECISION!")
