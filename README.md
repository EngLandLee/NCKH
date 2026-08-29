# 🚀 SupplyChain-AgenticHub

> **Hệ Thống Multi-Agent Tự Động Hóa Chuỗi Cung Ứng & Hạch Toán Doanh Nghiệp Thời Gian Thực với Ràng Buộc Độ Trễ Dưới 200ms**  
> *Targeted for MLAI Hackathon 2026 (Domain 5: Tối Ưu Hóa Vận Hành) & Faculty-Level Scientific Research Paper.*

---

## 🌟 Tổng Quan Hệ Thống

**SupplyChain-AgenticHub** là nền tảng điều phối đa tác thể (Multi-Agent Swarm) kết hợp giữa trí tuệ nhân tạo và các công cụ toán học tối ưu hóa tất định, giúp doanh nghiệp tự động hóa 4 quy trình trọng yếu:
1. **Invoice & Accounting Agent:** Tự động đọc hiểu hóa đơn VAT, bóc tách dữ liệu và định khoản kế toán VAS/Circular 200 (TK 152/156/133/331) với đối soát toán học 3 chiều.
2. **Dynamic VRP Logistics Agent:** Bộ giải Google OR-Tools C++ giải bài toán định tuyến đa phương tiện (CVRP), đo được **~1.0ms** với 4 điểm giao / 2 xe (giới hạn solver 25ms), tự động tính toán lại lộ trình theo kẹt xe và mưa bão ngập lụt.
3. **Demand & Disruption Forecaster:** Dự báo nhu cầu 30 ngày bằng mô hình chuỗi thời gian kết hợp xu hướng và tính mùa vụ, tính toán Tồn kho an toàn (Safety Stock) và Điểm đặt hàng lại (ROP).
4. **Enterprise SOP RAG Agent:** Tra cứu quy chế tài chính, sổ tay logistics và quy chuẩn kho bằng **BM25 + OpenAI embeddings** (cosine similarity), có ngưỡng từ chối khi không tài liệu nào phù hợp. Đo được **~0.07ms** ở nhánh BM25.

---

## ⚡ Kiến Trúc Phân Luồng 2 Tốc Độ (Dual-Speed Routing)

```
                            [ Web Dashboard / API Gateway ]
                                           │
                                           ▼
                            [ Dual-Speed Agent Router ]
                                           │
          ┌────────────────────────────────┼────────────────────────────────┐
          ▼                                ▼                                ▼
  [ Fast-Path: Heuristics ]       [ Fast-Path: OR-Tools ]          [ Fast-Path: In-Memory ]
  - Regex & VAS GL Mapper         - C++ CVRP Solver (~1.0ms)       - Keyword rank + exact cache
  - Time-series Forecast (~0.18ms) - Traffic/Weather penalties     - BM25 rank + exact cache
          │                                │                                │
          └────────────────────────────────┼────────────────────────────────┘
                                           │
                        (Nếu Độ Tin Cậy < 0.85 hoặc Bất Thường)
                                           ▼
                       [ OpenAI LLM Escalation & HITL ]  ✅ ĐÃ TRIỂN KHAI
                       - OpenAI Structured Outputs (Pydantic schema, temp=0)
                       - Trigger: confidence < 0.85 | lệch số học | thiếu MST
                       - RAG: Embeddings + cosine similarity (semantic)
                       - Fail-safe: không key/lỗi API → giữ kết quả fast-path
                       - AgentDB Long-term Memory (ghi log quyết định)
```

---

## 📊 Kết Quả Benchmark Hiệu Năng (10,000 Records)

Số liệu dưới đây **tái lập được** bằng một lệnh duy nhất trên máy sạch:

```bash
PYTHONPATH=. backend/venv/bin/python -m backend.app.benchmark.report
```

### In-distribution (10,000 bản ghi của `operations_benchmark_v2.json`)

