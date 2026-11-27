# Web UI bundle. Node appears only in this stage: the runtime image receives
# static files and no Node toolchain.
FROM node:24-bookworm-slim AS ui

ARG FORGETFUL_UI_REPO=https://github.com/ScottRBK/forgetful-ui.git
# A commit, never a branch. This is the revision pinned in flake.lock, so the
# image, the wheel and the Nix package all build one commit of the UI. A moving
# ref would make it impossible to rebuild an old tag and get the UI it shipped
# with, which is what "one artifact" rules out.
ARG FORGETFUL_UI_REV

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ui
RUN test -n "$FORGETFUL_UI_REV" || { \
        echo "FORGETFUL_UI_REV is required: pass the commit pinned in flake.lock" >&2; \
        exit 1; \
    } \
    && git init -q . \
    && git remote add origin "$FORGETFUL_UI_REPO" \
    && git fetch --depth 1 origin "$FORGETFUL_UI_REV" \
    && git checkout --detach FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = "$FORGETFUL_UI_REV"

RUN npm ci --ignore-scripts && npm run build

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
# Build hook and its helper: hatch loads them by path at wheel build time.
COPY hatch_build.py ui_bundle.py ./
COPY alembic ./alembic
COPY app ./app

# The bundle is package data. Requiring it below makes a missing bundle fail the
# image build rather than producing an image whose UI_ENABLED serves nothing.
COPY --from=ui /ui/dist ./app/web/ui

# Install the complete project and generate its version without requiring .git.
ARG VERSION=0.0.0+dev
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION
# Required for this build only; nothing at runtime reads it.
RUN FORGETFUL_REQUIRE_UI_BUNDLE=1 uv sync --frozen --no-dev

COPY tests ./tests
COPY pytest.ini ./

# Expose port
EXPOSE 8020

# Use the installed environment; startup must not resolve or rebuild packages.
CMD ["uv", "run", "--no-sync", "main.py", "--transport", "http"]
