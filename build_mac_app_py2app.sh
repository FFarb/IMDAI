#!/bin/bash

# IMDAI py2app Builder
# Uses py2app (macOS-specific) to create a native Mac application

set -e

echo "=========================================="
echo "IMDAI py2app Builder"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Install py2app if needed
echo "Checking for py2app..."
pip3 install py2app 2>/dev/null || {
    echo "Installing py2app..."
    pip3 install py2app
}

echo "✓ py2app is ready"

# Build frontend
echo ""
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✓ Frontend built"

# Create setup.py for py2app
echo ""
echo "Creating py2app configuration..."

cat > setup_mac.py << 'SETUP_EOF'
"""
py2app build script for IMDAI
"""

from setuptools import setup
import os

APP = ['backend/app.py']
DATA_FILES = [
    ('backend/agents', ['backend/agents']),
    ('backend/models', ['backend/models']),
    ('backend/utils', ['backend/utils']),
    ('backend/rag', ['backend/rag']),
    ('frontend/dist', ['frontend/dist']),
    ('data', ['data']),
    ('.', ['backend/.env.example']),
]

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'uvicorn',
        'fastapi',
        'pydantic',
        'openai',
        'httpx',
        'dotenv',
        'langgraph',
        'langchain_openai',
        'langchain_core',
        'chromadb',
        'PIL',
        'ddgs',
        'rembg',
        'sqlalchemy',
    ],
    'includes': [
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'numpy.distutils',
    ],
    'plist': {
        'CFBundleName': 'IMDAI',
        'CFBundleDisplayName': 'IMDAI - POD Merch Swarm',
        'CFBundleIdentifier': 'com.imdai.podmerch',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13',
        'LSBackgroundOnly': False,
    },
    'iconfile': None,  # Add path to .icns file if you have one
}

setup(
    name='IMDAI',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
SETUP_EOF

# Install dependencies in current environment
echo ""
echo "Installing dependencies..."
pip3 install -r backend/requirements.txt

# Build the app
echo ""
echo "Building app with py2app..."
python3 setup_mac.py py2app

# Create launcher script
echo ""
echo "Creating launcher..."

LAUNCHER_SCRIPT="dist/IMDAI.app/Contents/MacOS/imdai_launcher"

cat > "$LAUNCHER_SCRIPT" << 'LAUNCHER_EOF'
#!/bin/bash

# Get app directory
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../Resources" && pwd )"

# User data directory
USER_DATA_DIR="$HOME/Library/Application Support/IMDAI"
mkdir -p "$USER_DATA_DIR/data"

# Check for .env
if [ ! -f "$USER_DATA_DIR/.env" ]; then
    cat > "$USER_DATA_DIR/.env" << 'ENV_EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here
ENV_EOF
    
    osascript -e 'display dialog "Welcome to IMDAI!\n\nConfigure your OpenAI API key:\n~/Library/Application Support/IMDAI/.env" buttons {"Open Folder"} default button "Open Folder"' && open "$USER_DATA_DIR"
    exit 0
fi

# Check if configured
if grep -q "your-api-key-here" "$USER_DATA_DIR/.env"; then
    osascript -e 'display dialog "Please configure your OpenAI API key in:\n~/Library/Application Support/IMDAI/.env" buttons {"Open Folder"} default button "Open Folder"' && open "$USER_DATA_DIR"
    exit 0
fi

# Export environment
export $(cat "$USER_DATA_DIR/.env" | grep -v '^#' | xargs)

# Start backend
cd "$APP_DIR"
exec python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

sleep 3

# Open browser
open "http://localhost:8000/index.html"

# Notification
osascript -e 'display notification "IMDAI is running!" with title "IMDAI"'

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT

wait $BACKEND_PID
LAUNCHER_EOF

chmod +x "$LAUNCHER_SCRIPT"

# Update Info.plist to use launcher
PLIST_FILE="dist/IMDAI.app/Contents/Info.plist"
if [ -f "$PLIST_FILE" ]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleExecutable imdai_launcher" "$PLIST_FILE"
fi

echo ""
echo "=========================================="
echo "Build Complete! ✨"
echo "=========================================="
echo ""
echo "Your app is at: dist/IMDAI.app"
echo ""
echo "Test it:"
echo "  open dist/IMDAI.app"
echo ""
echo "Create DMG:"
echo "  ./create_dmg_py2app.sh"
echo ""
