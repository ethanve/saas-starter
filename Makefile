.PHONY: setup dev dev-api dev-web test test-api lint migrate db-up db-down

setup: db-up
	cd api && uv sync --all-extras
	cd web && bun install
	cd api && uv run alembic upgrade head

dev:
	$(MAKE) dev-api & $(MAKE) dev-web & wait

dev-api:
	cd api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd web && bun run dev

test: test-api

test-api:
	cd api && uv run pytest

lint:
	cd api && uv run ruff check src tests && uv run ruff format --check src tests

migrate:
	cd api && uv run alembic upgrade head

migration:
	cd api && uv run alembic revision --autogenerate -m "$(name)"

db-up:
	docker compose up -d

db-down:
	docker compose down
