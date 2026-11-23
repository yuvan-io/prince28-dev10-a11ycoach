
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder
ARG GIT_SHA=dev
ENV A11YCOACH_GIT_SHA=$GIT_SHA

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency metadata first for caching
COPY pyproject.toml uv.lock ./

# Install production dependencies
RUN uv sync --frozen --no-install-project --no-dev

# Copy application files
COPY src/ ./src/
COPY README.md ./
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Install the project
RUN uv sync --frozen --no-dev


# Stage 2: Production runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd --system app && \
    useradd --system --gid app --create-home app

# Copy application and virtual environment
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src ./src
COPY --from=builder --chown=app:app /app/alembic.ini ./alembic.ini
COPY --from=builder --chown=app:app /app/migrations ./migrations
COPY --from=builder --chown=app:app /app/scripts ./scripts
COPY --from=builder --chown=app:app /app/data ./data

USER app

EXPOSE 8000

CMD ["uvicorn", "a11ycoach.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
