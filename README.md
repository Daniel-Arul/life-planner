# Life Planner

A self-hosted planner for workouts, expenses, to-dos, ideas, and plans, all in one calendar. It runs on a Raspberry Pi and is reached privately over Tailscale. See [PLAN.md](PLAN.md) for the full design and milestones.

## Local development

You need Python 3.12+ and Node 22+.

```bash
# Backend (terminal 1)
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
mkdir -p data && alembic upgrade head
python -m app.cli create-user <your-name>
PLANNER_COOKIE_SECURE=false uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend
npm install
npm run dev   # http://localhost:5173, /api is proxied to :8000
```

Checks:

```bash
cd backend && pytest
cd frontend && npm run check
```

## Deploy on the Pi

These steps assume Raspberry Pi OS (64-bit) with [rootless Docker](https://docs.docker.com/engine/security/rootless/) and Tailscale installed.

```bash
git clone <this repo> life-planner && cd life-planner
cp .env.example .env            # then set PLANNER_SECRET_KEY
mkdir -p data                   # owned by you; the container's root is your user under rootless Docker
docker compose up -d --build
docker compose exec app python -m app.cli create-user <your-name>
sudo tailscale serve --bg 8000  # https://<pi-name>.<tailnet>.ts.net
```

To update: `git pull && docker compose up -d --build`. Database migrations run automatically on start.
