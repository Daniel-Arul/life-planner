import logging
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse

from .config import DEFAULT_SECRET_KEY, get_settings
from .routers import auth, health

logger = logging.getLogger("life_planner")


def _mount_frontend(app: FastAPI, static_dir: Path) -> None:
    """Serve the built SvelteKit SPA, falling back to index.html for client-side routes."""
    static_dir = static_dir.resolve()
    index = static_dir / "index.html"

    @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404)
        candidate = (static_dir / path).resolve()
        if candidate.is_relative_to(static_dir) and candidate.is_file():
            headers = {}
            if path.startswith("_app/immutable/"):
                headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return FileResponse(candidate, headers=headers)
        return FileResponse(index)


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.secret_key == DEFAULT_SECRET_KEY:
        logger.warning("PLANNER_SECRET_KEY is not set; using an insecure development key")

    app = FastAPI(title="Life Planner", docs_url="/api/docs", openapi_url="/api/openapi.json")

    api = APIRouter(prefix="/api")
    api.include_router(health.router)
    api.include_router(auth.router)
    app.include_router(api)

    if settings.static_dir is not None:
        _mount_frontend(app, settings.static_dir)
    return app


app = create_app()
