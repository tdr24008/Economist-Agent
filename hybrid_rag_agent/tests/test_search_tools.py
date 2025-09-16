"""Test individual search tools with mock dependencies."""

import pytest
from pydantic_ai import RunContext
from pydantic_ai.models.test import TestModel

from agent import hybrid_rag_agent
from dependencies import SearchDependencies, MockSearchDependencies

class TestSearchTools:
    """Test suite for individual search tools."""

    @pytest.fixture
    def run_context_mock(self, search_dependencies_mock_mode):
        """Create a RunContext with mock dependencies."""
        return RunContext(deps=search_dependencies_mock_mode, retry=0)

    @pytest.mark.asyncio
    async def test_hybrid_search_tool(self, run_context_mock):
        """Test hybrid search tool functionality."""
        from agent import hybrid_search
        
        result = await hybrid_search(run_context_mock, "machine learning", limit=5, text_weight=0.3)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "results" in result.lower()

    @pytest.mark.asyncio
    async def test_graph_search_tool(self, run_context_mock):
        """Test graph search tool functionality."""
        from agent import graph_search
        
        result = await graph_search(run_context_mock, "artificial intelligence", include_timeline=True)
        
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_comprehensive_search_tool(self, run_context_mock):
        """Test comprehensive search tool functionality."""
        from agent import comprehensive_search
        
        result = await comprehensive_search(run_context_mock, "neural networks", limit=5)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert ("document search" in result.lower() or "knowledge graph" in result.lower())

    @pytest.mark.asyncio
    async def test_get_document_tool(self, run_context_mock, sample_document_id):
        """Test document retrieval tool."""
        from agent import get_document
        
        result = await get_document(run_context_mock, sample_document_id)
        
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_list_documents_tool(self, run_context_mock):
        """Test document listing tool."""
        from agent import list_documents
        
        result = await list_documents(run_context_mock, limit=10, offset=0)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "documents" in result.lower()

    @pytest.mark.asyncio
    async def test_hybrid_search_parameter_validation(self, run_context_mock):
        """Test parameter validation in hybrid search."""
        from agent import hybrid_search
        
        # Test limit bounds
        result = await hybrid_search(run_context_mock, "test", limit=0)  # Should be adjusted to 1
        assert "results" in result.lower()
        
        result = await hybrid_search(run_context_mock, "test", limit=100)  # Should be capped at 20
        assert isinstance(result, str)
        
        # Test text_weight bounds
        result = await hybrid_search(run_context_mock, "test", text_weight=-0.5)  # Should be 0.0
        assert isinstance(result, str)
        
        result = await hybrid_search(run_context_mock, "test", text_weight=1.5)  # Should be 1.0
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_search_tool_error_handling(self):
        """Test error handling in search tools."""
        from agent import hybrid_search
        
        # Create dependencies that will cause errors
        broken_deps = SearchDependencies(use_mocks=False, database_pool=None)
        broken_context = RunContext(deps=broken_deps, retry=0)
        
        result = await hybrid_search(broken_context, "test query")
        
        # Should return error message, not raise exception
        assert isinstance(result, str)
        assert ("failed" in result.lower() or "error" in result.lower())

    @pytest.mark.asyncio
    async def test_mock_dependencies_functionality(self, mock_dependencies):
        """Test that mock dependencies work correctly."""
        # Test vector search
        vector_results = await mock_dependencies.mock_vector_search("test", limit=3)
        assert isinstance(vector_results, list)
        assert len(vector_results) <= 3
        assert all('content' in result for result in vector_results)
        
        # Test hybrid search
        hybrid_results = await mock_dependencies.mock_hybrid_search("test", limit=3, text_weight=0.5)
        assert isinstance(hybrid_results, list)
        assert len(hybrid_results) <= 3
        assert all('combined_score' in result for result in hybrid_results)
        
        # Test graph search
        graph_results = await mock_dependencies.mock_graph_search("test entity")
        assert isinstance(graph_results, list)
        assert all('fact' in result for result in graph_results)
        
        # Test document operations
        docs = await mock_dependencies.mock_list_documents(limit=5)
        assert isinstance(docs, list)
        assert len(docs) <= 5
        
        if docs:
            doc_id = docs[0]['id']
            doc = await mock_dependencies.mock_get_document(doc_id)
            assert isinstance(doc, dict)
            assert doc['id'] == doc_id

    @pytest.mark.asyncio
    async def test_comprehensive_search_combination(self, mock_dependencies):
        """Test that comprehensive search properly combines results."""
        results = await mock_dependencies.mock_comprehensive_search("AI research", limit=5)
        
        assert isinstance(results, dict)
        assert 'vector_results' in results
        assert 'graph_results' in results
        assert 'total_results' in results
        
        vector_count = len(results['vector_results'])
        graph_count = len(results['graph_results'])
        total = results['total_results']
        
        assert total == vector_count + graph_count

    def test_search_tools_registration(self):
        """Test that all search tools are properly registered with the agent."""
        tool_names = [tool.name for tool in hybrid_rag_agent.tools]
        
        required_tools = [
            'hybrid_search',
            'graph_search', 
            'comprehensive_search',
            'get_document',
            'list_documents'
        ]
        
        for tool_name in required_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered with agent"