"""Student Success Assistant source package.

Exposes the core application components:
- src.api: FastAPI routes, schemas, handlers, and security
- src.agents: Multi-agent workflow, copilot, and generative features
- src.rag: Hybrid case retrieval (BM25 + behavioural kNN + dense embeddings)
- src.services: High-level StudentSuccessService
- src.utils: Shared utility functions and logging
"""
from __future__ import annotations

__version__ = "6.0.0"
