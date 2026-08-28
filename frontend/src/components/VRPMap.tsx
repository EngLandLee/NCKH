import React, { useState } from 'react';
import { Navigation, CloudRain, ShieldAlert, Zap, Truck, MapPin, ArrowRight } from 'lucide-react';
import { api, VRPResponse, DeliveryStop } from '../services/api';

export const VRPMap: React.FC = () => {
  const [weather, setWeather] = useState('HEAVY_RAIN');
  const [congestion, setCongestion] = useState(1.4);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VRPResponse | null>(null);

  const stops: DeliveryStop[] = [
    { id: 1, name: 'Hub Quận 1 (Chợ Bến Thành)', lat: 10.7725, lng: 106.6980, demand: 15 },
    { id: 2, name: 'Kho Bình Thạnh (Điện Biên Phủ)', lat: 10.8010, lng: 106.7110, demand: 20 },
    { id: 3, name: 'Khu Công Nghệ Cao Thủ Đức', lat: 10.8500, lng: 106.7720, demand: 25 },
    { id: 4, name: 'Cảng Tân Thuận Quận 7', lat: 10.7340, lng: 106.7210, demand: 30 },
  ];

  const handleSolve = async () => {
    setLoading(true);
    try {
      const res = await api.solveVRP({
        depot: [10.7769, 106.7009],
        stops,
        vehicle_count: 2,
        vehicle_capacity: 60,
        weather,
        traffic_congestion_level: congestion
      });
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Điều Phối & Định Tuyến Logistics Động (Dynamic VRP)</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Tối ưu hóa đa xe với Google OR-Tools C++ Solver dưới 50ms, kết hợp yếu tố thời tiết mưa ngập và kẹt xe.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
            <Navigation className="w-4 h-4 text-cyan-400" />
            <span>Ràng Buộc Thời Gian Thực (Real-Time Constraints)</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 text-[10px]">Thời Tiết (Weather Condition)</label>
              <select
                value={weather}
                onChange={(e) => setWeather(e.target.value)}
                className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="CLEAR">Trời quang đãng (Hệ số x1.0)</option>
                <option value="RAIN">Mưa vừa (Hệ số x1.2)</option>
                <option value="HEAVY_RAIN">Mưa lớn / Triều cường (Hệ số x1.4)</option>
                <option value="STORM">Bão / Ngập nặng diện rộng (Hệ số x1.8)</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 text-[10px]">Mức Độ Ùn Tắc Giao Thông (Traffic Multiplier)</label>
              <input
                type="range"
                min="1.0"
                max="2.0"
                step="0.1"
                value={congestion}
                onChange={(e) => setCongestion(Number(e.target.value))}
                className="w-full mt-2 accent-cyan-400"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>Bình thường (1.0x)</span>
                <span className="text-cyan-400 font-bold">{congestion}x</span>
                <span>Kẹt xe nghiêm trọng (2.0x)</span>
              </div>
            </div>

            <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-1.5">
              <span className="text-[10px] text-slate-400 font-bold block">Danh Sách 4 Điểm Giao Hàng:</span>
              {stops.map((s) => (
                <div key={s.id} className="flex items-center justify-between text-[11px] text-slate-300">
                  <span className="truncate max-w-[170px]">{s.name}</span>
                  <span className="text-cyan-400 font-mono">{s.demand} units</span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handleSolve}
            disabled={loading}
            className="w-full mt-4 py-2.5 rounded-lg bg-cyan-400 text-black font-bold text-xs hover:brightness-110 shadow-md shadow-cyan-500/20 flex items-center justify-center space-x-2 transition-all"
          >
            <Zap className="w-4 h-4" />
            <span>{loading ? 'Đang Giải Toán...' : 'Tối Ưu Tuyến Đường (< 50ms)'}</span>
          </button>
        </div>

        {/* Map & Results */}
        <div className="lg:col-span-2 bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
                <Truck className="w-4 h-4 text-emerald-400" />
                <span>Kết Quả Phân Bổ Đội Xe & Lộ Trình Giao Hàng</span>
              </span>
              {result && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Solver Latency: {result.solver_latency_ms} ms
                </span>
              )}
            </div>

            {result ? (
              <div className="mt-4 space-y-4">
                {/* Metrics */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400">Tổng Quãng Đường</span>
                    <p className="text-lg font-black text-white mt-1">{result.total_distance_km} <span className="text-xs font-normal text-slate-400">km</span></p>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400">Thời Gian Ước Tính</span>
                    <p className="text-lg font-black text-cyan-400 mt-1">{result.total_time_min} <span className="text-xs font-normal text-slate-400">phút</span></p>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400">Số Phương Tiện</span>
                    <p className="text-lg font-black text-emerald-400 mt-1">{result.routes.length} <span className="text-xs font-normal text-slate-400">xe tải</span></p>
                  </div>
                </div>

                {/* Explanation */}
                <div className="p-3.5 rounded-lg bg-blue-950/30 border border-blue-500/30 text-xs text-blue-200">
                  <strong className="block text-cyan-300 mb-1">Giải Thích Điều Phối (Dispatcher Explanation):</strong>
                  {result.explanation}
                </div>

                {/* Route Cards */}
                <div className="space-y-2.5">
                  {result.routes.map((route) => (
                    <div key={route.vehicle_id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs">
                          Xe {route.vehicle_id}
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-white">
                            Lộ trình: {route.node_sequence.map(n => n === 0 ? 'Trung Tâm Điều Hành' : stops[n - 1]?.name || `Điểm ${n}`).join(' ➔ ')}
                          </span>
                          <p className="text-[10px] text-slate-400">Quãng đường xe chạy: {route.distance_km} km</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2">
                <Navigation className="w-8 h-8 opacity-40" />
                <span>Nhấn "Tối Ưu Tuyến Đường" để khởi chạy Google OR-Tools C++ Engine</span>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Thuật toán: Capacitated Vehicle Routing Problem (CVRP)</span>
            <span>Fast-Path Benchmark: &lt; 50ms</span>
          </div>
        </div>
      </div>
    </div>
  );
};
