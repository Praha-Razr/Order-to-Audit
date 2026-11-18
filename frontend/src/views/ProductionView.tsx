import React, { useState, useEffect } from 'react';
import { Layers, AlertTriangle, CheckCircle, Calculator, History, Factory } from 'lucide-react';
import { api } from '../api';
import { BOM, ProductionRun, Item } from '../types';

export const ProductionView: React.FC = () => {
  const [boms, setBoms] = useState<BOM[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [runs, setRuns] = useState<ProductionRun[]>([]);
  const [selectedBomId, setSelectedBomId] = useState<number>(0);
  
  // Production form state
  const [actualOutput, setActualOutput] = useState<number>(188);
  const [flourQty, setFlourQty] = useState<number>(40);
  const [oilQty, setOilQty] = useState<number>(10.5);
  const [spiceQty, setSpiceQty] = useState<number>(1.2);
  const [pouchQty, setPouchQty] = useState<number>(188);
  const [damagedPouches, setDamagedPouches] = useState<number>(6);
  const [cartonQty, setCartonQty] = useState<number>(9);
  const [labourCost, setLabourCost] = useState<number>(1200);
  const [powerGasCost, setPowerGasCost] = useState<number>(600);

  const [loading, setLoading] = useState<boolean>(false);
  const [msg, setMsg] = useState<string>('');

  const loadData = async () => {
    try {
      const [bList, itmList, rList] = await Promise.all([
        api.getBOMs(),
        api.getItems(),
        api.getProductionRuns()
      ]);
      setBoms(bList);
      setItems(itmList);
      setRuns(rList);
      if (bList.length > 0 && selectedBomId === 0) {
        setSelectedBomId(bList[0].id);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const selectedBom = boms.find(b => b.id === selectedBomId);

  // Live variance calculations
  const plannedYield = selectedBom ? selectedBom.batch_output_qty : 200;
  const yieldVariance = Number((((actualOutput - plannedYield) / plannedYield) * 100).toFixed(2));
  const isYieldFlagged = Math.abs(yieldVariance) > 3.0;

  const standardOil = 10.0;
  const oilVariance = Number((((oilQty - standardOil) / standardOil) * 100).toFixed(2));
  const isOilFlagged = Math.abs(oilVariance) > 3.0;

  // Approximate live cost preview
  const estFlourCost = flourQty * 43.125;
  const estOilCost = oilQty * 140;
  const estSpiceCost = spiceQty * 200;
  const estPouchCost = (pouchQty + damagedPouches) * 2.5;
  const estCartonCost = cartonQty * 15;
  const estTotalMaterial = estFlourCost + estOilCost + estSpiceCost + estPouchCost + estCartonCost;
  const estTotalCost = estTotalMaterial + labourCost + powerGasCost;
  const estCostPerPkt = actualOutput > 0 ? (estTotalCost / actualOutput).toFixed(2) : '0.00';
  const estMargin = actualOutput > 0 ? (((50 - Number(estCostPerPkt)) / 50) * 100).toFixed(2) : '0.00';

  const handleRecordRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBom) return;
    setLoading(true);
    setMsg('');

    try {
      const flourItem = items.find(i => i.code === 'RM-FLOUR');
      const oilItem = items.find(i => i.code === 'RM-OIL');
      const spiceItem = items.find(i => i.code === 'RM-SPICE');
      const pouchItem = items.find(i => i.code === 'PM-POUCH-200');
      const cartonItem = items.find(i => i.code === 'PM-CARTON-20');

      if (!flourItem || !oilItem || !spiceItem || !pouchItem || !cartonItem) {
        alert('Items not ready');
        return;
      }

      const res = await api.recordProductionRun({
        bom_id: selectedBom.id,
        actual_output_qty: actualOutput,
        materials_issued: [
          { item_id: flourItem.id, actual_qty: flourQty },
          { item_id: oilItem.id, actual_qty: oilQty },
          { item_id: spiceItem.id, actual_qty: spiceQty },
          { item_id: pouchItem.id, actual_qty: pouchQty },
          { item_id: cartonItem.id, actual_qty: cartonQty }
        ],
        labour_cost: labourCost,
        power_gas_cost: powerGasCost,
        damaged_pouches_qty: damagedPouches,
        notes: 'Batch 1 Murukku 200g production run',
        user: 'supervisor'
      });

      setMsg(`✅ Production run ${res.run_number} recorded! Unit cost: ₹${res.cost_per_packet}/pkt, Yield Variance: ${res.yield_variance_percent}%`);
      loadData();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
        <span className="text-xs font-semibold uppercase tracking-wider text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full">
          Production Floor Supervisor
        </span>
        <h1 className="text-xl font-bold text-slate-800 mt-1">Recipe-based Production & Variance Tracking</h1>
        <p className="text-xs text-slate-500">Record raw material issues, track planned vs actual yield, detect wastage variances & calculate cost per packet</p>
      </div>

      {msg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-medium flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{msg}</span>
        </div>
      )}

      {/* Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Production Run Logger */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-5">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Factory className="w-4 h-4 text-amber-600" /> Log Production Run (Benchmark Steps 2, 3 & 8)
          </h2>

          <form onSubmit={handleRecordRun} className="space-y-4 text-xs">
            {/* BOM Selector */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Select BOM (Bill of Materials)</label>
              <select
                value={selectedBomId}
                onChange={(e) => setSelectedBomId(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 font-semibold"
              >
                {boms.map(b => (
                  <option key={b.id} value={b.id}>{b.name} (Expected: {b.batch_output_qty} {b.output_unit}s)</option>
                ))}
              </select>
            </div>

            {/* Actual Output & Yield Variance */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <label className="block font-bold text-slate-800">Actual Good Packets Produced</label>
                  <p className="text-[11px] text-slate-500">Standard batch expects 200 packets</p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={actualOutput}
                    onChange={(e) => setActualOutput(Number(e.target.value))}
                    className="w-28 text-center text-lg font-bold border border-slate-300 rounded-xl py-1"
                  />
                  <span className="font-semibold text-slate-600">packets</span>
                </div>
              </div>

              {/* Yield Variance Badge */}
              <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200">
                <span className="text-slate-600 font-medium">Yield Variance:</span>
                <span className={`px-2.5 py-0.5 rounded-full font-bold text-xs flex items-center gap-1 ${
                  isYieldFlagged ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {isYieldFlagged && <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />}
                  {yieldVariance}% {isYieldFlagged ? '(FLAGGED: Exceeds ±3% tolerance)' : '(Within tolerance)'}
                </span>
              </div>
            </div>

            {/* Raw Material Consumption Inputs */}
            <div>
              <label className="block font-bold text-slate-800 mb-2">Raw & Packaging Material Issues</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded-xl border border-slate-200 bg-white space-y-1">
                  <span className="font-semibold text-slate-700">Flour (Standard: 40 kg)</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      step="0.1"
                      value={flourQty}
                      onChange={(e) => setFlourQty(Number(e.target.value))}
                      className="w-full border border-slate-300 rounded-lg px-2.5 py-1 font-bold text-slate-900"
                    />
                    <span className="text-slate-500 font-medium">kg</span>
                  </div>
                </div>

                <div className={`p-3 rounded-xl border space-y-1 ${isOilFlagged ? 'border-amber-300 bg-amber-50/40' : 'border-slate-200 bg-white'}`}>
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-slate-700">Cooking Oil (Std: 10 L)</span>
                    {isOilFlagged && <span className="text-[10px] bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded font-bold">+{oilVariance}% (FLAGGED)</span>}
                  </div>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      step="0.1"
                      value={oilQty}
                      onChange={(e) => setOilQty(Number(e.target.value))}
                      className="w-full border border-slate-300 rounded-lg px-2.5 py-1 font-bold text-slate-900"
                    />
                    <span className="text-slate-500 font-medium">litre</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl border border-slate-200 bg-white space-y-1">
                  <span className="font-semibold text-slate-700">Spice Mix (Std: 1.2 kg)</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      step="0.1"
                      value={spiceQty}
                      onChange={(e) => setSpiceQty(Number(e.target.value))}
                      className="w-full border border-slate-300 rounded-lg px-2.5 py-1 font-bold text-slate-900"
                    />
                    <span className="text-slate-500 font-medium">kg</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl border border-slate-200 bg-white space-y-1">
                  <span className="font-semibold text-slate-700">Good Pouches Used</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={pouchQty}
                      onChange={(e) => setPouchQty(Number(e.target.value))}
                      className="w-full border border-slate-300 rounded-lg px-2.5 py-1 font-bold text-slate-900"
                    />
                    <span className="text-slate-500 font-medium">pcs</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl border border-amber-200 bg-amber-50/30 space-y-1">
                  <span className="font-semibold text-amber-900">Damaged / Scrap Pouches</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={damagedPouches}
                      onChange={(e) => setDamagedPouches(Number(e.target.value))}
                      className="w-full border border-amber-300 rounded-lg px-2.5 py-1 font-bold text-slate-900"
                    />
                    <span className="text-slate-500 font-medium">pcs</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl border border-slate-200 bg-white space-y-1">
                  <span className="font-semibold text-slate-700">Cartons Used (Std: 10)</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={cartonQty}
                      onChange={(e) => setCartonQty(Number(e.target.value))}
                      className="w-full border border-slate-300 rounded-lg px-2.5 py-1 font-bold text-slate-900"
                    />
                    <span className="text-slate-500 font-medium">pcs</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Overheads (Labour & Power/Gas) */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <label className="block font-bold text-slate-800">Production Overheads Allocation</label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[11px] text-slate-600 block mb-1">Labour Cost (₹)</span>
                  <input
                    type="number"
                    value={labourCost}
                    onChange={(e) => setLabourCost(Number(e.target.value))}
                    className="w-full border border-slate-300 rounded-xl px-3 py-1.5 font-bold"
                  />
                </div>
                <div>
                  <span className="text-[11px] text-slate-600 block mb-1">Gas / Power Overhead (₹)</span>
                  <input
                    type="number"
                    value={powerGasCost}
                    onChange={(e) => setPowerGasCost(Number(e.target.value))}
                    className="w-full border border-slate-300 rounded-xl px-3 py-1.5 font-bold"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold py-3 rounded-xl transition flex items-center justify-center gap-2 shadow-md shadow-amber-600/20"
            >
              <CheckCircle className="w-4 h-4" /> Save Production Run & Update Stock Ledger
            </button>
          </form>
        </div>

        {/* Right Col: Costing & Unit Economics Card */}
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Calculator className="w-4 h-4 text-blue-600" /> Unit Cost & Margin Analysis
            </h3>
            
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Flour (40 kg @ ₹43.125):</span>
                <span className="font-semibold text-slate-800">₹{estFlourCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Cooking Oil (10.5 L @ ₹140):</span>
                <span className="font-semibold text-slate-800">₹{estOilCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Spice Mix (1.2 kg @ ₹200):</span>
                <span className="font-semibold text-slate-800">₹{estSpiceCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Pouches (194 pcs @ ₹2.50):</span>
                <span className="font-semibold text-slate-800">₹{estPouchCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Cartons (9 pcs @ ₹15):</span>
                <span className="font-semibold text-slate-800">₹{estCartonCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 text-slate-700 font-bold">
                <span>Total Direct Materials:</span>
                <span>₹{estTotalMaterial.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 text-slate-700 font-bold border-b border-slate-200">
                <span>Overheads (Labour + Power):</span>
                <span>₹{(labourCost + powerGasCost).toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 text-slate-900 font-bold text-sm">
                <span>Total Production Cost:</span>
                <span>₹{estTotalCost.toFixed(2)}</span>
              </div>
            </div>

            {/* Cost Per Packet Highlight */}
            <div className="bg-blue-50 p-4 rounded-xl border border-blue-200 text-center space-y-1">
              <span className="text-xs text-blue-700 font-semibold uppercase tracking-wider">Computed Cost per Packet</span>
              <div className="text-2xl font-black text-blue-900">₹{estCostPerPkt}</div>
              <div className="text-[11px] text-blue-700 font-medium">
                Selling Price: ₹50.00 | Gross Margin: <span className="font-bold">{estMargin}%</span>
              </div>
            </div>
          </div>

          {/* Standard BOM Reference Card */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs space-y-2">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-600" /> Standard BOM Reference
            </span>
            <p className="text-[11px] text-slate-500">Standard batch output = 200 packets</p>
            <ul className="space-y-1 text-slate-600 text-[11px]">
              <li>• Flour: 40 kg</li>
              <li>• Cooking Oil: 10 Litres</li>
              <li>• Spice Mix: 1.2 kg</li>
              <li>• 200g Pouch: 200 pieces</li>
              <li>• Carton: 10 pieces</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Production Run History */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <History className="w-5 h-5 text-slate-600" /> Production Runs & Historical Variances
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="p-3">Run #</th>
                <th className="p-3">Product</th>
                <th className="p-3">Planned Yield</th>
                <th className="p-3">Actual Yield</th>
                <th className="p-3">Yield Variance</th>
                <th className="p-3">Total Cost</th>
                <th className="p-3">Cost / Packet</th>
                <th className="p-3">Margin %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/50">
                  <td className="p-3 font-bold text-slate-900">{r.run_number}</td>
                  <td className="p-3 font-semibold">{r.product_name}</td>
                  <td className="p-3">{r.planned_output} pkts</td>
                  <td className="p-3 font-bold">{r.actual_output} pkts</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded font-bold text-[11px] ${
                      Math.abs(r.yield_variance_percent) > 3.0 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {r.yield_variance_percent}%
                    </span>
                  </td>
                  <td className="p-3">₹{r.total_production_cost.toFixed(2)}</td>
                  <td className="p-3 font-bold text-blue-700">₹{r.cost_per_packet.toFixed(2)}</td>
                  <td className="p-3 font-bold text-emerald-700">{r.margin_percent}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
