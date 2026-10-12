"""Entry point for local deployment: ``uvicorn src.main:app --reload``.

Serves the REST API under ``/api`` (interactive docs at ``/api/docs``) and the built React console at ``/``.
Creating the app only reads settings; models, indexes and the LLM client load lazily on first use.
"""
from src.api.app import app_factory

app = app_factory()
