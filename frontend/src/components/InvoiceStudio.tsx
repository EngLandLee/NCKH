import React, { useState } from 'react';
import { FileText, ShieldCheck, Clock, CheckCircle2, AlertCircle, ArrowRight, UploadCloud } from 'lucide-react';
import { api, InvoiceResult } from '../services/api';

export const InvoiceStudio: React.FC = () => {
  const [inputText, setInputText] = useState(`HÓA ĐƠN GIÁ TRỊ GIA TĂNG (VAT INVOICE)
Mẫu số: 01GTKT0/001 - Ký hiệu: AA/26E - Số: 0019284
Đơn vị bán hàng: CÔNG TY TNHH VẬT LIỆU XÂY DỰNG TOÀN CẦU
Mã số thuế: 0312345678
Tên hàng hóa, dịch vụ: Thép cuộn xây dựng Hòa Phát D10 (Nguyên vật liệu sản xuất)
Cộng tiền hàng: 50,000,000 VND
Thuế suất GTGT: 10%
Tiền thuế GTGT: 5,000,000 VND
Tổng cộng tiền thanh toán: 55,000,000 VND
Hình thức thanh toán: Chuyển khoản (Chưa thanh toán)`);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InvoiceResult | null>(null);

  const handleProcess = async () => {
    setLoading(true);
    try {
      const res = await api.processInvoice(inputText, 'demo_invoice.txt');
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
          <h2 className="text-xl font-bold text-white tracking-wide">Studio Xử Lý Hóa Đơn & Hạch Toán Kế Toán</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Bóc tách dữ liệu từ chứng từ đầu vào và tự động gán mã tài khoản định khoản (GL Code) trong vòng &lt; 120ms.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Nội dung Hóa Đơn / Chứng Từ (Raw OCR Text / PDF)</span>
            </span>
          </div>

          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            rows={12}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500 custom-scrollbar"
            placeholder="Dán nội dung văn bản hóa đơn vào đây..."
          />

          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-slate-400">
              Chế độ: <strong className="text-emerald-400">Fast-Path Auto-Extraction</strong>
            </span>
            <button
              onClick={handleProcess}
              disabled={loading}
              className="px-5 py-2 rounded-lg bg-cyan-400 text-black font-bold text-xs hover:brightness-110 shadow-md shadow-cyan-500/20 flex items-center space-x-2 transition-all"
            >
              {loading ? <span>Đang xử lý...</span> : <span>Trích Xuất & Hạch Toán</span>}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right: Output Result */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Kết Quả Hạch Toán & Phân Loại Định Khoản</span>
              </span>
              {result && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {result.processing_latency_ms} ms
                </span>
              )}
            </div>

            {result ? (
              <div className="mt-4 space-y-4">
                {/* Status Bar */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold text-white">Trạng thái: {result.status}</span>
                  </div>
                  <span className="text-xs text-slate-400 font-mono">
                    Độ tin cậy: <strong className="text-cyan-400">{(result.confidence_score * 100).toFixed(1)}%</strong>
                  </span>
                </div>

                {/* Accounting Mapping Box */}
                <div className="p-4 rounded-lg bg-gradient-to-r from-blue-950/40 to-slate-900 border border-blue-500/30 space-y-2">
                  <span className="text-[11px] font-mono text-blue-300 uppercase tracking-wide">
                    Định khoản kế toán tự động (General Ledger)
                  </span>
                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-400">Tài khoản Nợ (Debit):</span>
                      <p className="text-sm font-bold text-emerald-400">{result.debit_account}</p>
                      <span className="text-[10px] text-slate-500">Nguyên vật liệu nhập kho</span>
                    </div>
                    <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-400">Tài khoản Có (Credit):</span>
                      <p className="text-sm font-bold text-cyan-400">{result.credit_account}</p>
                      <span className="text-[10px] text-slate-500">Phải trả người bán (Công nợ)</span>
                    </div>
                  </div>
                </div>

                {/* Extracted Fields */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-400 text-[10px]">Số Hóa Đơn</span>
                    <p className="font-bold text-slate-100">{result.invoice_number}</p>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-400 text-[10px]">Mã Số Thuế</span>
                    <p className="font-bold text-slate-100 font-mono">{result.tax_code}</p>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-400 text-[10px]">Tiền Trước Thuế</span>
                    <p className="font-bold text-slate-100">{result.subtotal.toLocaleString()} VND</p>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-400 text-[10px]">Tiền Thuế VAT ({result.vat_rate}%)</span>
                    <p className="font-bold text-slate-100">{result.vat_amount.toLocaleString()} VND</p>
                  </div>
                </div>

                <div className="p-3 rounded bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">Tổng Cộng Thanh Toán</span>
                  <span className="text-base font-extrabold text-emerald-400">
                    {result.total_amount.toLocaleString()} VND
                  </span>
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs space-y-2">
                <UploadCloud className="w-8 h-8 opacity-40" />
                <span>Nhấn "Trích Xuất & Hạch Toán" để xem kết quả</span>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Tiêu chuẩn kế toán: VAS / Circular 200</span>
            <span>Fast-Path Latency Target: &lt; 150ms</span>
          </div>
        </div>
      </div>
    </div>
  );
};
