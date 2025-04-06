#!/bin/bash

echo "🧠 Bootstrapping LocalGenius setup..."

# Step 1: Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Step 2: Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Start Ollama in background (if available)
if command -v ollama &> /dev/null
then
    echo "🚀 Checking for llama3 model..."
    ollama run llama3 &
else
    echo "⚠️ Ollama not found. Please install it: https://ollama.com/download"
fi

echo "✅ Setup complete. You can now run:"
echo "  python llama_dev_agent.py   # for CLI"
echo "  streamlit run streamlit_ui.py   # for Web UI"

