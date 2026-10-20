FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

COPY . .

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "src.cloud.backend:app", "--host", "0.0.0.0", "--port", "8080"]
