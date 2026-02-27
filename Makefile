.PHONY: help install-dev up down down-v logs logs-all test test-cov test-fast \
        lint fmt typecheck shell run-local clean mfe-install mfe-build mfe-clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install app + dev dependencies
	pip install -e ".[dev]"

up: ## Build and start all containers (core + MFEs)
	docker compose up --build -d

down: ## Stop containers
	docker compose down

down-v: ## Stop containers + remove volumes
	docker compose down -v

logs: ## Tail core-api logs
	docker compose logs -f core-api

logs-all: ## Tail all container logs
	docker compose logs -f

test: ## Run all tests (no Docker needed)
	pytest tests/ -v

test-cov: ## Tests with coverage report
	pytest tests/ -v --cov=. --cov-report=term-missing

test-fast: ## Stop on first failure
	pytest tests/ -x -v

lint: ## Ruff lint
	ruff check .

fmt: ## Ruff auto-format
	ruff format .

typecheck: ## Mypy type check
	mypy . --ignore-missing-imports

shell: ## Shell into core-api container
	docker compose exec core-api sh

run-local: ## FastAPI with hot reload (needs .env)
	uvicorn core.app:create_app --factory --reload --host 0.0.0.0 --port 8000

mfe-install: ## Install npm deps for all MFEs
	$(MAKE) -C ui/mfe install

mfe-build: ## Build all MFEs locally
	$(MAKE) -C ui/mfe build

mfe-clean: ## Clean MFE dist + node_modules
	$(MAKE) -C ui/mfe clean

clean: ## Remove caches + build artefacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__ \
	       */__pycache__ */*/__pycache__ */*/*/__pycache__ \
	       htmlcov .coverage dist build *.egg-info
