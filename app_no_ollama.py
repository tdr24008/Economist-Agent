import os
import sys
import streamlit as st
import pandas as pd
import PyPDF2
from io import BytesIO

# Simple app without Ollama dependencies for testing
st.set_page_config(page_title="Economist RAG Agent", page_icon="📊", layout="wide")

# Windows compatibility for asyncio
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.getvalue()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def main():
    st.title("📊 Economist RAG Agent")
    st.write("Interactive Economist Research Assistant (Demo Mode - Ollama Required for Full Functionality)")

    # Sidebar for file upload
    with st.sidebar:
        st.header("📄 Document Upload")
        uploaded_file = st.file_uploader(
            "Upload PDF documents for analysis",
            type=['pdf'],
            help="Upload economic research papers, reports, or datasets in PDF format"
        )

        if uploaded_file:
            st.success(f"✅ Uploaded: {uploaded_file.name}")

            # Extract text from PDF
            with st.spinner("Extracting text from PDF..."):
                pdf_text = extract_text_from_pdf(uploaded_file)

            if pdf_text:
                st.success(f"📄 Extracted {len(pdf_text)} characters")

                # Show first 500 characters as preview
                with st.expander("📖 Document Preview"):
                    st.text_area("First 500 characters:", pdf_text[:500], height=200, disabled=True)

                # Save to directory for later processing
                save_dir = "code_executor"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, uploaded_file.name)

                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.info(f"💾 Saved to: {save_path}")

    # Main chat interface
    st.header("💬 Chat Interface")

    # Information about missing Ollama
    st.warning("""
    ⚠️ **Ollama Required**: This app requires Ollama to be running for full functionality.

    **To get the full experience:**
    1. Install Ollama from https://ollama.com/
    2. Run: `ollama serve`
    3. Pull models: `ollama pull llama3.1` and `ollama pull qwen2.5:3b-instruct-q4_K_M`
    4. Restart this app

    **Current Status**: Demo mode - file upload and text extraction working
    """)

    # Mock chat interface
    if "demo_messages" not in st.session_state:
        st.session_state.demo_messages = [
            {"role": "assistant", "content": "Hello! I'm the Economist RAG Agent. Please install Ollama to enable full chat functionality."}
        ]

    # Display demo messages
    for message in st.session_state.demo_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Mock input (disabled)
    user_input = st.chat_input("Chat functionality requires Ollama to be running...", disabled=True)

    # Status section
    with st.expander("🔧 System Status"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Services Status")

            # Check Docker services
            try:
                import subprocess
                result = subprocess.run(['docker', 'compose', 'ps'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    st.success("✅ Docker Compose services running")
                    st.code(result.stdout)
                else:
                    st.error("❌ Docker Compose services not running")
            except Exception as e:
                st.error(f"❌ Docker check failed: {e}")

        with col2:
            st.subheader("Database Connections")

            # Check Weaviate
            try:
                import requests
                response = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=2)
                if response.status_code == 200:
                    st.success("✅ Weaviate connected")
                else:
                    st.error("❌ Weaviate not accessible")
            except Exception as e:
                st.error(f"❌ Weaviate connection failed: {e}")

            # Check Neo4j (basic port check)
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', 7474))
                if result == 0:
                    st.success("✅ Neo4j port accessible")
                else:
                    st.error("❌ Neo4j not accessible")
                sock.close()
            except Exception as e:
                st.error(f"❌ Neo4j check failed: {e}")

            # Check Ollama
            try:
                import requests
                response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    st.success("✅ Ollama connected")
                    models = response.json().get('models', [])
                    st.write(f"Models available: {len(models)}")
                else:
                    st.error("❌ Ollama not responding")
            except Exception as e:
                st.error(f"❌ Ollama not running: {e}")

if __name__ == "__main__":
    main()