.PHONY: install install-dev up down restart logs test test-cov lint fmt typecheck shell clean

# ── Python env ────────────────────────────────────────────────────────────────
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# ── Docker Compose ────────────────────────────────────────────────────────────
up:
	docker compose up --build -d

up-fg:
	docker compose up --build

down:
	docker compose down

down-v:
	docker compose down -v   # also removes volumes

restart:
	docker compose restart core-api

logs:
	docker compose logs -f core-api

logs-all:
	docker compose logs -f

ps:
	docker compose ps

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=core --cov=transformer --cov=plugins --cov-report=term-missing

test-fast:
	pytest tests/ -v -x   # stop on first failure

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	ruff check core/ transformer/ plugins/ tests/

fmt:
	ruff format core/ transformer/ plugins/ tests/

fmt-check:
	ruff format --check core/ transformer/ plugins/ tests/

typecheck:
	mypy core/ transformer/ plugins/

# ── Local dev ─────────────────────────────────────────────────────────────────
shell:
	docker compose exec core-api /bin/bash

run-local:
	uvicorn core.app:app --reload --host 0.0.0.0 --port 8000

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
