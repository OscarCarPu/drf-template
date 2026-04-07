.DEFAULT_GOAL := help

# Detect runner UID/GID for chown (avoids root-owned files on Linux)
runner := $(shell whoami)

DC := docker compose
EXEC := $(DC) exec backend
MANAGE := $(EXEC) python manage.py

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

.PHONY: init
init: ## Initialize project (copy .env, build, start, migrate, hooks)
	@test -f .env || cp .env.example .env
	$(DC) build
	$(DC) up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	$(MANAGE) migrate --noinput
	@$(MAKE) install-hooks
	@echo "Project ready! Visit http://localhost:8000/api/schema/swagger/"

.PHONY: install-hooks
install-hooks: ## Install git pre-commit hook
	@printf '#!/bin/sh\nmake lint && make testing\n' > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed."

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

.PHONY: build
build: ## Build all containers
	$(DC) build

.PHONY: up
up: ## Start all services
	$(DC) up

.PHONY: up-d
up-d: ## Start all services (detached)
	$(DC) up -d

.PHONY: down
down: ## Stop and remove containers
	$(DC) down

.PHONY: logs
logs: ## Tail logs for all services
	$(DC) logs -f

# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

.PHONY: shell
shell: ## Django shell_plus
	$(MANAGE) shell_plus

.PHONY: bash
bash: ## Bash shell inside backend
	$(EXEC) bash

.PHONY: dbshell
dbshell: ## PostgreSQL shell
	$(MANAGE) dbshell

# ---------------------------------------------------------------------------
# Django
# ---------------------------------------------------------------------------

.PHONY: migrate
migrate: ## Run database migrations
	$(MANAGE) migrate

.PHONY: makemigrations
makemigrations: ## Create new migrations
	$(DC) run --rm backend python manage.py makemigrations
	sudo chown -R $(runner):$(runner) -Rf .

.PHONY: createsuperuser
createsuperuser: ## Create admin user
	$(MANAGE) createsuperuser

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

.PHONY: testing
testing: ## Run all tests: unit+integration parallel, then e2e sequential
	$(DC) run --rm backend sh -c 'pytest -m "not e2e" -n auto && pytest -m e2e'

.PHONY: testing-unit
testing-unit: ## Run only unit tests (no DB, no Redis)
	$(DC) run --rm backend pytest -m unit -n auto

.PHONY: testing-integration
testing-integration: ## Run only integration tests (with DB + Redis)
	$(DC) run --rm backend pytest -m integration -n auto

.PHONY: testing-e2e
testing-e2e: ## Run only E2E tests (sequential — shared fixtures)
	$(DC) run --rm backend pytest -m e2e

.PHONY: testing-cov
testing-cov: ## Run tests with coverage report
	$(DC) run --rm backend pytest --cov --cov-report=html --cov-report=term
	@cp -r src/htmlcov htmlcov 2>/dev/null; true

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ruff check + format check
	$(DC) run --rm backend ruff check .
	$(DC) run --rm backend ruff format --check .

.PHONY: lint-fix
lint-fix: ## Run ruff check --fix + format
	$(DC) run --rm backend ruff check --fix .
	$(DC) run --rm backend ruff format .

# ---------------------------------------------------------------------------
# OpenAPI
# ---------------------------------------------------------------------------

.PHONY: schema
schema: ## Generate OpenAPI schema to schema.yml
	$(MANAGE) spectacular --color --file schema.yml
