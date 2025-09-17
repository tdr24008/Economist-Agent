"""
UI components for Streamlit interface with routing visualization.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import plotly.graph_objects as go


def display_routing_decision(routing_info: Dict[str, Any]):
    """
    Display query routing decision in the sidebar.

    Args:
        routing_info: Dictionary containing routing decision information
    """
    st.sidebar.header("🎯 Query Routing")

    # Show which databases were queried
    databases_queried = routing_info.get('databases_queried', [])
    if databases_queried:
        st.sidebar.subheader("Databases Queried:")
        for db in databases_queried:
            if 'weaviate' in db.lower():
                st.sidebar.success(f"✓ Weaviate ({db.split('_')[-1] if '_' in db else 'search'})")
            elif 'neo4j' in db.lower():
                st.sidebar.success("✓ Neo4j (graph)")
            else:
                st.sidebar.info(f"✓ {db}")

    # Show confidence scores
    confidence_scores = routing_info.get('confidence_scores', {})
    if confidence_scores:
        st.sidebar.subheader("Routing Confidence:")

        # Create metrics for each search type
        col1, col2 = st.sidebar.columns(2)

        with col1:
            vector_conf = confidence_scores.get('vector', 0)
            st.metric("Vector", f"{vector_conf:.2f}",
                     delta=f"{'+' if vector_conf > 0.5 else ''}High" if vector_conf > 0.5 else "Low",
                     delta_color="normal" if vector_conf > 0.5 else "off")

            keyword_conf = confidence_scores.get('keyword', 0)
            st.metric("Keyword", f"{keyword_conf:.2f}",
                     delta=f"{'+' if keyword_conf > 0.5 else ''}High" if keyword_conf > 0.5 else "Low",
                     delta_color="normal" if keyword_conf > 0.5 else "off")

        with col2:
            hybrid_conf = confidence_scores.get('hybrid', 0)
            st.metric("Hybrid", f"{hybrid_conf:.2f}",
                     delta=f"{'+' if hybrid_conf > 0.5 else ''}High" if hybrid_conf > 0.5 else "Low",
                     delta_color="normal" if hybrid_conf > 0.5 else "off")

            graph_conf = confidence_scores.get('graph', 0)
            st.metric("Graph", f"{graph_conf:.2f}",
                     delta=f"{'+' if graph_conf > 0.5 else ''}High" if graph_conf > 0.5 else "Low",
                     delta_color="normal" if graph_conf > 0.5 else "off")

    # Show reasoning if available
    reasoning = routing_info.get('reasoning', '')
    if reasoning:
        st.sidebar.subheader("Routing Logic:")
        st.sidebar.info(reasoning)

    # Show processing time if available
    processing_time = routing_info.get('processing_time')
    if processing_time:
        st.sidebar.subheader("Performance:")
        st.sidebar.metric("Query Time", f"{processing_time:.3f}s")


def display_search_results_summary(results_summary: Dict[str, Any]):
    """
    Display summary of search results.

    Args:
        results_summary: Dictionary containing search results summary
    """
    st.subheader("📊 Search Results Summary")

    # Main metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Results", results_summary.get('total_results', 0))

    with col2:
        st.metric("Processing Time", f"{results_summary.get('processing_time', 0):.3f}s")

    with col3:
        avg_score = results_summary.get('average_score', 0)
        st.metric("Avg Score", f"{avg_score:.3f}")

    with col4:
        error_count = results_summary.get('error_count', 0)
        st.metric("Errors", error_count, delta_color="inverse")

    # Source breakdown
    source_breakdown = results_summary.get('source_breakdown', {})
    search_type_breakdown = results_summary.get('search_type_breakdown', {})

    if source_breakdown or search_type_breakdown:
        col1, col2 = st.columns(2)

        with col1:
            if source_breakdown:
                st.subheader("Results by Database")
                df_sources = pd.DataFrame(list(source_breakdown.items()),
                                        columns=['Database', 'Count'])
                st.bar_chart(df_sources.set_index('Database'))

        with col2:
            if search_type_breakdown:
                st.subheader("Results by Search Type")
                df_types = pd.DataFrame(list(search_type_breakdown.items()),
                                      columns=['Search Type', 'Count'])
                st.bar_chart(df_types.set_index('Search Type'))


def create_routing_visualization(confidence_scores: Dict[str, float]) -> go.Figure:
    """
    Create a polar chart showing routing confidence scores.

    Args:
        confidence_scores: Dictionary of search type to confidence score

    Returns:
        Plotly figure object
    """
    # Prepare data
    search_types = list(confidence_scores.keys())
    scores = list(confidence_scores.values())

    # Close the radar chart by adding the first point at the end
    search_types.append(search_types[0])
    scores.append(scores[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=search_types,
        fill='toself',
        fillcolor='rgba(66, 165, 245, 0.2)',
        line=dict(color='rgba(66, 165, 245, 1)', width=2),
        marker=dict(size=8, color='rgba(66, 165, 245, 1)'),
        name='Confidence'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0, 0.25, 0.5, 0.75, 1],
                ticktext=['0%', '25%', '50%', '75%', '100%']
            )
        ),
        showlegend=False,
        title="Query Routing Confidence",
        title_x=0.5,
        width=300,
        height=300
    )

    return fig


def display_routing_flow(databases_queried: List[str], query: str):
    """
    Display a simple flow diagram showing the routing decision.

    Args:
        databases_queried: List of databases that were queried
        query: The original query
    """
    st.subheader("🔄 Query Flow")

    # Create a simple flow using columns and arrows
    cols = st.columns(len(databases_queried) * 2 - 1)

    for i, db in enumerate(databases_queried):
        col_idx = i * 2

        with cols[col_idx]:
            if 'weaviate' in db.lower():
                st.markdown(
                    """
                    <div style='text-align: center; padding: 10px; border: 2px solid #4CAF50; border-radius: 10px; background-color: #E8F5E8;'>
                        <strong>🔍 Weaviate</strong><br>
                        <small>{}</small>
                    </div>
                    """.format(db.split('_')[-1].title() if '_' in db else 'Vector Search'),
                    unsafe_allow_html=True
                )
            elif 'neo4j' in db.lower():
                st.markdown(
                    """
                    <div style='text-align: center; padding: 10px; border: 2px solid #FF9800; border-radius: 10px; background-color: #FFF3E0;'>
                        <strong>🕸️ Neo4j</strong><br>
                        <small>Graph Search</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Add arrow between databases (except after the last one)
        if i < len(databases_queried) - 1:
            with cols[col_idx + 1]:
                st.markdown(
                    "<div style='text-align: center; font-size: 24px; padding-top: 20px;'>➕</div>",
                    unsafe_allow_html=True
                )


