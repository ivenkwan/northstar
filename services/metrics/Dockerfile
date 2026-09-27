# Metrics service image (also serves the semantic catalog under /app/data).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
COPY services ./services
COPY data ./data
COPY tests ./tests
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "metrics.api:app", "--host", "0.0.0.0", "--port", "8000"]
