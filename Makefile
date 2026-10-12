.PHONY: install test lint fmt check

install:
	uv sync

test:
	uv run pytest --cov=triagekit

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

check: lint
	uv run ruff format --check .
	uv run pytest