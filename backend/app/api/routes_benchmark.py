from fastapi import APIRouter, Query
from backend.app.benchmark.generator import generate_benchmark_dataset
from backend.app.benchmark.evaluator import BenchmarkEvaluator, BenchmarkReport

router = APIRouter(prefix="/api/benchmark", tags=["Benchmark"])
evaluator = BenchmarkEvaluator()

@router.get("/run", response_model=BenchmarkReport)
def run_benchmark(samples: int = Query(default=1000, le=100000)):
    dataset = generate_benchmark_dataset(sample_size=samples)
    return evaluator.run_evaluation(dataset["records"])
