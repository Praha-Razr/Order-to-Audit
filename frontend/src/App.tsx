import React, { useState } from 'react';
import { Smartphone, Building2, Factory, FileSpreadsheet, Crown, PlayCircle } from 'lucide-react';
import { SalesmanView } from './views/SalesmanView';
import { AdminView } from './views/AdminView';
import { ProductionView } from './views/ProductionView';
import { AuditorView } from './views/AuditorView';
import { OwnerDashboard } from './views/OwnerDashboard';
import { BenchmarkRunner } from './views/BenchmarkRunner';

type RoleTab = 'SALESMAN' | 'ADMIN' | 'PRODUCTION' | 'AUDITOR' | 'OWNER' | 'BENCHMARK';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<RoleTab>('BENCHMARK');

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Navigation Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo & Name */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-md shadow-blue-500/20">
                🏭
              </div>
              <div>
                <h1 className="text-sm font-bold text-slate-900 tracking-tight">Order-to-Audit System</h1>
                <p className="text-[11px] text-slate-500 font-medium">South Indian Snacks Manufacturer • NIT Tiruchirappalli</p>
              </div>
            </div>

            {/* Role Switcher Tabs */}
            <nav className="flex items-center gap-1.5 overflow-x-auto py-1">
              {[
                { id: 'BENCHMARK', label: '🧪 Benchmark Runner', icon: PlayCircle },
                { id: 'SALESMAN', label: '📱 Salesman', icon: Smartphone },
                { id: 'ADMIN', label: '🏢 Factory Admin', icon: Building2 },
                { id: 'PRODUCTION', label: '🏭 Production Floor', icon: Factory },
                { id: 'AUDITOR', label: '📊 Auditor & Tax', icon: FileSpreadsheet },
                { id: 'OWNER', label: '👑 Owner', icon: Crown },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as RoleTab)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === 'BENCHMARK' && <BenchmarkRunner />}
        {activeTab === 'SALESMAN' && <SalesmanView />}
        {activeTab === 'ADMIN' && <AdminView />}
        {activeTab === 'PRODUCTION' && <ProductionView />}
        {activeTab === 'AUDITOR' && <AuditorView />}
        {activeTab === 'OWNER' && <OwnerDashboard />}
      </main>

      {/* Minimal Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        <p>Order-to-Audit Prototype • Centre for Digital Infrastructure, NIT Tiruchirappalli • Built with FastAPI, PostgreSQL/SQLite & React</p>
      </footer>
    </div>
  );
};
