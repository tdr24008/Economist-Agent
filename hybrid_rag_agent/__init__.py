"""Hybrid RAG Agent - Intelligent research assistant with multi-modal search."""

from .agent import hybrid_rag_agent, run_hybrid_rag_sync, run_hybrid_rag_async
from .dependencies import SearchDependencies, MockSearchDependencies
from .settings import load_settings
from .providers import get_llm_model

__version__ = "1.0.0"
__author__ = "Claude Code"
__description__ = "Hybrid RAG agent combining vector, keyword, and graph search"

__all__ = [
    "hybrid_rag_agent",
    "run_hybrid_rag_sync", 
    "run_hybrid_rag_async",
    "SearchDependencies",
    "MockSearchDependencies",
    "load_settings",
    "get_llm_model",
]