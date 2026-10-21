# syntax=docker/dockerfile:1
# Build context is the repository root (see compose.yaml); ignore rules are in Dockerfile.dockerignore.

# ---- 1. Build the dashboard (Node is only needed here) ----------------------------------------------------------
FROM node:22-alpine AS dashboard
WORKDIR /app/scraper/dashboard
COPY scraper/dashboard/package.json scraper/dashboard/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY scraper/dashboard/ ./
RUN npm run build

# ---- 2. Runtime: Python 3.13 + the collectors, parsers and server ------------------------------------------------
FROM python:3.13-alpine AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Dependencies first so code changes don't reinstall them.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project && rm /usr/local/bin/uv

# Same layout as the repository: code in scraper/, README.md and data/ at the root (collect.config.ROOT).
COPY README.md ./
COPY scraper/collect/ scraper/collect/
COPY scraper/parse/ scraper/parse/
COPY scraper/pipeline.py scraper/serve.py scraper/run_all.py scraper/validate.py scraper/
COPY --from=dashboard /app/scraper/dashboard/dist scraper/dashboard/dist

RUN adduser -D -u 1000 app && mkdir -p data && chown app:app data
USER app

# Raw data, tables, manifest and run state live on the mounted volume.
ENV DASHBOARD_HOST=0.0.0.0 MANIFEST_PATH=/app/data/manifest.csv
VOLUME ["/app/data"]
EXPOSE 8765
WORKDIR /app/scraper
ENTRYPOINT ["python", "run_all.py"]
