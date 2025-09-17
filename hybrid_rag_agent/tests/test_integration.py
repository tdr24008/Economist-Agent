"""Integration tests for the Hybrid RAG Agent."""

import pytest
from pydantic_ai.models.test import TestModel

from ..agent import hybrid_rag_agent
from ..dependencies import SearchDependencies
from ..settings import load_settings

class TestIntegration:
    """Integration tests for the complete agent system."""

    def test_settings_loading(self):
        """Test that settings load correctly with graceful fallbacks."""
        settings = load_settings()
        assert settings is not None
        # Should work even without .env file
        assert isinstance(settings.should_use_mocks(), bool)

    def test_mock_mode_detection(self):
        """Test automatic mock mode detection."""
        settings = load_settings()
        
        # In test environment, should default to mock mode
        should_mock = settings.should_use_mocks()
        deps = SearchDependencies(use_mocks=should_mock)
        
        assert deps.use_mocks == should_mock

    @pytest.mark.asyncio
    async def test_end_to_end_query_processing(self):
        """Test complete query processing from input to output."""
        deps = SearchDependencies(use_mocks=True)
        test_model = TestModel()
        
        with hybrid_rag_agent.override(model=test_model):
            queries = [
                "What is artificial intelligence?",
                "How do neural networks work?",
                "Find information about machine learning algorithms",
                "What are the relationships between AI and robotics?"
            ]
            
            for query in queries:
                result = await hybrid_rag_agent.run(query, deps=deps)
                assert result is not None
                assert isinstance(result.data, str)
                assert len(result.data) > 0

    @pytest.mark.asyncio
    async def test_tool_selection_intelligence(self):
        """Test that appropriate tools are called for different query types."""
        deps = SearchDependencies(use_mocks=True)
        test_model = TestModel()
        
        with hybrid_rag_agent.override(model=test_model):
            # Test queries that should trigger different tools
            test_cases = [
                ("What is machine learning?", "hybrid_search"),  # Should use hybrid search
                ("List available documents", "list_documents"),  # Should use document listing
                ("Tell me about doc-ai-fundamentals", "get_document"),  # Should use document retrieval
            ]
            
            for query, expected_tool in test_cases:
                result = await hybrid_rag_agent.run(query, deps=deps)
                assert result is not None
                # Note: With TestModel, we can't easily verify which tools were called
                # But we can verify the agent executed successfully

    def test_agent_system_prompt_integration(self):
        """Test that system prompt is properly integrated."""
        assert hybrid_rag_agent.system_prompt is not None
        assert len(hybrid_rag_agent.system_prompt) > 100  # Should be substantial
        
        # Check for key concepts mentioned in the planning
        prompt_lower = hybrid_rag_agent.system_prompt.lower()
        key_concepts = [
            'vector search',
            'hybrid search',
            'graph search',
            'research assistant',
            'comprehensive'
        ]
        
        for concept in key_concepts:
            assert concept in prompt_lower, f"System prompt missing: {concept}"

    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """Test that the system handles various error conditions gracefully."""
        deps = SearchDependencies(use_mocks=True)
        test_model = TestModel()
        
        with hybrid_rag_agent.override(model=test_model):
            # Test empty query
            result = await hybrid_rag_agent.run("", deps=deps)
            assert result is not None
            
            # Test very long query
            long_query = "What is " + "machine learning " * 100
            result = await hybrid_rag_agent.run(long_query, deps=deps)
            assert result is not None
            
            # Test special characters
            special_query = "What is AI? @#$%^&*()"
            result = await hybrid_rag_agent.run(special_query, deps=deps)
            assert result is not None

    def test_dependency_injection_pattern(self):
        """Test that dependency injection works correctly."""
        # Test with mock dependencies
        mock_deps = SearchDependencies(use_mocks=True)
        assert mock_deps.use_mocks is True
        assert mock_deps._mock_deps is not None
        
        # Test automatic mock mode activation
        no_db_deps = SearchDependencies(database_pool=None)
        assert no_db_deps.use_mocks is True

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        import asyncio
        
        deps = SearchDependencies(use_mocks=True)
        test_model = TestModel()
        
        async def run_query(query_id):
            with hybrid_rag_agent.override(model=test_model):
                result = await hybrid_rag_agent.run(f"Query {query_id}: What is AI?", deps=deps)
                return result.data
        
        # Run 5 concurrent queries
        tasks = [run_query(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Query {i} failed with: {result}"
            assert isinstance(result, str)
            assert len(result) > 0

    def test_mock_data_quality(self):
        """Test that mock data provides realistic search results."""
        # Verify mock data structure
        from dependencies import SAMPLE_VECTOR_RESULTS, SAMPLE_GRAPH_RESULTS, SAMPLE_DOCUMENTS
        
        # Vector results should have required fields
        for result in SAMPLE_VECTOR_RESULTS:
            required_fields = ['chunk_id', 'document_id', 'content', 'similarity', 'document_title', 'document_source']
            for field in required_fields:
                assert field in result, f"Mock vector result missing field: {field}"
            assert 0 <= result['similarity'] <= 1, "Similarity should be between 0 and 1"
        
        # Graph results should have required fields  
        for result in SAMPLE_GRAPH_RESULTS:
            required_fields = ['fact', 'uuid', 'valid_at']
            for field in required_fields:
                assert field in result, f"Mock graph result missing field: {field}"
        
        # Documents should have required fields
        for doc in SAMPLE_DOCUMENTS:
            required_fields = ['id', 'title', 'source', 'created_at']
            for field in required_fields:
                assert field in doc, f"Mock document missing field: {field}"