| Hạng mục (Domain) | N | Mean | P95 | Acc | Macro-F1 | Tiêu chí chấm đúng |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Invoice & Accounting** | 2,500 | 0.033 ms | 0.040 ms | 100.00% | 1.0000 | Đúng TK Nợ **và** tổng tiền khớp nhãn |
| **Dynamic VRP Logistics** | 2,500 | 1.023 ms | 1.180 ms | 100.00% | — | Lời giải **khả thi**: mọi điểm giao đúng 1 lần, không vượt tải |
| **Demand Forecasting** | 2,500 | 0.179 ms | 0.220 ms | 100.00% | — | SS & ROP khớp công thức tính lại độc lập (sai số < 0.5) |
| **Enterprise SOP RAG** | 2,500 | 0.016 ms | 0.020 ms | 100.00% | 1.0000 | Trích dẫn đầu tiên đúng mã SOP của nhãn |
| **Toàn Hệ Thống** | **10,000** | **0.311 ms** | **1.070 ms** | **100.00%** | **1.0000** | |

> ✅ Mean **0.311 ms**, P95 **1.070 ms** — thỏa ngưỡng 200ms của cuộc thi với biên rất rộng.

### ⚠️ Held-out: giới hạn thật của Fast-Path

Bộ dữ liệu benchmark được sinh từ **6 mẫu nhà cung cấp**. Điểm 100% ở trên đo *trong phân phối đó*; nó **không** chứng minh khả năng tổng quát hóa. Trên hóa đơn chưa từng gặp:

| Bộ đo | Accuracy phân loại TK | Ghi chú |
| :--- | :---: | :--- |
| In-distribution (10,000 bản ghi) | **100.00%** | Khớp 6 mẫu sinh dữ liệu |
| **Held-out (mặt hàng mới)** | **25.00%** | = baseline "luôn đoán TK 152" → **không có kỹ năng thật** |

Bộ luật regex mặc định về TK 152 cho mọi mặt hàng lạ. Đây chính là **lý do định lượng** để kích hoạt nhánh LLM escalation (xem `backend/tests/test_generalization.py`).

### 🧠 Nhánh LLM Escalation (Slow Path)

Nhánh chậm **chỉ** kích hoạt trên phần đuôi khó — đo được **0/2500 hóa đơn sạch** phải escalate, nên fast-path vẫn giữ nguyên 100% và độ trễ ~0.35ms.

| Điều kiện kích hoạt | Ý nghĩa nghiệp vụ |
| :--- | :--- |
| `LOW_CONFIDENCE` | Regex không chắc chắn (`confidence < 0.85`) |
| `MATH_MISMATCH` | Tiền hàng + thuế ≠ tổng thanh toán |
| `UNKNOWN_VENDOR` | Không đọc được Mã số thuế |

Triển khai: **OpenAI Structured Outputs** (`chat.completions.parse` + Pydantic schema, `temperature=0`) buộc mô hình trả đúng 1 trong 4 tài khoản VAS, kèm `confidence` và `reasoning` tiếng Việt.

**Nguyên tắc an toàn cho Demo Day:** không có API key, mất mạng, hoặc lỗi/timeout → hệ thống **giữ nguyên kết quả fast-path** và ghi trạng thái `UNAVAILABLE`/`FAILED`, **không bao giờ ném lỗi**. Mọi lần escalate đều lưu vết `fast_path_debit_account` để đối chiếu trước/sau.

```bash
# Đo mức cải thiện của nhánh LLM trên tập held-out
export OPENAI_API_KEY=sk-...
PYTHONPATH=. backend/venv/bin/python -m backend.app.benchmark.report
```

### 🔍 Truy Xuất SOP: BM25 → Embeddings

Bảng benchmark ở trên chỉ dùng **4 câu hỏi cố định** khớp đúng 4 tài liệu — giống trường hợp hóa đơn, nó không đo được khả năng tổng quát. Chúng tôi bổ sung tập **câu hỏi diễn đạt lại** (hỏi cùng ý nhưng dùng từ ngữ khác hẳn tài liệu):

| Bộ đo | BM25 (lexical) | Semantic (embeddings) |
| :--- | :---: | :---: |
| Diễn đạt lại — dễ (10 câu) | **10/10** | cần key để đo |
| **Diễn đạt lại — khó (6 câu)** | **4/6** | cần key để đo |
| Ngoài phạm vi (3 câu) | từ chối đúng 3/3 | — |

