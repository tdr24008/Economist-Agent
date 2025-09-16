#!/usr/bin/env python3
"""
Test script to verify the Economist RAG Agent integration works correctly.
This tests the core components without running the full Streamlit app.
"""

import sys
import os
import asyncio

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_rag_integration():
    """Test the RAG integration components."""
    print("🧪 Testing Economist RAG Agent Integration")
    print("=" * 50)

    # Test 1: Import check
    print("\n1. Testing imports...")
    try:
        from agents import get_data_analyst_team, RAGRetrieverAgent
        from hybrid_rag_agent.dependencies import SearchDependencies
        from hybrid_rag_agent.agent import hybrid_rag_agent
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: RAG Dependencies initialization
    print("\n2. Testing RAG Dependencies (Mock Mode)...")
    try:
        deps = SearchDependencies(use_mocks=True)
        await deps.initialize()
        print("✅ RAG Dependencies initialized successfully")
    except Exception as e:
        print(f"❌ RAG Dependencies failed: {e}")
        return False

    # Test 3: Mock search functionality
    print("\n3. Testing mock search functionality...")
    try:
        query = "What is machine learning?"
        results = await deps.vector_search(query, limit=2)
        print(f"✅ Vector search returned {len(results)} results")

        results = await deps.hybrid_search(query, limit=2)
        print(f"✅ Hybrid search returned {len(results)} results")

        results = await deps.graph_search(query)
        print(f"✅ Graph search returned {len(results)} results")
    except Exception as e:
        print(f"❌ Search functionality failed: {e}")
        return False
    finally:
        await deps.close()

    # Test 4: Agent team creation
    print("\n4. Testing agent team creation...")
    try:
        # Mock model client for testing
        class MockModelClient:
            def __init__(self):
                self.model = "test-model"

        model_client = MockModelClient()
        team = get_data_analyst_team("test-model")
        print(f"✅ Agent team created with {len(team.participants)} agents")
        print(f"   Agents: {[agent.name for agent in team.participants]}")
    except Exception as e:
        print(f"❌ Agent team creation failed: {e}")
        return False

    # Test 5: RAGRetrieverAgent initialization
    print("\n5. Testing RAGRetrieverAgent...")
    try:
        rag_agent = RAGRetrieverAgent(
            name="TestRAGAgent",
            model_client=MockModelClient()
        )
        print("✅ RAGRetrieverAgent created successfully")

        # Test search method
        search_result = await rag_agent.search_documents("machine learning", "hybrid")
        print(f"✅ RAG Agent search completed")
        print(f"   Result preview: {search_result[:100]}...")
    except Exception as e:
        print(f"❌ RAGRetrieverAgent failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All integration tests passed!")
    print("\nYou can now run the Streamlit app with:")
    print("   streamlit run app.py")
    return True

async def test_directory_structure():
    """Test that all necessary directories exist."""
    print("\n📁 Testing directory structure...")

    required_dirs = [
        "hybrid_rag_agent",
        "documents",
        "documents/economics",
        "documents/data",
        "documents/ingested"
    ]

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - Missing!")
            return False

    print("✅ All required directories exist")
    return True

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Economist RAG Agent Integration Tests\n")

        # Test directory structure first
        if not await test_directory_structure():
            print("\n❌ Directory structure test failed!")
            sys.exit(1)

        # Test integration
        if await test_rag_integration():
            print("\n✅ Integration test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Integration test failed!")
            sys.exit(1)

    # Run tests
    asyncio.run(main())