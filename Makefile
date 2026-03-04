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
init: ## Initialize project (copy .env, build, start, migrate)
	@test -f .env || cp .env.example .env
	$(DC) build
	$(DC) up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	$(MANAGE) migrate --noinput
	@echo "Project ready! Visit http://localhost:8000/api/schema/swagger/"

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

.PHONY: test
test: ## Run all tests with pytest
	$(EXEC) pytest

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	$(EXEC) pytest --cov --cov-report=html --cov-report=term
	@cp -r src/htmlcov htmlcov 2>/dev/null; true

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ruff check + format check
	$(EXEC) ruff check .
	$(EXEC) ruff format --check .

.PHONY: lint-fix
lint-fix: ## Run ruff check --fix + format
	$(EXEC) ruff check --fix .
	$(EXEC) ruff format .

# ---------------------------------------------------------------------------
# OpenAPI
# ---------------------------------------------------------------------------

.PHONY: schema
schema: ## Generate OpenAPI schema to schema.yml
	$(MANAGE) spectacular --color --file schema.yml
