import React, { useState, useEffect } from 'react';
import { FileText, CheckCircle, Truck, DollarSign, PlusCircle, AlertCircle, Download, FileSpreadsheet, Ban, Share2, Edit3 } from 'lucide-react';
import { api } from '../api';
import { SalesOrder, Invoice, Item, Customer } from '../types';

export const AdminView: React.FC = () => {
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [receivables, setReceivables] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [msg, setMsg] = useState<string>('');

  // Payment modal state
  const [payCustId, setPayCustId] = useState<number>(0);
  const [payAmount, setPayAmount] = useState<number>(4000);
  const [payRef, setPayRef] = useState<string>('NEFT-RET-A-001');

  // Purchase modal state
  const [purchItemId, setPurchItemId] = useState<number>(0);
  const [purchQty, setPurchQty] = useState<number>(60);
  const [purchRate, setPurchRate] = useState<number>(45);

  const loadData = async () => {
    try {
      const [ords, invs, itms, custs, recs] = await Promise.all([
        api.getOrders(),
        api.getInvoices(),
        api.getItems(),
        api.getCustomers(),
        api.getReceivables()
      ]);
      setOrders(ords);
      setInvoices(invs);
      setItems(itms);
      setCustomers(custs);
      setReceivables(recs);
      if (custs.length > 0 && payCustId === 0) setPayCustId(custs[0].id);
      const flour = itms.find(i => i.code === 'RM-FLOUR');
      if (flour && purchItemId === 0) setPurchItemId(flour.id);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = async (orderId: number) => {
    try {
      setLoading(true);
      await api.approveOrder(orderId);
      setMsg(`Order approved successfully.`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (orderId: number) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;
    try {
      setLoading(true);
      await api.rejectOrder(orderId, reason);
      setMsg(`Order rejected.`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEditOrder = async (orderId: number, itemId: number, currentQty: number) => {
    const newQtyStr = prompt(`Enter new quantity for item (Current: ${currentQty}):`, currentQty.toString());
    if (!newQtyStr) return;
    const newQty = parseFloat(newQtyStr);
    if (isNaN(newQty) || newQty <= 0) return;
    try {
      setLoading(true);
      await api.editOrder(orderId, itemId, newQty);
      setMsg(`Order updated to ${newQty} units.`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInvoice = async (orderId: number) => {
    try {
      setLoading(true);
      const res = await api.generateInvoice(orderId);
      setMsg(`GST Tax Invoice ${res.invoice_number} created! Taxable: ₹${res.taxable_amount}, Total: ₹${res.total_amount}`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDispatch = async (invoiceId: number) => {
    try {
      setLoading(true);
      await api.dispatchInvoice(invoiceId);
      setMsg(`Invoice dispatched! Finished goods stock deducted from ledger.`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelInvoice = async (invoiceId: number) => {
    const reason = prompt('Enter reason for cancelling invoice with Credit Note:');
    if (!reason) return;
    try {
      setLoading(true);
      const res = await api.cancelInvoice(invoiceId, reason);
      setMsg(`Invoice cancelled via Credit Note ${res.credit_note_number}. Reversal logged.`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await api.recordPayment({
        customer_id: payCustId,
        amount: payAmount,
        reference: payRef,
        payment_mode: 'Bank Transfer'
      });
      setMsg(`Payment of ₹${payAmount} recorded successfully!`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordPurchase = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await api.recordPurchase({
        item_id: purchItemId,
        quantity: purchQty,
        unit_cost: purchRate,
        reference_id: `PO-${Date.now().toString().slice(-4)}`,
        notes: 'Raw material procurement'
      });
      setMsg(`Recorded purchase of ${purchQty} units @ ₹${purchRate}. Stock updated!`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
            Factory Admin & Billing Desk
          </span>
          <h1 className="text-xl font-bold text-slate-800 mt-1">Order Verification, GST Billing & Dispatches</h1>
          <p className="text-xs text-slate-500">Approve incoming salesman orders, generate GST tax invoices, record dispatches & payments</p>
        </div>
      </div>

      {msg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-medium flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{msg}</span>
        </div>
      )}

      {/* Two-Column Quick Forms */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Record Raw Material Purchase */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
            <PlusCircle className="w-4 h-4 text-indigo-600" /> Quick Purchase Entry (Step 1)
          </h2>
          <form onSubmit={handleRecordPurchase} className="space-y-3 text-xs">
            <div>
              <label className="block font-semibold text-slate-600 mb-1">Item to Purchase</label>
              <select
                value={purchItemId}
                onChange={(e) => setPurchItemId(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 font-medium"
              >
                {items.filter(i => i.category !== 'FINISHED_GOOD').map(i => (
                  <option key={i.id} value={i.id}>{i.name} (Current: {i.current_stock} {i.unit})</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-600 mb-1">Quantity</label>
                <input
                  type="number"
                  value={purchQty}
                  onChange={(e) => setPurchQty(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-xl px-3 py-1.5 font-bold"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-600 mb-1">Purchase Rate (₹/unit)</label>
                <input
                  type="number"
                  value={purchRate}
                  onChange={(e) => setPurchRate(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-xl px-3 py-1.5 font-bold"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 rounded-xl transition"
            >
              Record Inward Purchase Movement
            </button>
          </form>
        </div>

        {/* Record Payment */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-emerald-600" /> Record Customer Payment (Step 7)
          </h2>
          <form onSubmit={handleRecordPayment} className="space-y-3 text-xs">
            <div>
              <label className="block font-semibold text-slate-600 mb-1">Customer</label>
              <select
                value={payCustId}
                onChange={(e) => setPayCustId(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 font-medium"
              >
                {customers.map(c => (
                  <option key={c.id} value={c.id}>{c.name} ({c.state})</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-600 mb-1">Amount Paid (₹)</label>
                <input
                  type="number"
                  value={payAmount}
                  onChange={(e) => setPayAmount(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-xl px-3 py-1.5 font-bold"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-600 mb-1">Reference / UTR</label>
                <input
                  type="text"
                  value={payRef}
                  onChange={(e) => setPayRef(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3 py-1.5"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-xl transition"
            >
              Record Payment Receipt
            </button>
          </form>
        </div>
      </div>

      {/* Incoming Sales Orders Section */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center justify-between">
          <span className="flex items-center gap-2"><FileText className="w-5 h-5 text-indigo-600" /> Incoming Orders for Verification</span>
          <span className="text-xs font-medium text-slate-500">{orders.length} orders total</span>
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="p-3">Order #</th>
                <th className="p-3">Customer</th>
                <th className="p-3">State / POS</th>
                <th className="p-3">Items & Qty</th>
                <th className="p-3">Taxable Value</th>
                <th className="p-3">Stock Check</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-slate-50/50">
                  <td className="p-3 font-bold text-slate-900">{o.order_number}</td>
                  <td className="p-3 font-semibold">{o.customer_name}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${o.customer_state === 'Tamil Nadu' ? 'bg-blue-50 text-blue-700' : 'bg-purple-50 text-purple-700'}`}>
                      {o.customer_state} ({o.customer_state === 'Tamil Nadu' ? 'Intra-state: CGST+SGST' : 'Inter-state: IGST'})
                    </span>
                  </td>
                  <td className="p-3">
                    {o.items.map((i, idx) => (
                      <div key={idx}><b>{i.ordered_qty} pkts</b> {i.item_name}</div>
                    ))}
                  </td>
                  <td className="p-3 font-bold text-slate-900">₹{o.total_amount.toLocaleString()}</td>
                  <td className="p-3">
                    {o.shortage_flag ? (
                      <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-1 rounded font-bold text-[11px]">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                        Shortage: {o.shortage_qty} pkts
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-1 rounded font-medium text-[11px]">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                        Stock Available
                      </span>
                    )}
                  </td>
                  <td className="p-3 font-bold uppercase text-[10px]">
                    <span className={`px-2 py-1 rounded-full ${
                      o.status === 'DISPATCHED' ? 'bg-emerald-100 text-emerald-800' :
                      o.status === 'INVOICED' ? 'bg-blue-100 text-blue-800' :
                      o.status === 'APPROVED' ? 'bg-amber-100 text-amber-800' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="p-3 text-right space-x-1.5 whitespace-nowrap">
                    {o.status === 'SUBMITTED' && (
                      <>
                        <button
                          onClick={() => handleApprove(o.id)}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white px-2.5 py-1.5 rounded-lg font-bold"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleReject(o.id)}
                          className="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 px-2 py-1.5 rounded-lg font-bold"
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {o.status === 'APPROVED' && (
                      <button
                        onClick={() => handleInvoice(o.id)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-2.5 py-1.5 rounded-lg font-bold flex-inline items-center gap-1"
                      >
                        Raise GST Invoice
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Posted GST Invoices & Dispatch Table */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center justify-between">
          <span className="flex items-center gap-2"><Truck className="w-5 h-5 text-emerald-600" /> GST Tax Invoices & Dispatch Desk</span>
          <span className="text-xs font-medium text-slate-500">{invoices.length} invoices generated</span>
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="p-3">Invoice #</th>
                <th className="p-3">Customer</th>
                <th className="p-3">Taxable Value</th>
                <th className="p-3">CGST (2.5%)</th>
                <th className="p-3">SGST (2.5%)</th>
                <th className="p-3">IGST (5.0%)</th>
                <th className="p-3">Total Invoice</th>
                <th className="p-3">Dispatch Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-slate-50/50">
                  <td className="p-3 font-bold text-slate-900">{inv.invoice_number}</td>
                  <td className="p-3 font-semibold">{inv.customer_name} ({inv.customer_state})</td>
                  <td className="p-3">₹{inv.taxable_amount.toFixed(2)}</td>
                  <td className="p-3 text-blue-700">₹{inv.cgst_amount.toFixed(2)}</td>
                  <td className="p-3 text-blue-700">₹{inv.sgst_amount.toFixed(2)}</td>
                  <td className="p-3 text-purple-700 font-medium">₹{inv.igst_amount.toFixed(2)}</td>
                  <td className="p-3 font-bold text-slate-900">₹{inv.total_amount.toFixed(2)}</td>
                  <td className="p-3">
                    {inv.is_dispatched ? (
                      <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-bold text-[10px]">
                        DISPATCHED (Stock Deducted)
                      </span>
                    ) : inv.status === 'CANCELLED_VIA_CREDIT_NOTE' ? (
                      <span className="bg-rose-100 text-rose-800 px-2 py-0.5 rounded-full font-bold text-[10px]">
                        CANCELLED VIA CN
                      </span>
                    ) : (
                      <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-bold text-[10px]">
                        AWAITING DISPATCH
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-right space-x-1.5 whitespace-nowrap">
                    {!inv.is_dispatched && inv.status !== 'CANCELLED_VIA_CREDIT_NOTE' && (
                      <button
                        onClick={() => handleDispatch(inv.id)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1.5 rounded-lg font-bold"
                      >
                        Record Dispatch
                      </button>
                    )}
                    <a
                      href={api.getInvoicePdfUrl(inv.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1.5 rounded-lg font-bold border border-slate-200"
                    >
                      <Download className="w-3.5 h-3.5" /> PDF
                    </a>
                    <a
                      href={`https://api.whatsapp.com/send?text=${encodeURIComponent(`Dear Customer, your Tax Invoice ${inv.invoice_number} from South Indian Snacks Factory for ₹${inv.total_amount.toFixed(2)} has been generated.`)}`}
                      target="_blank"
                      rel="noreferrer"
                      title="Share via WhatsApp"
                      className="inline-flex items-center gap-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 px-2.5 py-1.5 rounded-lg font-bold border border-emerald-200"
                    >
                      <Share2 className="w-3.5 h-3.5" /> WhatsApp
                    </a>
                    {inv.status !== 'CANCELLED_VIA_CREDIT_NOTE' && (
                      <button
                        onClick={() => handleCancelInvoice(inv.id)}
                        title="Cancel with Credit Note"
                        className="text-rose-600 hover:bg-rose-50 p-1.5 rounded-lg"
                      >
                        <Ban className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Customer Receivables & Outstanding Table */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center justify-between">
          <span className="flex items-center gap-2"><DollarSign className="w-5 h-5 text-emerald-600" /> Customer Receivables & Outstanding Ledger</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {receivables.map((r, idx) => (
            <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-bold text-sm text-slate-900">{r.customer_name}</span>
                <span className="font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700">Customer ID: {r.customer_id}</span>
              </div>
              <div className="flex justify-between text-slate-600 border-t border-slate-200 pt-2">
                <span>Total Invoiced:</span>
                <span className="font-semibold text-slate-800">₹{r.total_invoiced.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Total Payments Collected:</span>
                <span className="font-semibold text-emerald-700">₹{r.total_paid.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-900 font-bold border-t border-slate-200 pt-2 text-sm">
                <span>Current Outstanding Due:</span>
                <span className={r.outstanding > 0 ? 'text-rose-600' : 'text-slate-700'}>₹{r.outstanding.toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
