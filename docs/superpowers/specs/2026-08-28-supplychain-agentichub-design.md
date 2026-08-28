# Design Document: SupplyChain-AgenticHub (M-Agentic Operational Hub)

- **Date:** 2026-08-28
- **Project Name:** SupplyChain-AgenticHub
- **Target Venues:** MLAI Hackathon 2026 (Domain 5: Operations Optimization / Supply Chain & Enterprise Automation), Open Source Competitions, Faculty-Level Scientific Research Paper.
- **Paper Title (English):** *"A Dual-Speed Agentic Multi-Agent Framework for Real-Time Enterprise Supply Chain Optimization and Automated Financial Accounting under Sub-200ms Latency Constraints"*

---

## 1. Executive Summary & Goals

Enterprise digital transformation often stumbles on fragmented legacy systems, high latencies in large language models, and lack of domain-aware guardrails. **SupplyChain-AgenticHub** is an open-source, event-driven multi-agent platform designed to automate end-to-end supply chain operations and financial accounting under strict latency (`< 200ms`), high accuracy, and high F1-score constraints.

### Core Objectives:
1. **End-to-End Enterprise Automation:** Interlink 4 core operations: Invoice Extraction & Accounting, Raw Material Demand Forecasting, Dynamic Vehicle Routing (VRP), and Internal SOP Knowledge Retrieval (RAG).
2. **Dual-Speed Hybrid Latency Architecture:**
   - **Fast Path (< 150ms):** Rule-based heuristics, in-memory caches, and high-performance C++/Python solvers (`Google OR-Tools`, local statistical forecasters, lexical/dense indices) handle 85–90% of routine workloads.
   - **Slow/Reasoning Path (LLM Exception Handling):** OpenAI API (`gpt-4o-mini` / `gpt-4o`) with Structured Outputs and Function Calling handles complex anomalies, edge cases, and human-in-the-loop escalation.
3. **Rigorous Benchmark Evaluation:** Built-in generator and evaluation engine for `operations_benchmark_v2.json` (100,000+ multi-domain enterprise records) measuring Accuracy, F1-Score, and P50/P90/P95/P99 latency profiles.
4. **Interactive Demo Day Dashboard:** Full-featured modern web application providing live interactive VRP maps, drag-and-drop invoice accounting studio, inventory risk charts, and real-time benchmark execution.

---

## 2. System Architecture

The system utilizes a Hybrid Microservices Architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND: NEXT.JS / REACT DASHBOARD                    │
│  - Leaflet Dynamic VRP Map            - Drag-and-Drop Invoice Studio       │
│  - Real-Time Inventory Risk Charts    - Sub-200ms Benchmark Suite Tab       │
│  - Agent Swarm Reasoning Stream       - Human-in-the-Loop Approval Queue   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / WebSocket (Port 8000)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BACKEND CORE: FASTAPI (PYTHON 3.11+)                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    DUAL-SPEED AGENT ROUTER                            │  │
│  │  - Fast Path: Heuristics, Regex, Local Cache, Fast Index (< 150ms)    │  │
│  │  - Slow Path: OpenAI Function Calling & Structured Outputs (Exceptions)│ │
│  └───────┬──────────────┬──────────────┬──────────────┬──────────────────┘  │
│          │              │              │              │                     │
│          ▼              ▼              ▼              ▼                     ▼
│   ┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐      ┌─────────────┐
│   │Invoice Agent││Demand Agent ││Logistics Agt││  RAG Agent  │      │Human-in-Loop│
│   │(Unstructured││(TFT/LightGBM││(Google OR-  ││(Hybrid Qdr- │      │  Guardrail  │
│   │+ GL Matcher)││+ Risk Score)││ Tools VRP)  ││ ant/Vector) │      │  (Review Q) │
│   └─────────────┘└─────────────┘└─────────────┘└─────────────┘      └─────────────┘
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Agent Protocol / Subprocess / MCP
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RUFLO AGENTIC HARNESS (Node.js/TS V3)                     │
│  - AgentDB / RuVector Memory (Cross-session state & learned heuristics)     │
│  - Multi-Agent Consensus & Swarm Coordination                               │
│  - Security Guardrails (Model Armor: Prompt injection & Tool Poisoning)     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component & Agent Specifications

