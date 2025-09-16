# Tool Specifications for Hybrid RAG Agent

## Essential Tools (5 Core Functions)

### 1. `hybrid_search`
**Purpose**: Primary search combining vector similarity and keyword matching
**Parameters**:
- `query` (str): The search query
- `limit` (int, default=10): Number of results to return
- `text_weight` (float, default=0.3): Balance between semantic (0.0) and keyword (1.0) search

**Error Handling**: Return empty results with warning message on database connection failure

---

### 2. `graph_search`
**Purpose**: Search knowledge graph for entity relationships and facts
**Parameters**:
- `query` (str): Entity or relationship query
- `include_timeline` (bool, default=False): Include temporal information

**Error Handling**: Gracefully fallback to empty results if graph database unavailable

---

### 3. `comprehensive_search`
**Purpose**: Execute parallel vector and graph search for complex queries
**Parameters**:
- `query` (str): The search query
- `limit` (int, default=10): Maximum results per search type

**Error Handling**: Return partial results if one search method fails

---

### 4. `get_document`
**Purpose**: Retrieve complete document content by ID
**Parameters**:
- `document_id` (str): UUID of the document

**Error Handling**: Return None with error message if document not found

---

### 5. `list_documents`
**Purpose**: Browse available documents in the knowledge base
**Parameters**:
- `limit` (int, default=20): Number of documents to list
- `offset` (int, default=0): Pagination offset

**Error Handling**: Return empty list if database unavailable

## Tool Design Principles

- **Single Purpose**: Each tool has one clear responsibility
- **Minimal Parameters**: 1-4 parameters per tool for simplicity
- **Graceful Degradation**: All tools handle failures without crashing
- **Type Safety**: All parameters have clear types and defaults where appropriate