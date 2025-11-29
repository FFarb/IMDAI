#!/bin/bash

# One-Click Installer Creator for IMDAI
# This creates a self-installing app that requires ZERO user technical knowledge

set -e

echo "=========================================="
echo "Creating One-Click Installer for IMDAI"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Install Platypus if needed
if ! command -v platypus &> /dev/null; then
    echo "Installing Platypus..."
    brew install --cask platypus || {
        echo "❌ Please install Platypus: brew install --cask platypus"
        exit 1
    }
fi

echo "✓ Platypus ready"

# Build frontend
echo ""
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✓ Frontend built"

# Create the auto-installer script
echo ""
echo "Creating auto-installer script..."

cat > auto_installer.sh << 'AUTO_INSTALLER_EOF'
#!/bin/bash

# IMDAI Auto-Installer
# This script runs when the user double-clicks the app
# It handles EVERYTHING automatically

# Show welcome dialog
osascript << 'WELCOME_EOF'
display dialog "Welcome to IMDAI - POD Merch Swarm!

This installer will:
✓ Set up the application
✓ Install all dependencies
✓ Configure the environment
✓ Launch IMDAI

Click 'Install' to begin." buttons {"Cancel", "Install"} default button "Install" with title "IMDAI Installer" with icon note

if button returned of result is "Cancel" then
    error number -128
end if
WELCOME_EOF

if [ $? -ne 0 ]; then
    exit 0
fi

# Show progress
osascript -e 'display notification "Installing IMDAI... This may take a few minutes." with title "IMDAI Installer"' &

# Get the app's resource directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_RESOURCES="$SCRIPT_DIR/../Resources"

# Create application directory in user's home
APP_DIR="$HOME/Applications/IMDAI"
mkdir -p "$APP_DIR"

# Create user data directory
USER_DATA_DIR="$HOME/Library/Application Support/IMDAI"
mkdir -p "$USER_DATA_DIR/data"

# Check if already installed
if [ -f "$APP_DIR/.installed" ]; then
    # Already installed, just launch
    source "$APP_DIR/venv/bin/activate"
    export $(cat "$USER_DATA_DIR/.env" | grep -v '^#' | xargs 2>/dev/null || true)
    
    # Check if API key is configured
    if [ ! -f "$USER_DATA_DIR/.env" ] || grep -q "your-api-key-here" "$USER_DATA_DIR/.env" 2>/dev/null; then
        # Need to configure API key
        API_KEY=$(osascript << 'API_KEY_EOF'
display dialog "Please enter your OpenAI API Key:" default answer "" with title "IMDAI Setup" with icon note buttons {"Cancel", "OK"} default button "OK"
if button returned of result is "OK" then
    return text returned of result
else
    error number -128
end if
API_KEY_EOF
)
        
        if [ $? -eq 0 ] && [ ! -z "$API_KEY" ]; then
            cat > "$USER_DATA_DIR/.env" << ENV_EOF
# OpenAI API Configuration
OPENAI_API_KEY=$API_KEY
ENV_EOF
            export OPENAI_API_KEY="$API_KEY"
        else
            osascript -e 'display dialog "API key is required to use IMDAI." buttons {"OK"} with title "IMDAI" with icon stop'
            exit 1
        fi
    fi
    
    # Launch the app
    cd "$APP_DIR/backend"
    uvicorn app:app --host 127.0.0.1 --port 8000 > "$USER_DATA_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    sleep 3
    
    # Open browser
    open "http://localhost:8000/index.html"
    
    osascript -e 'display notification "IMDAI is now running at http://localhost:8000" with title "IMDAI Started"'
    
    # Create a simple quit mechanism
    trap "kill $BACKEND_PID 2>/dev/null; osascript -e 'display notification \"IMDAI has been stopped\" with title \"IMDAI\"'" EXIT
    
    wait $BACKEND_PID
    exit 0
fi

# First-time installation
echo "Installing IMDAI..."

# Copy application files
cp -R "$APP_RESOURCES/backend" "$APP_DIR/"
cp -R "$APP_RESOURCES/frontend" "$APP_DIR/"
cp -R "$APP_RESOURCES/data" "$APP_DIR/" 2>/dev/null || mkdir -p "$APP_DIR/data"

# Create Python virtual environment
cd "$APP_DIR"
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate

# Show progress
osascript -e 'display notification "Installing Python packages... Please wait." with title "IMDAI Installer"' &

# Install requirements
pip install --upgrade pip > "$USER_DATA_DIR/install.log" 2>&1
pip install -r backend/requirements.txt >> "$USER_DATA_DIR/install.log" 2>&1

# Mark as installed
touch "$APP_DIR/.installed"

# Ask for API key
API_KEY=$(osascript << 'API_KEY_EOF'
display dialog "Installation complete!

Please enter your OpenAI API Key to continue:" default answer "" with title "IMDAI Setup" with icon note buttons {"Skip", "OK"} default button "OK"
if button returned of result is "OK" then
    return text returned of result
else
    return "your-api-key-here"
end if
API_KEY_EOF
)

