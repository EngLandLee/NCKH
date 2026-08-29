import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
from backend.app.agents.router import DualSpeedRouter, AgentTaskRequest


class DomainMetrics(BaseModel):
    """Per-domain scores. Each domain is graded by its own verifiable criterion."""
    domain: str
    samples: int
    criterion: str  # what "correct" means for this domain
    accuracy: float
    macro_f1: Optional[float] = None  # only for classification domains
    mean_latency_ms: float
    p95_latency_ms: float


class BenchmarkReport(BaseModel):
    total_samples: int
    mean_latency_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    fast_path_ratio_pct: float
    overall_f1_score: float
    accuracy: float
    per_domain: List[DomainMetrics]
    latex_table: str


def _macro_f1(y_true: List[str], y_pred: List[str]) -> float:
    """Macro-averaged F1 over the union of observed labels.

    Averaged over classes present in y_true so that absent classes do not
    dilute the score. Returns 0.0 for an empty input.
    """
    if not y_true:
        return 0.0

    labels = sorted(set(y_true))
    f1s = []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        f1s.append(f1)

    return float(np.mean(f1s)) if f1s else 0.0


def _check_invoice(record: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Correct iff the predicted GL debit account matches the labelled account
    AND the extracted total reconciles with the labelled total.
    Returns (is_correct, true_label, predicted_label) for F1 computation.
    """
    truth = record.get("ground_truth_label")
    pred = data.get("debit_account")

    gl_ok = pred == truth
    expected_total = record.get("ground_truth_total")
    if expected_total is None:
        total_ok = True
    else:
        total_ok = abs(float(data.get("total_amount", 0.0)) - float(expected_total)) < 1.0

    return (gl_ok and total_ok), str(truth), str(pred)


def _check_logistics(record: Dict[str, Any], data: Dict[str, Any]) -> bool:
    """Correct iff the solver returned a *feasible* CVRP solution:
    solved, every stop visited exactly once, and no vehicle over capacity.
    This is an independent feasibility audit of the solver output, not a
    restatement of its own status flag.
    """
    if data.get("status") != "SUCCESS":
        return False

    payload = record["payload"]
    stops = payload["stops"]
    n_stops = len(stops)
    capacity = payload["vehicle_capacity"]
    # node 0 is the depot; stops are nodes 1..n_stops
    demand_by_node = {i + 1: stops[i]["demand"] for i in range(n_stops)}

    visited: List[int] = []
    for route in data.get("routes", []):
        seq = route.get("node_sequence", [])
        customers = [n for n in seq if n != 0]
        load = sum(demand_by_node.get(n, 0) for n in customers)
        if load > capacity:
            return False
        visited.extend(customers)

    # every customer served exactly once
    return sorted(visited) == list(range(1, n_stops + 1))


def _check_demand(record: Dict[str, Any], data: Dict[str, Any]) -> bool:
    """Correct iff safety stock and reorder point match an independent
    recomputation of the textbook formulas:
        SS  = z * sigma * sqrt(LT)
        ROP = mean_demand * LT + SS
    and the 30-day forecast is well formed (right length, non-negative).
    """
    payload = record["payload"]
    history = np.array(payload["historical_demand"], dtype=np.float64)
    lead_time = payload.get("lead_time_days", 7)
    z = 1.65  # 95% service level, matching FastDemandForecaster

    expected_ss = z * float(np.std(history)) * np.sqrt(lead_time)
    expected_rop = float(np.mean(history)) * lead_time + expected_ss

    ss_ok = abs(float(data.get("safety_stock", 0.0)) - expected_ss) < 0.5
    rop_ok = abs(float(data.get("reorder_point", 0.0)) - expected_rop) < 0.5

    forecast = data.get("forecast_30d", [])
    forecast_ok = len(forecast) == 30 and all(v >= 0 for v in forecast)

    return ss_ok and rop_ok and forecast_ok


def _check_rag(record: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Correct iff the top citation resolves to the labelled SOP document id."""
    truth = str(record.get("ground_truth_label"))
    citations = data.get("citations") or []
    pred = citations[0].split(":")[0].strip() if citations else "NONE"
    return (pred == truth), truth, pred


class BenchmarkEvaluator:
    def __init__(self):
        self.router = DualSpeedRouter()

    def run_evaluation(self, records: List[Dict[str, Any]]) -> BenchmarkReport:
        latencies: List[float] = []
        fast_path_count = 0
        n = len(records)

        # per-domain accumulators
        dom_correct: Dict[str, int] = {}
        dom_total: Dict[str, int] = {}
        dom_lat: Dict[str, List[float]] = {}
        # classification labels for macro-F1 (invoice, rag)
        cls_true: Dict[str, List[str]] = {"invoice": [], "rag": []}
        cls_pred: Dict[str, List[str]] = {"invoice": [], "rag": []}

        for record in records:
            domain = record["domain"]
            req = AgentTaskRequest(domain=domain, payload=record["payload"])
            res = self.router.execute(req)

            latencies.append(res.latency_ms)
            dom_lat.setdefault(domain, []).append(res.latency_ms)
            dom_total[domain] = dom_total.get(domain, 0) + 1
            if res.is_fast_path:
                fast_path_count += 1

            if domain == "invoice":
                ok, t, p = _check_invoice(record, res.data)
                cls_true["invoice"].append(t)
                cls_pred["invoice"].append(p)
            elif domain == "rag":
                ok, t, p = _check_rag(record, res.data)
                cls_true["rag"].append(t)
                cls_pred["rag"].append(p)
            elif domain == "logistics":
                ok = _check_logistics(record, res.data)
            elif domain == "demand":
                ok = _check_demand(record, res.data)
            else:
                ok = False

            if ok:
                dom_correct[domain] = dom_correct.get(domain, 0) + 1

        criteria = {
            "invoice": "GL debit account matches label AND extracted total reconciles",
            "logistics": "CVRP solution feasible: all stops served once, capacity respected",
            "demand": "safety stock & ROP match independent recomputation (tol 0.5)",
            "rag": "top citation resolves to the labelled SOP document id",
        }

        per_domain: List[DomainMetrics] = []
        for domain in sorted(dom_total.keys()):
            total = dom_total[domain]
            correct = dom_correct.get(domain, 0)
            lat = np.array(dom_lat[domain], dtype=np.float64)
            per_domain.append(DomainMetrics(
                domain=domain,
                samples=total,
                criterion=criteria.get(domain, "unknown"),
                accuracy=round(correct / max(1, total), 4),
                macro_f1=(round(_macro_f1(cls_true[domain], cls_pred[domain]), 4)
                          if domain in cls_true else None),
                mean_latency_ms=round(float(np.mean(lat)), 3),
                p95_latency_ms=round(float(np.percentile(lat, 95)), 3),
            ))

        total_correct = sum(dom_correct.values())
        acc = round(total_correct / max(1, n), 4)

        # Overall F1 = macro-F1 averaged across the classification domains only.
        # Feasibility-checked domains (logistics, demand) have no class labels,
        # so folding them into an F1 would be meaningless.
        cls_f1s = [_macro_f1(cls_true[d], cls_pred[d]) for d in ("invoice", "rag") if cls_true[d]]
        f1 = round(float(np.mean(cls_f1s)), 4) if cls_f1s else 0.0

        arr_lat = np.array(latencies, dtype=np.float64) if latencies else np.array([0.0])
        mean_lat = float(np.mean(arr_lat))
        p50 = float(np.percentile(arr_lat, 50))
        p90 = float(np.percentile(arr_lat, 90))
        p95 = float(np.percentile(arr_lat, 95))
        p99 = float(np.percentile(arr_lat, 99))
        fast_ratio = round((fast_path_count / max(1, n)) * 100.0, 2)

        rows = "\n".join(
            f"{d.domain} & {d.samples:,} & {d.accuracy * 100:.2f}\\% & "
            f"{('%.4f' % d.macro_f1) if d.macro_f1 is not None else '--'} & "
            f"{d.mean_latency_ms:.3f} & {d.p95_latency_ms:.3f} \\\\"
            for d in per_domain
        )
        latex_code = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Per-domain benchmark results of SupplyChain-AgenticHub under a sub-200ms latency budget.
Invoice and RAG are graded as classification against labelled ground truth (macro-F1 reported);
logistics and demand are graded by independent feasibility and formula-recomputation audits,
for which a class-based F1 is not defined.}}
\\label{{tab:benchmark_results}}
\\begin{{tabular}}{{lccccc}}
\\hline
\\textbf{{Domain}} & \\textbf{{N}} & \\textbf{{Accuracy}} & \\textbf{{Macro-F1}} & \\textbf{{Mean (ms)}} & \\textbf{{P95 (ms)}} \\\\
\\hline
{rows}
\\hline
\\textbf{{Overall}} & {n:,} & {acc * 100:.2f}\\% & {f1:.4f} & {mean_lat:.3f} & {p95:.3f} \\\\
\\hline
\\end{{tabular}}
\\end{{table}}"""

        return BenchmarkReport(
            total_samples=n,
            mean_latency_ms=round(mean_lat, 3),
            p50_ms=round(p50, 3),
            p90_ms=round(p90, 3),
            p95_ms=round(p95, 3),
            p99_ms=round(p99, 3),
            fast_path_ratio_pct=fast_ratio,
            overall_f1_score=f1,
            accuracy=acc,
            per_domain=per_domain,
            latex_table=latex_code.strip(),
        )
