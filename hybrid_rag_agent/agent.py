"""Hybrid RAG Agent with vector, keyword, and graph search capabilities."""

from pydantic_ai import Agent, RunContext
from typing import Optional, List, Dict, Any
import warnings

from providers import get_llm_model
from dependencies import SearchDependencies
from orchestrator import QueryOrchestrator

# System prompt for enhanced hybrid RAG capabilities
SYSTEM_PROMPT = """You are an intelligent research assistant with access to an advanced Hybrid RAG (Retrieval-Augmented Generation) system. You have access to multiple specialized search tools:

**Available Search Methods:**
1. **Vector Search**: Semantic similarity using Weaviate - best for conceptual queries
2. **Hybrid Search**: Balanced semantic + keyword search - best for mixed queries
3. **Keyword Search**: Exact text matching - best for specific terms, dates, numbers
4. **Graph Search**: Entity relationships via Neo4j - best for relationship queries
5. **Comprehensive Search**: Intelligent auto-routing across all databases

**Smart Routing Guidelines:**
- Use `comprehensive_search` for most queries - it automatically selects the best approach
- Use specific search types when you need to force a particular strategy
- For entity relationships or "who knows who" type queries → graph search
- For conceptual explanations → vector search
- For exact quotes or specific data → keyword search
- For balanced analysis → hybrid search

**Response Requirements:**
- Always cite sources with document titles and database used
- Show routing decisions when using comprehensive search
- Combine insights from multiple sources when available
- Be transparent about search limitations or conflicts
- Format responses clearly with proper attribution

Your goal is to provide accurate, well-sourced answers by intelligently leveraging the most appropriate search strategy for each query."""

# Create the hybrid RAG agent
hybrid_rag_agent = Agent(
    get_llm_model(),
    deps_type=SearchDependencies,
    system_prompt=SYSTEM_PROMPT,
)

@hybrid_rag_agent.tool
async def hybrid_search(
    ctx: RunContext[SearchDependencies], 
    query: str, 
    limit: int = 10, 
    text_weight: float = 0.3
) -> str:
    """
    Primary search combining vector similarity and keyword matching.
    
    Args:
        query: The search query
        limit: Number of results to return (1-20)
        text_weight: Balance between semantic (0.0) and keyword (1.0) search
    
    Returns:
        Formatted search results with sources
    """
    try:
        # Validate parameters
        limit = max(1, min(limit, 20))
        text_weight = max(0.0, min(text_weight, 1.0))
        
        results = await ctx.deps.hybrid_search(query, limit, text_weight)
        
        if not results:
            return "No results found for the query."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            source_info = f"Source: {result.get('document_source', 'Unknown')} - {result.get('document_title', 'Untitled')}"
            
            if 'combined_score' in result:
                score_info = f"Relevance: {result['combined_score']:.2f} (Vector: {result.get('vector_similarity', 0):.2f}, Text: {result.get('text_similarity', 0):.2f})"
            else:
                score_info = f"Similarity: {result.get('similarity', 0):.2f}"
            
            chunk = f"{i}. {result['content']}\n   {source_info}\n   {score_info}\n"
            formatted_results.append(chunk)
        
        return f"Found {len(results)} results:\n\n" + "\n".join(formatted_results)
    
    except Exception as e:
        return f"Search failed: {str(e)}. Please try a different query."

@hybrid_rag_agent.tool
async def graph_search(
    ctx: RunContext[SearchDependencies],
    query: str,
    include_timeline: bool = False
) -> str:
    """
    Search knowledge graph for entity relationships and facts.
    
    Args:
        query: Entity or relationship query
        include_timeline: Include temporal information
    
    Returns:
        Formatted graph search results
    """
    try:
        results = await ctx.deps.graph_search(query, include_timeline)
        
        if not results:
            return "No graph relationships found for the query."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            fact = result.get('fact', 'Unknown fact')
            valid_at = result.get('valid_at', 'Unknown time')
            
            timeline_info = ""
            if include_timeline and 'timeline_context' in result:
                timeline_info = f" ({result['timeline_context']})"
            
            formatted_results.append(f"{i}. {fact} (Valid from: {valid_at}){timeline_info}")
        
        return f"Found {len(results)} graph relationships:\n\n" + "\n".join(formatted_results)
    
    except Exception as e:
        return f"Graph search failed: {str(e)}. Falling back to empty results."

