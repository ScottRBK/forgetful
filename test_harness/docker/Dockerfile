# The UAT walkthrough container: opencode + agent-shell + the locked forgetful deps.
# The working-tree wheel installs --no-deps at container start (see container.py), so
# a code change never needs an image rebuild - only a dependency change does, and
# ensure_image() detects that from the requirements.lock hash label automatically.
FROM node:24

# node:24 inherits docker-entrypoint.sh which prepends `node` to any command it can't
# resolve, mangling python/opencode invocations. Clear it so commands run directly.
ENTRYPOINT []

ARG OPENCODE_VERSION=2.2.6

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        procps \
        ca-certificates \
        curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# uv manages Python 3.12 since Debian bookworm only ships 3.11 (forgetful needs 3.12+).
# Download-then-run (not curl|sh) so a failed download fails the build.
RUN curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh && \
    env UV_INSTALL_DIR=/usr/local/bin sh /tmp/uv-install.sh && \
    rm /tmp/uv-install.sh

# Install under /opt so the non-root `node` user can read it; chown the venv so the
# working-tree wheel can install into it at container start.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
COPY requirements.lock /tmp/requirements.lock
RUN uv python install 3.12 && \
    uv venv /opt/venv --python 3.12 && \
    uv pip install --python /opt/venv/bin/python -r /tmp/requirements.lock && \
    uv pip install --python /opt/venv/bin/python "agent-shell-py>=0.1.16" && \
    chown -R node:node /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# npm global prefix relocated so the non-root `node` user can install globals
RUN mkdir -p /usr/local/share/npm-global && \
    chown -R node:node /usr/local/share

RUN mkdir -p /skills /home/node/.local/share/opencode /home/node/.config/opencode && \
    chown -R node:node /skills /home/node/.local /home/node/.config

WORKDIR /skills

USER node

ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# OpenCode 2 is published under @opencode/cli, not the legacy opencode-ai package.
RUN npm install -g @opencode/cli@${OPENCODE_VERSION}
