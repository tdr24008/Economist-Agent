"""
Weaviate client utilities for vector and hybrid search.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
# Lazy import of weaviate to avoid slow startup
weaviate = None
Auth = None
Configure = None
MetadataQuery = None

def _import_weaviate():
    """Lazy import of weaviate modules."""
    global weaviate, Auth, Configure, MetadataQuery
    if weaviate is None:
        import weaviate as _weaviate
        from weaviate.classes.init import Auth as _Auth
        from weaviate.classes.config import Configure as _Configure
        from weaviate.classes.query import MetadataQuery as _MetadataQuery
        weaviate = _weaviate
        Auth = _Auth
        Configure = _Configure
        MetadataQuery = _MetadataQuery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WeaviateClient:
    """Manages Weaviate operations for vector and hybrid search."""

    def __init__(self, url: str = None, api_key: Optional[str] = None):
        """
        Initialize Weaviate client.

        Args:
            url: Weaviate instance URL
            api_key: API key for cloud instances
        """
        self.url = url or os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.api_key = api_key or os.getenv("WEAVIATE_API_KEY")
        self.collection_name = "EconomistDocuments"
        self.client = None
        self._initialized = False

    async def initialize(self):
        """Initialize Weaviate client and create collection if needed."""
        if self._initialized:
            return

        # Import weaviate modules only when needed
        _import_weaviate()

        try:
            # Connect to Weaviate
            if self.url.startswith("https://") and self.api_key:
                # Cloud instance
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.url,
                    auth_credentials=Auth.api_key(self.api_key)
                )
            else:
                # Local instance
                host = self.url.replace("http://", "").replace("https://", "").split(":")[0]
                port = int(self.url.split(":")[-1]) if ":" in self.url else 8080
                self.client = weaviate.connect_to_local(
                    host=host,
                    port=port
                )

            # Verify connection
            if self.client.is_ready():
                logger.info("Weaviate client connected successfully")
                await self._create_collection_if_not_exists()
                self._initialized = True
            else:
                raise ConnectionError("Weaviate client not ready")

        except Exception as e:
            logger.error(f"Failed to initialize Weaviate client: {e}")
            # Fall back to mock mode
            self.client = None
            self._initialized = False

    async def _create_collection_if_not_exists(self):
        """Create the documents collection if it doesn't exist."""
        try:
            # Check if collection exists
            if self.client.collections.exists(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' already exists")
                return

            # Create collection with schema
            self.client.collections.create(
                name=self.collection_name,
                properties=[
                    _build_property("content", "TEXT", "Main content of the document chunk"),
                    _build_property("document_id", "TEXT", "Unique identifier for the source document"),
                    _build_property("document_title",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Title of the source document"
                    ),
                    weaviate.classes.config.Property(
                        name="document_source",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Source/filename of the document"
                    ),
                    weaviate.classes.config.Property(
                        name="chunk_index",
                        data_type=weaviate.classes.config.DataType.INT,
                        description="Index of this chunk within the document"
                    ),
                    weaviate.classes.config.Property(
                        name="metadata",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Additional metadata as JSON string"
                    ),
                    weaviate.classes.config.Property(
                        name="created_at",
                        data_type=weaviate.classes.config.DataType.DATE,
                        description="Timestamp when the chunk was created"
                    )
                ],
                # Vector configuration for OpenAI embeddings
                vector_config=Configure.VectorIndex.text2vec_openai(
                    model="text-embedding-3-small"
                ),
                # HNSW index configuration for performance
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=weaviate.classes.config.VectorDistances.COSINE,
                    ef=64,
                    ef_construction=128,
                    max_connections=32
                )
            )

            logger.info(f"Created collection '{self.collection_name}' successfully")

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def vector_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform pure vector similarity search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results with similarity scores
        """
        if not self.client:
            return await self._mock_vector_search(query, limit)

        try:
            collection = self.client.collections.get(self.collection_name)

            response = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(distance=True),
                return_properties=["content", "document_title", "document_source", "metadata", "chunk_index"]
            )

            results = []
            for obj in response.objects:
                results.append({
                    "content": obj.properties.get("content", ""),
                    "document_title": obj.properties.get("document_title", "Unknown"),
                    "document_source": obj.properties.get("document_source", "Unknown"),
                    "metadata": obj.properties.get("metadata", "{}"),
                    "chunk_index": obj.properties.get("chunk_index", 0),
                    "similarity": 1.0 - (obj.metadata.distance or 0.0),  # Convert distance to similarity
                    "search_type": "vector"
                })

            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return await self._mock_vector_search(query, limit)

    async def hybrid_search(self, query: str, limit: int = 10, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and keyword matching.

        Args:
            query: Search query
            limit: Maximum number of results
            alpha: Balance between vector (1.0) and keyword (0.0) search

        Returns:
            List of search results with hybrid scores
        """
        if not self.client:
            return await self._mock_hybrid_search(query, limit, alpha)

        try:
            collection = self.client.collections.get(self.collection_name)

            response = collection.query.hybrid(
                query=query,
                alpha=alpha,
                limit=limit,
                return_metadata=MetadataQuery(score=True),
                return_properties=["content", "document_title", "document_source", "metadata", "chunk_index"]
            )

            results = []
            for obj in response.objects:
                results.append({
                    "content": obj.properties.get("content", ""),
                    "document_title": obj.properties.get("document_title", "Unknown"),
                    "document_source": obj.properties.get("document_source", "Unknown"),
                    "metadata": obj.properties.get("metadata", "{}"),
                    "chunk_index": obj.properties.get("chunk_index", 0),
                    "score": obj.metadata.score or 0.0,
                    "alpha": alpha,
                    "search_type": "hybrid"
                })

            return results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return await self._mock_hybrid_search(query, limit, alpha)

    async def keyword_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results with BM25 scores
        """
        if not self.client:
            return await self._mock_keyword_search(query, limit)

        try:
            collection = self.client.collections.get(self.collection_name)

            response = collection.query.bm25(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(score=True),
                return_properties=["content", "document_title", "document_source", "metadata", "chunk_index"]
            )

            results = []
            for obj in response.objects:
                results.append({
                    "content": obj.properties.get("content", ""),
                    "document_title": obj.properties.get("document_title", "Unknown"),
                    "document_source": obj.properties.get("document_source", "Unknown"),
                    "metadata": obj.properties.get("metadata", "{}"),
                    "chunk_index": obj.properties.get("chunk_index", 0),
                    "score": obj.metadata.score or 0.0,
                    "search_type": "keyword"
                })

            return results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return await self._mock_keyword_search(query, limit)

    async def batch_insert(self, documents: List[Dict[str, Any]]):
        """
        Batch insert documents into Weaviate.

        Args:
            documents: List of document dictionaries with properties and vectors
        """
        if not self.client:
            logger.info("Mock mode: Would insert {} documents".format(len(documents)))
            return

        try:
            collection = self.client.collections.get(self.collection_name)

            with collection.batch.dynamic() as batch:
                for doc in documents:
                    properties = {
                        "content": doc.get("content", ""),
                        "document_id": doc.get("document_id", ""),
                        "document_title": doc.get("document_title", ""),
                        "document_source": doc.get("document_source", ""),
                        "chunk_index": doc.get("chunk_index", 0),
                        "metadata": json.dumps(doc.get("metadata", {})),
                        "created_at": datetime.utcnow().isoformat()
                    }

                    # Add object (vector will be generated automatically by text2vec-openai)
                    batch.add_object(properties=properties)

            logger.info(f"Successfully inserted {len(documents)} documents")

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            raise

    async def delete_all(self):
        """Delete all objects in the collection."""
        if not self.client:
            logger.info("Mock mode: Would delete all documents")
            return

        try:
            collection = self.client.collections.get(self.collection_name)
            collection.data.delete_many()
            logger.info("Deleted all documents from collection")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

    async def close(self):
        """Close the Weaviate client connection."""
        if self.client:
            self.client.close()
            self._initialized = False

    # Mock methods for development without Weaviate
    async def _mock_vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Mock vector search for development."""
        await asyncio.sleep(0.1)  # Simulate network delay

        mock_results = [
            {
                "content": "Interest rate changes have historically shown a strong inverse correlation with technology stock valuations. When the Federal Reserve raises rates, growth companies typically see their valuations decline due to higher discount rates applied to future cash flows.",
                "document_title": "Federal Reserve Interest Rate Policy 2024",
                "document_source": "fed_policy_2024.pdf",
                "metadata": '{"page": 15, "section": "Tech Sector Impact"}',
                "chunk_index": 12,
                "similarity": 0.92,
                "search_type": "vector"
            },
            {
                "content": "Tech company valuations are particularly sensitive to interest rate movements because these companies typically trade at high price-to-earnings ratios and depend on future growth expectations.",
                "document_title": "Tech Sector Valuation Analysis",
                "document_source": "tech_valuations.pdf",
                "metadata": '{"page": 8, "author": "Market Research Corp"}',
                "chunk_index": 5,
                "similarity": 0.88,
                "search_type": "vector"
            }
        ]

        return mock_results[:limit]

    async def _mock_hybrid_search(self, query: str, limit: int, alpha: float) -> List[Dict[str, Any]]:
        """Mock hybrid search for development."""
        await asyncio.sleep(0.1)

        # Simulate hybrid scoring
        vector_results = await self._mock_vector_search(query, limit)
        for result in vector_results:
            result["search_type"] = "hybrid"
            result["alpha"] = alpha
            result["score"] = result["similarity"] * alpha + 0.7 * (1 - alpha)

        return vector_results

    async def _mock_keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Mock keyword search for development."""
        await asyncio.sleep(0.1)

        mock_results = [
            {
                "content": "Apple Inc reported quarterly earnings with revenue growth of 8% year-over-year, driven by strong iPhone sales and services revenue.",
                "document_title": "NASDAQ Company Reports Q4",
                "document_source": "nasdaq_q4_reports.pdf",
                "metadata": '{"page": 23, "company": "Apple Inc"}',
                "chunk_index": 18,
                "score": 0.85,
                "search_type": "keyword"
            }
        ]

        return mock_results[:limit]


# Utility functions
async def create_weaviate_client(url: str = None, api_key: str = None) -> WeaviateClient:
    """Create and initialize a Weaviate client."""
    client = WeaviateClient(url, api_key)
    await client.initialize()
    return client


async def health_check(client: WeaviateClient) -> Dict[str, Any]:
    """Check Weaviate client health and connection status."""
    if not client.client:
        return {"status": "disconnected", "mode": "mock"}

    try:
        is_ready = client.client.is_ready()
        collection_exists = client.client.collections.exists(client.collection_name)

        return {
            "status": "connected" if is_ready else "error",
            "mode": "production",
            "collection_exists": collection_exists,
            "collection_name": client.collection_name
        }
    except Exception as e:
        return {
            "status": "error",
            "mode": "production",
            "error": str(e)
        }