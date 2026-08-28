import React, { useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, TrendingUp, RefreshCw } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { api, DemandResponse } from '../services/api';

export const DemandForecaster: React.FC = () => {
  const [skuId, setSkuId] = useState('RAW-STEEL-D10');
  const [currentStock, setCurrentStock] = useState(350);
  const [leadTime, setLeadTime] = useState(7);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DemandResponse | null>(null);

  const handleForecast = async () => {
    setLoading(true);
    try {
      const res = await api.forecastDemand({
        sku_id: skuId,
        historical_demand: [120, 125, 118, 130, 145, 150, 160, 155, 170, 180],
        current_stock: currentStock,
        lead_time_days: leadTime,
        supplier_reliability: 0.85
      });
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const chartData = result?.forecast_30d.map((val, idx) => ({
    day: `Ngày ${idx + 1}`,
    demand: val,
    safety_stock: result.safety_stock,
    rop: result.reorder_point
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Dự Báo Nhu Cầu Nguyên Vật Liệu & Chống Đứt Gãy</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Mô hình chuỗi thời gian dự báo nhu cầu 30 ngày, tính toán Tồn kho an toàn và Điểm đặt hàng lại (ROP).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <span>Thông Số Nguyên Vật Liệu (SKU Parameters)</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 text-[10px]">Mã Nguyên Vật Liệu (SKU ID)</label>
              <input
                type="text"
                value={skuId}
                onChange={(e) => setSkuId(e.target.value)}
                className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 text-[10px]">Tồn Kho Hiện Tại (Đơn vị: kg/cái)</label>
              <input
                type="number"
                value={currentStock}
                onChange={(e) => setCurrentStock(Number(e.target.value))}
                className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="text-slate-400 text-[10px]">Thời Gian Giao Hàng Nhà Cung Cấp (Lead Time: ngày)</label>
              <input
                type="number"
                value={leadTime}
                onChange={(e) => setLeadTime(Number(e.target.value))}
                className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <button
            onClick={handleForecast}
            disabled={loading}
            className="w-full mt-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-bold text-xs hover:brightness-110 shadow-md shadow-cyan-500/20 flex items-center justify-center space-x-2 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Đang Tính Toán...' : 'Chạy Mô Hình Dự Báo'}</span>
          </button>
        </div>

        {/* Chart & Results */}
        <div className="lg:col-span-2 bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <span className="text-xs font-semibold text-slate-300">Biểu Đồ Nhu Cầu 30 Ngày Tiếp Theo (Forecast Curve)</span>
            {result && (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                Độ trễ: {result.latency_ms} ms
              </span>
            )}
          </div>

          {result ? (
            <div className="space-y-4">
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                    <Line type="monotone" dataKey="demand" stroke="#06b6d4" strokeWidth={2} name="Nhu Cầu Dự Báo" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Action Banner */}
              <div
                className={`p-3.5 rounded-lg border flex items-start space-x-3 ${
                  result.stockout_risk_pct > 70
                    ? 'bg-red-950/40 border-red-500/40 text-red-200'
                    : 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
                }`}
              >
                {result.stockout_risk_pct > 70 ? (
                  <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <span className="text-xs font-bold block">Khuyến Nghị Điều Hành Tự Động:</span>
                  <p className="text-xs mt-0.5 opacity-90">{result.action_recommendation}</p>
                </div>
              </div>

              {/* Stat Grid */}
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400">Tồn Kho An Toàn (Safety Stock)</span>
                  <p className="text-sm font-bold text-white mt-1">{result.safety_stock} units</p>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400">Điểm Đặt Hàng Lại (ROP)</span>
                  <p className="text-sm font-bold text-cyan-400 mt-1">{result.reorder_point} units</p>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400">Nguy Cơ Đứt Gãy</span>
                  <p className={`text-sm font-bold mt-1 ${result.stockout_risk_pct > 50 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {result.stockout_risk_pct}%
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2">
              <Activity className="w-8 h-8 opacity-40" />
              <span>Nhấn "Chạy Mô Hình Dự Báo" để xem đường cong chuỗi thời gian</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
