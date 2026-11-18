export interface User {
  id: number;
  username: string;
  full_name: string;
  role: 'SALESMAN' | 'ADMIN' | 'PRODUCTION_SUPERVISOR' | 'AUDITOR' | 'OWNER';
}

export interface Item {
  id: number;
  code: string;
  name: string;
  category: 'RAW_MATERIAL' | 'PACKAGING' | 'FINISHED_GOOD';
  unit: string;
  pack_size_grams?: number;
  hsn_code: string;
  gst_rate: number;
  selling_price?: number;
  standard_cost?: number;
  current_stock: number;
}

export interface Customer {
  id: number;
  name: string;
  type: string;
  state: string;
  state_code: string;
  gstin?: string;
  address?: string;
}

export interface BOMItem {
  id: number;
  item_id: number;
  item_name: string;
  item_code: string;
  quantity: number;
  unit: string;
}

export interface BOM {
  id: number;
  name: string;
  batch_output_qty: number;
  output_unit: string;
  items: BOMItem[];
}

export interface SalesOrder {
  id: number;
  order_number: string;
  customer_name: string;
  customer_state: string;
  salesman_name: string;
  order_date: string;
  status: 'SUBMITTED' | 'APPROVED' | 'INVOICED' | 'DISPATCHED' | 'REJECTED' | 'CANCELLED';
  shortage_flag: boolean;
  shortage_qty: number;
  shortage_notes?: string;
  total_amount: number;
  items: {
    item_name: string;
    ordered_qty: number;
    unit_price: number;
    taxable_amount: number;
    total_amount: number;
  }[];
}

export interface Invoice {
  id: number;
  invoice_number: string;
  customer_name: string;
  customer_state: string;
  date: string;
  taxable_amount: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  total_amount: number;
  status: string;
  is_dispatched: boolean;
}

export interface ProductionRun {
  id: number;
  run_number: string;
  product_name: string;
  run_date: string;
  planned_output: number;
  actual_output: number;
  yield_variance_percent: number;
  labour_cost: number;
  power_gas_cost: number;
  total_production_cost: number;
  cost_per_packet: number;
  margin_percent: number;
  items: {
    item_name: string;
    standard_qty: number;
    actual_qty: number;
    unit: string;
    variance_percent: number;
    is_damaged_scrap: boolean;
    unit_cost: number;
    total_cost: number;
  }[];
}

export interface StockSummaryRow {
  item_id: number;
  code: string;
  name: string;
  category: string;
  unit: string;
  opening_stock: number;
  receipts: number;
  issues: number;
  closing_stock: number;
}

export interface LedgerEntry {
  id: number;
  timestamp: string;
  item_id: number;
  item_code: string;
  item_name: string;
  category: string;
  unit: string;
  movement_type: string;
  reference_type: string;
  reference_id: string;
  quantity: number;
  unit_cost: number;
  running_balance: number;
  notes?: string;
  created_by?: string;
}
