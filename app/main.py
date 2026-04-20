from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database.init_db import ensure_schema_ready, init_db, should_auto_create_schema
from app.routes.assets import router as assets_router
from app.routes.clients import router as clients_router
from app.routes.evaluation import router as evaluation_router
from app.routes.rules import router as rules_router
from app.routes.sources import router as sources_router
from app.routes.tenants import router as tenants_router

BASE_DIR = Path(__file__).resolve().parent.parent


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=BASE_DIR / "frontend"), name="frontend")
app.mount("/styles", StaticFiles(directory=BASE_DIR / "styles"), name="styles")

app.include_router(sources_router)
app.include_router(rules_router)
app.include_router(clients_router)
app.include_router(assets_router)
app.include_router(tenants_router)
app.include_router(evaluation_router)


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
