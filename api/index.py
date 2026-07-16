"""Vercel Python serverless entry point.

Exposes the FastAPI ASGI app from backend/app so Vercel's Python
runtime can serve it. All backend source lives under backend/app;
this file only wires the import path.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
