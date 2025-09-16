"""
Query orchestrator for managing multi-database searches in Hybrid RAG Agent.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .router import QueryRouter, RoutingDecision, SearchType, should_use_weaviate, should_use_neo4j
from .dependencies import SearchDependencies

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result with metadata."""
    content: str
    source_database: str
    search_type: str
    score: float
    metadata: Dict[str, Any]
    document_title: str = "Unknown"
    document_source: str = "Unknown"
    chunk_index: int = 0


@dataclass
class OrchestratedResult:
    """Represents the complete result of an orchestrated query."""
    query: str
    routing_decision: RoutingDecision
    databases_queried: List[str]
    search_results: List[SearchResult]
    total_results: int
    processing_time: float
    errors: List[str]
    merged_results: List[SearchResult]


class QueryOrchestrator:
    """Orchestrates queries across multiple databases and merges results."""

    def __init__(self, dependencies: SearchDependencies):
        """
        Initialize the query orchestrator.

        Args:
            dependencies: SearchDependencies instance with initialized clients
        """
        self.dependencies = dependencies
        self.router = QueryRouter()
        self.max_results_per_source = 20
        self.deduplication_threshold = 0.85  # Similarity threshold for deduplication

    async def process_query(
        self,
        query: str,
        manual_routing: Optional[RoutingDecision] = None,
        max_results: int = 15
    ) -> OrchestratedResult:
        """
        Process a query through the complete orchestration pipeline.

        Args:
            query: The search query
            manual_routing: Optional manual routing override
            max_results: Maximum number of results to return

        Returns:
            OrchestratedResult with complete processing information
        """
        start_time = datetime.now()
        errors = []
        search_results = []
        databases_queried = []

        try:
            # Step 1: Route the query
            if manual_routing:
                routing_decision = manual_routing
                logger.info(f"Using manual routing: {[t.value for t in routing_decision.search_types]}")
            else:
                routing_decision = await self.router.analyze_query(query)
                logger.info(f"Auto-routed query to: {[t.value for t in routing_decision.search_types]}")

            # Step 2: Execute searches in parallel
            search_tasks = []

            # Weaviate searches
            if should_use_weaviate(routing_decision):
                for search_type in routing_decision.search_types:
                    if search_type in [SearchType.VECTOR, SearchType.HYBRID, SearchType.KEYWORD]:
                        task = self._create_weaviate_search_task(
                            query, search_type, routing_decision
                        )
                        search_tasks.append(task)
                        databases_queried.append(f"weaviate_{search_type.value}")

            # Neo4j searches
            if should_use_neo4j(routing_decision):
                task = self._create_neo4j_search_task(query)
                search_tasks.append(task)
                databases_queried.append("neo4j_graph")

            # Execute all searches
            if search_tasks:
                logger.info(f"Executing {len(search_tasks)} parallel searches")
                results = await asyncio.gather(*search_tasks, return_exceptions=True)

                # Process results and collect errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_msg = f"Search task {i} failed: {str(result)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                    elif isinstance(result, list):
                        search_results.extend(result)
                    else:
                        logger.warning(f"Unexpected result type from task {i}: {type(result)}")

            # Step 3: Merge and deduplicate results
            merged_results = await self._merge_and_deduplicate(search_results)

            # Step 4: Rank and limit results
            final_results = self._rank_and_limit_results(merged_results, max_results)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            result = OrchestratedResult(
                query=query,
                routing_decision=routing_decision,
                databases_queried=databases_queried,
                search_results=search_results,
                total_results=len(final_results),
                processing_time=processing_time,
                errors=errors,
                merged_results=final_results
            )

            logger.info(f"Query processed in {processing_time:.3f}s, {len(final_results)} final results")
            return result

        except Exception as e:
            error_msg = f"Query orchestration failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg, exc_info=True)

            processing_time = (datetime.now() - start_time).total_seconds()
            return OrchestratedResult(
                query=query,
                routing_decision=routing_decision if 'routing_decision' in locals() else None,
                databases_queried=databases_queried,
                search_results=[],
                total_results=0,
                processing_time=processing_time,
                errors=errors,
                merged_results=[]
            )

    async def _create_weaviate_search_task(
        self,
        query: str,
        search_type: SearchType,
        routing_decision: RoutingDecision
    ) -> asyncio.Task:
        """Create an async task for Weaviate search."""

        async def execute_weaviate_search():
            try:
                if search_type == SearchType.VECTOR:
                    raw_results = await self.dependencies.vector_search(
                        query, limit=self.max_results_per_source
                    )
                elif search_type == SearchType.HYBRID:
                    # Convert alpha to text_weight for dependencies interface
                    text_weight = 1.0 - routing_decision.weaviate_alpha
                    raw_results = await self.dependencies.hybrid_search(
                        query, limit=self.max_results_per_source, text_weight=text_weight
                    )
                elif search_type == SearchType.KEYWORD:
                    raw_results = await self.dependencies.keyword_search(
                        query, limit=self.max_results_per_source
                    )
                else:
                    return []

                # Convert to SearchResult objects
                results = []
                for item in raw_results:
                    result = SearchResult(
                        content=item.get("content", ""),
                        source_database="weaviate",
                        search_type=search_type.value,
                        score=item.get("score", item.get("similarity", 0.0)),
                        metadata=item.get("metadata", {}),
                        document_title=item.get("document_title", "Unknown"),
                        document_source=item.get("document_source", "Unknown"),
                        chunk_index=item.get("chunk_index", 0)
                    )
                    results.append(result)

                logger.debug(f"Weaviate {search_type.value} search returned {len(results)} results")
                return results

            except Exception as e:
                logger.error(f"Weaviate {search_type.value} search failed: {e}")
                raise

        return asyncio.create_task(execute_weaviate_search())

    async def _create_neo4j_search_task(self, query: str) -> asyncio.Task:
        """Create an async task for Neo4j graph search."""

        async def execute_neo4j_search():
            try:
                raw_results = await self.dependencies.graph_search(
                    query, include_timeline=True
                )

                # Convert to SearchResult objects
                results = []
                for item in raw_results:
                    result = SearchResult(
                        content=item.get("fact", ""),
                        source_database="neo4j",
                        search_type="graph",
                        score=1.0,  # Graph results don't have similarity scores
                        metadata={
                            "uuid": item.get("uuid", ""),
                            "valid_at": item.get("valid_at", ""),
                            "invalid_at": item.get("invalid_at", ""),
                            "source_node_uuid": item.get("source_node_uuid", ""),
                            "timeline_context": item.get("timeline_context", "")
                        },
                        document_title="Knowledge Graph",
                        document_source="neo4j_graphiti"
                    )
                    results.append(result)

                logger.debug(f"Neo4j graph search returned {len(results)} results")
                return results

            except Exception as e:
                logger.error(f"Neo4j graph search failed: {e}")
                raise

        return asyncio.create_task(execute_neo4j_search())

    async def _merge_and_deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Merge results from different sources and remove duplicates.

        Args:
            results: List of SearchResult objects from different sources

        Returns:
            Deduplicated list of SearchResult objects
        """
        if not results:
            return []

        # Group results by content hash for deduplication
        content_groups = {}

        for result in results:
            content_key = self._generate_content_hash(result.content)

            if content_key not in content_groups:
                content_groups[content_key] = []
            content_groups[content_key].append(result)

        # Select best result from each group
        merged_results = []
        for content_key, group in content_groups.items():
            if len(group) == 1:
                merged_results.append(group[0])
            else:
                # Choose the result with the highest score
                best_result = max(group, key=lambda x: x.score)

                # Merge metadata from all sources
                combined_metadata = {}
                source_databases = set()
                search_types = set()

                for result in group:
                    combined_metadata.update(result.metadata)
                    source_databases.add(result.source_database)
                    search_types.add(result.search_type)

                # Update best result with combined information
                best_result.metadata.update(combined_metadata)
                best_result.metadata["source_databases"] = list(source_databases)
                best_result.metadata["search_types"] = list(search_types)
                best_result.metadata["duplicate_count"] = len(group)

                merged_results.append(best_result)

        logger.info(f"Merged {len(results)} results into {len(merged_results)} unique results")
        return merged_results

    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash key for content deduplication."""
        # Normalize content for comparison
        normalized = content.lower().strip()

        # Use first 200 characters as hash key
        # This allows for slight variations while catching duplicates
        return normalized[:200]

    def _rank_and_limit_results(
        self,
        results: List[SearchResult],
        max_results: int
    ) -> List[SearchResult]:
        """
        Rank results by relevance and limit to max_results.

        Args:
            results: List of SearchResult objects
            max_results: Maximum number of results to return

        Returns:
            Ranked and limited list of SearchResult objects
        """
        if not results:
            return []

        # Sort by score (descending) with graph results getting priority boost
        def get_sort_key(result: SearchResult) -> Tuple[float, str]:
            score = result.score

            # Boost graph results slightly as they represent explicit relationships
            if result.source_database == "neo4j":
                score += 0.1

            # Secondary sort by search type preference
            type_priority = {
                "graph": 3,
                "vector": 2,
                "hybrid": 1,
                "keyword": 0
            }

            return (score, type_priority.get(result.search_type, 0))

        sorted_results = sorted(results, key=get_sort_key, reverse=True)

        # Limit results
        limited_results = sorted_results[:max_results]

        logger.debug(f"Ranked and limited to {len(limited_results)} results")
        return limited_results

    async def get_result_summary(self, result: OrchestratedResult) -> Dict[str, Any]:
        """
        Generate a summary of the orchestrated result for UI display.

        Args:
            result: OrchestratedResult to summarize

        Returns:
            Dictionary with summary information
        """
        # Count results by source
        source_counts = {}
        search_type_counts = {}

        for search_result in result.merged_results:
            source = search_result.source_database
            search_type = search_result.search_type

            source_counts[source] = source_counts.get(source, 0) + 1
            search_type_counts[search_type] = search_type_counts.get(search_type, 0) + 1

        # Calculate average scores
        scores = [r.score for r in result.merged_results if r.score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        summary = {
            "query": result.query,
            "total_results": result.total_results,
            "processing_time": result.processing_time,
            "databases_queried": result.databases_queried,
            "source_breakdown": source_counts,
            "search_type_breakdown": search_type_counts,
            "average_score": avg_score,
            "has_errors": len(result.errors) > 0,
            "error_count": len(result.errors),
            "routing_explanation": await self.router.get_routing_explanation(result.routing_decision)
        }

        return summary

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of all connected services."""
        health_status = {
            "orchestrator": "healthy",
            "router": "healthy",
            "dependencies": {},
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Check Weaviate
            if self.dependencies.weaviate_client:
                weaviate_health = await self.dependencies.weaviate_client.health_check()
                health_status["dependencies"]["weaviate"] = weaviate_health
            else:
                health_status["dependencies"]["weaviate"] = {"status": "disconnected", "mode": "mock"}

            # Check Neo4j
            if self.dependencies.graph_client:
                # Simplified health check - could be expanded
                health_status["dependencies"]["neo4j"] = {"status": "connected", "mode": "production"}
            else:
                health_status["dependencies"]["neo4j"] = {"status": "disconnected", "mode": "mock"}

            # Overall status
            if self.dependencies.use_mocks:
                health_status["orchestrator"] = "mock_mode"

        except Exception as e:
            health_status["orchestrator"] = "error"
            health_status["error"] = str(e)

        return health_status


# Utility functions
async def create_orchestrator(dependencies: SearchDependencies) -> QueryOrchestrator:
    """Create and initialize a QueryOrchestrator."""
    await dependencies.initialize()
    return QueryOrchestrator(dependencies)


async def quick_search(
    query: str,
    dependencies: SearchDependencies,
    search_type: str = "auto",
    max_results: int = 10
) -> OrchestratedResult:
    """
    Convenience function for quick searches.

    Args:
        query: Search query
        dependencies: SearchDependencies instance
        search_type: Search type override ("auto", "vector", "hybrid", "keyword", "graph")
        max_results: Maximum results to return

    Returns:
        OrchestratedResult
    """
    orchestrator = QueryOrchestrator(dependencies)

    if search_type != "auto":
        # Create manual routing
        manual_routing = await orchestrator.router.manual_override(search_type)
        return await orchestrator.process_query(query, manual_routing, max_results)
    else:
        return await orchestrator.process_query(query, max_results=max_results)