### 3.1. Invoice & Accounting Agent (`InvoiceAgent`)
- **Purpose:** Automatically parse invoices/purchase orders (PDF/Images), extract structured metadata, calculate line-item totals, and assign General Ledger (GL) accounting codes (e.g. Vietnamese Standard Chart of Accounts: TK 152/156 Raw Materials, TK 133 Input VAT, TK 331 Supplier Payables).
- **Fast Path (< 120ms):**
  - Uses regex rules and cached vendor templates for recognized vendors.
  - Computes subtotal, VAT 8%/10%, and grand total instantly.
  - Matches 3-way reconciliation (Invoice vs PO vs Goods Receipt).
- **Slow Path (OpenAI Structured Outputs):**
  - Triggers when vendor is unknown or OCR confidence is below 85%.
  - Invokes `gpt-4o-mini` with Pydantic schema `InvoiceExtractionResult`.
- **Guardrails:**
  - If `abs(grand_total - (subtotal + vat_amount)) > 1.0`, triggers `FLAG_HUMAN_REVIEW`.

### 3.2. Dynamic Logistics & VRP Agent (`LogisticsAgent`)
- **Purpose:** Solve the Capacitated Vehicle Routing Problem with Time Windows (CVRPTW) under real-time traffic congestion and adverse weather conditions.
- **Fast Path (< 50ms):**
  - Implements **Google OR-Tools** routing solver in Python/C++.
  - Distance and duration matrices updated with traffic/weather penalty multipliers.
  - Computes optimal vehicle routes and delivery stops within 20–50ms.
- **Slow Path (OpenAI Natural Language Explanations):**
  - Generates situational driver alerts explaining why a route changed (e.g., localized flooding or accident).

### 3.3. Supply Demand & Disruption Agent (`DemandAgent`)
- **Purpose:** Forecast raw material requirements, identify supply bottlenecks, compute Safety Stock and Reorder Points (ROP), and assess disruption risks.
- **Fast Path (< 40ms):**
  - Statistical Exponential Smoothing & fast LightGBM regression.
  - Evaluates stockout probability $P(\text{Stockout}) = P(D_{\text{lead}} > \text{Stock Level})$.
- **Slow Path (OpenAI Procurement Assistance):**
  - When $P(\text{Stockout}) > 0.75$, drafts an automated Purchase Order (PO) and prepares a root cause summary for management.

### 3.4. Enterprise RAG Knowledge Agent (`RAGAgent`)
- **Purpose:** Provide sub-200ms answers to employee inquiries regarding Standard Operating Procedures (SOP), procurement guidelines, and financial compliance.
- **Fast Path (< 90ms):**
  - In-memory Semantic Cache + BM25 Lexical + Dense Vector Index (Qdrant/FAISS).
  - Cache hits return verified answers under 40ms.
- **Slow Path (OpenAI RAG Generation):**
  - Uses `gpt-4o-mini` with retrieved document chunks, enforcing strict markdown citations (document name, page number, clause).

---

## 4. Ruflo Agent Harness & Governance

- **AgentDB / RuVector Memory:** Persists learned vendor mappings, recurring traffic bottlenecks, and human-in-the-loop decisions across sessions.
- **Model Armor & Security:** Sanitizes all document inputs and user queries to prevent prompt injection and tool poisoning attacks.
- **Human-in-the-Loop Review Queue:**
  - Tasks with confidence score $< 0.85$ or safety violations transition to `PENDING_HUMAN_APPROVAL`.
  - Review queue accessible on Dashboard with one-click approve, modify, or reject actions.
  - Feedback is recorded back to AgentDB for continuous self-learning.

---

## 5. Benchmark Suite (`operations_benchmark_v2.json`) & Evaluation Engine

- **Dataset Composition (100,000 Records):**
  1. `invoices`: 40,000 samples (Tax codes, subtotals, VAT, line items, GL accounting labels, noisy edge cases).
  2. `demand_forecasts`: 30,000 samples (Multi-echelon demand sequences, demand spikes, lead time disruptions).
  3. `logistics_vrp`: 20,000 samples (GPS coordinates, depot locations, vehicle capacities, weather/congestion matrices).
  4. `sop_qa`: 10,000 samples (SOP questions, verified answers, exact ground-truth citations).
