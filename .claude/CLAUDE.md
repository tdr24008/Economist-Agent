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
```

### Setup and Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run main Streamlit application
streamlit run app.py

# Alternative: Run simplified version
streamlit run our-attempt/app.py

# Interactive RAG CLI (works in mock mode)
cd hybrid_rag_agent
python cli.py
```

### Testing
```bash
# Run RAG agent tests
cd hybrid_rag_agent
python -m pytest tests/ -v

# Run integration tests
python test_integration.py

# Validate RAG structure
python test_structure_validation.py
```

### Available Models
- `llama3.1:8b` (default)
- `qwen2.5-coder`
- `qwen3:8b`

## Key Implementation Details

### Agent System Messages
- **DataAnalystAgent**: Must plan analysis steps, write complete Python code, save visualizations as PNG, and end with 'TERMINATE'
- **CodeExecutorAgent**: Executes code and provides concise feedback on success/failure
- **RAG Retriever Agent**: Searches literature using multiple methods and provides context citations

### RAG System Architecture
- **Mock Mode**: Works without database setup using realistic sample data
- **Vector Search**: Uses embeddings for semantic similarity matching
- **Hybrid Search**: Combines semantic + keyword search with PostgreSQL TSVector
- **Knowledge Graph**: Entity relationships via Neo4j/Graphiti integration
- **Pydantic AI**: Type-safe agent development with dependency injection

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

- All LLM calls and code execution are offline via Ollama
- Code execution is isolated to the `code_executor/` directory
- The system expects datasets with datetime columns (datetime, date, timestamp, or time)
- Generated visualizations are automatically detected and displayed in the Streamlit interface
- RAG system works in mock mode without external dependencies for development
- Two implementation approaches available: full integration (`app.py`) and simplified (`our-attempt/app.py`)

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