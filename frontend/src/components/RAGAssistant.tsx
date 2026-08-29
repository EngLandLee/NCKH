import React, { useState } from 'react';
import { Database, Search, Sparkles, BookOpen, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import { api, RAGQueryResponse } from '../services/api';

export const RAGAssistant: React.FC = () => {
  const [query, setQuery] = useState('Quy trình thanh toán tạm ứng cho nhà cung cấp vật tư cần giấy tờ gì?');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGQueryResponse | null>(null);

  const sampleQueries = [
    'Quy trình thanh toán tạm ứng cho nhà cung cấp vật tư cần giấy tờ gì?',
    'Nguyên vật liệu nhập kho hạch toán tài khoản nào?',
    'Xử lý thế nào khi giao hàng trễ do ngập lụt?',
    'Khi nào kích hoạt Reorder Point tồn kho an toàn?'
  ];

  const handleSearch = async (textToSearch?: string) => {
    const q = textToSearch || query;
    setLoading(true);
    try {
      const res = await api.queryRAG(q);
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
          <h2 className="text-xl font-bold text-white tracking-wide">Trợ Lý Tra Cứu Quy Trình SOP Nội Bộ (Enterprise RAG)</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Truy xuất tài liệu quy chế tài chính, quy chuẩn kho vận và hướng dẫn xử lý sự cố với độ trễ &lt; 90ms.
          </p>
        </div>
      </div>

      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-5">
        {/* Search Bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Nhập câu hỏi tra cứu quy trình nội bộ doanh nghiệp..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-cyan-500 placeholder:text-slate-500"
            />
          </div>
          <button
            onClick={() => handleSearch()}
            disabled={loading}
            className="px-5 py-2.5 bg-cyan-400 text-black font-bold text-xs rounded-lg hover:brightness-110 shadow-md shadow-cyan-500/20 flex items-center space-x-2 transition-all shrink-0"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loading ? 'Đang Tra Cứu...' : 'Tra Cứu Nhanh'}</span>
          </button>
        </div>

        {/* Suggestion Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] text-slate-400">Câu hỏi gợi ý:</span>
          {sampleQueries.map((sq, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(sq);
                handleSearch(sq);
              }}
              className="px-3 py-1 rounded-full bg-slate-950 border border-slate-800 hover:border-cyan-500/40 text-[11px] text-slate-300 hover:text-cyan-300 transition-all text-left truncate max-w-xs"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Answer Box */}
        {result ? (
          <div className="mt-4 p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white">Câu Trả Lời Trích Xuất Từ SOP Doanh Nghiệp</span>
              </div>
              <div className="flex items-center space-x-2">
                {result.is_cache_hit && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    Cache Hit
                  </span>
                )}
                <span
                  title={
                    result.retrieval_mode === 'SEMANTIC'
                      ? `Embeddings: ${result.embedding_model} · cosine ${result.retrieval_score.toFixed(3)}`
                      : `BM25 · score ${result.retrieval_score.toFixed(2)}${
                          result.fallback_reason ? ` · ${result.fallback_reason}` : ''
                        }`
                  }
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border cursor-help ${
                    result.retrieval_mode === 'SEMANTIC'
                      ? 'bg-violet-500/20 text-violet-300 border-violet-500/30'
                      : 'bg-slate-600/20 text-slate-300 border-slate-500/30'
                  }`}
                >
                  {result.retrieval_mode === 'SEMANTIC' ? 'SEMANTIC' : 'BM25'}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Độ trễ: {result.latency_ms} ms
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line">
              {result.answer}
            </div>

            {/* Citations */}
            <div className="pt-3 border-t border-slate-800 space-y-2">
              <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                <span>Nguồn Trích Dẫn & Cơ Sở Pháp Lý Nội Bộ (Citations):</span>
              </span>
              <div className="flex flex-wrap gap-2">
                {result.citations.map((cite, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 rounded bg-blue-950/40 border border-blue-500/30 text-[11px] text-blue-300 font-mono"
                  >
                    {cite}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="h-44 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2">
            <Database className="w-8 h-8 opacity-40" />
            <span>Chọn hoặc nhập câu hỏi phía trên để tra cứu quy chế tức thì</span>
          </div>
        )}
      </div>
    </div>
  );
};
