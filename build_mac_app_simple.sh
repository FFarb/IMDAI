#!/bin/bash

# IMDAI Simple Mac App Builder (using Platypus)
# This is a simpler alternative that creates a Mac app wrapper around the startup script

set -e  # Exit on error

echo "=========================================="
echo "IMDAI Simple Mac App Builder"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Check for Platypus
if ! command -v platypus &> /dev/null; then
    echo "❌ Platypus is not installed."
    echo ""
    echo "Please install Platypus using one of these methods:"
    echo "  1. Homebrew: brew install --cask platypus"
    echo "  2. Download from: https://sveinbjorn.org/platypus"
    echo ""
    exit 1
fi

echo "✓ Found Platypus"

# Build frontend first
echo ""
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✓ Frontend built"

# Create app bundle directory structure
APP_NAME="IMDAI.app"
BUILD_DIR="dist_simple"
APP_DIR="$BUILD_DIR/$APP_NAME"

echo ""
echo "Creating app structure..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create a launcher script that will be wrapped
cat > "$BUILD_DIR/imdai_launcher.sh" << 'LAUNCHER_EOF'
#!/bin/bash

# Get the app's resource directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_RESOURCES="$SCRIPT_DIR/../Resources"

# Create user data directory
USER_DATA_DIR="$HOME/Library/Application Support/IMDAI"
mkdir -p "$USER_DATA_DIR/data"

# Check for .env file
if [ ! -f "$USER_DATA_DIR/.env" ]; then
    cat > "$USER_DATA_DIR/.env" << 'ENV_EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here

# Optional: Uncomment and configure if needed
# OPENAI_ORG_ID=your-org-id-here
# OPENAI_BASE_URL=https://api.openai.com/v1
ENV_EOF
    
    osascript -e 'display dialog "Welcome to IMDAI!\n\nPlease configure your OpenAI API key in:\n~/Library/Application Support/IMDAI/.env\n\nThen restart the application." buttons {"Open Folder", "OK"} default button "Open Folder"' && open "$USER_DATA_DIR"
    exit 0
fi

# Check if API key is configured
if grep -q "your-api-key-here" "$USER_DATA_DIR/.env"; then
    osascript -e 'display dialog "Please configure your OpenAI API key in:\n~/Library/Application Support/IMDAI/.env" buttons {"Open Folder", "Cancel"} default button "Open Folder"' && open "$USER_DATA_DIR"
    exit 0
fi

# Set up Python virtual environment path
VENV_PATH="$APP_RESOURCES/venv"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Export environment variables
export $(cat "$USER_DATA_DIR/.env" | grep -v '^#' | xargs)

# Change to backend directory
cd "$APP_RESOURCES/backend"

# Start backend server
uvicorn app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Open frontend in default browser
open "http://localhost:5173"

# Show notification
osascript -e 'display notification "IMDAI is now running at http://localhost:5173" with title "IMDAI Started"'

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    osascript -e 'display notification "IMDAI has been stopped" with title "IMDAI"'
}

trap cleanup EXIT INT TERM

# Keep running
wait $BACKEND_PID
LAUNCHER_EOF

chmod +x "$BUILD_DIR/imdai_launcher.sh"

# Create the app using Platypus
echo ""
echo "Creating app with Platypus..."

platypus \
    --name "IMDAI" \
    --app-icon /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns \
    --author "IMDAI Team" \
    --app-version "1.0.0" \
    --bundle-identifier "com.imdai.podmerch" \
    --interface-type "None" \
    --interpreter "/bin/bash" \
    --background \
    "$BUILD_DIR/imdai_launcher.sh" \
    "$APP_DIR"

# Copy application files into the app bundle
echo ""
echo "Copying application files..."

RESOURCES_DIR="$APP_DIR/Contents/Resources"

# Create Python virtual environment in the app
echo "Creating embedded Python environment..."
python3 -m venv "$RESOURCES_DIR/venv"
source "$RESOURCES_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r backend/requirements.txt

# Copy backend
echo "Copying backend..."
cp -R backend "$RESOURCES_DIR/"

# Copy frontend
echo "Copying frontend..."
cp -R frontend "$RESOURCES_DIR/"

# Copy data directory
echo "Copying data directory..."
mkdir -p "$RESOURCES_DIR/data"
if [ -d "data" ]; then
    cp -R data/* "$RESOURCES_DIR/data/" 2>/dev/null || true
fi

# Copy .env.example
cp backend/.env.example "$RESOURCES_DIR/backend/" 2>/dev/null || true

echo ""
echo "=========================================="
echo "Build Complete! ✨"
echo "=========================================="
echo ""
echo "Your app is located at: $APP_DIR"
echo ""
echo "To test:"
echo "  1. Double-click $APP_DIR"
echo "  2. Configure your API key when prompted"
echo ""
echo "To create a DMG installer:"
echo "  ./create_dmg_simple.sh"
echo ""
