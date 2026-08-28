const API_BASE = '/api';

export interface InvoiceResult {
  invoice_number: string;
  tax_code: string;
  subtotal: number;
  vat_rate: number;
  vat_amount: number;
  total_amount: number;
  debit_account: string;
  credit_account: string;
  confidence_score: number;
  status: string;
  processing_latency_ms: number;
  is_fast_path: boolean;
}

export interface DeliveryStop {
  id: number;
  name: string;
  lat: number;
  lng: number;
  demand: number;
}

export interface VRPResponse {
  status: string;
  routes: Array<{
    vehicle_id: number;
    node_sequence: number[];
    distance_km: number;
  }>;
  total_distance_km: number;
  total_time_min: number;
  solver_latency_ms: number;
  explanation: string;
}

export interface DemandResponse {
  sku_id: string;
  forecast_30d: number[];
  safety_stock: number;
  reorder_point: number;
  stockout_risk_pct: number;
  action_recommendation: string;
  latency_ms: number;
}

export interface RAGQueryResponse {
  answer: string;
  citations: string[];
  confidence: number;
  latency_ms: number;
  is_cache_hit: boolean;
}

export interface BenchmarkReport {
  total_samples: number;
  mean_latency_ms: number;
  p50_ms: number;
  p90_ms: number;
  p95_ms: number;
  p99_ms: number;
  fast_path_ratio_pct: number;
  overall_f1_score: number;
  accuracy: number;
  latex_table: string;
}

export const api = {
  processInvoice: async (raw_text: string, filename: string): Promise<InvoiceResult> => {
    const res = await fetch(`${API_BASE}/invoice/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text, filename, is_pdf: false })
    });
    return res.json();
  },

  solveVRP: async (payload: {
    depot: [number, number];
    stops: DeliveryStop[];
    vehicle_count: number;
    vehicle_capacity: number;
    weather: string;
    traffic_congestion_level: number;
  }): Promise<VRPResponse> => {
    const res = await fetch(`${API_BASE}/logistics/solve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  forecastDemand: async (payload: {
    sku_id: string;
    historical_demand: number[];
    current_stock: number;
    lead_time_days: number;
    supplier_reliability: number;
  }): Promise<DemandResponse> => {
    const res = await fetch(`${API_BASE}/demand/forecast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  queryRAG: async (query: string): Promise<RAGQueryResponse> => {
    const res = await fetch(`${API_BASE}/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, user_role: 'MANAGER' })
    });
    return res.json();
  },

  runBenchmark: async (samples: number = 1000): Promise<BenchmarkReport> => {
    const res = await fetch(`${API_BASE}/benchmark/run?samples=${samples}`);
    return res.json();
  }
};
