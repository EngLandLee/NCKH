#!/usr/bin/env bash
# Demo Day launcher.
#
# Fails loudly and early rather than half-starting. The previous version
# backgrounded both servers without checking anything: if port 3000 was taken,
# Vite silently moved to 3001 while the banner still advertised 3000 — which on
# stage looks like a broken app.
#
#   ./run_demo.sh              # ports 3000 / 8008
#   FRONTEND_PORT=3100 ./run_demo.sh
#   ./run_demo.sh --check      # preflight only, start nothing

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BACKEND_PORT="${BACKEND_PORT:-8008}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
VENV_PY="$ROOT_DIR/backend/venv/bin/python3"

if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; NC=''
fi
ok()   { printf "  %b✓%b %s\n" "$GREEN" "$NC" "$1"; }
warn() { printf "  %b!%b %s\n" "$YELLOW" "$NC" "$1"; }
die()  { printf "  %b✗ %s%b\n" "$RED" "$1" "$NC" >&2; exit 1; }

port_busy() {
    if command -v ss >/dev/null 2>&1; then
        ss -tln 2>/dev/null | grep -qE "[:.]$1[[:space:]]"
    else
        (echo >"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1
    fi
}

echo "================================================================="
echo "   SupplyChain-AgenticHub | Multi-Agent Operations Platform"
echo "        Dual-Speed Orchestration (Fast-Path + LLM Escalation)"
echo "================================================================="
echo
echo "[Preflight]"

[ -x "$VENV_PY" ] || die "Python venv missing. Run:
      uv venv backend/venv --python 3.12
      VIRTUAL_ENV=backend/venv uv pip install -r backend/requirements.txt"
ok "Python venv: $("$VENV_PY" --version 2>&1)"

"$VENV_PY" -c "import ortools, fastapi, numpy" 2>/dev/null \
    || die "Backend dependencies missing. Run:
      VIRTUAL_ENV=backend/venv uv pip install -r backend/requirements.txt"
ok "Backend dependencies importable (ortools, fastapi, numpy)"

[ -d "$ROOT_DIR/frontend/node_modules" ] \
    || die "Frontend dependencies missing. Run: cd frontend && pnpm install"
ok "Frontend dependencies present"

if [ -f "$ROOT_DIR/.env" ] && grep -q '^OPENAI_API_KEY=sk-' "$ROOT_DIR/.env" 2>/dev/null; then
    ok "OPENAI_API_KEY configured — LLM escalation ACTIVE"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
    ok "OPENAI_API_KEY from environment — LLM escalation ACTIVE"
else
    warn "No OPENAI_API_KEY — escalation degrades to fast-path (demo still works)"
fi

for p in "$BACKEND_PORT:backend:BACKEND_PORT" "$FRONTEND_PORT:frontend:FRONTEND_PORT"; do
    port="${p%%:*}"; rest="${p#*:}"; role="${rest%%:*}"; var="${rest##*:}"
    if port_busy "$port"; then
        die "Port $port ($role) is already in use.
      Free it, or choose another:  $var=<port> ./run_demo.sh
      Find the holder with:        ss -tlnp | grep :$port"
    fi
done
ok "Ports $BACKEND_PORT and $FRONTEND_PORT are free"

if [ "${1:-}" = "--check" ]; then
    echo
    printf "%bPreflight passed. Re-run without --check to start.%b\n" "$GREEN" "$NC"
    exit 0
fi

BACKEND_PID=""; FRONTEND_PID=""
cleanup() {
    echo
    echo "Stopping servers..."
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    wait 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

echo
echo "[1/2] Backend  → http://localhost:$BACKEND_PORT"
PYTHONPATH=. "$VENV_PY" -m uvicorn backend.app.main:app \
    --host 0.0.0.0 --port "$BACKEND_PORT" > /tmp/agentichub_backend.log 2>&1 &
BACKEND_PID=$!

for i in $(seq 1 40); do
    if curl -fsS -m 2 "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
        ok "Backend healthy after ${i}00ms"
        break
    fi
    kill -0 "$BACKEND_PID" 2>/dev/null || {
        printf "%bBackend died. Last lines:%b\n" "$RED" "$NC" >&2
        tail -20 /tmp/agentichub_backend.log >&2
        exit 1
    }
    sleep 0.1
    [ "$i" = 40 ] && die "Backend did not become healthy within 4s (see /tmp/agentichub_backend.log)"
done

echo "[2/2] Frontend → http://localhost:$FRONTEND_PORT"
# --strictPort so Vite fails instead of silently drifting to another port.
(cd "$ROOT_DIR/frontend" && exec npx vite --port "$FRONTEND_PORT" --strictPort --host 0.0.0.0) \
    > /tmp/agentichub_frontend.log 2>&1 &
FRONTEND_PID=$!

for i in $(seq 1 60); do
    if curl -fsS -m 2 -o /dev/null "http://127.0.0.1:$FRONTEND_PORT/" 2>/dev/null; then
        ok "Frontend serving after ${i}00ms"
        break
    fi
    kill -0 "$FRONTEND_PID" 2>/dev/null || {
        printf "%bFrontend died. Last lines:%b\n" "$RED" "$NC" >&2
        tail -20 /tmp/agentichub_frontend.log >&2
        exit 1
    }
    sleep 0.1
    [ "$i" = 60 ] && die "Frontend did not serve within 6s (see /tmp/agentichub_frontend.log)"
done

# Prove the proxy hop works now, not mid-presentation.
if curl -fsS -m 10 -X POST "http://127.0.0.1:$FRONTEND_PORT/api/invoice/process" \
        -H 'Content-Type: application/json' \
        -d '{"raw_text":"Số: 1. Mã số thuế: 0312345678. Hàng hóa: Thép cuộn D10. Cộng tiền hàng: 100,000,000 VND. Tiền thuế GTGT: 10,000,000 VND. Tổng cộng tiền thanh toán: 110,000,000 VND. Chuyển khoản.","filename":"preflight.txt"}' \
        2>/dev/null | grep -q '"debit_account"'; then
    ok "Frontend → backend proxy verified end-to-end"
else
    warn "Proxy check failed — the UI may not reach the API"
fi

printf "\n%b🚀 SupplyChain-AgenticHub is LIVE%b\n" "$GREEN" "$NC"
cat <<BANNER
   Dashboard   : http://localhost:$FRONTEND_PORT
   API docs    : http://localhost:$BACKEND_PORT/docs
   Benchmark   : http://localhost:$BACKEND_PORT/api/benchmark/run?samples=1000
   Logs        : /tmp/agentichub_{backend,frontend}.log

Press Ctrl+C to stop.
BANNER

wait
