import os
import sys
import asyncio

from agents import get_data_analyst_team
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import streamlit as st
import pandas as pd
import PyPDF2
from io import BytesIO

# Import RAG ingestion pipeline
from hybrid_rag_agent.ingestion.ingest import DocumentIngestionPipeline
from hybrid_rag_agent.utils.models import IngestionConfig

async def reset_chat():
    """Clear the chat history."""
    if "messages" in st.session_state:
        st.session_state["messages"] = []
    if "agent" in st.session_state:
        await st.session_state["agent"].reset()

async def ingest_pdf_to_rag(pdf_text: str, filename: str) -> bool:
    """
    Ingest PDF text into the RAG system (Weaviate + Neo4j).

    Args:
        pdf_text: Extracted text from PDF
        filename: Original filename for metadata

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a temporary markdown file for ingestion
        temp_dir = "temp_ingestion"
        os.makedirs(temp_dir, exist_ok=True)

        # Convert filename to markdown
        markdown_filename = filename.replace(".pdf", ".md")
        temp_file_path = os.path.join(temp_dir, markdown_filename)

        # Create markdown content with metadata header
        markdown_content = f"""---
title: {filename.replace('.pdf', '')}
source: uploaded_pdf
upload_date: {pd.Timestamp.now().isoformat()}
document_type: pdf
---

# {filename.replace('.pdf', '')}

{pdf_text}
"""

        # Write temporary markdown file
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Create ingestion configuration
        config = IngestionConfig(
            chunk_size=1000,
            chunk_overlap=200,
            use_semantic_chunking=True,
            extract_entities=True,
            skip_graph_building=False  # Include knowledge graph
        )

        # Create and run ingestion pipeline
        pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder=temp_dir,
            clean_before_ingest=False  # Don't clean existing data
        )

        # Run ingestion
        results = await pipeline.ingest_documents()

        # Close pipeline
        await pipeline.close()

        # Clean up temporary file
        os.remove(temp_file_path)
        os.rmdir(temp_dir)

        # Check if ingestion was successful
        if results and len(results) > 0 and not results[0].errors:
            st.success(f"✅ PDF successfully ingested into RAG system! Created {results[0].chunks_created} chunks.")
            return True
        else:
            error_msg = results[0].errors[0] if results and results[0].errors else "Unknown error"
            st.error(f"❌ Failed to ingest PDF into RAG system: {error_msg}")
            return False

    except Exception as e:
        st.error(f"❌ Error during RAG ingestion: {str(e)}")
        return False

def initialize_data_analyst_agent():
    """Initialize the Data Analyst Agent."""
    # Initialize the agent with the provided GitHub PAT and model selection
    print(f"Creating agent with model {st.session_state['model_selection']}...")
    st.session_state["agent"] = get_data_analyst_team(
        # st.session_state["gh_pat"], 
        st.session_state["model_selection"]
    )

# Solution for Windows users
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Streamlit app
st.set_page_config(page_title="📊 Economist Agent", layout="wide")


# initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Ensure the event loop is created only once
if "event_loop" not in st.session_state:
    st.session_state["event_loop"] = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state["event_loop"])

st.title("📊 Economist Agent")
st.markdown(
    """
    A powerful multi-agent system built with AutoGen 0.4 that provides automated data analysis, visualization, and insights generation through an interactive chat interface.

    - **Data Analysis**: Ask questions about your dataset and get insights.
    - **Data Visualization**: Request visualizations to better understand your data.
    - **Interactive Chat**: Engage in a conversation with the agent to refine your queries and get more detailed answers.

    """
)

st.sidebar.header("Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV, TSV, or PDF file", type=["csv", "tsv", "pdf"]
)

# Add reset button to sidebar
st.sidebar.button(
    "New Chat",
    on_click=lambda: asyncio.run(reset_chat()),
    type="secondary",
    use_container_width=True
)

# gh_pat = st.sidebar.text_input(
#     "GitHub Personal Access Token (PAT)",
#     placeholder="Enter your GitHub PAT here",
#     type="password",
#     key="gh_pat"
# )


# if gh_pat:
st.sidebar.selectbox(
    "Select a model",
    options=["llama3.1:8b","qwen2.5-coder","qwen3:8b"],
    index=0,
    key="model_selection",
    on_change=initialize_data_analyst_agent
)

# Handle file upload
uploaded_data_info = ""
if uploaded_file:
    try:
        # Create a directory to save the uploaded file
        if not os.path.exists("code_executor"):
            os.makedirs("code_executor")
        # Save the uploaded file to the local directory
        local_file_path = os.path.join("code_executor", uploaded_file.name)

        st.write("### Data Preview")
        # Determine file type and read accordingly
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding="utf-8")
            st.dataframe(df)
            df.to_csv(local_file_path, index=False)
            uploaded_data_info = f" (CSV dataset to be analysed is present at: {uploaded_file.name})"
        elif uploaded_file.name.endswith(".tsv"):
            df = pd.read_csv(uploaded_file, sep="\t", encoding="utf-8")
            st.dataframe(df)
            df.to_csv(local_file_path, sep="\t", index=False)
            uploaded_data_info = f" (TSV dataset to be analysed is present at: {uploaded_file.name})"
        elif uploaded_file.name.endswith(".pdf"):
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() + "\n"

            # Save PDF text to a text file for analysis
            txt_file_path = os.path.join("code_executor", uploaded_file.name.replace(".pdf", ".txt"))
            with open(txt_file_path, "w", encoding="utf-8") as f:
                f.write(pdf_text)

            # Also save the original PDF
            with open(local_file_path, "wb") as f:
                uploaded_file.seek(0)
                f.write(uploaded_file.read())

            st.text_area("PDF Content Preview", pdf_text[:2000] + "..." if len(pdf_text) > 2000 else pdf_text, height=200)

            # Ingest PDF into RAG system
            with st.spinner("🔄 Ingesting PDF into RAG system..."):
                ingestion_success = asyncio.run(ingest_pdf_to_rag(pdf_text, uploaded_file.name))

            if ingestion_success:
                uploaded_data_info = f" (PDF document ingested into RAG system and available for search. Local files: {uploaded_file.name}, {uploaded_file.name.replace('.pdf', '.txt')})"
            else:
                uploaded_data_info = f" (PDF document to be analysed is present at: {uploaded_file.name}, text extracted to {uploaded_file.name.replace('.pdf', '.txt')})"

    except Exception as e:
        st.error(f"Error processing file: {e}")

# Chat interface (always visible)
st.write("### Chat with Economist Agent")

# Initialize agent if model is selected
if not st.session_state["model_selection"]:
    st.info("Please select a model from the sidebar to start chatting.")
else:
    if "agent" not in st.session_state:
        initialize_data_analyst_agent()

    # Display chat history messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_query = st.chat_input("Ask a question about economics, data analysis, or upload data for analysis...")

    if user_query:
        if user_query.strip() == "":
            st.warning("Please enter a query.")
        else:
            st.session_state["messages"].append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Add file context if available
            full_query = user_query + uploaded_data_info

            # Define an asynchronous function: this is needed to use await
            async def initiate_chat():
                await st.session_state["agent"].run(
                    task=[TextMessage(content=full_query, source="user")],
                    cancellation_token=CancellationToken(),
                )
                st.stop()  # Stop code execution after termination command

            # Run the asynchronous function within the event loop
            st.session_state["event_loop"].run_until_complete(initiate_chat())

# stop app after termination command
st.stop()