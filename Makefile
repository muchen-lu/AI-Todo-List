.PHONY: check

check:
	uv run ruff format .
	uv run ruff check . --fix
	uv run mypy .
	uv run pytest
	uv run pytest --cov=src --cov-report=term-missing
