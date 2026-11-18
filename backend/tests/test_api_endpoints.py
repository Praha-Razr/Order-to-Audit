import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.seed import seed_master_data
from app.schemas import PurchaseCreate, OrderCreate, OrderItemInput, ProductionRunCreate, MaterialIssueInput, PaymentCreate
from app.routers.items import list_items, record_purchase, get_stock_summary
from app.routers.production import list_boms, record_production_run
from app.routers.sales import create_sales_order, approve_order, generate_gst_invoice, dispatch_invoice, record_payment
from app.routers.reports import get_owner_dashboard, get_gst_summary

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    seed_master_data(db)
    yield db
    db.close()

def test_items_and_purchase_api(db_session):
    items = list_items(db=db_session)
    assert len(items) >= 6
    flour_item = [i for i in items if i.code == "RM-FLOUR"][0]
    assert flour_item.current_stock == 100.0

    # Test purchase endpoint
    purchase_payload = PurchaseCreate(
        item_id=flour_item.id,
        quantity=60.0,
        unit_cost=45.0,
        reference_id="PO-TEST-001",
        notes="60 kg flour purchase"
    )
    res = record_purchase(payload=purchase_payload, db=db_session)
    assert res["new_stock_balance"] == 160.0

def test_production_and_dashboard_api(db_session):
    boms = list_boms(db=db_session)
    assert len(boms) >= 1
    bom = boms[0]

    # Test production run endpoint
    run_payload = ProductionRunCreate(
        bom_id=bom.id,
        actual_output_qty=188.0,
        materials_issued=[
            MaterialIssueInput(item_id=b.item_id, actual_qty=b.quantity)
            for b in bom.items
        ],
        labour_cost=1200.0,
        power_gas_cost=600.0,
        damaged_pouches_qty=6.0
    )
    res = record_production_run(payload=run_payload, db=db_session)
    assert res["actual_output"] == 188.0
    assert res["yield_variance_percent"] == -6.0

    # Test Dashboard API
    dash = get_owner_dashboard(db=db_session)
    assert "stock_summary" in dash
    assert dash["latest_cost_per_packet"] > 0

def test_order_rejection_edit_and_tally_xml(db_session):
    from app.routers.sales import reject_order, edit_order
    from app.routers.reports import export_tally_xml
    from app.routers.items import reset_benchmark_data
    from app.models import Item, Customer, User

    flour = db_session.query(Item).filter(Item.code == "RM-FLOUR").first()
    murukku = db_session.query(Item).filter(Item.code == "FG-MURUKKU-200").first()
    cust = db_session.query(Customer).first()
    salesman = db_session.query(User).filter(User.username == "salesman_a").first()

    # Create order
    ord_payload = OrderCreate(
        salesman_id=salesman.id,
        customer_id=cust.id,
        items=[OrderItemInput(item_id=murukku.id, quantity=50.0)]
    )
    order_res = create_sales_order(payload=ord_payload, db=db_session)
    order_id = order_res["order_id"]

    # Test Edit Order Qty
    edit_res = edit_order(order_id=order_id, item_id=murukku.id, quantity=30.0, db=db_session)
    assert edit_res["total_amount"] == 30.0 * 50.0 * 1.05

    # Test Reject Order
    reject_res = reject_order(order_id=order_id, reason="Testing rejection flow", db=db_session)
    assert "rejected" in reject_res["message"]

    # Test Tally XML export
    tally_res = export_tally_xml(db=db_session)
    assert tally_res.status_code == 200
    assert b"<ENVELOPE>" in tally_res.body
    assert b"<TALLYREQUEST>Import Data</TALLYREQUEST>" in tally_res.body

    # Test Reset Benchmark
    reset_res = reset_benchmark_data(db=db_session)
    assert "successfully" in reset_res["message"]
