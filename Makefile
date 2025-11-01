.PHONY: help install dev test run docker-build docker-run clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Install dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run the server"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run with Docker Compose"
	@echo "  make clean        - Clean cache and temporary files"

install:
	pip install -r requirements.txt
	playwright install chromium
	playwright install-deps chromium

dev: install
	pip install pytest pytest-asyncio pytest-playwright black ruff

test:
	pytest tests/ -v

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -f docker/Dockerfile -t mini-atlas .

docker-run:
	docker-compose -f docker/docker-compose.yml up -d

docker-stop:
	docker-compose -f docker/docker-compose.yml down

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

format:
	black app/ tests/
	ruff --fix app/ tests/

lint:
	ruff app/ tests/
	black --check app/ tests/