def display_health_status(health_info: Dict[str, Any]):
    """
    Display system health status.

    Args:
        health_info: Dictionary containing health information
    """
    st.sidebar.header("🏥 System Health")

    # Overall status
    orchestrator_status = health_info.get('orchestrator', 'unknown')
    if orchestrator_status == 'healthy':
        st.sidebar.success("✅ System Healthy")
    elif orchestrator_status == 'mock_mode':
        st.sidebar.warning("⚠️ Mock Mode")
    else:
        st.sidebar.error("❌ System Error")

    # Database statuses
    dependencies = health_info.get('dependencies', {})

    if dependencies:
        st.sidebar.subheader("Database Status:")

        # Weaviate status
        weaviate_info = dependencies.get('weaviate', {})
        weaviate_status = weaviate_info.get('status', 'unknown')
        weaviate_mode = weaviate_info.get('mode', 'unknown')

        if weaviate_status == 'connected':
            st.sidebar.success(f"✅ Weaviate ({weaviate_mode})")
        elif weaviate_status == 'disconnected' and weaviate_mode == 'mock':
            st.sidebar.warning("⚠️ Weaviate (mock)")
        else:
            st.sidebar.error("❌ Weaviate")

        # Neo4j status
        neo4j_info = dependencies.get('neo4j', {})
        neo4j_status = neo4j_info.get('status', 'unknown')
        neo4j_mode = neo4j_info.get('mode', 'unknown')

        if neo4j_status == 'connected':
            st.sidebar.success(f"✅ Neo4j ({neo4j_mode})")
        elif neo4j_status == 'disconnected' and neo4j_mode == 'mock':
            st.sidebar.warning("⚠️ Neo4j (mock)")
        else:
            st.sidebar.error("❌ Neo4j")


def create_search_config_panel():
    """
    Create a configuration panel for search settings.

    Returns:
        Dictionary with search configuration
    """
    st.sidebar.header("⚙️ Search Configuration")

    # Search mode selection
    search_mode = st.sidebar.selectbox(
        "Search Mode",
        ["Auto (Intelligent Routing)", "Vector Only", "Hybrid", "Keyword Only", "Graph Only", "All Databases"],
        help="Choose how to route your queries"
    )

    # Advanced settings (collapsible)
    with st.sidebar.expander("Advanced Settings"):
        max_results = st.slider("Max Results", 5, 25, 15)

        # Hybrid search alpha (only show if hybrid mode)
        alpha = 0.5
        if "Hybrid" in search_mode:
            alpha = st.slider(
                "Vector vs Keyword Balance",
                0.0, 1.0, 0.5,
                help="0 = Pure keyword, 1 = Pure vector"
            )

        # Confidence threshold
        confidence_threshold = st.slider(
            "Routing Confidence Threshold",
            0.1, 0.9, 0.4,
            help="Minimum confidence required for routing decisions"
        )

        show_debug_info = st.checkbox("Show Debug Information", False)

    return {
        "search_mode": search_mode,
        "max_results": max_results,
        "alpha": alpha,
        "confidence_threshold": confidence_threshold,
        "show_debug_info": show_debug_info
    }


def format_search_result(result: Dict[str, Any], index: int) -> str:
    """
    Format a search result for display.

    Args:
        result: Dictionary containing search result
        index: Result index number

    Returns:
        Formatted string for display
    """
    content = result.get('content', 'No content available')
    source_db = result.get('source_database', 'Unknown')
    search_type = result.get('search_type', 'unknown')
    score = result.get('score', result.get('similarity', 0))
    document_title = result.get('document_title', 'Unknown Document')
    document_source = result.get('document_source', 'Unknown Source')

    # Create database icon
    db_icon = "🔍" if "weaviate" in source_db.lower() else "🕸️" if "neo4j" in source_db.lower() else "📄"

    # Format the result
    formatted = f"""
**{index}. {db_icon} {document_title}**

{content}

📁 *Source: {document_source}*
🎯 *Score: {score:.3f}*
🗄️ *Database: {source_db} ({search_type})*

---
"""

    return formatted