"""Quick validation test for the properly structured Hybrid RAG Agent."""

import sys
import asyncio
import traceback

def test_imports():
    """Test that all components can be imported successfully."""
    try:
        from agent import hybrid_rag_agent, run_hybrid_rag_sync
        from dependencies import SearchDependencies, MockSearchDependencies, create_search_dependencies
        from settings import load_settings
        from providers import get_llm_model
        from utils.db_utils import DatabasePool
        from utils.graph_utils import GraphitiClient
        from utils.providers import get_embedding_client, get_embedding_model
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_agent_creation():
    """Test agent creation and tool registration."""
    try:
        from agent import hybrid_rag_agent
        
        assert hybrid_rag_agent is not None, "Agent not created"
        
        tool_names = {tool.name for tool in hybrid_rag_agent.tools}
        expected_tools = {'hybrid_search', 'graph_search', 'comprehensive_search', 'get_document', 'list_documents'}
        missing_tools = expected_tools - tool_names
        
        assert not missing_tools, f"Missing tools: {missing_tools}"
        print(f"✅ Agent created with {len(tool_names)} tools: {', '.join(tool_names)}")
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        traceback.print_exc()
        return False

async def test_dependencies_creation():
    """Test dependencies creation with the new factory function."""
    try:
        from dependencies import create_search_dependencies
        
        # Test mock mode
        deps = await create_search_dependencies(use_mocks=True)
        assert deps.use_mocks is True
        
        # Test basic operations
        vector_results = await deps.vector_search("test query", limit=3)
        assert isinstance(vector_results, list)
        
        hybrid_results = await deps.hybrid_search("test query", limit=3)
        assert isinstance(hybrid_results, list)
        
        graph_results = await deps.graph_search("test entity")
        assert isinstance(graph_results, list)
        
        docs = await deps.list_documents(limit=5)
        assert isinstance(docs, list)
        
        await deps.close()
        
        print("✅ Dependencies creation and operations working")
        return True
    except Exception as e:
        print(f"❌ Dependencies creation failed: {e}")
        traceback.print_exc()
        return False

def test_sync_agent_run():
    """Test synchronous agent execution."""
    try:
        from agent import run_hybrid_rag_sync
        
        # Test with auto-detection (should use mocks)
        result = run_hybrid_rag_sync("What is machine learning?")
        assert isinstance(result, str)
        assert len(result) > 0
        
        print(f"✅ Sync agent run successful. Result length: {len(result)}")
        return True
    except Exception as e:
        print(f"❌ Sync agent run failed: {e}")
        traceback.print_exc()
        return False

async def test_async_agent_run():
    """Test asynchronous agent execution."""
    try:
        from agent import run_hybrid_rag_async
        
        # Test with auto-detection (should use mocks)
        result = await run_hybrid_rag_async("How do neural networks work?")
        assert isinstance(result, str)
        assert len(result) > 0
        
        print(f"✅ Async agent run successful. Result length: {len(result)}")
        return True
    except Exception as e:
        print(f"❌ Async agent run failed: {e}")
        traceback.print_exc()
        return False

def test_infrastructure_integration():
    """Test that infrastructure components are accessible."""
    try:
        from utils.db_utils import vector_search, hybrid_search, get_document, list_documents
        from utils.graph_utils import search_knowledge_graph, get_entity_relationships
        from utils.providers import get_llm_model as infra_get_llm_model, get_embedding_client
        
        print("✅ Infrastructure integration working - utils accessible")
        return True
    except Exception as e:
        print(f"❌ Infrastructure integration failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all validation tests."""
    print("🔍 Starting Hybrid RAG Agent Structure Validation")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Agent Creation", test_agent_creation),
        ("Infrastructure Integration", test_infrastructure_integration),
        ("Dependencies Creation", test_dependencies_creation),
        ("Sync Agent Run", test_sync_agent_run),
        ("Async Agent Run", test_async_agent_run),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Structure Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All structure validation tests passed!")
        print("📁 Properly structured Hybrid RAG Agent is ready!")
    else:
        print(f"⚠️  {total - passed} tests failed. Review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())