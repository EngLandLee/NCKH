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
    assert report.overall_f1_score >= 0.85
    assert "\\begin{table}" in report.latex_table # Verification for faculty research paper
