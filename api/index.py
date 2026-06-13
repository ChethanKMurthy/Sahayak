"""Vercel Python serverless entrypoint for the Sahayak FastAPI backend.

Vercel builds any file under /api with the Python runtime and serves the module
attribute named `app` as an ASGI application. We add the repo's /backend to the
import path, expose the existing FastAPI `app`, and create tables on cold start
(Vercel does not reliably fire ASGI startup events)."""
from __future__ import annotations

import sys
from pathlib import Path

# /api/index.py -> repo root -> /backend on the import path so `app.*` resolves.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402  (this is the ASGI app Vercel serves)

try:
    init_db()
except Exception as e:  # never block cold start on a transient DB hiccup
    print(f"[vercel] init_db skipped: {e}")
