# Economist Agent 📈🏦💰

An interactive **economist research assistant** built with **Streamlit** and **Autogen AgentChat**, running locally for maximum data security.  

The system combines multiple agents:
- **Data Analyst Agent**: proposes specifications, checks identification assumptions, explains methods.  
- **Code Executor Agent**: runs Python analysis in a sandbox (DuckDB) and returns only safe artifacts (plots, tables).  
- **Retriever Agent**: provides literature and documentation lookups via local RAG, allowing the economist to have access to relevant policies and research whilst still running locally.

Models are served locally via **[Ollama](https://ollama.com/)** — no API keys, no external data leakage.

---

## Features

- 🔒 **Secure by default**: all LLM calls and code execution are offline.  
- 📊 **Reproducible analysis**: each run generates a manifest (dataset hash, code, seeds, library versions).  
- 🧑‍💻 **Sandboxed execution**: Docker-isolated runner with read-only datasets and restricted permissions.  
- 📚 **Domain memory (RAG)**: ingest PDFs, docs, and notes so the agent can be an expert within a field.  
- 🖥️ **Economist-native UX**: Streamlit interface with chat, pre-analysis plan, results tabs, and traceable citations.

---

## Getting Started

### 1. Install Ollama
Download from [ollama.com](https://ollama.com). After install, run:

```bash
ollama pull llama3.1
ollama serve
