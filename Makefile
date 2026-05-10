.PHONY: stack-up stack-down test-python test-web lint-python

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
