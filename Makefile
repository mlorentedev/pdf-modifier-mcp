# =============================================================================
# Makefile – PDF Modifier MCP
# =============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -c -o pipefail

POETRY := poetry
APP_NAME := pdf-modifier-mcp

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2} /^## [a-zA-Z]/ {printf "\n\033[1;33m%s\033[0m\n", substr($$0, 4)}' $(MAKEFILE_LIST)

## Dev
setup: ## Install dependencies and pre-commit hooks
	@command -v python3 >/dev/null || (echo "Python 3 required"; exit 1)
	@command -v poetry >/dev/null || pip install poetry
	@$(POETRY) install
	@$(POETRY) run pre-commit install
	@echo "✓ Setup complete. Run 'make run-mcp' or 'make run-cli' to start."

install: ## Install dependencies (CI)
	@$(POETRY) install --no-interaction

run-mcp: ## Start MCP server locally
	@$(POETRY) run pdf-modifier-mcp

run-cli: ## Run CLI (usage: make run-cli ARGS="--help")
	-@$(POETRY) run pdf-mod $(ARGS)

## Quality
check: lint type test ## Run all quality checks

test: ## Run tests with coverage
	@$(POETRY) run pytest --cov=src --cov-report=term-missing

lint: ## Run ruff linter
	@$(POETRY) run ruff check src/ tests/

format: ## Format code with ruff
	@$(POETRY) run ruff format src/ tests/
	@$(POETRY) run ruff check --fix src/ tests/

type: ## Run mypy type checker
	@$(POETRY) run mypy src/

## Dist
build: ## Build distribution artifacts
	@$(POETRY) build

publish: build ## Publish to PyPI (requires PYPI_TOKEN)
	@$(POETRY) publish --username __token__ --password $(PYPI_TOKEN)

clean: ## Clean build artifacts
	@rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/ .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✓ Clean complete."
