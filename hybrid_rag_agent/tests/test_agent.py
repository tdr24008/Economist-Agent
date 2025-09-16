"""Test the Hybrid RAG Agent with TestModel validation."""

import pytest
from pydantic_ai.models.test import TestModel

from agent import hybrid_rag_agent, run_hybrid_rag_sync, run_hybrid_rag_async
from dependencies import SearchDependencies

class TestHybridRAGAgent:
    """Test suite for the Hybrid RAG Agent."""

    def test_agent_creation(self):
        """Test that the agent is created successfully."""
        assert hybrid_rag_agent is not None
        assert hybrid_rag_agent.deps_type == SearchDependencies
        assert "intelligent research assistant" in hybrid_rag_agent.system_prompt.lower()

    def test_agent_tools_registered(self):
        """Test that all required tools are registered."""
        tool_names = {tool.name for tool in hybrid_rag_agent.tools}
        expected_tools = {
            'hybrid_search',
            'graph_search', 
            'comprehensive_search',
            'get_document',
            'list_documents'
        }
        assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"

    def test_sync_run_with_mocks(self, sample_query):
        """Test synchronous agent execution with mock dependencies."""
        result = run_hybrid_rag_sync(sample_query, use_mocks=True)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_async_run_with_mocks(self, sample_query):
        """Test asynchronous agent execution with mock dependencies."""
        result = await run_hybrid_rag_async(sample_query, use_mocks=True)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_agent_with_test_model(self, agent_with_test_model, search_dependencies_mock_mode, sample_query):
        """Test agent with TestModel override."""
        result = agent_with_test_model.run_sync(sample_query, deps=search_dependencies_mock_mode)
        assert result is not None
        assert isinstance(result.data, str)

    @pytest.mark.asyncio 
    async def test_agent_async_with_test_model(self, agent_with_test_model, search_dependencies_mock_mode, sample_query):
        """Test async agent execution with TestModel."""
        result = await agent_with_test_model.run(sample_query, deps=search_dependencies_mock_mode)
        assert result is not None
        assert isinstance(result.data, str)

    def test_agent_conversation_flow(self, agent_with_test_model, search_dependencies_mock_mode):
        """Test multi-turn conversation with the agent."""
        queries = [
            "What is machine learning?",
            "How does it relate to AI?",
            "Find documents about neural networks"
        ]
        
        for query in queries:
            result = agent_with_test_model.run_sync(query, deps=search_dependencies_mock_mode)
            assert result is not None
            assert isinstance(result.data, str)
            assert len(result.data) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, agent_with_test_model):
        """Test agent error handling with invalid dependencies."""
        # Create dependencies that will fail
        invalid_deps = SearchDependencies(use_mocks=False, database_pool=None)
        
        try:
            result = await agent_with_test_model.run("test query", deps=invalid_deps)
            # Should not raise exception, should handle gracefully
            assert result is not None
        except Exception as e:
            pytest.fail(f"Agent should handle errors gracefully, but raised: {e}")

    def test_system_prompt_content(self):
        """Test that system prompt contains expected content."""
        prompt = hybrid_rag_agent.system_prompt.lower()
        expected_keywords = [
            'vector search',
            'hybrid search', 
            'graph search',
            'research assistant',
            'sources'
        ]
        for keyword in expected_keywords:
            assert keyword in prompt, f"System prompt missing keyword: {keyword}"

    def test_agent_tool_descriptions(self):
        """Test that all tools have proper descriptions."""
        for tool in hybrid_rag_agent.tools:
            assert hasattr(tool, 'description') or hasattr(tool, '__doc__')
            # Tools should have meaningful names
            assert len(tool.name) > 3
            assert '_' in tool.name or tool.name.islower()