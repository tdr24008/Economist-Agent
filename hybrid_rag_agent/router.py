"""
Query router for intelligent database selection in Hybrid RAG Agent.
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Types of search operations."""
    VECTOR = "vector"
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    GRAPH = "graph"


@dataclass
class RoutingDecision:
    """Represents a routing decision with confidence scores."""
    search_types: List[SearchType]
    confidence_scores: Dict[str, float]
    weaviate_alpha: float = 0.5  # For hybrid search balance
    reasoning: str = ""


class QueryRouter:
    """Intelligent query router for selecting appropriate search strategies."""

    def __init__(self):
        """Initialize the query router with pattern matching rules."""

        # Patterns that indicate graph/relationship queries
        self.graph_patterns = [
            r'\b(relationship|connection|linked|related|associated)\b',
            r'\b(who|which)\s+\w+\s+(with|to|from)\b',
            r'\b(connect|link|relate)\b',
            r'\b(network|graph|tree)\b',
            r'\b(entity|entities)\b',
            r'\b(company|person|organization)\s+\w+\s+(and|with)\b',
            r'\b(interaction|collaboration|partnership)\b',
            r'\b(between|among)\s+\w+\s+(and|&)\b',
            r'\b[A-Z][a-z]+\s+(Inc|Corp|LLC|Ltd)\b',  # Company names
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b.*\b(and|with|vs|versus)\b'  # Named entities with relationships
        ]

        # Patterns that indicate conceptual/semantic queries
        self.vector_patterns = [
            r'\b(explain|describe|what is|how does|why)\b',
            r'\b(concept|theory|principle|idea)\b',
            r'\b(similar|like|comparable|analogous)\b',
            r'\b(meaning|definition|understanding)\b',
            r'\b(implications|effects|impact|influence)\b',
            r'\b(analysis|assessment|evaluation)\b',
            r'\b(trend|pattern|behavior)\b'
        ]

        # Patterns that indicate keyword/exact match queries
        self.keyword_patterns = [
            r'"[^"]+"',  # Quoted phrases
            r'\b(specific|exact|precisely|exactly)\b',
            r'\b\d{4}\b',  # Years
            r'\b\d+(\.\d+)?%\b',  # Percentages
            r'\b\$\d+(\.\d+)?\b',  # Dollar amounts
            r'\b(Q[1-4]|quarter|fiscal)\b',  # Financial quarters
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',  # Months
            r'\b(report|document|file|publication)\b.*\b(titled|named|called)\b'
        ]

        # Patterns that suggest complex queries needing multiple approaches
        self.complex_patterns = [
            r'\b(compare|contrast|difference)\b',
            r'\b(comprehensive|complete|full)\b',
            r'\b(analysis|overview|summary)\b.*\b(including|with|and)\b',
            r'\b(historical|timeline|over time)\b',
            r'\b(multiple|various|different|several)\b'
        ]

    async def analyze_query(self, query: str) -> RoutingDecision:
        """
        Analyze a query and determine the best search strategy.

        Args:
            query: The user's search query

        Returns:
            RoutingDecision with recommended search types and configurations
        """
        logger.debug(f"Analyzing query: {query}")

        # Initialize confidence scores
        confidence = {
            "vector": 0.0,
            "hybrid": 0.0,
            "keyword": 0.0,
            "graph": 0.0
        }

        reasoning_parts = []
        query_lower = query.lower()

        # Check for graph patterns
        graph_matches = self._count_pattern_matches(self.graph_patterns, query)
        if graph_matches > 0:
            confidence["graph"] = min(0.9, 0.4 + (graph_matches * 0.2))
            reasoning_parts.append(f"Graph search (found {graph_matches} relationship indicators)")

        # Check for vector patterns
        vector_matches = self._count_pattern_matches(self.vector_patterns, query_lower)
        if vector_matches > 0:
            confidence["vector"] = min(0.9, 0.5 + (vector_matches * 0.2))
            reasoning_parts.append(f"Vector search (found {vector_matches} semantic indicators)")

        # Check for keyword patterns
        keyword_matches = self._count_pattern_matches(self.keyword_patterns, query)
        if keyword_matches > 0:
            confidence["keyword"] = min(0.9, 0.4 + (keyword_matches * 0.25))
            reasoning_parts.append(f"Keyword search (found {keyword_matches} exact match indicators)")

        # Check for complex patterns
        complex_matches = self._count_pattern_matches(self.complex_patterns, query_lower)
        if complex_matches > 0:
            confidence["hybrid"] = min(0.8, 0.5 + (complex_matches * 0.15))
            reasoning_parts.append(f"Multiple approaches needed (found {complex_matches} complexity indicators)")

        # Query length analysis
        word_count = len(query.split())
        if word_count > 15:
            confidence["hybrid"] = max(confidence["hybrid"], 0.6)
            reasoning_parts.append("Long query suggests multiple search approaches")
        elif word_count < 5:
            confidence["keyword"] = max(confidence["keyword"], 0.4)
            reasoning_parts.append("Short query suggests keyword search")

        # Entity detection (simple heuristic)
        entity_count = len(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query))
        if entity_count >= 2:
            confidence["graph"] = max(confidence["graph"], 0.6)
            reasoning_parts.append(f"Multiple entities detected ({entity_count})")

        # Default to hybrid if no strong indicators
        if max(confidence.values()) < 0.4:
            confidence["hybrid"] = 0.5
            reasoning_parts.append("Default to hybrid search")

        # Determine search types based on confidence threshold
        threshold = 0.4
        selected_types = []

        # Always include the highest confidence type
        max_confidence_type = max(confidence, key=confidence.get)
        if confidence[max_confidence_type] > 0.3:
            selected_types.append(SearchType(max_confidence_type))

        # Include additional types if they meet the threshold
        for search_type, conf in confidence.items():
            if conf >= threshold and SearchType(search_type) not in selected_types:
                selected_types.append(SearchType(search_type))

        # Fallback to hybrid if no types selected
        if not selected_types:
            selected_types = [SearchType.HYBRID]
            confidence["hybrid"] = 0.5

        # Determine Weaviate alpha for hybrid search
        alpha = self._calculate_alpha(confidence, query)

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Default routing applied"

        decision = RoutingDecision(
            search_types=selected_types,
            confidence_scores=confidence,
            weaviate_alpha=alpha,
            reasoning=reasoning
        )

        logger.info(f"Routing decision: {[t.value for t in selected_types]} with alpha={alpha:.2f}")
        return decision

    def _count_pattern_matches(self, patterns: List[str], text: str) -> int:
        """Count the number of pattern matches in the text."""
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        return matches

    def _calculate_alpha(self, confidence: Dict[str, float], query: str) -> float:
        """
        Calculate alpha parameter for Weaviate hybrid search.

        Alpha values:
        - 1.0 = Pure vector search
        - 0.5 = Balanced hybrid
        - 0.0 = Pure keyword search
        """
        vector_strength = confidence.get("vector", 0.0)
        keyword_strength = confidence.get("keyword", 0.0)

        # If one approach is clearly better, lean towards it
        if vector_strength > keyword_strength + 0.3:
            return 0.8  # Lean towards vector
        elif keyword_strength > vector_strength + 0.3:
            return 0.2  # Lean towards keyword

        # Check for specific indicators
        if any(indicator in query.lower() for indicator in ["similar", "like", "explain", "concept"]):
            return 0.7  # Favor vector for semantic queries

        if any(indicator in query for indicator in ['"', '$', '%', 'Q1', 'Q2', 'Q3', 'Q4']):
            return 0.3  # Favor keyword for exact matches

        # Default balanced approach
        return 0.5

    async def get_routing_explanation(self, decision: RoutingDecision) -> Dict[str, Any]:
        """Get a detailed explanation of the routing decision for UI display."""
        return {
            "selected_databases": [t.value for t in decision.search_types],
            "confidence_scores": decision.confidence_scores,
            "hybrid_balance": {
                "alpha": decision.weaviate_alpha,
                "vector_weight": decision.weaviate_alpha,
                "keyword_weight": 1.0 - decision.weaviate_alpha
            },
            "reasoning": decision.reasoning,
            "recommendation": self._get_search_recommendation(decision)
        }

    def _get_search_recommendation(self, decision: RoutingDecision) -> str:
        """Generate a human-readable recommendation for the search strategy."""
        types = [t.value for t in decision.search_types]

        if len(types) == 1:
            type_name = types[0]
            if type_name == "vector":
                return "Using semantic search to find conceptually similar content"
            elif type_name == "keyword":
                return "Using keyword search for exact matches"
            elif type_name == "graph":
                return "Using knowledge graph to explore entity relationships"
            elif type_name == "hybrid":
                return f"Using balanced hybrid search (vector: {decision.weaviate_alpha:.0%}, keyword: {1-decision.weaviate_alpha:.0%})"

        elif "graph" in types and len(types) > 1:
            return "Using both semantic search and knowledge graph for comprehensive results"

        else:
            return f"Using multiple search approaches: {', '.join(types)}"

    async def manual_override(self, search_type: str, alpha: float = 0.5) -> RoutingDecision:
        """
        Create a manual routing decision, bypassing automatic analysis.

        Args:
            search_type: Force a specific search type
            alpha: Alpha value for hybrid search

        Returns:
            RoutingDecision with manual configuration
        """
        confidence_scores = {t.value: 0.0 for t in SearchType}
        confidence_scores[search_type] = 1.0

        return RoutingDecision(
            search_types=[SearchType(search_type)],
            confidence_scores=confidence_scores,
            weaviate_alpha=alpha,
            reasoning=f"Manual override: forced {search_type} search"
        )


# Utility functions for integration
async def route_query(query: str, router: QueryRouter = None) -> RoutingDecision:
    """Convenience function for routing a single query."""
    if router is None:
        router = QueryRouter()
    return await router.analyze_query(query)


def should_use_weaviate(decision: RoutingDecision) -> bool:
    """Check if the routing decision requires Weaviate."""
    weaviate_types = {SearchType.VECTOR, SearchType.HYBRID, SearchType.KEYWORD}
    return any(t in weaviate_types for t in decision.search_types)


def should_use_neo4j(decision: RoutingDecision) -> bool:
    """Check if the routing decision requires Neo4j."""
    return SearchType.GRAPH in decision.search_types


def get_search_priority(decision: RoutingDecision) -> List[Tuple[SearchType, float]]:
    """Get search types ordered by confidence score."""
    priorities = []
    for search_type in decision.search_types:
        confidence = decision.confidence_scores.get(search_type.value, 0.0)
        priorities.append((search_type, confidence))

    return sorted(priorities, key=lambda x: x[1], reverse=True)