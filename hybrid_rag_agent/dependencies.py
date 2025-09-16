"""Dependencies for Hybrid RAG Agent using Weaviate and Neo4j."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import asyncio
import warnings
import os
import logging

from utils.weaviate_utils import WeaviateClient
from utils.graph_utils import GraphitiClient, search_knowledge_graph, get_entity_relationships
from utils.providers import get_embedding_client, get_embedding_model
from settings import load_settings

logger = logging.getLogger(__name__)

# Sample data for mock mode - Federal Reserve Economic Research
SAMPLE_VECTOR_RESULTS = [
    {
        "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
        "document_id": "doc-fed-q4-2024",
        "content": "The Federal Open Market Committee (FOMC) decided to raise the federal funds rate by 25 basis points to 5.50-5.75% in Q4 2024, citing persistent inflationary pressures in the services sector and robust labor market conditions. This decision reflects the Committee's commitment to achieving its dual mandate of price stability and maximum employment.",
        "similarity": 0.95,
        "metadata": {"page": 1, "section": "executive_summary"},
        "document_title": "Federal Reserve Interest Rate Decision Q4 2024",
        "document_source": "Federal Reserve Interest Rate Decision Q4 2024.pdf"
    },
    {
        "chunk_id": "550e8400-e29b-41d4-a716-446655440001",
        "document_id": "doc-fed-q4-2024",
        "content": "The Committee expects that the cumulative effects of monetary policy tightening will continue to slow economic activity and reduce inflation toward the 2% target. Recent data indicates core PCE inflation remains elevated at 3.7%, though showing signs of moderation in goods prices while services inflation persists.",
        "similarity": 0.92,
        "metadata": {"page": 2, "section": "inflation_outlook"},
        "document_title": "Federal Reserve Interest Rate Decision Q4 2024",
        "document_source": "Federal Reserve Interest Rate Decision Q4 2024.pdf"
    },
    {
        "chunk_id": "550e8400-e29b-41d4-a716-446655440002",
        "document_id": "doc-fed-q4-2024",
        "content": "Labor market conditions remain tight with unemployment at 3.9% and job openings still elevated relative to historical norms. The Committee will continue to monitor employment data closely as policy transmission effects through credit markets may affect hiring and wage growth in coming quarters.",
        "similarity": 0.89,
        "metadata": {"page": 3, "section": "labor_market"},
        "document_title": "Federal Reserve Interest Rate Decision Q4 2024",
        "document_source": "Federal Reserve Interest Rate Decision Q4 2024.pdf"
    },
    {
        "chunk_id": "550e8400-e29b-41d4-a716-446655440003",
        "document_id": "doc-monetary-policy-2024",
        "content": "Financial conditions have tightened considerably since the beginning of the tightening cycle, with corporate bond spreads widening and equity valuations declining from peak levels. Bank lending standards have tightened for both commercial and consumer loans, which should contribute to slower credit growth.",
        "similarity": 0.85,
        "metadata": {"page": 15, "section": "financial_conditions"},
        "document_title": "Monetary Policy Transmission Mechanisms 2024",
        "document_source": "monetary_policy_2024.pdf"
    }
]

SAMPLE_GRAPH_RESULTS = [
    {
        "fact": "Federal Reserve RAISED federal_funds_rate TO 5.50-5.75% IN Q4_2024 DUE_TO persistent_inflation",
        "uuid": "fact-550e8400-e29b-41d4-a716-446655440000",
        "valid_at": "2024-10-01T00:00:00Z",
        "invalid_at": None,
        "source_node_uuid": "node-federal-reserve"
    },
    {
        "fact": "core_PCE_inflation MEASURED_AT 3.7% ABOVE federal_reserve_target OF 2%",
        "uuid": "fact-550e8400-e29b-41d4-a716-446655440001",
        "valid_at": "2024-10-01T00:00:00Z",
        "invalid_at": None,
        "source_node_uuid": "node-inflation-metrics"
    },
    {
        "fact": "unemployment_rate DECREASED_TO 3.9% INDICATING tight_labor_market",
        "uuid": "fact-550e8400-e29b-41d4-a716-446655440002",
        "valid_at": "2024-10-01T00:00:00Z",
        "invalid_at": None,
        "source_node_uuid": "node-labor-market"
    },
    {
        "fact": "financial_conditions TIGHTENED due_to higher_interest_rates AFFECTING credit_markets",
        "uuid": "fact-550e8400-e29b-41d4-a716-446655440003",
        "valid_at": "2024-10-01T00:00:00Z",
        "invalid_at": None,
        "source_node_uuid": "node-financial-conditions"
    }
]

SAMPLE_DOCUMENTS = [
    {
        "id": "doc-fed-q4-2024",
        "title": "Federal Reserve Interest Rate Decision Q4 2024",
        "source": "Federal Reserve Interest Rate Decision Q4 2024.pdf",
        "metadata": {"author": "Federal Open Market Committee", "pages": 25, "category": "monetary_policy"},
        "created_at": "2024-10-15T10:00:00Z",
        "updated_at": "2024-10-15T10:00:00Z",
        "chunk_count": 18
    },
    {
        "id": "doc-monetary-policy-2024",
        "title": "Monetary Policy Transmission Mechanisms 2024",
        "source": "monetary_policy_2024.pdf",
        "metadata": {"author": "Federal Reserve Economic Research", "pages": 47, "category": "economic_analysis"},
        "created_at": "2024-09-20T14:30:00Z",
        "updated_at": "2024-09-20T14:30:00Z",
        "chunk_count": 32
    }
]

@dataclass
class MockSearchDependencies:
    """Mock dependencies for development without real database credentials."""
    use_mocks: bool = True
    mock_delay: float = 0.1
    
    async def mock_vector_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.mock_delay)
        return SAMPLE_VECTOR_RESULTS[:limit]
    
    async def mock_hybrid_search(self, query: str, limit: int = 10, text_weight: float = 0.3) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.mock_delay)
        results = []
        for result in SAMPLE_VECTOR_RESULTS[:limit]:
            result_copy = result.copy()
            result_copy["combined_score"] = result["similarity"] * (1 - text_weight) + 0.8 * text_weight
            result_copy["vector_similarity"] = result["similarity"]
            result_copy["text_similarity"] = 0.8
            results.append(result_copy)
        return results
    
    async def mock_graph_search(self, query: str, include_timeline: bool = False) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.mock_delay)
        results = SAMPLE_GRAPH_RESULTS.copy()
        if include_timeline:
            for result in results:
                result["timeline_context"] = "Historical fact from knowledge graph"
        return results

    async def mock_keyword_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.mock_delay)
        # Simulate keyword matching based on query terms
        results = []
        query_lower = query.lower()
        for result in SAMPLE_VECTOR_RESULTS[:limit]:
            if any(word in result["content"].lower() for word in query_lower.split()):
                result_copy = result.copy()
                result_copy["keyword_score"] = 0.8
                results.append(result_copy)
        return results
    
    async def mock_get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        await asyncio.sleep(self.mock_delay)
        return next((doc for doc in SAMPLE_DOCUMENTS if doc["id"] == document_id), None)
    
    async def mock_list_documents(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.mock_delay)
        return SAMPLE_DOCUMENTS[offset:offset + limit]

@dataclass
class SearchDependencies:
    """Production dependencies for the Hybrid RAG Agent using Weaviate and Neo4j."""
    weaviate_client: Optional[WeaviateClient] = None
    graph_client: Optional[GraphitiClient] = None
    embedding_client: Optional[Any] = None
    search_preferences: Dict[str, Any] = field(default_factory=dict)
    use_mocks: bool = False
    _mock_deps: Optional[MockSearchDependencies] = field(default=None, init=False)
    _initialized: bool = field(default=False, init=False)

    def __post_init__(self):
        """Initialize dependencies."""
        settings = load_settings()

        # Determine if we should use mocks
        if settings.should_use_mocks():
            self.use_mocks = True
            self._mock_deps = MockSearchDependencies()
            logger.info("Initialized SearchDependencies in MOCK mode")
        else:
            logger.info("Initialized SearchDependencies for production mode")

    async def initialize(self):
        """Initialize Weaviate and graph connections."""
        if self._initialized:
            return

        if self.use_mocks:
            logger.info("Skipping database initialization (mock mode)")
            self._initialized = True
            return

        try:
            # Initialize Weaviate client
            if not self.weaviate_client:
                settings = load_settings()
                self.weaviate_client = WeaviateClient(
                    url=settings.weaviate_url,
                    api_key=settings.weaviate_api_key
                )
                await self.weaviate_client.initialize()
                logger.info("Weaviate client initialized")

            # Initialize graph client
            if not self.graph_client:
                try:
                    self.graph_client = GraphitiClient()
                    await self.graph_client.initialize()
                    logger.info("Graph client initialized")
                except Exception as e:
                    logger.warning(f"Graph client initialization failed: {e}. Will use empty results for graph searches.")
                    self.graph_client = None

            # Initialize embedding client
            if not self.embedding_client:
                try:
                    self.embedding_client = get_embedding_client()
                    logger.info("Embedding client initialized")
                except Exception as e:
                    logger.warning(f"Embedding client initialization failed: {e}")
                    self.embedding_client = None

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            # Fallback to mock mode
            self.use_mocks = True
            self._mock_deps = MockSearchDependencies()
            logger.warning("Falling back to mock mode due to initialization failure")

    async def close(self):
        """Close all connections."""
        if self.weaviate_client:
            await self.weaviate_client.close()
            self.weaviate_client = None

        if self.graph_client:
            await self.graph_client.close()
            self.graph_client = None
        
        self._initialized = False
        logger.info("SearchDependencies closed")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text query."""
        if self.use_mocks:
            # Return mock embedding (1536 dimensions)
            import random
            return [random.random() for _ in range(1536)]
        
        if not self.embedding_client:
            logger.error("Embedding client not available")
            return None
        
        try:
            model = get_embedding_model()
            response = await self.embedding_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def vector_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform vector similarity search using Weaviate or mocks."""
        await self.initialize()

        if self.use_mocks or not self.weaviate_client:
            return await self._mock_deps.mock_vector_search(query, limit)

        try:
            return await self.weaviate_client.vector_search(query, limit)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def hybrid_search(self, query: str, limit: int = 10, text_weight: float = 0.3) -> List[Dict[str, Any]]:
        """Perform hybrid search using Weaviate or mocks."""
        await self.initialize()

        if self.use_mocks or not self.weaviate_client:
            return await self._mock_deps.mock_hybrid_search(query, limit, text_weight)

        try:
            # Convert text_weight to alpha (inverse relationship)
            alpha = 1.0 - text_weight
            return await self.weaviate_client.hybrid_search(query, limit, alpha)
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def keyword_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform keyword search using Weaviate or mocks."""
        await self.initialize()

        if self.use_mocks or not self.weaviate_client:
            return await self._mock_deps.mock_keyword_search(query, limit)

        try:
            return await self.weaviate_client.keyword_search(query, limit)
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    async def graph_search(self, query: str, include_timeline: bool = False) -> List[Dict[str, Any]]:
        """Search knowledge graph using real Graphiti or mocks."""
        await self.initialize()
        
        if self.use_mocks or not self.graph_client:
            if self._mock_deps:
                return await self._mock_deps.mock_graph_search(query, include_timeline)
            return []
        
        try:
            # Use real graph search
            results = await search_knowledge_graph(query)
            
            # Add timeline context if requested
            if include_timeline:
                for result in results:
                    result["timeline_context"] = "Temporal fact from Graphiti knowledge graph"
            
            return results
            
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document using real database or mocks."""
        await self.initialize()
        
        if self.use_mocks:
            return await self._mock_deps.mock_get_document(document_id)
        
        try:
            # Use real database function
            return await db_get_document(document_id)
            
        except Exception as e:
            logger.error(f"Get document failed: {e}")
            return None
    
    async def list_documents(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List documents using real database or mocks."""
        await self.initialize()
        
        if self.use_mocks:
            return await self._mock_deps.mock_list_documents(limit, offset)
        
        try:
            # Use real database function
            return await db_list_documents(limit, offset)
            
        except Exception as e:
            logger.error(f"List documents failed: {e}")
            return []
    
    async def comprehensive_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Perform comprehensive search using both vector and graph methods."""
        await self.initialize()
        
        if self.use_mocks:
            vector_results = await self._mock_deps.mock_vector_search(query, limit)
            graph_results = await self._mock_deps.mock_graph_search(query)
            return {
                "vector_results": vector_results,
                "graph_results": graph_results,
                "total_results": len(vector_results) + len(graph_results)
            }
        
        # Execute vector and graph search in parallel
        vector_task = asyncio.create_task(self.vector_search(query, limit))
        graph_task = asyncio.create_task(self.graph_search(query))
        
        try:
            vector_results, graph_results = await asyncio.gather(
                vector_task, graph_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(vector_results, Exception):
                logger.error(f"Vector search failed in comprehensive search: {vector_results}")
                vector_results = []
            
            if isinstance(graph_results, Exception):
                logger.error(f"Graph search failed in comprehensive search: {graph_results}")
                graph_results = []
            
            return {
                "vector_results": vector_results,
                "graph_results": graph_results,
                "total_results": len(vector_results) + len(graph_results)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive search failed: {e}")
            return {
                "vector_results": [],
                "graph_results": [],
                "total_results": 0
            }

async def create_search_dependencies(use_mocks: Optional[bool] = None) -> SearchDependencies:
    """Factory function to create properly initialized SearchDependencies."""
    if use_mocks is None:
        settings = load_settings()
        use_mocks = settings.should_use_mocks()
    
    deps = SearchDependencies(use_mocks=use_mocks)
    await deps.initialize()
    return deps