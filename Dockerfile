# syntax=docker/dockerfile:1

# ---- 1. Build the dashboard (Node is only needed here) ----------------------------------------------------------
FROM node:22-alpine AS dashboard
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY dashboard/ ./
# styles import ../ui-handoff/tokens.css
COPY ui-handoff/tokens.css /app/ui-handoff/tokens.css
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

COPY collect/ collect/
COPY parse/ parse/
COPY pipeline.py serve.py run_all.py validate.py README.md ./
COPY --from=dashboard /app/dashboard/dist dashboard/dist

RUN adduser -D -u 1000 app && mkdir -p data && chown app:app data
USER app

# Raw data, tables, manifest and run state live on the mounted volume.
ENV DASHBOARD_HOST=0.0.0.0 MANIFEST_PATH=/app/data/manifest.csv
VOLUME ["/app/data"]
EXPOSE 8765
ENTRYPOINT ["python", "run_all.py"]
