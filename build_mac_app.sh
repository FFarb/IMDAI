#!/bin/bash

# IMDAI macOS App Builder
# This script creates a standalone macOS application bundle (.app)
# that includes Python, all dependencies, and the frontend

set -e  # Exit on error

echo "=========================================="
echo "IMDAI macOS App Builder"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Check for Python 3.11+
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check for Node.js
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Found Node.js $NODE_VERSION"

# Create build directory
BUILD_DIR="build_macos"
echo ""
echo "Creating build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Install PyInstaller if not present
echo ""
echo "Installing PyInstaller..."
pip3 install pyinstaller

# Build frontend
echo ""
echo "=========================================="
echo "Building Frontend..."
echo "=========================================="
cd frontend
npm install
npm run build
cd ..

echo "✓ Frontend built successfully!"

# Create backend bundle with PyInstaller
echo ""
echo "=========================================="
echo "Building Backend Bundle..."
echo "=========================================="

# Create PyInstaller spec file
cat > backend_bundle.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend/.env.example', '.'),
        ('backend/agents', 'agents'),
        ('backend/models', 'models'),
        ('backend/utils', 'utils'),
        ('backend/rag', 'rag'),
        ('frontend/dist', 'frontend/dist'),
        ('data', 'data'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'openai',
        'fastapi',
        'pydantic',
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
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='imdai_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='imdai_backend',
)

app = BUNDLE(
    coll,
    name='IMDAI.app',
    icon=None,
    bundle_identifier='com.imdai.podmerch',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024',
    },
)
EOF

# Run PyInstaller
echo "Running PyInstaller..."
pyinstaller backend_bundle.spec --clean --noconfirm

echo "✓ Backend bundle created successfully!"

# Create launcher script inside the app
echo ""
echo "Creating launcher script..."
mkdir -p "dist/IMDAI.app/Contents/MacOS"

cat > "dist/IMDAI.app/Contents/MacOS/IMDAI_launcher.sh" << 'LAUNCHER_EOF'
#!/bin/bash

# Get the directory where the app is located
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
RESOURCES_DIR="$APP_DIR/Resources"

# Set up environment
export PYTHONPATH="$RESOURCES_DIR"

# Create data directory in user's home if it doesn't exist
USER_DATA_DIR="$HOME/Library/Application Support/IMDAI"
mkdir -p "$USER_DATA_DIR/data"

# Check for .env file
if [ ! -f "$USER_DATA_DIR/.env" ]; then
    # Copy example .env
    if [ -f "$RESOURCES_DIR/.env.example" ]; then
        cp "$RESOURCES_DIR/.env.example" "$USER_DATA_DIR/.env"
    else
        # Create default .env
        cat > "$USER_DATA_DIR/.env" << 'ENV_EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here

# Optional: Uncomment and configure if needed
# OPENAI_ORG_ID=your-org-id-here
# OPENAI_BASE_URL=https://api.openai.com/v1
ENV_EOF
    fi
    
    # Prompt user to configure API key
    osascript -e 'display dialog "Welcome to IMDAI!\n\nPlease configure your OpenAI API key in:\n~/Library/Application Support/IMDAI/.env\n\nThen restart the application." buttons {"OK"} default button "OK" with icon caution'
    open "$USER_DATA_DIR"
    exit 0
fi

# Check if API key is configured
if grep -q "your-api-key-here" "$USER_DATA_DIR/.env"; then
    osascript -e 'display dialog "Please configure your OpenAI API key in:\n~/Library/Application Support/IMDAI/.env\n\nThen restart the application." buttons {"Open Folder", "Cancel"} default button "Open Folder" with icon caution' && open "$USER_DATA_DIR"
    exit 0
fi

# Export .env variables
export $(cat "$USER_DATA_DIR/.env" | grep -v '^#' | xargs)

# Start backend server in background
cd "$RESOURCES_DIR"
"$RESOURCES_DIR/imdai_backend/imdai_backend" &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Open frontend in default browser
open "http://localhost:8000/index.html"

# Show notification
osascript -e 'display notification "IMDAI is now running!" with title "IMDAI" subtitle "Access at http://localhost:8000"'

# Keep the app running
wait $BACKEND_PID
LAUNCHER_EOF

chmod +x "dist/IMDAI.app/Contents/MacOS/IMDAI_launcher.sh"

# Update Info.plist to use launcher script
cat > "dist/IMDAI.app/Contents/Info.plist" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>IMDAI_launcher.sh</string>
    <key>CFBundleIdentifier</key>
    <string>com.imdai.podmerch</string>
    <key>CFBundleName</key>
    <string>IMDAI</string>
    <key>CFBundleDisplayName</key>
    <string>IMDAI - POD Merch Swarm</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024</string>
</dict>
</plist>
PLIST_EOF

# Copy frontend build to Resources
echo "Copying frontend to app bundle..."
cp -r frontend/dist/* "dist/IMDAI.app/Contents/Resources/"

echo ""
echo "=========================================="
echo "Build Complete! ✨"
echo "=========================================="
echo ""
echo "Your app is located at: dist/IMDAI.app"
echo ""
echo "Next steps:"
echo "1. Test the app by double-clicking dist/IMDAI.app"
echo "2. Run ./create_dmg.sh to create a distributable installer"
echo ""
