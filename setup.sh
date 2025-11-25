#!/bin/bash
# Quick setup script for Agritech Assistant
# Run this after cloning the repository

set -e  # Exit on error

echo "🌱 Agritech Assistant - Setup Script"
echo "===================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "🔨 Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  .venv directory already exists, skipping..."
else
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip -q
echo "✅ pip upgraded"

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -e .[dev] -q
echo "✅ Dependencies installed"

# Create .env if it doesn't exist
echo ""
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists, skipping..."
else
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY"
    echo "   Get your key from: https://aistudio.google.com/app/apikey"
fi

# Run tests
echo ""
echo "🧪 Running tests..."
pytest -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed"
    exit 1
fi

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Edit .env and add your GEMINI_API_KEY"
echo ""
echo "3. Start the server:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "4. Visit http://127.0.0.1:8000/docs to test the API"
echo ""
echo "For more details, see docs/SETUP.md"
