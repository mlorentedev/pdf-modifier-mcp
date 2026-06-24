# =============================================================================
# Makefile – PDF Modifier MCP
# =============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -c -o pipefail

UV := uv
APP_NAME := pdf-modifier-mcp
COMPOSE := docker compose
COMPOSE_FILES := -f infra/compose.base.yml -f infra/compose.dev.yml

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2} /^## [a-zA-Z]/ {printf "\n\033[1;33m%s\033[0m\n", substr($$0, 4)}' $(MAKEFILE_LIST)

## Dev
setup: ## Install dependencies and pre-commit hooks
	@command -v $(UV) >/dev/null || (echo "uv required: https://docs.astral.sh/uv/install/"; exit 1)
	@$(UV) sync --all-extras
	@$(UV) run pre-commit install
	@echo "✓ Setup complete. Run 'make run-mcp' or 'make run-cli' to start."

install: ## Install dependencies (CI)
	@$(UV) sync --all-extras

run-mcp: ## Start MCP server locally
	@$(UV) run pdf-modifier-mcp

run-cli: ## Run CLI (usage: make run-cli ARGS="--help")
	-@$(UV) run pdf-mod $(ARGS)

## Quality
check: lint type test ## Run all quality checks

test: ## Run tests with coverage
	@$(UV) run pytest --cov=src --cov-report=term-missing --cov-report=xml

lint: ## Run ruff linter
	@$(UV) run ruff check src/ tests/

format: ## Format code with ruff
	@$(UV) run ruff format src/ tests/
	@$(UV) run ruff check --fix src/ tests/

type: ## Run mypy type checker
	@$(UV) run mypy src/

## Dist
build: ## Build distribution artifacts
	@$(UV) build

## Docker — Build, tag, and push images

.PHONY: docker-build docker-push docker-clean docker-prune docker-compose-up docker-compose-down docker-compose-logs docker-compose-ps docker-compose-up-prod docker-compose-stop

docker-build: ## Build backend Docker image
	@docker build -t $(APP_NAME)-api:latest -f Dockerfile .
	@echo "✓ Backend image: $(APP_NAME)-api:latest"

docker-build-frontend: ## Build frontend Docker image
	@docker build -t $(APP_NAME)-web:latest -f Dockerfile.frontend .
	@echo "✓ Frontend image: $(APP_NAME)-web:latest"

docker-build-all: docker-build docker-build-frontend ## Build all images

docker-push: docker-build-all ## Push all images to registry
	@docker push $(APP_NAME)-api:latest
	@docker push $(APP_NAME)-web:latest
	@echo "✓ Images pushed."

docker-clean: ## Remove all build artifacts (images, containers, volumes)
	@docker rmi $(APP_NAME)-api:latest $(APP_NAME)-web:latest 2>/dev/null || true
	@docker rm -f test-pdf-mod 2>/dev/null || true
	@echo "✓ Docker clean complete."

docker-prune: ## Aggressive prune (dangling images, stopped containers, build cache)
	@docker system prune -af --volumes 2>/dev/null || docker system prune -af
	@echo "✓ Docker prune complete."

## Docker Compose

## Stack management — the full dev stack (api + web + nginx)

.PHONY: up down logs ps status

up: ## Build all images and start the full dev stack
	$(COMPOSE) $(COMPOSE_FILES) up -d --build
	@echo ""
	@echo "  Stack:"
	@echo "  ┌─────────────────────────────────────────────┐"
	@echo "  │  API      → http://localhost:8000           │"
	@echo "  │  Frontend → http://localhost:80             │"
	@echo "  │  Health   → http://localhost:8000/health    │"
	@echo "  └─────────────────────────────────────────────┘"

down: ## Stop and remove all compose services + volumes
	$(COMPOSE) $(COMPOSE_FILES) down --remove-orphans
	@echo "✓ Stack down (volumes preserved for speed)."

logs: ## Follow logs from all services
	$(COMPOSE) $(COMPOSE_FILES) logs -f --tail=100

ps: ## List compose services status
	$(COMPOSE) $(COMPOSE_FILES) ps

status: up ## Build, start, and verify all services
	@sleep 5
	@echo ""
	@echo "  Checking services..."
	@curl -sf http://localhost:8000/health && echo "  ✓ API OK" || echo "  ✗ API down"

## Docker Compose — advanced

.PHONY: docker-compose-up-prod docker-compose-stop docker-compose-logs docker-compose-ps

docker-compose-up-prod: ## Start all services (prod mode, no hot-reload)
	$(COMPOSE) -f infra/compose.base.yml -f infra/compose.prod.yml up -d

docker-compose-stop: docker-compose-down ## Alias for docker-compose-down

docker-compose-logs: ## Follow logs from all services
	$(COMPOSE) $(COMPOSE_FILES) logs -f

docker-compose-ps: ## List compose services status
	$(COMPOSE) $(COMPOSE_FILES) ps

## Housekeeping

.PHONY: housekeep housekeep-uv housekeep-docker housekeep-py housekeep-all

housekeep: housekeep-all ## Run all housekeeping tasks

housekeep-all: housekeep-py housekeep-docker ## Run Python + Docker housekeeping

.PHONY: housekeep-py
housekeep-py: ## Clean Python artifacts (cache, bytecode, distributions)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf dist/ build/ *.egg-info/ .coverage
	@echo "✓ Python housekeeping complete."

housekeep-docker: ## Clean Docker (stopped containers, dangling images)
	@docker container prune -f 2>/dev/null || true
	@docker image prune -f 2>/dev/null || true
	@echo "✓ Docker housekeeping complete."

housekeep-uv: ## Refresh uv venv and lockfile
	@$(UV) sync --all-extras
	@echo "✓ UV venv synced."

## Health

.PHONY: docker-health

docker-health: ## Check all running containers
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers running."
	@echo ""
	@curl -sf http://localhost:8000/health && echo " ✓ Backend OK" || echo " ✗ Backend down"
	@curl -sf http://localhost:80/nginx-health && echo " ✓ Frontend OK" || echo " ✗ Frontend down"

## CI Pre-check (local mirror of CI)

.PHONY: pre-commit-check

pre-commit-check: ## Run pre-commit hooks on all files
	@$(UV) run pre-commit run --all-files || (echo "Pre-commit checks failed. Run 'make format' and 'make lint' to fix."; exit 1)
