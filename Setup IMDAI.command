#!/bin/bash

# IMDAI One-Click Setup for Mac
# This script does everything automatically!

echo "╔════════════════════════════════════════╗"
echo "║   IMDAI - POD Merch Swarm Setup       ║"
echo "╔════════════════════════════════════════╗"
echo ""

# Show welcome message
osascript << 'WELCOME'
display dialog "Welcome to IMDAI!

This setup will:
✓ Install Python dependencies
✓ Build the frontend
✓ Configure your API key
✓ Launch IMDAI

Click 'Continue' to begin." buttons {"Cancel", "Continue"} default button "Continue" with title "IMDAI Setup" with icon note
WELCOME

if [ $? -ne 0 ]; then
    echo "Setup cancelled."
    exit 0
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Show progress
osascript -e 'display notification "Setting up IMDAI... This will take a few minutes." with title "IMDAI Setup"' &

echo ""
echo "📦 Installing Backend Dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for Python
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 is not installed.\n\nPlease install Python from:\nhttps://www.python.org/downloads/" buttons {"OK"} with icon stop'
    open "https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python packages (this may take 2-5 minutes)..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -ne 0 ]; then
    osascript -e 'display dialog "Failed to install Python packages.\n\nPlease check your internet connection and try again." buttons {"OK"} with icon stop'
    exit 1
fi

echo "✓ Backend dependencies installed!"

cd ..

# Check for Node.js
echo ""
echo "🎨 Building Frontend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v node &> /dev/null; then
    osascript -e 'display dialog "Node.js is not installed.\n\nPlease install Node.js from:\nhttps://nodejs.org/" buttons {"OK"} with icon stop'
    open "https://nodejs.org/"
    exit 1
fi

cd frontend

# Install frontend dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend packages..."
    npm install > /dev/null 2>&1
fi

# Build frontend
echo "Building frontend..."
npm run build > /dev/null 2>&1

if [ $? -ne 0 ]; then
    osascript -e 'display dialog "Failed to build frontend.\n\nPlease check your internet connection and try again." buttons {"OK"} with icon stop'
    exit 1
fi

echo "✓ Frontend built!"

cd ..

# Configure API key
echo ""
echo "🔑 Configuring API Key..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "backend/.env" ]; then
    # Ask for API key
    API_KEY=$(osascript << 'APIKEY'
display dialog "Please enter your OpenAI API Key:" default answer "" with title "IMDAI Setup" with icon note buttons {"Skip", "Save"} default button "Save"
if button returned of result is "Save" then
    return text returned of result
else
    return "your-api-key-here"
end if
APIKEY
)
    
    # Create .env file
    cat > backend/.env << ENVFILE
# OpenAI API Configuration
OPENAI_API_KEY=$API_KEY

# Optional: Uncomment and configure if needed
# OPENAI_ORG_ID=your-org-id-here
# OPENAI_BASE_URL=https://api.openai.com/v1
ENVFILE
    
    if [ "$API_KEY" = "your-api-key-here" ]; then
        echo "⚠️  API key not configured. You can set it later in backend/.env"
    else
        echo "✓ API key saved!"
    fi
else
    echo "✓ API key already configured!"
fi

# Create data directory
mkdir -p data

# Create launcher script
echo ""
echo "🚀 Creating Launcher..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > "Launch IMDAI.command" << 'LAUNCHER'
#!/bin/bash

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source backend/venv/bin/activate

# Load environment variables
if [ -f "backend/.env" ]; then
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

# Check API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-api-key-here" ]; then
    osascript -e 'display dialog "Please configure your OpenAI API key in:\nbackend/.env" buttons {"Open Folder", "Cancel"} default button "Open Folder"' && open "$SCRIPT_DIR/backend"
    exit 0
fi

# Start backend
echo "Starting IMDAI..."
cd backend
uvicorn app:app --host 127.0.0.1 --port 8000 > ../imdai.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    osascript -e 'display dialog "Failed to start backend.\n\nCheck imdai.log for details." buttons {"OK"} with icon stop'
    exit 1
fi

# Open browser
open "http://localhost:8000/index.html"

# Show notification
osascript -e 'display notification "IMDAI is running at http://localhost:8000" with title "IMDAI Started"'

# Show dialog
osascript << 'RUNNING'
display dialog "IMDAI is now running!

Access it at: http://localhost:8000

To stop IMDAI, close this window or press Ctrl+C in Terminal." buttons {"OK"} with title "IMDAI" giving up after 5
RUNNING

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null; osascript -e 'display notification \"IMDAI stopped\" with title \"IMDAI\"'" EXIT

# Keep running
wait $BACKEND_PID
LAUNCHER

chmod +x "Launch IMDAI.command"

echo "✓ Launcher created!"

# Setup complete
echo ""
echo "╔════════════════════════════════════════╗"
echo "║     Setup Complete! ✨                 ║"
echo "╔════════════════════════════════════════╗"
echo ""
echo "To launch IMDAI:"
echo "  → Double-click 'Launch IMDAI.command'"
echo ""
echo "Or run from Terminal:"
echo "  → ./start_mac.sh"
echo ""

osascript << 'COMPLETE'
display dialog "Setup Complete! ✨

IMDAI has been installed successfully!

To launch IMDAI:
• Double-click 'Launch IMDAI.command'

Would you like to launch IMDAI now?" buttons {"Later", "Launch Now"} default button "Launch Now" with title "IMDAI Setup Complete"
COMPLETE

if [ $? -eq 0 ]; then
    # User clicked "Launch Now"
    ./Launch\ IMDAI.command &
fi
