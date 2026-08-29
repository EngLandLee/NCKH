import pytest
from backend.app.benchmark.generator import generate_benchmark_dataset
from backend.app.benchmark.evaluator import BenchmarkEvaluator

def test_benchmark_generation_and_evaluation():
    # Generate 100 samples for test
    dataset = generate_benchmark_dataset(sample_size=100)
    assert len(dataset["records"]) == 100

    evaluator = BenchmarkEvaluator()
    report = evaluator.run_evaluation(dataset["records"])

    assert report.total_samples == 100
    assert report.mean_latency_ms < 200.0  # Must strictly satisfy latency requirement
    assert report.p95_ms < 200.0
    assert "\\begin{table}" in report.latex_table # Verification for faculty research paper

    # Every domain must be graded by a stated, falsifiable criterion.
    assert {m.domain for m in report.per_domain} == {"invoice", "demand", "logistics", "rag"}
    for m in report.per_domain:
        assert m.criterion, f"{m.domain} has no stated grading criterion"
        assert 0.0 <= m.accuracy <= 1.0

    # Macro-F1 is reported only where classification labels exist.
    by_domain = {m.domain: m for m in report.per_domain}
    assert by_domain["invoice"].macro_f1 is not None
    assert by_domain["rag"].macro_f1 is not None
    assert by_domain["logistics"].macro_f1 is None
    assert by_domain["demand"].macro_f1 is None


def test_f1_is_computed_not_derived_from_accuracy():
    """Guards against the previous `f1 = accuracy * 0.99` placeholder.

    A macro-F1 that is merely accuracy scaled by a constant would hide
    per-class failures; the invoice classifier once read 65% accuracy while
    two of four GL classes were unreachable (macro-F1 0.37).
    """
    from backend.app.benchmark.evaluator import _macro_f1

    # Perfect prediction -> 1.0
    assert _macro_f1(["a", "b", "a"], ["a", "b", "a"]) == pytest.approx(1.0)

    # Majority-class-only prediction: 75% accuracy but macro-F1 well below it.
    y_true = ["a", "a", "a", "b"]
    y_pred = ["a", "a", "a", "a"]
    f1 = _macro_f1(y_true, y_pred)
    assert f1 == pytest.approx(0.4286, abs=1e-3)
    assert f1 < 0.75 * 0.99  # would have passed the old placeholder formula