@hybrid_rag_agent.tool
async def vector_search(
    ctx: RunContext[SearchDependencies],
    query: str,
    limit: int = 10
) -> str:
    """
    Pure vector similarity search using Weaviate.

    Args:
        query: The search query
        limit: Number of results to return (1-20)

    Returns:
        Formatted vector search results with similarity scores
    """
    try:
        limit = max(1, min(limit, 20))
        results = await ctx.deps.vector_search(query, limit)

        if not results:
            return "No vector search results found for the query."

        formatted_results = []
        for i, result in enumerate(results, 1):
            source_info = f"Source: {result.get('document_source', 'Unknown')} - {result.get('document_title', 'Untitled')}"
            score_info = f"Similarity: {result.get('similarity', result.get('score', 0)):.3f}"

            chunk = f"{i}. {result['content']}\n   {source_info}\n   {score_info}\n"
            formatted_results.append(chunk)

        return f"Vector search found {len(results)} results:\n\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"Vector search failed: {str(e)}. Please try a different query."

@hybrid_rag_agent.tool
async def keyword_search(
    ctx: RunContext[SearchDependencies],
    query: str,
    limit: int = 10
) -> str:
    """
    BM25 keyword search using Weaviate.

    Args:
        query: The search query
        limit: Number of results to return (1-20)

    Returns:
        Formatted keyword search results with BM25 scores
    """
    try:
        limit = max(1, min(limit, 20))
        results = await ctx.deps.keyword_search(query, limit)

        if not results:
            return "No keyword search results found for the query."

        formatted_results = []
        for i, result in enumerate(results, 1):
            source_info = f"Source: {result.get('document_source', 'Unknown')} - {result.get('document_title', 'Untitled')}"
            score_info = f"BM25 Score: {result.get('score', 0):.3f}"

            chunk = f"{i}. {result['content']}\n   {source_info}\n   {score_info}\n"
            formatted_results.append(chunk)

        return f"Keyword search found {len(results)} results:\n\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"Keyword search failed: {str(e)}. Please try a different query."

@hybrid_rag_agent.tool
async def intelligent_search(
    ctx: RunContext[SearchDependencies],
    query: str,
    max_results: int = 15
) -> str:
    """
    Intelligent search using automatic query routing across all databases.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        Formatted results with routing explanation and sources
    """
    try:
        max_results = max(1, min(max_results, 25))

        # Create orchestrator
        orchestrator = QueryOrchestrator(ctx.deps)

        # Process query with intelligent routing
        result = await orchestrator.process_query(query, max_results=max_results)

        if not result.merged_results:
            return f"Intelligent search found no results for: '{query}'"

        # Format routing information
        routing_info = []
        routing_info.append(f"**Query Routing Decision:**")
        routing_info.append(f"- Databases queried: {', '.join(result.databases_queried)}")
        routing_info.append(f"- Processing time: {result.processing_time:.3f}s")

        if result.routing_decision:
            confidence = result.routing_decision.confidence_scores
            routing_info.append(f"- Routing confidence: Vector={confidence.get('vector', 0):.2f}, Hybrid={confidence.get('hybrid', 0):.2f}, Keyword={confidence.get('keyword', 0):.2f}, Graph={confidence.get('graph', 0):.2f}")
            routing_info.append(f"- Reasoning: {result.routing_decision.reasoning}")

        # Format search results
        formatted_results = []
        for i, search_result in enumerate(result.merged_results, 1):
            source_db = search_result.source_database
            search_type = search_result.search_type
            source_info = f"Source: {search_result.document_source} - {search_result.document_title}"
            score_info = f"Score: {search_result.score:.3f}"
            db_info = f"Database: {source_db} ({search_type})"

            formatted_results.append(
                f"{i}. {search_result.content}\n"
                f"   {source_info}\n"
                f"   {score_info} | {db_info}\n"
            )

        # Combine everything
        output = "\n".join(routing_info) + "\n\n"
        output += f"**Search Results ({len(result.merged_results)} found):**\n\n"
        output += "\n".join(formatted_results)

        if result.errors:
            output += f"\n\n**Warnings:** {'; '.join(result.errors)}"

        return output

    except Exception as e:
        return f"Intelligent search failed: {str(e)}. Please try individual search methods."

