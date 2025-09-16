# Dependency Specifications for Hybrid RAG Agent

## Environment Variables (Essential Only)

```env
# Database Connection
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

# LLM Provider  
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1

# Embedding Service
EMBEDDING_API_KEY=your-embedding-key-here
EMBEDDING_MODEL=text-embedding-3-small

# Graph Database (Optional - will use mocks if not provided)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## Dependencies Dataclass

```markdown
SearchDependencies:
  - db_pool: Database connection pool (asyncpg)
  - embedding_client: Client for generating embeddings
  - graph_client: Optional Neo4j/Graphiti client
  - use_mocks: Boolean flag for development mode
```

## Python Packages (Minimal)

```requirements
pydantic-ai>=0.0.10
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
asyncpg>=0.29.0
openai>=1.0.0
numpy>=1.24.0
```

## Configuration Strategy

1. **Single Model Provider**: OpenAI-compatible endpoint only
2. **Graceful Fallbacks**: Automatic mock mode when credentials missing
3. **Development First**: Full functionality without real connections using MockSearchDependencies
4. **Simple Validation**: Warning messages for missing credentials, not errors

## Mock Dependencies Support

```markdown
MockSearchDependencies:
  - Returns realistic sample data for all search operations
  - Simulates network delays (0.1s default)
  - No external connections required
  - Enables full agent testing without credentials
```