.PHONY: dev-api dev-web stack-up stack-down test-python test-web lint-python verify-release1

dev-api:
	uv run uvicorn omnibridge_api.main:app --host 127.0.0.1 --port 8001

dev-web:
	pnpm -C apps/web exec vite --host 0.0.0.0 --port 5174

stack-up:
	docker compose up -d neo4j postgres minio minio-init

stack-down:
	docker compose down

test-python:
	uv run pytest

test-web:
	pnpm -C apps/web test

lint-python:
	uv run ruff check .

verify-release1:
	./scripts/verify-release1-demo.sh
