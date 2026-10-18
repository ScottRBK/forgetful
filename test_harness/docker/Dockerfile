# The UAT walkthrough container: opencode + agent-shell + the locked forgetful deps.
# The working-tree wheel installs --no-deps at container start (see container.py), so
# a code change never needs an image rebuild - only a dependency change does, and
# ensure_image() detects that from the requirements.lock hash label automatically.
FROM node:24

# node:24 inherits docker-entrypoint.sh which prepends `node` to any command it can't
# resolve, mangling python/opencode invocations. Clear it so commands run directly.
ENTRYPOINT []

ARG OPENCODE_VERSION=latest

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

# Install under /opt so the non-root `node` user can read it. The harness runs this
# container as the invoking host user (see container.py) so the bind mounts keep their
# private host modes; that uid is arbitrary, so the venv the working-tree wheel installs
# into at container start is made writable for any uid (inside a throwaway sandbox this
# widens nothing). The chmod is in the same RUN that creates the files: a separate
# trailing `chmod -R` layer would copy every file up and add ~0.9 GB to the image.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
COPY requirements.lock /tmp/requirements.lock
RUN uv python install 3.12 && \
    uv venv /opt/venv --python 3.12 && \
    uv pip install --python /opt/venv/bin/python -r /tmp/requirements.lock && \
    uv pip install --python /opt/venv/bin/python "agent-shell-py>=0.1.16" && \
    chown -R node:node /opt/venv && \
    chmod -R a+rwX /opt/venv
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

# HOME (uv cache, agent state) must be writable for an arbitrary uid too. All of
# /home/node is opened, not just its .local and dot-config subtrees: npm and node create
# /home/node/.cache only while this RUN executes, so the chmod has to run in the same
# RUN, and a narrower one would leave ~/.cache unwritable and break `uv pip install`.
RUN npm install -g opencode-ai@${OPENCODE_VERSION} && \
    chmod -R a+rwX /home/node
