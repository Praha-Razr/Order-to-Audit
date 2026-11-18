import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, Package, DollarSign, Layers, PieChart } from 'lucide-react';
import { api } from '../api';

export const OwnerDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.getDashboard().then(res => {
      setData(res);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading || !data) {
    return <div className="text-center py-12 text-slate-500 text-xs">Loading Owner KPI Dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
        <span className="text-xs font-semibold uppercase tracking-wider text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full">
          Business Owner / Managing Director
        </span>
        <h1 className="text-xl font-bold text-slate-800 mt-1">Executive Factory Operations Dashboard</h1>
        <p className="text-xs text-slate-500">Real-time pulse: Sales orders, inventory health, variance alerts, unit costing & receivables</p>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Sales Orders Booked</span>
            <Package className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{data.total_orders_count}</div>
          <div className="text-xs text-slate-500">Total Value: <span className="font-bold text-slate-800">₹{data.total_orders_value.toLocaleString()}</span></div>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Production Cost / Packet</span>
            <DollarSign className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-indigo-900">₹{data.latest_cost_per_packet.toFixed(2)}</div>
          <div className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> Margin: {data.latest_margin_percent}% vs ₹50 SP
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Outstanding Customer Dues</span>
            <DollarSign className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-600">₹{data.total_outstanding_receivables.toLocaleString()}</div>
          <div className="text-xs text-slate-500">Uncollected market receivables</div>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Active Production Alerts</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-600">{data.variance_alerts.length}</div>
          <div className="text-xs text-slate-500">Wastage / yield deviations &gt; 3%</div>
        </div>
      </div>

      {/* Variance Alerts Banner */}
      {data.variance_alerts.length > 0 && (
        <div className="bg-amber-50/80 border border-amber-300 rounded-2xl p-5 space-y-3">
          <h2 className="text-sm font-bold text-amber-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" /> Active Production & Wastage Alerts (Exceeding ±3% Tolerance)
          </h2>
          <div className="space-y-2">
            {data.variance_alerts.map((alt: any, idx: number) => (
              <div key={idx} className="bg-white p-3 rounded-xl border border-amber-200 flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-800">{alt.message}</span>
                <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-rose-100 text-rose-700">ALERT</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Current Stock Levels */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-5 h-5 text-slate-700" /> Current Inventory Balances (Derived From Ledger)
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {data.stock_summary.map((item: any) => (
            <div key={item.item_id} className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/70 space-y-1 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 block truncate">{item.name}</span>
              <div className="text-lg font-black text-slate-900">{item.closing_stock}</div>
              <span className="text-[11px] text-slate-500">{item.unit}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
