# Hybrid RAG Agent Demo Setup

This guide will help you set up the Hybrid RAG Agent for your demo.

## Quick Start (Mock Mode - No Setup Required)

For the fastest demo setup, you can run in mock mode:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (will automatically use mock data)
streamlit run app.py
```

The system will display a warning about running in mock mode and use realistic sample data.

## Full Setup (With Real Databases)

### 1. Start the Databases

```bash
# Start Weaviate and Neo4j
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your OpenAI API key
nano .env  # or your preferred editor
```

**Required:** Set your OpenAI API key in the `.env` file:
```env
OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app.py
```

## Demo Workflow

### Sample Demo Queries

Try these queries to showcase the routing system:

1. **Conceptual Query (Vector Search):**
   ```
   "Explain how monetary policy affects economic growth"
   ```

2. **Specific Data Query (Keyword Search):**
   ```
   "Find reports from Q4 2024 with GDP growth rates"
   ```

3. **Relationship Query (Graph Search):**
   ```
   "What companies are connected to Apple Inc?"
   ```

4. **Complex Query (Hybrid/Multiple Databases):**
   ```
   "How do interest rate changes affect tech company valuations?"
   ```

### Demo Features to Highlight

1. **Intelligent Routing Visualization**
   - Show the routing decision in the sidebar
   - Explain why each database was selected

2. **Multiple Search Methods**
   - Vector: Semantic similarity
   - Hybrid: Balanced approach
   - Keyword: Exact matching
   - Graph: Entity relationships

3. **Source Attribution**
   - Each result shows which database it came from
   - Document titles and sources are displayed

4. **Performance Metrics**
   - Query processing time
   - Number of results from each source
   - Confidence scores

## Troubleshooting

### Common Issues

1. **"No results found"**
   - Check if databases are running: `docker-compose ps`
   - Verify .env configuration
   - Try mock mode for demo

2. **Connection errors**
   - Restart databases: `docker-compose restart`
   - Check ports aren't in use: `netstat -an | grep :8080`

3. **Weaviate schema errors**
   - Reset Weaviate: `docker-compose down weaviate && docker-compose up -d weaviate`

### Database URLs

- **Weaviate**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474 (username: neo4j, password: password123)

## Adding Demo Data

### Upload Documents

1. Use the sidebar file upload in Streamlit
2. Upload economic reports, research papers, or any text documents
3. Documents are automatically processed and stored in both databases

### Or Use the CLI

```bash
cd hybrid_rag_agent
python -m ingestion.ingest --documents ../documents --clean
```

## Demo Script

### Opening (2 minutes)
1. "This is a Hybrid RAG Agent that intelligently routes queries to the best database"
2. Show the architecture diagram
3. Explain the two databases: Weaviate (vectors) + Neo4j (relationships)

### Core Demo (5 minutes)
1. **Smart Routing**: Start with intelligent_search tool
2. **Show routing decision**: Point out sidebar visualization
3. **Try different query types**: Show how routing changes
4. **Performance**: Highlight speed and result quality

### Advanced Features (3 minutes)
1. **Manual override**: Show individual search tools
2. **Source attribution**: Point out database sources
3. **Result merging**: Show deduplication
4. **Error handling**: Demo graceful fallbacks

### Q&A (5 minutes)
- Technical questions about implementation
- Use cases for different industries
- Scaling and production considerations

## Production Notes

- For production, use Weaviate Cloud and Neo4j AuraDB
- Set proper authentication and SSL
- Monitor query performance and costs
- Consider caching for frequently accessed data

## Support

If you encounter issues during the demo:
1. Check the console for error messages
2. Try refreshing the Streamlit app
3. Restart the Docker containers if needed
4. Fall back to mock mode for a guaranteed working demo