**Hai lỗi đã sửa ở bản trước:**
1. Chấm điểm bằng **đếm substring** không chuẩn hóa độ dài → tài liệu dài nhất (`SOP-KHO-05`) hút hết câu hỏi lạ. Nay dùng **BM25** có chuẩn hóa độ dài.
2. Trả lời sai nhưng vẫn báo **confidence 0.85** — tệ hơn cả sai, vì người dùng không phân biệt được. Nay `confidence` bám theo điểm truy xuất thật, và có **ngưỡng từ chối** (BM25 < 2.0, cosine < 0.30) suy ra từ khoảng cách đo được giữa câu trong phạm vi (≥ 3.40) và ngoài phạm vi (≤ 1.17).

**Giới hạn thành thật:** BM25 đã đủ cho tập dễ; embeddings chỉ thực sự cần cho **2/6 câu khó** mà từ vựng không giao nhau. Với kho 4 tài liệu, đây là kết quả hợp lý — giá trị của embeddings sẽ tăng theo số lượng tài liệu.

> 📌 **Ghi chú phương pháp:** Macro-F1 chỉ báo cáo cho 2 domain có nhãn phân loại (invoice, RAG). Logistics và Demand được chấm bằng *kiểm định khả thi* và *tính lại công thức* — F1 theo lớp không có ý nghĩa ở đó nên để trống thay vì điền số giả.

---

## 🛠️ Cài Đặt & Khởi Chạy (Quick Start)

### Chỉ cần một lệnh

```bash
make dev
```

Lệnh này **tự cài mọi thứ còn thiếu** (venv Python 3.12, thư viện backend,
`node_modules`) rồi khởi động cả backend lẫn frontend. Chạy được ngay trên bản
clone sạch. Lần chạy sau bỏ qua bước cài (idempotent).

- **Dashboard:** http://localhost:3000
- **Swagger API docs:** http://localhost:8008/docs
- **Benchmark:** http://localhost:8008/api/benchmark/run?samples=1000

Cổng bị chiếm thì đổi: `make dev FRONTEND_PORT=3100`

### Các lệnh khác

| Lệnh | Việc |
| :--- | :--- |
| `make dev` | Cài (nếu thiếu) rồi khởi động — **lệnh chính** |
| `make check` | Preflight: kiểm tra deps + cổng, không khởi động |
| `make doctor` | Báo cáo môi trường: uv, pnpm, venv, API key, cổng |
| `make test` | Chạy test suite (42 passed, 2 skipped) |
| `make bench` | Tái lập số liệu benchmark + truy xuất SOP |
| `make build` | Type-check và build bundle production |
| `make lint` | Byte-compile backend + `tsc --noEmit` frontend |
| `make clean` | Xóa build output và cache |
| `make clean-all` | Xóa luôn venv và `node_modules` |
| `make help` | Liệt kê toàn bộ lệnh |

### Yêu cầu

- **[uv](https://docs.astral.sh/uv/)** — tự tải Python 3.12, không cần sudo
  (`ortools` **chưa có wheel cho Python 3.14**)
- **pnpm** — `npm i -g pnpm`

```bash
# (Tùy chọn) Bật LLM escalation + semantic RAG — thiếu key hệ thống vẫn chạy
echo 'OPENAI_API_KEY=sk-...' > .env
```

---

## 🎤 Demo Day
- **Kịch bản trình diễn, Q&A & phương án dự phòng:** [`docs/DEMO_DAY.md`](docs/DEMO_DAY.md)

```bash
make check   # preflight: venv, deps, cổng, API key — không khởi động gì
```

---

## 📑 Tài Liệu Nghiên Cứu Khoa Học (Paper & Specs)
- **Đề Cương Bài Báo Khoa Học (LaTeX & English Draft):** [`docs/paper_outline.md`](docs/paper_outline.md)
- **Tài Liệu Đặc Tả Thiết Kế Hệ Thống:** [`docs/superpowers/specs/2026-08-28-supplychain-agentichub-design.md`](docs/superpowers/specs/2026-08-28-supplychain-agentichub-design.md)
- **Kế Hoạch Triển Khai (Implementation Plan):** [`docs/superpowers/plans/2026-08-28-supplychain-agentichub.md`](docs/superpowers/plans/2026-08-28-supplychain-agentichub.md)
- **Tập Dữ Liệu Benchmark:** [`data/operations_benchmark_v2.json`](data/operations_benchmark_v2.json)