# Create .env file
cat > "$USER_DATA_DIR/.env" << ENV_EOF
# OpenAI API Configuration
OPENAI_API_KEY=$API_KEY

# Optional: Uncomment and configure if needed
# OPENAI_ORG_ID=your-org-id-here
# OPENAI_BASE_URL=https://api.openai.com/v1
ENV_EOF

if [ "$API_KEY" = "your-api-key-here" ]; then
    osascript << 'SKIP_EOF'
display dialog "You can configure your API key later at:
~/Library/Application Support/IMDAI/.env

IMDAI will now launch." buttons {"OK"} with title "IMDAI Setup"
SKIP_EOF
fi

# Export environment
export OPENAI_API_KEY="$API_KEY"

# Launch the app
cd "$APP_DIR/backend"
uvicorn app:app --host 127.0.0.1 --port 8000 > "$USER_DATA_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

sleep 3

# Open browser
open "http://localhost:8000/index.html"

# Show success
osascript -e 'display notification "IMDAI is now running!" with title "Installation Complete"'

osascript << 'SUCCESS_EOF'
display dialog "IMDAI has been installed and is now running!

Access it at: http://localhost:8000

To quit IMDAI, close this window." buttons {"OK"} with title "IMDAI" with icon note
SUCCESS_EOF

# Keep running
trap "kill $BACKEND_PID 2>/dev/null; osascript -e 'display notification \"IMDAI has been stopped\" with title \"IMDAI\"'" EXIT

wait $BACKEND_PID
AUTO_INSTALLER_EOF

chmod +x auto_installer.sh

# Create the app using Platypus
echo ""
echo "Creating installer app..."

# Create a temporary icon (you can replace this with a real icon)
ICON_PATH="/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns"

platypus \
    --name "Install IMDAI" \
    --app-icon "$ICON_PATH" \
    --author "IMDAI Team" \
    --app-version "1.0.0" \
    --bundle-identifier "com.imdai.installer" \
    --interface-type "None" \
    --interpreter "/bin/bash" \
    --background \
    --quit-after-execution \
    auto_installer.sh \
    "Install IMDAI.app"

# Copy application files into the installer
echo ""
echo "Embedding application files..."

INSTALLER_RESOURCES="Install IMDAI.app/Contents/Resources"

# Copy backend
cp -R backend "$INSTALLER_RESOURCES/"

# Copy frontend
cp -R frontend "$INSTALLER_RESOURCES/"

# Copy data directory
mkdir -p "$INSTALLER_RESOURCES/data"
if [ -d "data" ]; then
    cp -R data/* "$INSTALLER_RESOURCES/data/" 2>/dev/null || true
fi

# Create requirements.txt in resources
cp backend/requirements.txt "$INSTALLER_RESOURCES/backend/"

# Create DMG
echo ""
echo "Creating DMG installer..."

DMG_NAME="IMDAI-OneClick-Installer.dmg"
STAGING="dmg_oneclick"

rm -rf "$STAGING"
rm -f "$DMG_NAME"
mkdir -p "$STAGING"

cp -R "Install IMDAI.app" "$STAGING/"

cat > "$STAGING/README.txt" << 'README_EOF'
IMDAI - POD Merch Swarm
One-Click Installer

INSTALLATION:
1. Double-click "Install IMDAI.app"
2. Click "Install" when prompted
3. Enter your OpenAI API key
4. Wait for installation to complete
5. IMDAI will launch automatically!

That's it! No technical knowledge required!

REQUIREMENTS:
- macOS 10.13 or later
- Internet connection
- OpenAI API key

WHAT HAPPENS:
The installer will automatically:
✓ Install Python and all dependencies
✓ Set up the application
✓ Configure your environment
✓ Launch IMDAI in your browser

AFTER INSTALLATION:
- IMDAI is installed in: ~/Applications/IMDAI
- Configuration: ~/Library/Application Support/IMDAI/.env
- To run again: Double-click "Install IMDAI.app"

Copyright © 2024
README_EOF

hdiutil create -volname "IMDAI Installer" -srcfolder "$STAGING" -ov -format UDZO "$DMG_NAME"
rm -rf "$STAGING"

# Clean up
rm -f auto_installer.sh

DMG_SIZE=$(du -h "$DMG_NAME" | cut -f1)

echo ""
echo "=========================================="
echo "✨ One-Click Installer Created!"
echo "=========================================="
echo ""
echo "File: $DMG_NAME"
echo "Size: $DMG_SIZE"
echo ""
echo "USER INSTRUCTIONS:"
echo "1. Download $DMG_NAME"
echo "2. Double-click to open"
echo "3. Double-click 'Install IMDAI.app'"
echo "4. Follow the prompts"
echo "5. Done!"
echo ""
echo "NO TERMINAL COMMANDS REQUIRED!"
echo "NO TECHNICAL KNOWLEDGE NEEDED!"
echo ""
