# =============================================================================
# Makefile – PDF Modifier MCP
# =============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -c -o pipefail

UV := uv
APP_NAME := pdf-modifier-mcp

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

clean: ## Clean build artifacts
	@rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/ .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✓ Clean complete."
