# Docker image for throughline's rag_server + daemon.
#
# Single image, two services. Compose picks the right command
# via `command:` so we only maintain one Dockerfile.
#
# Build args:
#   BASE           python base tag (default python:3.12-slim-bookworm)
#   INSTALL_LOCAL  `1` installs torch + transformers for the local
#                  bge-m3 embedder. Default `0` keeps the image
#                  small (~400 MB) and requires EMBEDDER=openai or
#                  another cloud backend. Set to 1 if you want the
#                  local-only privacy mode.
#
# Example:
#   docker build --build-arg INSTALL_LOCAL=1 -t throughline .
#
# The compose file passes INSTALL_LOCAL=0 by default so first-time
# `docker compose up` finishes in under 2 minutes on a fresh host.

ARG BASE=python:3.12-slim-bookworm
FROM ${BASE}

ARG INSTALL_LOCAL=0

# System packages needed for the daemon's watchdog + general deploy:
#   - build-essential + git: some Python deps build from source
#   - ca-certificates: HTTPS to LLM providers + Qdrant
#   - curl: healthcheck in compose
#   - procps: `ps` inside the container when debugging
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps in a layer the build cache can reuse.
# Everything except torch+transformers is in requirements.txt; those
# two are gated by INSTALL_LOCAL so the default image stays small.
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && if [ "${INSTALL_LOCAL}" = "0" ]; then \
         # Minimal install: skip the torch + transformers lines.
         grep -vE '^(torch|transformers)\b' /tmp/requirements.txt > /tmp/req-min.txt \
         && pip install --no-cache-dir -r /tmp/req-min.txt \
         && pip install --no-cache-dir openai; \
       else \
         pip install --no-cache-dir -r /tmp/requirements.txt \
         && pip install --no-cache-dir openai; \
       fi

# App code. Kept as a separate layer so code changes don't bust the
# pip-install cache.
COPY . /app/

# Default runtime env — overridden by compose. Pointing these at
# container paths by default; volumes mount into them.
ENV THROUGHLINE_VAULT_ROOT=/data/vault \
    THROUGHLINE_RAW_ROOT=/data/raw \
    THROUGHLINE_STATE_DIR=/data/state \
    THROUGHLINE_LOG_DIR=/data/logs \
    QDRANT_URL=http://qdrant:6333 \
    RAG_EMBED_URL=http://rag_server:8000/v1 \
    RAG_COLLECTION=obsidian_notes \
    VAULT_PATH=/data/vault \
    # Skip torch's automatic CUDA probes inside a minimal container.
    PYTORCH_CUDA_ALLOC_CONF=

# Create the mount points so bind-volumes work even on first boot.
RUN mkdir -p /data/vault /data/raw /data/state /data/logs

# No default CMD — compose picks the command per service. Running
# `docker run throughline` without args drops the user in a shell.
CMD ["/bin/bash"]
