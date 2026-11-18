from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

# User
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str

# Items
class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    category: str
    unit: str
    pack_size_grams: Optional[float] = None
    hsn_code: str
    gst_rate: float
    selling_price: Optional[float] = None
    standard_cost: Optional[float] = None
    current_stock: float = 0.0

class ItemCreate(BaseModel):
    code: str
    name: str
    category: str
    unit: str
    pack_size_grams: Optional[float] = None
    hsn_code: str = "1905"
    gst_rate: float = 0.05
    selling_price: Optional[float] = None
    standard_cost: Optional[float] = None

# Customer
class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str
    state: str
    state_code: str
    gstin: Optional[str] = None
    address: Optional[str] = None

# BOM
class BOMItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    item_code: str
    quantity: float
    unit: str

class BOMResponse(BaseModel):
    id: int
    name: str
    batch_output_qty: float
    output_unit: str
    items: List[BOMItemResponse] = []

# Production Run
class MaterialIssueInput(BaseModel):
    item_id: int
    actual_qty: float
    unit_rate: Optional[float] = None

class ProductionRunCreate(BaseModel):
    bom_id: int
    actual_output_qty: float
    materials_issued: List[MaterialIssueInput]
    labour_cost: float = 0.0
    power_gas_cost: float = 0.0
    damaged_pouches_qty: float = 0.0
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None
    user: str = "supervisor"

class PurchaseCreate(BaseModel):
    item_id: int
    quantity: float
    unit_cost: float
    reference_id: str
    notes: Optional[str] = None
    user: str = "admin"

# Sales Order
class OrderItemInput(BaseModel):
    item_id: int
    quantity: float
    unit_price: Optional[float] = None

class OrderCreate(BaseModel):
    salesman_id: int
    customer_id: int
    items: List[OrderItemInput]
    user: str = "salesman"

# Payment
class PaymentCreate(BaseModel):
    customer_id: int
    amount: float
    invoice_id: Optional[int] = None
    payment_mode: str = "Bank Transfer"
    reference: Optional[str] = None
    notes: Optional[str] = None
    user: str = "admin"

# Credit Note / Cancellation
class InvoiceCancelInput(BaseModel):
    reason: str
    user: str = "admin"