@hybrid_rag_agent.tool
async def comprehensive_search(
    ctx: RunContext[SearchDependencies],
    query: str,
    limit: int = 10
) -> str:
    """
    Execute parallel vector and graph search for complex queries.
    
    Args:
        query: The search query
        limit: Maximum results per search type
    
    Returns:
        Combined results from both vector and graph search
    """
    try:
        limit = max(1, min(limit, 20))
        results = await ctx.deps.comprehensive_search(query, limit)
        
        output = []
        
        # Add vector results
        vector_results = results.get('vector_results', [])
        if vector_results:
            output.append(f"**Document Search Results ({len(vector_results)} found):**\n")
            for i, result in enumerate(vector_results, 1):
                source_info = f"Source: {result.get('document_source', 'Unknown')} - {result.get('document_title', 'Untitled')}"
                similarity = f"Similarity: {result.get('similarity', 0):.2f}"
                output.append(f"{i}. {result['content']}\n   {source_info} | {similarity}\n")
        
        # Add graph results
        graph_results = results.get('graph_results', [])
        if graph_results:
            output.append(f"\n**Knowledge Graph Results ({len(graph_results)} found):**\n")
            for i, result in enumerate(graph_results, 1):
                fact = result.get('fact', 'Unknown fact')
                valid_at = result.get('valid_at', 'Unknown time')
                output.append(f"{i}. {fact} (Valid from: {valid_at})")
        
        if not output:
            return "No results found from comprehensive search."
        
        total = results.get('total_results', 0)
        return f"Comprehensive search found {total} total results:\n\n" + "\n".join(output)
    
    except Exception as e:
        return f"Comprehensive search failed: {str(e)}. Please try individual search methods."

@hybrid_rag_agent.tool
async def get_document(
    ctx: RunContext[SearchDependencies],
    document_id: str
) -> str:
    """
    Retrieve complete document content by ID.
    
    Args:
        document_id: UUID of the document
    
    Returns:
        Document details and metadata
    """
    try:
        document = await ctx.deps.get_document(document_id)
        
        if not document:
            return f"Document with ID '{document_id}' not found."
        
        metadata = document.get('metadata', {})
        metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
        
        return (
            f"**Document: {document.get('title', 'Untitled')}**\n"
            f"Source: {document.get('source', 'Unknown')}\n"
            f"ID: {document.get('id')}\n"
            f"Chunks: {document.get('chunk_count', 0)}\n"
            f"Metadata: {metadata_str}\n"
            f"Created: {document.get('created_at', 'Unknown')}\n"
            f"Updated: {document.get('updated_at', 'Unknown')}"
        )
    
    except Exception as e:
        return f"Failed to retrieve document: {str(e)}"

@hybrid_rag_agent.tool
async def list_documents(
    ctx: RunContext[SearchDependencies],
    limit: int = 20,
    offset: int = 0
) -> str:
    """
    Browse available documents in the knowledge base.
    
    Args:
        limit: Number of documents to list
        offset: Pagination offset
    
    Returns:
        List of available documents with basic information
    """
    try:
        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        
        documents = await ctx.deps.list_documents(limit, offset)
        
        if not documents:
            return "No documents found in the knowledge base."
        
        output = [f"Found {len(documents)} documents:\n"]
        
        for i, doc in enumerate(documents, offset + 1):
            title = doc.get('title', 'Untitled')
            source = doc.get('source', 'Unknown source')
            chunk_count = doc.get('chunk_count', 0)
            doc_id = doc.get('id', 'unknown-id')
            
            output.append(f"{i}. **{title}** ({source})")
            output.append(f"   ID: {doc_id} | Chunks: {chunk_count}\n")
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Failed to list documents: {str(e)}"

# Agent run helpers for easy testing
def run_hybrid_rag_sync(query: str, use_mocks: Optional[bool] = None) -> str:
    """Synchronous helper to run the hybrid RAG agent."""
    import asyncio
    
    async def _run():
        from dependencies import create_search_dependencies
        deps = await create_search_dependencies(use_mocks=use_mocks)
        try:
            result = await hybrid_rag_agent.run(query, deps=deps)
            return result.data
        finally:
            await deps.close()
    
    return asyncio.run(_run())

async def run_hybrid_rag_async(query: str, use_mocks: Optional[bool] = None) -> str:
    """Asynchronous helper to run the hybrid RAG agent."""
    from dependencies import create_search_dependencies
    deps = await create_search_dependencies(use_mocks=use_mocks)
    try:
        result = await hybrid_rag_agent.run(query, deps=deps)
        return result.data
    finally:
        await deps.close()