- **Evaluation Metrics:**
  - **Accuracy & F1-Score:** Macro/Micro precision, recall, F1 across GL classification and entity extraction.
  - **Latency Distribution:** P50, P90, P95, P99, and Mean Latency (Target: Mean $< 200\text{ms}$).
  - **Automated LaTeX Output:** Automatically exports benchmark summary tables formatted for direct inclusion into academic research papers.

---

## 6. Web Dashboard UI Specification

- **Tech Stack:** React 19 / Next.js / Vite + Tailwind CSS + Lucide Icons + Leaflet Maps + Recharts.
- **Tabs & Views:**
  1. **Command Center:** Swarm topology, active agents, live event stream, system throughput.
  2. **Invoice Studio:** PDF/image dropzone, bounding box overlay, parsed field table, 3-way matching badge, GL code mapper.
  3. **Demand Forecaster:** Interactive 30-day forecast curves, historical trendline, stockout risk radar, draft PO drawer.
  4. **Dynamic VRP Map:** Leaflet map with vehicle markers, color-coded routes, congestion/weather toggles, real-time reroute button with live millisecond clock.
  5. **SOP RAG Assistant:** Chat interface, source citation preview drawer, sub-200ms latency badge.
  6. **Benchmark & Research Hub:** 1k/10k/100k sample selector, live execution progress bar, latency histogram, confusion matrix, export LaTeX table button.

---

## 7. Directory Structure

```
SupplyChain-AgenticHub/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── config.py                   # Environment & settings
│   │   ├── agents/
│   │   │   ├── router.py               # Dual-Speed Agent Router
│   │   │   ├── invoice_agent.py        # Invoice & Accounting Agent
│   │   │   ├── demand_agent.py         # Demand Forecasting Agent
│   │   │   ├── logistics_agent.py      # Dynamic VRP Logistics Agent
│   │   │   └── rag_agent.py            # Enterprise SOP RAG Agent
│   │   ├── solvers/
│   │   │   ├── vrp_solver.py           # Google OR-Tools VRP Solver
│   │   │   ├── pdf_parser.py           # Unstructured / PyPDF Parser
│   │   │   └── forecaster.py           # Fast Time-Series Predictor
│   │   ├── memory/
│   │   │   └── agent_memory.py         # Ruflo AgentDB / RuVector bridge
│   │   ├── benchmark/
│   │   │   ├── generator.py            # Generates operations_benchmark_v2.json
│   │   │   └── evaluator.py            # Batch latency & accuracy evaluator
│   │   └── api/
│   │       ├── routes_invoice.py
│   │       ├── routes_demand.py
│   │       ├── routes_logistics.py
│   │       ├── routes_rag.py
│   │       └── routes_benchmark.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── CommandCenter.tsx
│   │   │   ├── InvoiceStudio.tsx
│   │   │   ├── DemandForecaster.tsx
│   │   │   ├── VRPMap.tsx
│   │   │   ├── RAGAssistant.tsx
│   │   │   └── BenchmarkHub.tsx
│   │   └── services/api.ts
│   ├── package.json
│   └── tailwind.config.js
├── data/
│   └── operations_benchmark_v2.json     # 100k benchmark dataset
├── docs/
│   └── paper_outline.md                # Research paper template for faculty publication
└── README.md
```

---

## 8. Verification & Acceptance Criteria

1. **Latency Verification:** Benchmark runner on 10,000 samples confirms average latency $< 200\text{ms}$ with Fast-Path ratio $\ge 80\%$.
2. **Accuracy Verification:** Invoice GL mapping F1-Score $\ge 0.95$; VRP solver returns valid, non-overlapping route solutions within $50\text{ms}$.
3. **OpenAI Integration:** OpenAI Function Calling and Structured Outputs operate seamlessly in Online Mode, with robust fallback in Offline/Mock Mode.
4. **UI Usability:** All 6 dashboard tabs render cleanly with responsive controls, interactive map routing, and live latency feedback.
