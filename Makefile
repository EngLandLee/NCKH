# SupplyChain-AgenticHub
#
#   make dev     start everything (installs whatever is missing first)
#   make help    list every target
#
# `make dev` is the only command needed on a clean clone.

SHELL := /bin/bash
.DEFAULT_GOAL := help

VENV       := backend/venv
PY         := $(VENV)/bin/python3
PYTEST     := $(VENV)/bin/pytest
PYTHON_VER := 3.12
export PYTHONPATH := .

BACKEND_PORT  ?= 8008
FRONTEND_PORT ?= 3000

# Marker files so install work is skipped once done. ortools is the heaviest
# dependency and the one with no Python 3.14 wheels, so probe on it.
VENV_STAMP := $(VENV)/.deps-installed
NODE_STAMP := frontend/node_modules/.package-lock.json

.PHONY: help dev run check test bench install install-backend install-frontend \
        build lint clean clean-all doctor

## help: show this list
help:
	@echo "SupplyChain-AgenticHub"
	@echo
	@grep -E '^## ' $(MAKEFILE_LIST) \
		| sed -e 's/## //' \
		| awk -F': ' '{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "  Ports: BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT)"
	@echo "  Override: make dev FRONTEND_PORT=3100"

# --- the one command ------------------------------------------------------

## dev: install if needed, then start backend + frontend
dev: install
	@LAUNCH_HINT="make dev" BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) ./run_demo.sh

## run: start without the install check (faster when deps are current)
run:
	@LAUNCH_HINT="make run" BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) ./run_demo.sh

## check: preflight only — verify deps and ports, start nothing
check: install
	@LAUNCH_HINT="make check" BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) ./run_demo.sh --check

# --- install --------------------------------------------------------------

## install: set up backend venv and frontend packages
install: install-backend install-frontend

install-backend: $(VENV_STAMP)

$(VENV_STAMP): backend/requirements.txt
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "uv not found. Install it with:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "Or create the venv manually (needs Python $(PYTHON_VER)):"; \
		echo "  python$(PYTHON_VER) -m venv $(VENV) && $(VENV)/bin/pip install -r backend/requirements.txt"; \
		exit 1; \
	fi
	@# ortools has no Python 3.14 wheels yet, so the version is pinned.
	@test -x "$(PY)" || uv venv $(VENV) --python $(PYTHON_VER)
	@echo "Installing backend dependencies..."
	@VIRTUAL_ENV=$(VENV) uv pip install -q -r backend/requirements.txt
	@touch $@

install-frontend: $(NODE_STAMP)

$(NODE_STAMP): frontend/package.json
	@command -v pnpm >/dev/null 2>&1 || { echo "pnpm not found: npm i -g pnpm"; exit 1; }
	@echo "Installing frontend dependencies..."
	@cd frontend && pnpm install --silent
	@touch $@

# --- verify ---------------------------------------------------------------

## test: run the backend test suite
test: install-backend
	@$(PYTEST) backend/tests/ -q

## bench: reproduce the benchmark and retrieval numbers
bench: install-backend
	@$(PY) -m backend.app.benchmark.report

## build: type-check and build the production frontend bundle
build: install-frontend
	@cd frontend && pnpm build

## lint: byte-compile the backend and type-check the frontend
lint: install
	@$(PY) -m compileall -q backend/app && echo "backend: ok"
	@cd frontend && npx tsc --noEmit && echo "frontend: ok"

## doctor: report environment and configuration status
doctor:
	@echo "make        : $$(make --version | head -1)"
	@echo "uv          : $$(command -v uv >/dev/null 2>&1 && uv --version || echo 'MISSING')"
	@echo "pnpm        : $$(command -v pnpm >/dev/null 2>&1 && pnpm --version || echo 'MISSING')"
	@echo "venv        : $$(test -x '$(PY)' && $(PY) --version || echo 'not created — run make install')"
	@echo "node_modules: $$(test -d frontend/node_modules && echo present || echo 'missing — run make install')"
	@if [ -f .env ] && grep -q '^OPENAI_API_KEY=sk-' .env 2>/dev/null; then \
		echo "OPENAI_API_KEY: set in .env — LLM escalation and semantic RAG ACTIVE"; \
	elif [ -n "$$OPENAI_API_KEY" ]; then \
		echo "OPENAI_API_KEY: set in environment — LLM escalation and semantic RAG ACTIVE"; \
	else \
		echo "OPENAI_API_KEY: not set — falls back to fast-path / BM25 (still runs)"; \
	fi
	@for p in $(BACKEND_PORT) $(FRONTEND_PORT); do \
		if ss -tln 2>/dev/null | grep -qE "[:.]$$p[[:space:]]"; then \
			echo "port $$p    : IN USE — override e.g. make dev FRONTEND_PORT=3100"; \
		else \
			echo "port $$p    : free"; \
		fi; \
	done

# --- cleanup --------------------------------------------------------------

## clean: remove build output and caches (keeps installed deps)
clean:
	@rm -rf frontend/dist .pytest_cache
	@find backend -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "cleaned build output and caches"

## clean-all: also remove the venv and node_modules
clean-all: clean
	@rm -rf $(VENV) frontend/node_modules
	@echo "removed venv and node_modules — run make dev to rebuild"
