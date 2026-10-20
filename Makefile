.PHONY: check

check:
	uv run ruff format .
	uv run ruff check . --fix
	uv run bandit -c pyproject.toml -r src --severity-level medium
	uv run mypy .
	uv run pytest -s -x
	uv run pytest --cov=src --cov-report=term-missing
