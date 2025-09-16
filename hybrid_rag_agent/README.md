# Hybrid RAG Agent

An intelligent research assistant that combines vector search, hybrid search, and knowledge graph capabilities using Pydantic AI.

## Features

🔍 **Multi-Modal Search**
- **Vector Search**: Semantic similarity matching using embeddings
- **Hybrid Search**: Combined semantic + keyword search with PostgreSQL TSVector
- **Graph Search**: Entity relationships and temporal facts via Neo4j/Graphiti
- **Comprehensive Search**: Parallel execution of multiple search methods

🤖 **Pydantic AI Integration**
- Type-safe agent development with structured outputs
- Dependency injection for database connections
- Comprehensive error handling and graceful fallbacks
- TestModel support for development and testing

🛠️ **Development-First Design**
- **Mock Mode**: Full functionality without database credentials
- Realistic sample data for all search operations
- Comprehensive test coverage with validation gates
- CLI interface for interactive querying

## Quick Start

### 1. Setup Environment

```bash
# Navigate to the hybrid_rag_agent directory
cd hybrid_rag_agent

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Required for production
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db
LLM_API_KEY=your-openai-api-key
EMBEDDING_API_KEY=your-embedding-api-key

# Optional - will use mocks if not provided
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

**Note**: The agent works in **MOCK MODE** without any credentials - perfect for development and testing!

### 3. Run the Agent

**Interactive CLI:**
```bash
cd hybrid_rag_agent
python3 cli.py
```

**Programmatic Usage:**
```python
import sys
sys.path.append('hybrid_rag_agent')

from agent import run_hybrid_rag_sync

# Quick sync usage (auto-detects mock mode)
result = run_hybrid_rag_sync("What is machine learning?")
print(result)
```

**Advanced Usage:**
```python
import asyncio
from agent import hybrid_rag_agent
from dependencies import SearchDependencies

async def main():
    deps = SearchDependencies(use_mocks=True)  # or False for production
    result = await hybrid_rag_agent.run("How do neural networks work?", deps=deps)
    print(result.data)

asyncio.run(main())
```

## Architecture

### Core Components

```
hybrid_rag_agent/
├── agent.py              # Main Pydantic AI agent with 5 search tools
├── dependencies.py       # SearchDependencies integrating with existing infrastructure
├── settings.py          # Environment configuration with graceful fallbacks
├── providers.py         # LLM model abstraction (OpenAI/TestModel)
├── cli.py               # Rich console interface
│
├── sql/                 # Database schema and functions (PostgreSQL + pgvector)
│   └── schema.sql       # Vector and hybrid search SQL functions
│
├── utils/               # Database and graph utilities (production infrastructure)
│   ├── db_utils.py      # PostgreSQL connection pool and search functions
│   ├── graph_utils.py   # Neo4j/Graphiti integration and graph operations
│   ├── models.py        # Pydantic models for search results
│   └── providers.py     # Flexible LLM and embedding model configuration
│
├── ingestion/           # Document processing pipeline
│   ├── ingest.py        # Main ingestion script
│   ├── chunker.py       # Document chunking logic
│   ├── embedder.py      # Embedding generation
│   └── graph_builder.py # Knowledge graph construction
│
├── documents/           # Sample documents for testing
├── tests/               # Comprehensive test suite
└── planning/            # Design specifications and prompts
```

### Search Tools

The agent provides 5 essential search tools:

1. **`hybrid_search`** - Primary search combining vector + keyword matching
2. **`graph_search`** - Entity relationships and temporal facts
3. **`comprehensive_search`** - Parallel vector + graph search 
4. **`get_document`** - Retrieve complete document by ID
5. **`list_documents`** - Browse available documents

### Mock Mode Features

Mock mode provides realistic search results without requiring database setup:

- **Vector search results** with similarity scores and document attribution
- **Graph relationships** with temporal validity and entity connections  
- **Document metadata** with realistic titles, sources, and chunk counts
- **Configurable response delays** to simulate network latency
- **Error simulation** for testing edge cases

## Development

### Running Tests

```bash
# Validation tests (no external dependencies)
python3 test_validation.py

