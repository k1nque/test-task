.PHONY: help install dev up down clean logs shell db-shell test migrate seed

# Detect Docker Compose command
DOCKER_COMPOSE := $(shell docker compose version > /dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv pip install -r pyproject.toml

dev:  ## Run application in development mode (without Docker)
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

up:  ## Start all services with Docker Compose
	$(DOCKER_COMPOSE) up -d --build

down:  ## Stop all services
	$(DOCKER_COMPOSE) down

clean:  ## Stop services and remove volumes
	$(DOCKER_COMPOSE) down -v

logs:  ## Show logs from all services
	$(DOCKER_COMPOSE) logs -f

shell:  ## Open shell in API container
	$(DOCKER_COMPOSE) exec api /bin/bash

db-shell:  ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec db psql -U postgres -d organizations_db

test:  ## Run tests (if implemented)
	pytest

migrate:  ## Run database migrations
	alembic upgrade head

seed:  ## Seed database with test data
	python scripts/seed_data.py

format:  ## Format code (if black installed)
	black app/ main.py

lint:  ## Lint code (if ruff installed)
	ruff check app/ main.py
