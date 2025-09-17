#!/bin/bash
# Document ingestion script for local RAG setup

echo "📄 Document Ingestion for Local RAG"
echo "================================="

# Activate virtual environment
source activate_venv.sh

echo ""
echo "📋 Available Documents:"
echo "   📄 documents/test_document.md (Economic indicators)"
echo "   📄 code_executor/Federal Reserve Interest Rate Decision Q4 2024.pdf"
echo ""

# Check if databases are running
if ! curl -s http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; then
    echo "❌ Weaviate not accessible at localhost:8080"
    echo "   Run: ./setup_local_rag.sh first"
    exit 1
fi

echo "✅ Weaviate is accessible"

# Run the ingestion test
echo ""
echo "🔄 Running document ingestion..."
echo "   This will process documents and store them in:"
echo "   - Weaviate (vector embeddings)"
echo "   - Neo4j (knowledge graph)"
echo ""

python test_rag_ingestion.py

echo ""
echo "🎯 Ingestion Complete!"
echo ""
echo "📊 Check Results:"
echo "   Weaviate: http://localhost:8080"
echo "   Neo4j: http://localhost:7474 (neo4j/password123)"
echo ""
echo "🚀 Test RAG System:"
echo "   ./run_app.sh"