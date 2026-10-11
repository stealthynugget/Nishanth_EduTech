"""Main executable entrypoint for the Student Success Assistant microservice.

Run locally using uvicorn:
    uvicorn src.main:app --reload --port 8000
Or directly:
    python -m src.main
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import uvicorn
from ssa.api.app import app_factory, create_app
from ssa.config import get_settings

# Primary FastAPI application instance
app = app_factory()


def main():
    """Run uvicorn server with default project settings."""
    s = get_settings()
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
