#!/bin/bash
# Complete setup script for local RAG with real databases

echo "🚀 Setting up Local RAG with Weaviate + Neo4j"
echo "=============================================="

# Step 1: Check Docker is running
echo "📋 Step 1: Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first!"
    echo "   1. Open Docker Desktop"
    echo "   2. Wait for it to fully start"
    echo "   3. Run this script again"
    exit 1
fi
echo "✅ Docker is running"

# Step 2: Start databases
echo ""
echo "📋 Step 2: Starting databases..."
echo "🔄 Starting Weaviate (Vector Database) and Neo4j (Knowledge Graph)..."
docker compose up -d

# Step 3: Wait for services to be ready
echo ""
echo "📋 Step 3: Waiting for services to start..."
echo "⏳ Waiting for Weaviate to be ready..."
timeout=60
counter=0
while ! curl -s http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Weaviate failed to start within $timeout seconds"
        break
    fi
    echo "   Still waiting... ($counter/${timeout}s)"
    sleep 2
    counter=$((counter + 2))
done

if curl -s http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; then
    echo "✅ Weaviate is ready at http://localhost:8080"
else
    echo "⚠️  Weaviate may not be ready yet, but continuing..."
fi

echo "✅ Neo4j is starting at http://localhost:7474 (neo4j/password123)"

# Step 4: Show status
echo ""
echo "📋 Step 4: Database Status"
docker compose ps

echo ""
echo "🎯 What's Running:"
echo "   📊 Weaviate (Vector DB): http://localhost:8080"
echo "   🔗 Neo4j Browser: http://localhost:7474"
echo "   🔐 Neo4j Credentials: neo4j/password123"

echo ""
echo "📂 Data Storage Locations:"
echo "   Weaviate Data: Docker volume 'weaviate_data'"
echo "   Neo4j Data: Docker volume 'neo4j_data'"
echo "   All data persists between restarts"

echo ""
echo "🔄 Next Steps:"
echo "   1. Configure .env file with API keys"
echo "   2. Run ingestion: python test_rag_ingestion.py"
echo "   3. Test RAG: ./run_app.sh"