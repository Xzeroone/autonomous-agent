#!/bin/bash
# Quick-start installation script for Autonomous Agent
# Ubuntu 24.04

set -e

echo "=================================="
echo "Autonomous Agent Quick Setup"
echo "=================================="
echo ""

# Check Ubuntu version
if ! grep -q "24.04" /etc/os-release; then
    echo "⚠️  Warning: This script is designed for Ubuntu 24.04"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.11+ required. Current: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION"

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Start service
    sudo systemctl start ollama
    sudo systemctl enable ollama
    
    echo "✓ Ollama installed and started"
else
    echo "✓ Ollama already installed"
fi

# Wait for Ollama to be ready
echo ""
echo "Waiting for Ollama service..."
for i in {1..10}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is ready"
        break
    fi
    sleep 1
done

# Pull model
echo ""
echo "Pulling qwen3-coder model (this may take 5-10 minutes)..."
if ollama pull qwen3-coder; then
    echo "✓ Model downloaded"
else
    echo "❌ Model download failed"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install dependencies
echo ""
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "Verifying installation..."
python3 << EOF
try:
    import langgraph
    import ollama
    from langchain_ollama import ChatOllama
    print(f"✓ LangGraph: {langgraph.__version__}")
    print(f"✓ Ollama: {ollama.__version__}")
    print("✓ All dependencies installed")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF

# Create workspace
echo ""
echo "Creating workspace structure..."
mkdir -p agent_workspace/{skills,exec}
echo "✓ Workspace created"

# Success message
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To start the agent:"
echo "  1. source venv/bin/activate"
echo "  2. python3 autonomous_agent.py"
echo ""
echo "Example commands:"
echo "  :directive Create a JSON validator"
echo "  :skills"
echo "  :memory"
echo ""
echo "See SETUP_GUIDE.md for detailed documentation"
