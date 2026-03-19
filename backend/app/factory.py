from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.bindings import build_entity_routers
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    from backend.app.bindings import build_entity_routers


def cors_origins() -> list[str]:
    raw = str(os.getenv("CORS_ORIGINS") or "").strip()
    if not raw:
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if not origins:
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    return origins


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in build_entity_routers():
        app.include_router(router)

    return app
