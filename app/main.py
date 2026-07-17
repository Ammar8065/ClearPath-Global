from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import cors_allow_origins
from app.database.init_db import ensure_schema_ready, init_db, should_auto_create_schema
from app.routes.ai import router as ai_router
from app.routes.assets import router as assets_router
from app.routes.auth import router as auth_router
from app.routes.clients import router as clients_router
from app.routes.evaluation import router as evaluation_router
from app.routes.rag import router as rag_router
from app.routes.rules import router as rules_router
from app.routes.sources import router as sources_router
from app.services.auth import require_user

BASE_DIR = Path(__file__).resolve().parent.parent

_NO_CACHE_PREFIXES = ("/frontend/", "/static/")


class NoCacheStaticAssetsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(_NO_CACHE_PREFIXES) or request.url.path == "/":
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    if should_auto_create_schema():
        init_db()
    else:
        ensure_schema_ready()
    yield


app = FastAPI(
    title="Risk Intelligence MVP",
    version="0.1.0",
    description="Backend foundation for a rules-based cross-border risk intelligence system.",
    lifespan=lifespan,
)

# The SPA is served same-origin by this app, so cross-origin access is off by
# default. Grant it explicitly via CORS_ALLOW_ORIGINS when a separately
# hosted frontend needs the API — never with a wildcard on an unauthenticated
# service that can expose client records when PRIVACY_MODE=0.
_cors_origins = cors_allow_origins()
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_middleware(NoCacheStaticAssetsMiddleware)

app.mount("/frontend", StaticFiles(directory=BASE_DIR / "frontend"), name="frontend")

# /auth is the only open API surface; every data router requires a session
# when auth is enabled (no-op otherwise — see app.services.auth.require_user).
# Admin-only mutations add require_admin at the endpoint level.
app.include_router(auth_router)
_authed = [Depends(require_user)]
app.include_router(sources_router, dependencies=_authed)
app.include_router(rules_router, dependencies=_authed)
app.include_router(clients_router, dependencies=_authed)
app.include_router(assets_router, dependencies=_authed)
app.include_router(evaluation_router, dependencies=_authed)
app.include_router(ai_router, dependencies=_authed)
app.include_router(rag_router, dependencies=_authed)


@app.get("/", tags=["System"])
def root() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")


@app.get("/static/script.js", include_in_schema=False)
def frontend_script() -> FileResponse:
    return FileResponse(BASE_DIR / "script.js", media_type="application/javascript")


@app.get("/static/styles.css", include_in_schema=False)
def frontend_styles() -> FileResponse:
    return FileResponse(BASE_DIR / "styles.css", media_type="text/css")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
