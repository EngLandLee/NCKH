"""Reproducible benchmark report.

Runs the evaluator over the committed dataset and prints per-domain metrics,
the held-out generalization check, and the LaTeX table for the paper.

    PYTHONPATH=. backend/venv/bin/python -m backend.app.benchmark.report
"""
import json
import os
import sys

from backend.app.benchmark.evaluator import BenchmarkEvaluator
from backend.app.solvers.pdf_parser import InvoiceRuleParser

DATASET = os.path.join("data", "operations_benchmark_v2.json")


def _held_out_gl_accuracy() -> tuple[int, int]:
    """Classifier accuracy on line items absent from the generator templates."""
    from backend.tests.test_generalization import HELD_OUT_INVOICES, _invoice_text

    parser = InvoiceRuleParser()
    correct = sum(
        1 for item, expected in HELD_OUT_INVOICES
        if parser.extract_fields(_invoice_text(item))["debit_account"] == expected
    )
    return correct, len(HELD_OUT_INVOICES)


def main() -> int:
    if not os.path.exists(DATASET):
        print(f"Dataset not found: {DATASET}", file=sys.stderr)
        return 1

    with open(DATASET, encoding="utf-8") as f:
        records = json.load(f)["records"]

    report = BenchmarkEvaluator().run_evaluation(records)

    print(f"=== In-distribution benchmark — {report.total_samples:,} records ===")
    header = f"{'domain':<11}{'N':>7}{'acc':>9}{'macroF1':>10}{'mean_ms':>10}{'p95_ms':>9}"
    print(header)
    print("-" * len(header))
    for m in report.per_domain:
        f1 = f"{m.macro_f1:.4f}" if m.macro_f1 is not None else "--"
        print(f"{m.domain:<11}{m.samples:>7}{m.accuracy * 100:>8.2f}%{f1:>10}"
              f"{m.mean_latency_ms:>10.3f}{m.p95_latency_ms:>9.3f}")
    print("-" * len(header))
    print(f"{'OVERALL':<11}{report.total_samples:>7}{report.accuracy * 100:>8.2f}%"
          f"{report.overall_f1_score:>10.4f}{report.mean_latency_ms:>10.3f}{report.p95_ms:>9.3f}")
    print()
    print(f"p50/p90/p99 : {report.p50_ms} / {report.p90_ms} / {report.p99_ms} ms")
    print(f"fast-path   : {report.fast_path_ratio_pct}%")
    print()

    print("Grading criteria (what 'correct' means):")
    for m in report.per_domain:
        print(f"  {m.domain:<11} {m.criterion}")
    print()

    correct, total = _held_out_gl_accuracy()
    print("=== Held-out generalization (line items absent from the templates) ===")
    print(f"Fast path (regex) accuracy: {correct}/{total} = {correct / total * 100:.2f}%")
    print("Baseline 'always TK 152'  : 25.00%")
    if correct / total <= 0.25:
        print("=> The rule-based fast path shows NO skill beyond the majority class.")
        print("   This is the quantified case for LLM escalation on low confidence.")
    print()

    _report_escalation()
    _report_rag_retrieval()

    print(report.latex_table)
    return 0


def _report_rag_retrieval() -> None:
    """Paraphrase retrieval accuracy: BM25 alone, and semantic if a key exists."""
    from backend.app.agents.rag_agent import RAGAgent, RAGQueryRequest
    from backend.tests.test_rag_retrieval import (
        HARD_PARAPHRASE_QUERIES,
        PARAPHRASE_QUERIES,
        _retrieved_id,
    )

    agent = RAGAgent()

    def score(queries, semantic: bool) -> int:
        return sum(
            1 for q, expected in queries
            if _retrieved_id(agent.query(RAGQueryRequest(query=q, allow_semantic=semantic))) == expected
        )

    print("=== SOP retrieval (paraphrased queries) ===")
    easy_n, hard_n = len(PARAPHRASE_QUERIES), len(HARD_PARAPHRASE_QUERIES)
    lex_easy = score(PARAPHRASE_QUERIES, False)
    lex_hard = score(HARD_PARAPHRASE_QUERIES, False)
    print(f"BM25 lexical   : easy {lex_easy}/{easy_n}, hard {lex_hard}/{hard_n}")

    if agent.embedder.is_available:
        agent.cache.clear()
        sem_easy = score(PARAPHRASE_QUERIES, True)
        sem_hard = score(HARD_PARAPHRASE_QUERIES, True)
        print(f"Semantic ({agent.embedder.model}): easy {sem_easy}/{easy_n}, hard {sem_hard}/{hard_n}")
    else:
        print("Semantic       : skipped (OPENAI_API_KEY not set) — falls back to BM25")
    print()


def _report_escalation() -> None:
    """Measure the slow path on the held-out set, if a key is configured."""
    from backend.app.agents.invoice_agent import InvoiceAgent, InvoiceRawInput
    from backend.app.agents.llm_escalation import LLMEscalationAgent
    from backend.tests.test_generalization import HELD_OUT_INVOICES, _invoice_text

    print("=== LLM escalation (slow path) ===")
    if not LLMEscalationAgent().is_available:
        print("OPENAI_API_KEY not set — skipping. The fast path degrades safely;")
        print("set the key and re-run to measure the escalation uplift.")
        print()
        return

    agent = InvoiceAgent()
    correct = escalated = 0
    latencies = []
    for item, expected in HELD_OUT_INVOICES:
        # Drop the tax code so these look like messy real-world scans.
        text = _invoice_text(item).replace("Mã số thuế: 0312345678. ", "")
        res = agent.process(InvoiceRawInput(raw_text=text, filename="held_out.txt"))
        if res.escalation_status == "ESCALATED":
            escalated += 1
            latencies.append(res.escalation_latency_ms)
        if res.debit_account == expected:
            correct += 1

    n = len(HELD_OUT_INVOICES)
    print(f"Escalated          : {escalated}/{n}")
    print(f"Accuracy after LLM : {correct}/{n} = {correct / n * 100:.2f}%")
    if latencies:
        print(f"Escalation latency : mean {sum(latencies) / len(latencies):.0f} ms, "
              f"max {max(latencies):.0f} ms")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
