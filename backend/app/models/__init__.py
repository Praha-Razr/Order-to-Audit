import enum
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Numeric, 
    ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

# Enums
class UserRole(str, enum.Enum):
    SALESMAN = "SALESMAN"
    ADMIN = "ADMIN"
    PRODUCTION_SUPERVISOR = "PRODUCTION_SUPERVISOR"
    AUDITOR = "AUDITOR"
    OWNER = "OWNER"

class ItemCategory(str, enum.Enum):
    RAW_MATERIAL = "RAW_MATERIAL"
    PACKAGING = "PACKAGING"
    FINISHED_GOOD = "FINISHED_GOOD"

class MovementType(str, enum.Enum):
    OPENING_BALANCE = "OPENING_BALANCE"
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    PRODUCTION_ISSUE = "PRODUCTION_ISSUE"
    PRODUCTION_YIELD = "PRODUCTION_YIELD"
    SCRAP_DAMAGE = "SCRAP_DAMAGE"
    SALES_DISPATCH = "SALES_DISPATCH"
    SALES_RETURN = "SALES_RETURN"
    ADJUSTMENT = "ADJUSTMENT"

class OrderStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    INVOICED = "INVOICED"
    DISPATCHED = "DISPATCHED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class InvoiceStatus(str, enum.Enum):
    POSTED = "POSTED"
    DISPATCHED = "DISPATCHED"
    CANCELLED_VIA_CREDIT_NOTE = "CANCELLED_VIA_CREDIT_NOTE"

class ProductionStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(Enum(ItemCategory), nullable=False, index=True)
    unit = Column(String(20), nullable=False)  # kg, litre, piece, packet, carton
    pack_size_grams = Column(Numeric(10, 2), nullable=True) # e.g. 200 for 200g
    hsn_code = Column(String(20), nullable=False, default="1905")
    gst_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0500")) # 5% default
    selling_price = Column(Numeric(12, 2), nullable=True) # e.g. ₹50.00 for Murukku 200g
    standard_cost = Column(Numeric(12, 2), nullable=True)

    stock_movements = relationship("StockMovement", back_populates="item")

class BOM(Base):
    __tablename__ = "boms"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    name = Column(String(100), nullable=False)
    batch_output_qty = Column(Numeric(12, 2), nullable=False, default=Decimal("200"))
    output_unit = Column(String(20), nullable=False, default="packet")
    is_active = Column(Boolean, default=True)

    product = relationship("Item")
    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")

class BOMItem(Base):
    __tablename__ = "bom_items"
    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)

    bom = relationship("BOM", back_populates="items")
    item = relationship("Item")

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    quantity = Column(Numeric(12, 4), nullable=False) # Positive = IN, Negative = OUT
    unit_cost = Column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    movement_type = Column(Enum(MovementType), nullable=False, index=True)
    reference_type = Column(String(50), nullable=False) # PURCHASE, PRODUCTION_RUN, SALES_INVOICE, etc.
    reference_id = Column(String(50), nullable=False)
    batch_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)

    item = relationship("Item", back_populates="stock_movements")

class ProductionRun(Base):
    __tablename__ = "production_runs"
    id = Column(Integer, primary_key=True, index=True)
    run_number = Column(String(50), unique=True, nullable=False, index=True)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    run_date = Column(DateTime, default=utc_now, nullable=False)
    
    planned_output_qty = Column(Numeric(12, 2), nullable=False)
    actual_output_qty = Column(Numeric(12, 2), nullable=False)
    yield_variance_percent = Column(Numeric(8, 2), nullable=False)
    
    labour_cost = Column(Numeric(12, 2), default=Decimal("0.00"))
    power_gas_cost = Column(Numeric(12, 2), default=Decimal("0.00"))
    total_material_cost = Column(Numeric(12, 2), default=Decimal("0.00"))
    total_production_cost = Column(Numeric(12, 2), default=Decimal("0.00"))
    cost_per_packet = Column(Numeric(12, 2), default=Decimal("0.00"))
    margin_percent = Column(Numeric(8, 2), default=Decimal("0.00"))
    
    status = Column(Enum(ProductionStatus), default=ProductionStatus.COMPLETED)
    notes = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)

    bom = relationship("BOM")
    product = relationship("Item")
    items = relationship("ProductionRunItem", back_populates="production_run", cascade="all, delete-orphan")

class ProductionRunItem(Base):
    __tablename__ = "production_run_items"
    id = Column(Integer, primary_key=True, index=True)
    production_run_id = Column(Integer, ForeignKey("production_runs.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    standard_qty = Column(Numeric(12, 4), nullable=False)
    actual_qty = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    consumption_variance_percent = Column(Numeric(8, 2), nullable=False, default=Decimal("0.00"))
    is_damaged_scrap = Column(Boolean, default=False)
    unit_cost = Column(Numeric(12, 4), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)

    production_run = relationship("ProductionRun", back_populates="items")
    item = relationship("Item")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), default="RETAILER") # RETAILER or DISTRIBUTOR
    state = Column(String(50), nullable=False)
    state_code = Column(String(5), nullable=False)
    gstin = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    salesman_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=utc_now, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.SUBMITTED, index=True)
    
    shortage_flag = Column(Boolean, default=False)
    shortage_qty = Column(Numeric(12, 2), default=Decimal("0.00"))
    shortage_notes = Column(Text, nullable=True)
    
    total_taxable_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    total_gst_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    total_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    
    salesman = relationship("User")
    customer = relationship("Customer")
    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="order", uselist=False)

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    id = Column(Integer, primary_key=True, index=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    ordered_qty = Column(Numeric(12, 2), nullable=False)
    approved_qty = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    gst_rate = Column(Numeric(5, 4), nullable=False)
    gst_amount = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    order = relationship("SalesOrder", back_populates="items")
    item = relationship("Item")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    financial_year = Column(String(10), nullable=False, default="2026-27")
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_date = Column(DateTime, default=utc_now, nullable=False)
    
    place_of_supply = Column(String(50), nullable=False)
    is_inter_state = Column(Boolean, default=False)
    
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    cgst_rate = Column(Numeric(5, 4), default=Decimal("0.0000"))
    cgst_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    sgst_rate = Column(Numeric(5, 4), default=Decimal("0.0000"))
    sgst_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    igst_rate = Column(Numeric(5, 4), default=Decimal("0.0000"))
    igst_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.POSTED, index=True)
    is_dispatched = Column(Boolean, default=False)
    dispatched_at = Column(DateTime, nullable=True)

    order = relationship("SalesOrder", back_populates="invoice")
    customer = relationship("Customer")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    hsn_code = Column(String(20), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    cgst_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    sgst_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    igst_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    total_amount = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    item = relationship("Item")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    payment_date = Column(DateTime, default=utc_now, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_mode = Column(String(50), default="Bank Transfer")
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    customer = relationship("Customer")
    invoice = relationship("Invoice", back_populates="payments")

class CreditNote(Base):
    __tablename__ = "credit_notes"
    id = Column(Integer, primary_key=True, index=True)
    credit_note_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    date = Column(DateTime, default=utc_now, nullable=False)
    reason = Column(Text, nullable=False)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    gst_amount = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    entity_name = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    performed_by = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
