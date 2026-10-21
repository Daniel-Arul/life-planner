# syntax=docker/dockerfile:1

# --- Stage 1: build the SvelteKit SPA -------------------------------------
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python runtime serving API + static files --------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLANNER_DATA_DIR=/data \
    PLANNER_STATIC_DIR=/app/static

WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install .
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY --from=frontend /build/build /app/static

# Matches the default Pi user (uid 1000) so ./data on the host stays writable.
RUN useradd --create-home --uid 1000 planner && mkdir -p /data && chown planner /data
USER planner

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

# Port is only published on the Pi's loopback, so trusting forwarded headers
# from any source just means trusting `tailscale serve` on the same host.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
