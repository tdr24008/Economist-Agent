#!/bin/bash
# Configure environment for local databases

echo "🔧 Configuring Environment for Local Databases"
echo "=============================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔑 Environment Configuration:"
echo "   WEAVIATE_URL=http://localhost:8080"
echo "   NEO4J_URI=bolt://localhost:7687"
echo "   NEO4J_PASSWORD=password123"
echo ""
echo "⚠️  You need to add your OpenAI API key to .env:"
echo "   OPENAI_API_KEY=your_actual_api_key_here"
echo ""
echo "🔄 Current .env contents:"
head -20 .env

echo ""
echo "💡 To edit .env file:"
echo "   nano .env"
echo "   or edit it in your preferred text editor"