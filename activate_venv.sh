#!/bin/bash
# Auto-activation script for the Economist Agent virtual environment

# Check if we're already in the virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment already active: $VIRTUAL_ENV"
else
    # Get the script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

    # Activate the virtual environment
    if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        echo "🔄 Activating virtual environment..."
        source "$SCRIPT_DIR/venv/bin/activate"
        echo "✅ Virtual environment activated: $VIRTUAL_ENV"
        echo "🐍 Python: $(which python)"
        echo "📦 Pip: $(which pip)"
    else
        echo "❌ Virtual environment not found at $SCRIPT_DIR/venv/bin/activate"
        echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
fi

# Optional: Show environment info
echo "📋 Environment Info:"
echo "   Working directory: $(pwd)"
echo "   Python version: $(python --version)"
echo "   Virtual env: $VIRTUAL_ENV"