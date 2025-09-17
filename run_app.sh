#!/bin/bash
# Start the Economist Agent with virtual environment
set -e

# Activate virtual environment
source activate_venv.sh

echo "🚀 Starting Economist Agent Streamlit App..."
echo "🌐 The app will be available at: http://localhost:8501"
echo ""

# Start Streamlit
streamlit run app.py