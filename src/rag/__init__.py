"""RAG retrieval module: hybrid search combining BM25 keyword matching and behavioural kNN."""
from ssa.retrieval.hybrid import HistoricalCaseIndex
from ssa.retrieval.descriptors import descriptor_tokens, parse_query

__all__ = ["HistoricalCaseIndex", "descriptor_tokens", "parse_query"]
