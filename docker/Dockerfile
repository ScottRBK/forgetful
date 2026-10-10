FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Cache third-party dependencies independently of application code and version.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy every input needed by hatch, including migrations and the application.
COPY README.md main.py alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Install the complete project and generate its version without requiring .git.
ARG VERSION=0.0.0+dev
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION
RUN uv sync --frozen --no-dev

COPY tests ./tests
COPY pytest.ini ./

# Expose port
EXPOSE 8020

# Use the installed environment; startup must not resolve or rebuild packages.
CMD ["uv", "run", "--no-sync", "main.py", "--transport", "http"]
