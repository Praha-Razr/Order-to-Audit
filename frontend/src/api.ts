const API_BASE = '/api/v1';

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'API Error' }));
    throw new Error(err.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  getUsers: () => fetchApi<any[]>('/auth/users'),
  getItems: () => fetchApi<any[]>('/items'),
  createItem: (data: any) => fetchApi<any>('/items', { method: 'POST', body: JSON.stringify(data) }),
  recordPurchase: (data: any) => fetchApi<any>('/items/purchase', { method: 'POST', body: JSON.stringify(data) }),
  resetBenchmark: () => fetchApi<any>('/items/reset-benchmark', { method: 'POST' }),
  getStockSummary: () => fetchApi<any[]>('/items/stock-summary'),
  getLedger: (itemId?: number) => fetchApi<any[]>(`/items/ledger${itemId ? `?item_id=${itemId}` : ''}`),
  
  getBOMs: () => fetchApi<any[]>('/production/boms'),
  recordProductionRun: (data: any) => fetchApi<any>('/production/run', { method: 'POST', body: JSON.stringify(data) }),
  getProductionRuns: () => fetchApi<any[]>('/production/runs'),
  
  getCustomers: () => fetchApi<any[]>('/sales/customers'),
  getOrders: () => fetchApi<any[]>('/sales/orders'),
  createOrder: (data: any) => fetchApi<any>('/sales/orders', { method: 'POST', body: JSON.stringify(data) }),
  approveOrder: (orderId: number) => fetchApi<any>(`/sales/orders/${orderId}/approve`, { method: 'POST' }),
  rejectOrder: (orderId: number, reason: string) => fetchApi<any>(`/sales/orders/${orderId}/reject?reason=${encodeURIComponent(reason)}`, { method: 'POST' }),
  editOrder: (orderId: number, itemId: number, qty: number, price?: number) => fetchApi<any>(`/sales/orders/${orderId}/edit?item_id=${itemId}&quantity=${qty}${price ? `&price=${price}` : ''}`, { method: 'PUT' }),
  generateInvoice: (orderId: number) => fetchApi<any>(`/sales/orders/${orderId}/invoice`, { method: 'POST' }),
  dispatchInvoice: (invoiceId: number) => fetchApi<any>(`/sales/invoices/${invoiceId}/dispatch`, { method: 'POST' }),
  cancelInvoice: (invoiceId: number, reason: string) => fetchApi<any>(`/sales/invoices/${invoiceId}/cancel`, { method: 'POST', body: JSON.stringify({ reason }) }),
  getInvoices: () => fetchApi<any[]>('/sales/invoices'),
  recordPayment: (data: any) => fetchApi<any>('/sales/payments', { method: 'POST', body: JSON.stringify(data) }),
  getReceivables: () => fetchApi<any[]>('/sales/receivables'),
  
  getDashboard: () => fetchApi<any>('/reports/dashboard'),
  getSalesRegister: () => fetchApi<any[]>('/reports/sales-register'),
  getGstSummary: () => fetchApi<any>('/reports/gst-summary'),
  getPurchaseRegister: () => fetchApi<any[]>('/reports/purchase-register'),
  getProductionReport: () => fetchApi<any[]>('/reports/production-report'),
  
  getInvoicePdfUrl: (invoiceId: number) => `${API_BASE}/reports/invoices/${invoiceId}/pdf`,
  getLedgerExcelUrl: () => `${API_BASE}/reports/export/ledger/excel`,
  getTallyXmlUrl: () => `${API_BASE}/reports/export/tally/xml`
};
