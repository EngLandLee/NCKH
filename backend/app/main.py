from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.api.routes_invoice import router as invoice_router
from backend.app.api.routes_demand import router as demand_router
from backend.app.api.routes_logistics import router as logistics_router
from backend.app.api.routes_rag import router as rag_router
from backend.app.api.routes_benchmark import router as benchmark_router

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise Supply Chain & Accounting Multi-Agent Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invoice_router)
app.include_router(demand_router)
app.include_router(logistics_router)
app.include_router(rag_router)
app.include_router(benchmark_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "latency_target_ms": settings.FAST_PATH_LATENCY_THRESHOLD_MS
    }
