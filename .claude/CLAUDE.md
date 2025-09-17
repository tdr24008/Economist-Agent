# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Economist RAG Agent** - an interactive economist research assistant built with **Streamlit**, **Autogen AgentChat**, and enhanced with **Hybrid RAG capabilities**, running locally for maximum data security. The system uses a multi-agent architecture combining:

- **RAG Retriever Agent**: Searches literature and provides research context using hybrid search (vector + keyword + knowledge graph)
- **Data Analyst Agent**: Proposes specifications, checks identification assumptions, explains methods
- **Code Executor Agent**: Runs Python analysis in a sandbox and returns safe artifacts (plots, tables)

All models are served locally via **Ollama** with no API keys or external data leakage. The system includes a sophisticated RAG module built with **Pydantic AI** that provides semantic search across economic literature.

## Architecture

### Core Components

- `app.py`: Main Streamlit application with chat interface and file upload
- `agents.py`: Contains `TrackableAssistantAgent` class and `get_data_analyst_team()` function
- `hybrid_rag_agent/`: Complete RAG system with Pydantic AI integration
  - `agent.py`: Main RAG agent with search capabilities
  - `ingestion/`: Document processing and knowledge graph building
  - `utils/`: Database utilities and provider configurations
  - `cli.py`: Interactive CLI interface for RAG queries
- `our-attempt/`: Alternative simplified implementation using direct tool integration
- `requirements.txt`: Combined dependencies for main app and RAG system

### Key Classes

- `TrackableAssistantAgent`: Extends `AssistantAgent` with Streamlit response tracking and visualization
- `get_data_analyst_team()`: Creates RoundRobinGroupChat with DataAnalystAgent and CodeExecutorAgent
- `hybrid_rag_agent`: Pydantic AI agent with vector search, hybrid search, and knowledge graph capabilities
- `SearchDependencies`: Dependency injection container for database connections and search tools

### Data Flow

1. User uploads CSV/TSV via Streamlit sidebar
2. File is saved to `code_executor/` directory
3. User queries are processed by the agent team:
   - RAG Retriever searches literature using hybrid methods (vector + keyword + graph)
   - Data Analyst proposes analysis based on query and available context
   - Code Executor runs analysis in isolated workspace
4. Code execution happens in isolated `code_executor/` workspace
5. Generated visualizations (PNG files) are automatically detected and displayed in chat

## Development Commands

### Prerequisites
```bash
# Install Ollama
# Download from ollama.com, then:
ollama pull llama3.1
ollama serve

# Optional: Start vector database services
docker compose up -d  # Starts Weaviate and Neo4j
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env
# Edit .env with your configuration (OPENAI_API_KEY required for full mode)

# Install dependencies
pip install -r requirements.txt

# Hybrid RAG module has separate requirements
cd hybrid_rag_agent
pip install -r requirements.txt
cd ..
```

### Running Applications
```bash
# Main Streamlit application (full multi-agent system)
streamlit run app.py

# Alternative simplified version (lighter dependencies)
streamlit run our-attempt/app.py

# Interactive RAG CLI (works in mock mode without databases)
cd hybrid_rag_agent
python cli.py
```

### Database Services (Optional)
```bash
# Start all services (Weaviate + Neo4j)
docker compose up -d

# Check service health
docker compose ps
docker compose logs weaviate
docker compose logs neo4j

# Stop services
docker compose down

# Reset data volumes
docker compose down -v
```

### Testing
```bash
# Run all RAG agent tests
cd hybrid_rag_agent
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_agent.py -v
python -m pytest tests/test_integration.py -v
python -m pytest tests/test_search_tools.py -v

# Run root-level integration tests
python test_integration.py
python test_rag_ingestion.py

# Validate project structure
python hybrid_rag_agent/test_structure_validation.py
```

### Available Models
- `llama3.1:8b` (default for main app)
- `qwen2.5:3b-instruct-q4_K_M` (default for agents.py)
- `qwen2.5-coder`
- `qwen3:8b`

## Key Implementation Details

### Agent System Messages
- **DataAnalystAgent**: Must plan analysis steps, write complete Python code, save visualizations as PNG, and end with 'TERMINATE'
- **CodeExecutorAgent**: Executes code and provides concise feedback on success/failure
- **RAG Retriever Agent**: Searches literature using multiple methods and provides context citations

### RAG System Architecture
- **Mock Mode**: Works without database setup using realistic sample data
- **Vector Search**: Uses embeddings for semantic similarity matching via Weaviate
- **Hybrid Search**: Combines semantic + keyword search with PostgreSQL TSVector
- **Knowledge Graph**: Entity relationships via Neo4j with APOC procedures
- **Pydantic AI**: Type-safe agent development with dependency injection
- **SearchDependencies**: Centralized dependency injection for database connections
- **Two-tier settings**: Environment variables via `.env` and Pydantic Settings

### File Handling
- Uploaded datasets are automatically saved to `code_executor/` directory
- All code execution is sandboxed within this directory
- Generated images must be saved as PNG format for proper display
- RAG documents can be ingested via the hybrid_rag_agent ingestion pipeline

### Termination Conditions
- Text mention of "TERMINATE" OR maximum 20 messages
- Agents should only terminate after successful analysis completion

### Windows Compatibility
The app includes Windows-specific asyncio event loop policy configuration for proper operation on Windows systems.

## Important Notes

- All LLM calls and code execution are offline via Ollama (except embedding services which may use OpenAI)
- Code execution is isolated to the `code_executor/` directory for security
- The system expects datasets with datetime columns (datetime, date, timestamp, or time)
- Generated visualizations are automatically detected and displayed in the Streamlit interface
- RAG system works in mock mode without external dependencies for development
- Two implementation approaches available: full integration (`app.py`) and simplified (`our-attempt/app.py`)
- Environment configuration handles both local Ollama and OpenAI API models
- Docker Compose provides optional Weaviate + Neo4j services for full RAG capabilities

## Project Structure Differences

### Main Implementation (`app.py` + `agents.py`)
- Full multi-agent system with RoundRobinGroupChat
- Integrated hybrid RAG agent with literature search
- TrackableAssistantAgent for Streamlit response tracking
- Comprehensive error handling and Windows compatibility

### Alternative Implementation (`our-attempt/`)
- Simplified direct tool integration approach
- Focuses on core economist analysis without RAG complexity
- Lighter dependencies and faster startup
- Good for development and testing core analysis features
- Uses different model defaults (configurable via environment variables)

## Configuration Management

### Environment Variables
Key environment variables (see `.env.example`):
- `OLLAMA_HOST`: Ollama server URL (default: http://127.0.0.1:11434)
- `MODEL_NAME`: Default model for agent system (default: qwen2.5:3b-instruct-q4_K_M)
- `OPENAI_API_KEY`: Required for OpenAI-based embeddings and models
- `WEAVIATE_URL`: Weaviate instance URL (default: http://localhost:8080)
- `NEO4J_URI`: Neo4j connection URI (default: bolt://localhost:7687)
- `NEO4J_PASSWORD`: Neo4j database password (default: password123)

### Mock vs Production Mode
- **Mock Mode**: Leave API keys empty in `.env` to use sample data
- **Production Mode**: Set OPENAI_API_KEY for full vector search capabilities
- **Hybrid Mode**: Use Ollama for LLM, OpenAI for embeddings