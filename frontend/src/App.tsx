import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { CommandCenter } from './components/CommandCenter';
import { InvoiceStudio } from './components/InvoiceStudio';
import { DemandForecaster } from './components/DemandForecaster';
import { VRPMap } from './components/VRPMap';
import { RAGAssistant } from './components/RAGAssistant';
import { BenchmarkHub } from './components/BenchmarkHub';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('command');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-black">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'command' && <CommandCenter setActiveTab={setActiveTab} />}
        {activeTab === 'invoice' && <InvoiceStudio />}
        {activeTab === 'demand' && <DemandForecaster />}
        {activeTab === 'logistics' && <VRPMap />}
        {activeTab === 'rag' && <RAGAssistant />}
        {activeTab === 'benchmark' && <BenchmarkHub />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        <p>SupplyChain-AgenticHub © 2026 | Multi-Agent Operations Optimization | MLAI Hackathon 2026 & Scientific Paper</p>
      </footer>
    </div>
  );
};

export default App;
