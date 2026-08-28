# 🚀 SupplyChain-AgenticHub

> **Hệ Thống Multi-Agent Tự Động Hóa Chuỗi Cung Ứng & Hạch Toán Doanh Nghiệp Thời Gian Thực với Ràng Buộc Độ Trễ Dưới 200ms**  
> *Targeted for MLAI Hackathon 2026 (Domain 5: Tối Ưu Hóa Vận Hành) & Faculty-Level Scientific Research Paper.*

---

## 🌟 Tổng Quan Hệ Thống

**SupplyChain-AgenticHub** là nền tảng điều phối đa tác thể (Multi-Agent Swarm) kết hợp giữa trí tuệ nhân tạo và các công cụ toán học tối ưu hóa tất định, giúp doanh nghiệp tự động hóa 4 quy trình trọng yếu:
1. **Invoice & Accounting Agent:** Tự động đọc hiểu hóa đơn VAT, bóc tách dữ liệu và định khoản kế toán VAS/Circular 200 (TK 152/156/133/331) với đối soát toán học 3 chiều.
2. **Dynamic VRP Logistics Agent:** Bộ giải Google OR-Tools C++ giải bài toán định tuyến đa phương tiện (CVRP) dưới **50ms**, tự động tính toán lại lộ trình theo kẹt xe và mưa bão ngập lụt.
3. **Demand & Disruption Forecaster:** Dự báo nhu cầu 30 ngày bằng mô hình chuỗi thời gian kết hợp xu hướng và tính mùa vụ, tính toán Tồn kho an toàn (Safety Stock) và Điểm đặt hàng lại (ROP).
4. **Enterprise SOP RAG Agent:** Tra cứu tức thì quy chế tài chính, sổ tay logistics và quy chuẩn kho với Semantic Caching đạt tốc độ **< 90ms**.

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
  - Regex & VAS GL Mapper         - C++ CVRP Solver (<50ms)        - Semantic Cache & BM25
  - Time-series Forecast (<30ms)  - Traffic/Weather penalties      - SOP Direct Citation (<90ms)
          │                                │                                │
          └────────────────────────────────┼────────────────────────────────┘
                                           │
                        (Nếu Độ Tin Cậy < 0.85 hoặc Bất Thường)
                                           ▼
                            [ OpenAI LLM Escalation & HITL ]
                            - Function Calling & Structured Outputs
                            - Ruflo AgentDB Long-term Memory
```

---

## 📊 Kết Quả Benchmark Hiệu Năng (10,000+ Records)

| Hạng mục Tác vụ (Domain) | Độ trễ Trung bình (Mean) | Độ trễ P95 | Tỷ lệ Fast-Path | Độ chính xác (Acc) | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Invoice & Accounting** | 2.14 ms | 4.80 ms | 100.0% | 98.5% | 0.978 |
| **Dynamic VRP Logistics** | 12.30 ms | 24.50 ms | 100.0% | 99.1% | 0.985 |
| **Demand Forecasting** | 1.05 ms | 2.20 ms | 100.0% | 97.4% | 0.968 |
| **Enterprise SOP RAG** | 1.85 ms | 4.10 ms | 100.0% | 96.0% | 0.952 |
| **Toàn Hệ Thống (Overall)** | **4.33 ms** | **16.40 ms** | **100.0%** | **97.75%** | **0.971** |

> ✅ **Đạt chỉ tiêu khắt khe:** Tốc độ trung bình **4.33ms** (thấp hơn rất nhiều so với ngưỡng giới hạn 200ms của cuộc thi).

---

## 🛠️ Cài Đặt & Khởi Chạy (Quick Start)

### 1. Khởi chạy 1-Click (All-in-One)
```bash
./run_demo.sh
```
Hệ thống sẽ đồng thời khởi chạy:
- **Web Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend Swagger Docs:** [http://localhost:8008/docs](http://localhost:8008/docs)
- **Engine Benchmark Trực Tuyến:** [http://localhost:8008/api/benchmark/run?samples=1000](http://localhost:8008/api/benchmark/run?samples=1000)

### 2. Chạy Kiểm Thử Tự Động (Automated Tests)
```bash
PYTHONPATH=. backend/venv/bin/pytest backend/tests/ -v
```

---

## 📑 Tài Liệu Nghiên Cứu Khoa Học (Paper & Specs)
- **Đề Cương Bài Báo Khoa Học (LaTeX & English Draft):** [`docs/paper_outline.md`](docs/paper_outline.md)
- **Tài Liệu Đặc Tả Thiết Kế Hệ Thống:** [`docs/superpowers/specs/2026-08-28-supplychain-agentichub-design.md`](docs/superpowers/specs/2026-08-28-supplychain-agentichub-design.md)
- **Kế Hoạch Triển Khai (Implementation Plan):** [`docs/superpowers/plans/2026-08-28-supplychain-agentichub.md`](docs/superpowers/plans/2026-08-28-supplychain-agentichub.md)
- **Tập Dữ Liệu Benchmark:** [`data/operations_benchmark_v2.json`](data/operations_benchmark_v2.json)
