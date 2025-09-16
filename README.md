# Economist Agent 📈🏦💰

An interactive **economist research assistant** built with **Streamlit**, **Autogen AgentChat**, and enhanced with **Hybrid RAG capabilities**, running locally for maximum data security.

The system combines multiple specialized agents:
- **RAG Retriever Agent**: Searches literature and provides research context using hybrid search (vector + keyword + knowledge graph)
- **Data Analyst Agent**: Proposes specifications, checks identification assumptions, explains methods
- **Code Executor Agent**: Runs Python analysis in a sandbox and returns safe artifacts (plots, tables)

Models are served locally via **[Ollama](https://ollama.com/)** — no API keys, no external data leakage. The system includes a sophisticated RAG module built with **Pydantic AI** that provides semantic search across economic literature.

---

## Features

- 🔒 **Secure by default**: All LLM calls and code execution are offline via Ollama
- 📊 **Reproducible analysis**: Each run generates traceable results with proper citations
- 🧑‍💻 **Sandboxed execution**: Code execution isolated to dedicated workspace directory
- 📚 **Hybrid RAG system**: Vector search + keyword search + knowledge graph for comprehensive literature retrieval
- 🖥️ **Economist-native UX**: Streamlit interface with chat, file upload, and automatic visualization display
- 🔍 **Multiple search methods**: Semantic similarity, hybrid search, and entity relationship queries
- 🏗️ **Mock mode development**: RAG system works without database setup using realistic sample data

---

## Architecture

### Core Components

- `app.py`: Main Streamlit application with chat interface and file upload
- `agents.py`: Contains `TrackableAssistantAgent` class and multi-agent team setup
- `hybrid_rag_agent/`: Complete RAG system with Pydantic AI integration
  - `agent.py`: Main RAG agent with search capabilities
  - `ingestion/`: Document processing and knowledge graph building
  - `utils/`: Database utilities and provider configurations
  - `cli.py`: Interactive CLI interface for RAG queries
- `our-attempt/`: Alternative simplified implementation using direct tool integration

### Two Implementation Approaches

**Main Implementation** (`app.py` + `agents.py`):
- Full multi-agent system with RoundRobinGroupChat
- Integrated hybrid RAG agent with literature search
- TrackableAssistantAgent for Streamlit response tracking
- Comprehensive error handling and Windows compatibility

**Alternative Implementation** (`our-attempt/`):
- Simplified direct tool integration approach
- Focuses on core economist analysis without RAG complexity
- Lighter dependencies and faster startup
- Good for development and testing core analysis features

---

## Getting Started

### 1. Install Ollama
Download from [ollama.com](https://ollama.com). After install, run:

```bash
ollama pull llama3.1
ollama serve
```

### 2. Setup and Installation

```bash
# Clone the repository
git clone <repository-url>
cd Economist-Agent

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application

**Main Application (Full RAG Integration):**
```bash
streamlit run app.py
```

**Alternative Simplified Version:**
```bash
streamlit run our-attempt/app.py
```

**Interactive RAG CLI (Mock Mode):**
```bash
cd hybrid_rag_agent
python cli.py
```

---

## Usage

### File Upload and Analysis
1. Upload CSV/TSV files via the Streamlit sidebar
2. Files are automatically saved to the `code_executor/` directory
3. Ask questions about your data in natural language
4. The system will:
   - Search relevant literature via RAG
   - Propose analysis methodology
   - Execute Python code in a sandboxed environment
   - Generate and display visualizations automatically

### Available Models
- `llama3.1:8b` (default)
- `qwen2.5-coder`
- `qwen3:8b`

### RAG System Features
- **Vector Search**: Semantic similarity matching using embeddings
- **Hybrid Search**: Combines semantic + keyword search with PostgreSQL TSVector
- **Knowledge Graph**: Entity relationships via Neo4j/Graphiti integration
- **Mock Mode**: Works without database setup using realistic sample data

---

## Development

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

### Project Structure
```
Economist-Agent/
├── app.py                     # Main Streamlit application
├── agents.py                  # Multi-agent system implementation
├── requirements.txt           # Combined dependencies
├── hybrid_rag_agent/          # Complete RAG system
│   ├── agent.py              # Main RAG agent
│   ├── cli.py                # Interactive CLI
│   ├── ingestion/            # Document processing
│   ├── utils/                # Database utilities
│   └── tests/                # Test suite
├── our-attempt/              # Simplified implementation
│   ├── app.py               # Alternative Streamlit app
│   ├── agents.py            # Direct tool integration
│   └── tools.py             # Economic analysis tools
└── code_executor/            # Sandboxed execution workspace
```

---

## Key Features

### Agent System Messages
- **DataAnalystAgent**: Plans analysis steps, writes complete Python code, saves visualizations as PNG
- **CodeExecutorAgent**: Executes code and provides concise feedback on success/failure
- **RAG Retriever Agent**: Searches literature using multiple methods and provides context citations

### File Handling
- Uploaded datasets are automatically saved to `code_executor/` directory
- All code execution is sandboxed within this directory
- Generated images must be saved as PNG format for proper display
- RAG documents can be ingested via the hybrid_rag_agent ingestion pipeline

### Security & Privacy
- All LLM calls and code execution are offline via Ollama
- No API keys or external data leakage
- Code execution isolated to dedicated workspace
- Read-only dataset access with restricted permissions

---

## Windows Compatibility

The application includes Windows-specific asyncio event loop policy configuration for proper operation on Windows systems.

---

## License

[Include your license information here]

---

## Contributing

[Include contribution guidelines here]
