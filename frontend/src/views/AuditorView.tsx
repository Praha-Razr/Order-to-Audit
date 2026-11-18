import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, ShieldCheck, Database, Calendar, Search } from 'lucide-react';
import { api } from '../api';
import { StockSummaryRow, LedgerEntry } from '../types';

export const AuditorView: React.FC = () => {
  const [stockSummary, setStockSummary] = useState<StockSummaryRow[]>([]);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [gstSummary, setGstSummary] = useState<any>(null);
  const [purchases, setPurchases] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'SUMMARY' | 'LEDGER' | 'GST' | 'PURCHASES'>('SUMMARY');
  const [filterText, setFilterText] = useState<string>('');

  const loadData = async () => {
    try {
      const [sum, ledg, gst, pur] = await Promise.all([
        api.getStockSummary(),
        api.getLedger(),
        api.getGstSummary(),
        api.getPurchaseRegister()
      ]);
      setStockSummary(sum);
      setLedger(ledg);
      setGstSummary(gst);
      setPurchases(pur);
    } catch (e: any) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredLedger = ledger.filter(l => 
    l.item_name.toLowerCase().includes(filterText.toLowerCase()) ||
    l.movement_type.toLowerCase().includes(filterText.toLowerCase()) ||
    l.reference_id.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full">
            Accountant & External Auditor
          </span>
          <h1 className="text-xl font-bold text-slate-800 mt-1">Audit Trail & Regulatory Ledger Reports</h1>
          <p className="text-xs text-slate-500">Immutable movement history, GSTR-1 / GSTR-3B tax reconciliations & Excel exports</p>
        </div>

        {/* Auditor Export Action Buttons */}
        <div className="flex items-center gap-2">
          <a
            href={api.getLedgerExcelUrl()}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-3.5 py-2 rounded-xl text-xs font-bold shadow-sm transition"
          >
            <FileSpreadsheet className="w-4 h-4" /> Export Stock Ledger (Excel)
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-2">
        {[
          { id: 'SUMMARY', label: 'Stock Summary (Opening + Receipts - Issues = Closing)' },
          { id: 'LEDGER', label: 'Immutable Movement Ledger' },
          { id: 'GST', label: 'GST Summary (GSTR-1 / 3B)' },
          { id: 'PURCHASES', label: 'Purchase Register' }
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            className={`pb-3 px-3 text-xs font-bold transition border-b-2 ${
              activeTab === t.id
                ? 'border-purple-600 text-purple-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Stock Summary */}
      {activeTab === 'SUMMARY' && (
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center justify-between">
            <span>Always-Current Stock Balances & Periodic Movement Summary</span>
            <span className="text-xs font-normal text-slate-500">Derived strictly from ledger entries</span>
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="p-3">Item Code</th>
                  <th className="p-3">Item Name</th>
                  <th className="p-3">Category</th>
                  <th className="p-3 text-right">Opening Stock</th>
                  <th className="p-3 text-right">Receipts (IN)</th>
                  <th className="p-3 text-right">Issues/Sales (OUT)</th>
                  <th className="p-3 text-right">Closing Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {stockSummary.map(s => (
                  <tr key={s.item_id} className="hover:bg-slate-50/50">
                    <td className="p-3 font-mono font-bold text-slate-900">{s.code}</td>
                    <td className="p-3 font-semibold">{s.name}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.category === 'RAW_MATERIAL' ? 'bg-amber-100 text-amber-800' :
                        s.category === 'PACKAGING' ? 'bg-indigo-100 text-indigo-800' :
                        'bg-emerald-100 text-emerald-800'
                      }`}>
                        {s.category}
                      </span>
                    </td>
                    <td className="p-3 text-right font-medium">{s.opening_stock} {s.unit}</td>
                    <td className="p-3 text-right text-emerald-700 font-medium">+{s.receipts} {s.unit}</td>
                    <td className="p-3 text-right text-rose-600 font-medium">-{s.issues} {s.unit}</td>
                    <td className="p-3 text-right font-black text-slate-900 text-sm">
                      {s.closing_stock} {s.unit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Movement Ledger */}
      {activeTab === 'LEDGER' && (
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-600" /> Full Audit Stock Movement Ledger
            </h2>
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search movements..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="p-3">#</th>
                  <th className="p-3">Timestamp (UTC)</th>
                  <th className="p-3">Item</th>
                  <th className="p-3">Movement Type</th>
                  <th className="p-3">Source Ref Doc</th>
                  <th className="p-3 text-right">Movement Qty</th>
                  <th className="p-3 text-right">Running Balance</th>
                  <th className="p-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {filteredLedger.map(l => (
                  <tr key={l.id} className="hover:bg-slate-50/50">
                    <td className="p-3 text-slate-400">{l.id}</td>
                    <td className="p-3 text-slate-500">{l.timestamp.slice(0, 19).replace('T', ' ')}</td>
                    <td className="p-3 font-sans font-semibold text-slate-900">{l.item_name}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        l.movement_type.includes('IN') || l.movement_type.includes('RECEIPT') || l.movement_type.includes('YIELD')
                          ? 'bg-emerald-50 text-emerald-800'
                          : 'bg-rose-50 text-rose-800'
                      }`}>
                        {l.movement_type}
                      </span>
                    </td>
                    <td className="p-3 text-slate-700 font-medium">{l.reference_type} #{l.reference_id}</td>
                    <td className={`p-3 text-right font-bold ${l.quantity > 0 ? 'text-emerald-700' : 'text-rose-600'}`}>
                      {l.quantity > 0 ? `+${l.quantity}` : l.quantity} {l.unit}
                    </td>
                    <td className="p-3 text-right font-black text-slate-900">{l.running_balance} {l.unit}</td>
                    <td className="p-3 font-sans text-slate-500 text-[11px]">{l.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: GST Summary */}
      {activeTab === 'GST' && gstSummary && (
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-5">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-sm font-bold text-slate-900">GSTR-1 / GSTR-3B Outward Supplies Tax Summary</h2>
              <p className="text-xs text-slate-500">Taxable turnover split by Place of Supply (Intra-state CGST+SGST vs Inter-state IGST)</p>
            </div>
            <div className="text-xs text-slate-500 text-right">
              <div>Factory GSTIN: <b>{gstSummary.factory_gstin}</b></div>
              <div>State: <b>{gstSummary.factory_state}</b></div>
            </div>
          </div>

          {/* Totals Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block">Total Taxable Value</span>
              <span className="text-lg font-bold text-slate-900">₹{gstSummary.totals.total_taxable_value.toFixed(2)}</span>
            </div>
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-200">
              <span className="text-blue-700 block">CGST (2.5%)</span>
              <span className="text-lg font-bold text-blue-900">₹{gstSummary.totals.total_cgst.toFixed(2)}</span>
            </div>
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-200">
              <span className="text-blue-700 block">SGST (2.5%)</span>
              <span className="text-lg font-bold text-blue-900">₹{gstSummary.totals.total_sgst.toFixed(2)}</span>
            </div>
            <div className="p-3 rounded-xl bg-purple-50 border border-purple-200">
              <span className="text-purple-700 block">IGST (5.0%)</span>
              <span className="text-lg font-bold text-purple-900">₹{gstSummary.totals.total_igst.toFixed(2)}</span>
            </div>
          </div>

          {/* Invoice-wise breakdown */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="p-3">Invoice #</th>
                  <th className="p-3">Customer</th>
                  <th className="p-3">Place of Supply</th>
                  <th className="p-3">Type</th>
                  <th className="p-3 text-right">Taxable Value</th>
                  <th className="p-3 text-right">CGST</th>
                  <th className="p-3 text-right">SGST</th>
                  <th className="p-3 text-right">IGST</th>
                  <th className="p-3 text-right">Invoice Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {gstSummary.records.map((r: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="p-3 font-mono font-bold text-slate-900">{r.invoice_number}</td>
                    <td className="p-3 font-semibold">{r.customer_name}</td>
                    <td className="p-3">{r.place_of_supply}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${r.is_inter_state ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'}`}>
                        {r.is_inter_state ? 'INTER-STATE (IGST)' : 'INTRA-STATE (CGST+SGST)'}
                      </span>
                    </td>
                    <td className="p-3 text-right">₹{r.taxable_value.toFixed(2)}</td>
                    <td className="p-3 text-right text-blue-700">₹{r.cgst.toFixed(2)}</td>
                    <td className="p-3 text-right text-blue-700">₹{r.sgst.toFixed(2)}</td>
                    <td className="p-3 text-right text-purple-700 font-medium">₹{r.igst.toFixed(2)}</td>
                    <td className="p-3 text-right font-bold text-slate-900">₹{r.invoice_value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Purchase Register */}
      {activeTab === 'PURCHASES' && (
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
          <h2 className="text-sm font-bold text-slate-900">Raw & Packaging Material Inward Purchases Register</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="p-3">Date</th>
                  <th className="p-3">PO Reference</th>
                  <th className="p-3">Item Purchased</th>
                  <th className="p-3 text-right">Quantity</th>
                  <th className="p-3 text-right">Purchase Rate</th>
                  <th className="p-3 text-right">Total Inward Value</th>
                  <th className="p-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {purchases.map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="p-3 text-slate-500">{p.date}</td>
                    <td className="p-3 font-mono font-bold text-slate-800">{p.reference_no}</td>
                    <td className="p-3 font-semibold">{p.item_name}</td>
                    <td className="p-3 text-right font-medium">{p.quantity} {p.unit}</td>
                    <td className="p-3 text-right">₹{p.rate.toFixed(2)}</td>
                    <td className="p-3 text-right font-bold text-slate-900">₹{p.total_value.toFixed(2)}</td>
                    <td className="p-3 text-slate-500">{p.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
