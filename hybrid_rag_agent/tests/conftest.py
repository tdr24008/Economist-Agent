"""Pytest fixtures and configuration for Hybrid RAG Agent tests."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from pydantic_ai.models.test import TestModel
from dependencies import SearchDependencies, MockSearchDependencies
from agent import hybrid_rag_agent

@pytest.fixture
def mock_dependencies():
    """Create mock search dependencies for testing."""
    return MockSearchDependencies()

@pytest.fixture
def search_dependencies_mock_mode():
    """Create SearchDependencies in mock mode."""
    return SearchDependencies(use_mocks=True)

@pytest.fixture
def test_model():
    """Create a TestModel instance for agent testing."""
    return TestModel()

@pytest.fixture
def agent_with_test_model(test_model):
    """Create agent instance with TestModel for testing."""
    return hybrid_rag_agent.override(model=test_model)

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Sample test data
@pytest.fixture
def sample_query():
    """Sample search query for testing."""
    return "What is machine learning?"

@pytest.fixture
def sample_document_id():
    """Sample document ID for testing."""
    return "doc-ai-fundamentals"

@pytest.fixture
def sample_vector_results():
    """Sample vector search results."""
    return [
        {
            "chunk_id": "test-chunk-1",
            "document_id": "test-doc-1",
            "content": "Machine learning is a subset of AI.",
            "similarity": 0.95,
            "metadata": {"page": 1},
            "document_title": "AI Guide",
            "document_source": "ai_guide.pdf"
        }
    ]

@pytest.fixture
def sample_graph_results():
    """Sample graph search results."""
    return [
        {
            "fact": "Machine Learning is related to Artificial Intelligence",
            "uuid": "fact-test-1",
            "valid_at": "2024-01-01T00:00:00Z",
            "invalid_at": None,
            "source_node_uuid": "node-ml"
        }
    ]