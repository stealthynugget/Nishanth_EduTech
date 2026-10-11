"""Retriever interface for student similarity search."""
from ssa.retrieval.hybrid import HistoricalCaseIndex, rrf_fuse

__all__ = ["HistoricalCaseIndex", "rrf_fuse"]
