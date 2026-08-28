import React from 'react';
import { Activity, ShieldCheck, Cpu, Database, Zap } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'command', label: 'Command Center', icon: Cpu },
    { id: 'invoice', label: 'Invoice & Accounting', icon: ShieldCheck },
    { id: 'demand', label: 'Demand Forecaster', icon: Activity },
    { id: 'logistics', label: 'Dynamic VRP Map', icon: Zap },
    { id: 'rag', label: 'Enterprise RAG', icon: Database },
    { id: 'benchmark', label: 'Benchmark & Research', icon: Activity },
  ];

  return (
    <header className="bg-slate-900/80 border-b border-slate-800 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-sky-200 to-indigo-400">
                  SupplyChain-AgenticHub
                </span>
                <span className="px-2 py-0.5 text-[10px] font-semibold uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-full">
                  Sub-200ms Dual-Speed
                </span>
              </div>
              <p className="text-[11px] text-slate-400">MLAI Hackathon 2026 | Operations Optimization</p>
            </div>
          </div>

          <nav className="flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};
