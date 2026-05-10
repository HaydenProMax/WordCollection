from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.exports import router as exports_router
from app.routers.lookups import router as lookups_router


def create_app() -> FastAPI:
    app = FastAPI(title="enCollect", version="0.1.0")
    app.include_router(lookups_router)
    app.include_router(exports_router)

    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()
