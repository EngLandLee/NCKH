#!/usr/bin/env bash
set -e

echo "================================================================="
echo "   SupplyChain-AgenticHub | Multi-Agent Operations Platform     "
echo "        Sub-200ms Latency Hybrid Orchestration System           "
echo "================================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Start Python FastAPI Backend on port 8008
echo "[1/2] Starting Python Backend on http://localhost:8008 ..."
cd "$ROOT_DIR"
PYTHONPATH=. "$ROOT_DIR/backend/venv/bin/python3" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8008 --reload &
BACKEND_PID=$!

# 2. Start Frontend Dev Server on port 3000
echo "[2/2] Starting React/Vite Frontend on http://localhost:3000 ..."
cd "$ROOT_DIR/frontend"
npx vite --port 3000 --host 0.0.0.0 &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo "🚀 SupplyChain-AgenticHub is LIVE!"
echo "   - Dashboard UI: http://localhost:3000"
echo "   - Backend API Docs: http://localhost:8008/docs"
echo "   - Benchmark Engine: http://localhost:8008/api/benchmark/run?samples=1000"
echo ""
echo "Press Ctrl+C to stop all servers."

wait
