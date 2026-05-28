.PHONY: help install dev lint format test migrate docker-build docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make lint         - Run linters (flake8, black, isort)"
	@echo "  make format       - Format code (black, isort)"
	@echo "  make test         - Run tests"
	@echo "  make migrate      - Run database migrations"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start services with docker-compose"
	@echo "  make docker-down  - Stop services"
	@echo "  make clean        - Clean cache and build files"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	black --check app tests
	isort --check-only app tests
	flake8 app tests

format:
	black app tests
	isort app tests

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

docker-ps:
	docker-compose ps

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
