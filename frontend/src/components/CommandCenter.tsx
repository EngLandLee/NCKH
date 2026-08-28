import React from 'react';
import { Cpu, ShieldCheck, Activity, Zap, CheckCircle2, ArrowRight, Clock, AlertTriangle } from 'lucide-react';

interface CommandCenterProps {
  setActiveTab: (tab: string) => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({ setActiveTab }) => {
  const agents = [
    {
      id: 'invoice',
      name: 'Invoice & Accounting Agent',
      status: 'ACTIVE',
      role: 'Document AI & GL Code Mapping',
      fastPath: '< 120ms',
      description: 'Tự động trích xuất hóa đơn VAT, bóc tách dòng hàng và gán tài khoản hạch toán (TK 152/156/133/331).',
      action: 'Mở Studio Hóa Đơn'
    },
    {
      id: 'demand',
      name: 'Demand & Disruption Agent',
      status: 'ACTIVE',
      role: 'Time-Series Forecast & Safety Stock',
      fastPath: '< 30ms',
      description: 'Dự báo chuỗi thời gian 30 ngày, tính Điểm đặt hàng lại (ROP) và phát hiện nguy cơ đứt gãy cung ứng.',
      action: 'Xem Dự Báo Tồn Kho'
    },
    {
      id: 'logistics',
      name: 'Dynamic VRP Logistics Agent',
      status: 'ACTIVE',
      role: 'Google OR-Tools Real-Time Rerouting',
      fastPath: '< 50ms',
      description: 'Tối ưu hóa đa phương tiện giao hàng có ràng buộc tải trọng, thời tiết mưa bão và kẹt xe giờ cao điểm.',
      action: 'Xem Bản Đồ Tuyến Đường'
    },
    {
      id: 'rag',
      name: 'Enterprise SOP RAG Agent',
      status: 'ACTIVE',
      role: 'Sub-200ms Knowledge Base Retrieval',
      fastPath: '< 90ms',
      description: 'Tra cứu quy trình vận hành SOP nội bộ, chính sách tạm ứng và kiểm toán tuân thủ tức thì.',
      action: 'Mở Hộp Chat RAG'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 border border-cyan-500/30 p-6 shadow-2xl">
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold mb-3">
              <Zap className="w-3.5 h-3.5" />
              <span>Multi-Agent Swarm Orchestrator</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Trung Tâm Điều Hành Chuỗi Cung Ứng & Hạch Toán Tự Động
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl">
              Hệ thống điều phối đa tác thể thời gian thực với kiến trúc phân luồng Dual-Speed, đảm bảo phản hồi tức thì
              dưới <strong className="text-cyan-400">200ms</strong> cho toàn bộ các quy trình vận hành và kiểm toán doanh nghiệp.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => setActiveTab('benchmark')}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-bold text-xs hover:brightness-110 shadow-lg shadow-cyan-500/20 flex items-center justify-center space-x-2 transition-all"
            >
              <Activity className="w-4 h-4" />
              <span>Chạy 100k Benchmark</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Thời gian phản hồi P50</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white mt-2">
            1.2 <span className="text-xs font-normal text-cyan-400">ms</span>
          </div>
          <p className="text-[11px] text-emerald-400 mt-1 flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>Fast-Path Heuristics</span>
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Độ trễ trung bình toàn mạng</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-white mt-2">
            8.4 <span className="text-xs font-normal text-emerald-400">ms</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Mục tiêu: &lt; 200ms</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Độ chính xác Hạch toán</span>
            <ShieldCheck className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-white mt-2">
            98.5 <span className="text-xs font-normal text-blue-400">%</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">F1-Score: 0.978</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Trạng thái Agent Swarm</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white mt-2">
            4/4 <span className="text-xs font-normal text-purple-400">Online</span>
          </div>
          <p className="text-[11px] text-emerald-400 mt-1">Tất cả Agent sẵn sàng</p>
        </div>
      </div>

      {/* Agents Grid */}
      <h2 className="text-lg font-bold text-white tracking-wide mt-6">Đội Ngũ Agent Chuyên Biệt (Active Agents)</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 rounded-xl p-5 transition-all flex flex-col justify-between group shadow-lg"
          >
            <div>
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-base text-white group-hover:text-cyan-300 transition-colors">
                  {agent.name}
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  {agent.status}
                </span>
              </div>
              <p className="text-xs text-cyan-400/80 font-mono mt-1">{agent.role}</p>
              <p className="text-xs text-slate-300 mt-3 leading-relaxed">{agent.description}</p>
            </div>

            <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between">
              <div className="text-[11px] text-slate-400">
                Tốc độ xử lý: <strong className="text-cyan-300">{agent.fastPath}</strong>
              </div>
              <button
                onClick={() => setActiveTab(agent.id)}
                className="text-xs font-semibold text-cyan-400 hover:text-white flex items-center space-x-1 group-hover:translate-x-1 transition-transform"
              >
                <span>{agent.action}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
