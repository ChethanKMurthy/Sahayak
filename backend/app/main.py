"""Sahayak backend entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import settings
from .db import init_db

app = FastAPI(
    title="Sahayak API",
    version="0.1.0",
    description="The phone becomes a government counter. Capture → fill → consent → submittable PDF.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    return {"app": "Sahayak", "docs": "/docs", "health": "/api/health"}


# ── Request-ID + timing middleware (improvement) ────────────────────────────
from .core.request_log import RequestLogMiddleware  # noqa: E402

app.add_middleware(RequestLogMiddleware)