# Full test suite (requires pytest)
pip install pytest pytest-asyncio
python3 -m pytest tests/ -v
```

### Mock vs Production Mode

**Mock Mode** (default when credentials missing):
- No external database connections required
- Uses realistic sample data from `dependencies.py`
- Perfect for development, testing, and demos
- Indicated by warning: "Running in MOCK MODE"

**Production Mode** (when all credentials provided):
- Connects to PostgreSQL with pgvector for vector/hybrid search
- Connects to Neo4j with Graphiti for knowledge graph operations
- Uses real embedding API for query vectorization
- Full performance and unlimited data access

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes* | PostgreSQL connection string | None (uses mocks) |
| `LLM_API_KEY` | Yes* | OpenAI API key | None (uses TestModel) |  
| `LLM_MODEL` | No | Model name | gpt-4o-mini |
| `LLM_BASE_URL` | No | API endpoint | https://api.openai.com/v1 |
| `EMBEDDING_API_KEY` | Yes* | Embedding service key | None (uses mocks) |
| `EMBEDDING_MODEL` | No | Embedding model | text-embedding-3-small |
| `NEO4J_URI` | No | Neo4j connection | None (uses mocks) |
| `NEO4J_USER` | No | Neo4j username | None |
| `NEO4J_PASSWORD` | No | Neo4j password | None |

*Required for production mode only

## Usage Examples

### CLI Interface

```bash
$ python3 cli.py

🔍 Welcome - Hybrid RAG Agent
╭─ Intelligent research assistant with: ─╮
│ • Vector Search: Semantic similarity   │
│ • Hybrid Search: Combined semantic +   │
│   keyword search                       │
│ • Graph Search: Entity relationships   │
│   and facts                           │
│ • Comprehensive Search: Multi-method   │
│   parallel search                     │
╰────────────────────────────────────────╯

Your question: What is machine learning?

🎯 Answer
Machine learning is a subset of artificial intelligence that enables 
computers to learn and make decisions from data without being explicitly 
programmed for every task...

Source: AI Fundamentals Guide - ai_fundamentals.pdf | Similarity: 0.95
```

### Python API

```python
# Synchronous usage
from agent import run_hybrid_rag_sync

answer = run_hybrid_rag_sync("How do neural networks work?")
print(answer)

# Asynchronous usage with custom dependencies
import asyncio
from agent import hybrid_rag_agent
from dependencies import SearchDependencies

async def research_query():
    deps = SearchDependencies(use_mocks=False)  # Use real databases
    result = await hybrid_rag_agent.run(
        "What are the relationships between transformers and NLP?",
        deps=deps
    )
    return result.data

answer = asyncio.run(research_query())
```

### Search Method Selection

The agent intelligently chooses search methods based on query type:

- **Conceptual queries** → `hybrid_search` (semantic + keyword)
- **Relationship queries** → `graph_search` (entity connections)
- **Complex research** → `comprehensive_search` (parallel methods)
- **Document browsing** → `list_documents` + `get_document`

## Production Deployment

### Database Setup

**PostgreSQL with pgvector:**
```sql
-- Enable extensions
CREATE EXTENSION vector;
CREATE EXTENSION pg_trgm;

-- Run schema from examples/rag_pipeline/sql/schema.sql
```

**Neo4j with Graphiti:**
```bash
# Install Neo4j and Graphiti
pip install neo4j graphiti-core

# Configure connection in .env
NEO4J_URI=bolt://localhost:7687
```

### Environment Configuration

1. Set all required environment variables in `.env`
2. Verify connectivity: `python3 -c "from settings import load_settings; print(load_settings().is_production_ready())"`
3. Run validation: `python3 test_validation.py`

### Performance Tuning

- **PostgreSQL**: Use HNSW indices for vector similarity
- **Neo4j**: Configure appropriate memory settings
- **Embedding API**: Implement rate limiting and caching
- **Agent**: Adjust search result limits based on use case

## Contributing

1. Follow the PRP development pattern (Plan-Research-Prototype)
2. All search functionality must work in mock mode
3. Add comprehensive tests for new features
4. Maintain backward compatibility with existing APIs
5. Update documentation for any new environment variables

## License

MIT License - see LICENSE file for details.

---

**Built with Pydantic AI** - Type-safe, production-ready AI agents with structured outputs and comprehensive testing.