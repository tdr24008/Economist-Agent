#!/usr/bin/env python3
"""
Test RAG ingestion system with Weaviate and Neo4j
"""

import asyncio
import os
import sys

# Add hybrid_rag_agent to path
sys.path.append('hybrid_rag_agent')

from hybrid_rag_agent.ingestion.ingest import DocumentIngestionPipeline
from hybrid_rag_agent.utils.models import IngestionConfig

async def test_ingestion():
    """Test the ingestion pipeline with a simple document."""
    print("🔄 Testing RAG ingestion pipeline...")

    try:
        # Create ingestion configuration
        config = IngestionConfig(
            chunk_size=500,
            chunk_overlap=100,
            use_semantic_chunking=True,
            extract_entities=True,
            skip_graph_building=True  # Skip for now to test basic functionality
        )

        # Create pipeline
        pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder="documents",
            clean_before_ingest=False
        )

        print("📡 Initializing connections to Weaviate and Neo4j...")
        await pipeline.initialize()
        print("✅ Connections established!")

        print("📄 Starting document ingestion...")
        results = await pipeline.ingest_documents()

        print(f"\n🎉 Ingestion complete!")
        print(f"Documents processed: {len(results)}")

        for result in results:
            print(f"  📖 {result.title}: {result.chunks_created} chunks")
            if result.errors:
                print(f"    ❌ Errors: {result.errors}")
            else:
                print(f"    ✅ Success!")

        # Close connections
        await pipeline.close()
        print("🔌 Connections closed.")

    except Exception as e:
        print(f"❌ Error during ingestion test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ingestion())