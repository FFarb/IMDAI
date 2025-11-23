#!/bin/bash

# IMDAI Installation Script for macOS
# This script sets up both backend and frontend environments

set -e  # Exit on error

echo "=========================================="
echo "IMDAI - POD Merch Swarm Installation"
echo "=========================================="
echo ""

# Check for Python 3.11+
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check for Node.js 18+
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Found Node.js $NODE_VERSION"

# Install Backend Dependencies
echo ""
echo "=========================================="
echo "Installing Backend Dependencies..."
echo "=========================================="
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

echo "✓ Backend dependencies installed successfully!"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cat > .env << 'EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here

# Optional: Uncomment and configure if needed
# OPENAI_ORG_ID=your-org-id-here
# OPENAI_BASE_URL=https://api.openai.com/v1
EOF
    echo "⚠️  Please edit backend/.env and add your OPENAI_API_KEY"
else
    echo ".env file already exists."
fi

cd ..

# Install Frontend Dependencies
echo ""
echo "=========================================="
echo "Installing Frontend Dependencies..."
echo "=========================================="
cd frontend

echo "Installing npm packages..."
npm install

echo "✓ Frontend dependencies installed successfully!"

cd ..

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo ""
    echo "Creating data directory..."
    mkdir -p data
fi

echo ""
echo "=========================================="
echo "Installation Complete! ✨"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your OPENAI_API_KEY"
echo "2. Run ./start_mac.sh to start the application"
echo ""
