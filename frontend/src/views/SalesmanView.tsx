import React, { useState, useEffect } from 'react';
import { ShoppingCart, CheckCircle, AlertTriangle, Clock, RefreshCw, Send, Plus, Minus } from 'lucide-react';
import { api } from '../api';
import { Customer, Item, SalesOrder } from '../types';

export const SalesmanView: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number>(0);
  const [selectedItemId, setSelectedItemId] = useState<number>(0);
  const [quantity, setQuantity] = useState<number>(150);
  const [loading, setLoading] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string>('');
  const [isOffline, setIsOffline] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [custs, itms, ords] = await Promise.all([
        api.getCustomers(),
        api.getItems(),
        api.getOrders()
      ]);
      setCustomers(custs);
      setItems(itms.filter(i => i.category === 'FINISHED_GOOD'));
      setOrders(ords);
      if (custs.length > 0 && selectedCustomerId === 0) {
        setSelectedCustomerId(custs[0].id);
      }
      const fg = itms.find(i => i.category === 'FINISHED_GOOD');
      if (fg && selectedItemId === 0) {
        setSelectedItemId(fg.id);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const selectedItem = items.find(i => i.id === selectedItemId);
  const availableStock = selectedItem ? selectedItem.current_stock : 0;
  const isShortage = quantity > availableStock;
  const shortageQty = isShortage ? quantity - availableStock : 0;

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !selectedItemId || quantity <= 0) return;
    setLoading(true);
    setSuccessMsg('');

    try {
      const res = await api.createOrder({
        salesman_id: 1, // Salesman A or B
        customer_id: selectedCustomerId,
        items: [{ item_id: selectedItemId, quantity: quantity }],
        user: 'salesman'
      });

      setSuccessMsg(
        res.shortage_flag
          ? `⚠️ Order ${res.order_number} submitted with SHORTAGE of ${res.shortage_qty} pkts flagged for factory.`
          : `✅ Order ${res.order_number} submitted successfully!`
      );
      loadData();
    } catch (err: any) {
      alert(`Error submitting order: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-4 pb-12">
      {/* Mobile Header Bar */}
      <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
              Mobile Field View
            </span>
            <h1 className="text-lg font-bold text-slate-800 mt-1">Field Order Taking</h1>
            <p className="text-xs text-slate-500">Fast 1-minute order booking for field salesmen</p>
          </div>
          <button
            onClick={() => setIsOffline(!isOffline)}
            className={`text-xs px-2.5 py-1.5 rounded-lg border font-medium flex items-center gap-1.5 transition ${
              isOffline
                ? 'bg-amber-50 text-amber-700 border-amber-300'
                : 'bg-emerald-50 text-emerald-700 border-emerald-300'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isOffline ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
            {isOffline ? 'Offline Mode' : 'Online (Direct Sync)'}
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-xl text-xs font-medium flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* New Order Card */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <ShoppingCart className="w-4 h-4 text-blue-600" /> Book New Order
        </h2>

        <form onSubmit={handlePlaceOrder} className="space-y-4 text-sm">
          {/* Customer Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Select Customer</label>
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.state} - {c.type})
                </option>
              ))}
            </select>
          </div>

          {/* Product Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Product</label>
            <select
              value={selectedItemId}
              onChange={(e) => setSelectedItemId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            >
              {items.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} — ₹{i.selling_price}/pkt (GST {i.gst_rate * 100}%)
                </option>
              ))}
            </select>
          </div>

          {/* Stock Indicator */}
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
            <span className="text-slate-600">Available Factory Stock:</span>
            <span className={`font-bold ${availableStock < 50 ? 'text-amber-600' : 'text-emerald-700'}`}>
              {availableStock} packets
            </span>
          </div>

          {/* Quantity Stepper */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Order Quantity (Packets)</label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setQuantity(Math.max(10, quantity - 10))}
                className="w-10 h-10 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl flex items-center justify-center font-bold"
              >
                <Minus className="w-4 h-4" />
              </button>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                className="flex-1 text-center font-bold text-lg border border-slate-300 rounded-xl py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setQuantity(quantity + 10)}
                className="w-10 h-10 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl flex items-center justify-center font-bold"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            {/* Quick Chips */}
            <div className="flex gap-2 mt-2">
              {[50, 100, 120, 150].map((qty) => (
                <button
                  type="button"
                  key={qty}
                  onClick={() => setQuantity(qty)}
                  className={`flex-1 py-1 text-xs rounded-lg border font-medium transition ${
                    quantity === qty ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 text-slate-600 border-slate-200'
                  }`}
                >
                  {qty}
                </button>
              ))}
            </div>
          </div>

          {/* Shortage Warning */}
          {isShortage && (
            <div className="bg-amber-50 border border-amber-300 text-amber-900 p-3 rounded-xl text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Shortage Warning ({shortageQty} pkts short)</span>
              </div>
              <p className="text-slate-600">
                Factory finished goods stock is only <b>{availableStock} packets</b>. Order will be sent to factory admin with an automatic shortage alert.
              </p>
            </div>
          )}

          {/* Price Calculation Card */}
          <div className="bg-blue-50/70 p-3 rounded-xl border border-blue-100 flex justify-between items-center text-xs">
            <div>
              <span className="text-slate-500">Taxable Value:</span>
              <span className="font-semibold text-slate-800 ml-1">₹{(quantity * (selectedItem?.selling_price || 50)).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-slate-500">Est. Total (+5% GST):</span>
              <span className="font-bold text-blue-700 text-sm ml-1">₹{(quantity * (selectedItem?.selling_price || 50) * 1.05).toLocaleString()}</span>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl shadow-md shadow-blue-500/20 transition flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {loading ? 'Submitting to Factory...' : 'Send Order to Factory'}
          </button>
        </form>
      </div>

      {/* Recent Orders List */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
        <h2 className="text-sm font-bold text-slate-900 flex items-center justify-between">
          <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-slate-500" /> My Recent Orders</span>
          <span className="text-xs font-normal text-slate-500">{orders.length} total</span>
        </h2>

        <div className="space-y-2">
          {orders.map((o) => (
            <div key={o.id} className="p-3 rounded-xl border border-slate-100 bg-slate-50/50 space-y-1.5 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-800">{o.order_number}</span>
                <span
                  className={`px-2 py-0.5 rounded-full font-bold uppercase tracking-wider text-[10px] ${
                    o.status === 'DISPATCHED'
                      ? 'bg-emerald-100 text-emerald-800'
                      : o.status === 'INVOICED'
                      ? 'bg-blue-100 text-blue-800'
                      : o.status === 'APPROVED'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-slate-200 text-slate-700'
                  }`}
                >
                  {o.status}
                </span>
              </div>
              <div className="text-slate-600 flex justify-between">
                <span>{o.customer_name} ({o.customer_state})</span>
                <span className="font-semibold text-slate-900">₹{o.total_amount.toLocaleString()}</span>
              </div>
              {o.shortage_flag && (
                <div className="text-[11px] font-medium text-amber-700 flex items-center gap-1 bg-amber-50 p-1 rounded">
                  <AlertTriangle className="w-3 h-3" />
                  <span>Shortage of {o.shortage_qty} pkts</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
