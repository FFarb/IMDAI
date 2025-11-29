#!/bin/bash

# Simple DMG Creator for Platypus-based app

set -e

echo "=========================================="
echo "Creating DMG Installer"
echo "=========================================="
echo ""

# Check if app exists
if [ ! -d "dist_simple/IMDAI.app" ]; then
    echo "❌ Error: dist_simple/IMDAI.app not found!"
    echo "Please run ./build_mac_app_simple.sh first"
    exit 1
fi

DMG_NAME="IMDAI-Installer-1.0.0.dmg"
VOLUME_NAME="IMDAI Installer"
SOURCE_DIR="dist_simple"
STAGING_DIR="dmg_staging"

# Clean up
echo "Preparing..."
rm -rf "$STAGING_DIR"
rm -f "$DMG_NAME"
mkdir -p "$STAGING_DIR"

# Copy app
echo "Copying application..."
cp -R "$SOURCE_DIR/IMDAI.app" "$STAGING_DIR/"

# Create Applications symlink
ln -s /Applications "$STAGING_DIR/Applications"

# Create README
cat > "$STAGING_DIR/README.txt" << 'README_EOF'
IMDAI - POD Merch Swarm
Version 1.0.0

INSTALLATION:
1. Drag IMDAI.app to the Applications folder
2. Open IMDAI from Applications
3. Configure your OpenAI API key when prompted

The app includes:
✓ Python 3.11+ (embedded)
✓ All required dependencies
✓ Frontend and backend

No additional installation required!

FIRST RUN:
- You'll be prompted to set up your OpenAI API key
- Configuration is stored in: ~/Library/Application Support/IMDAI/.env

REQUIREMENTS:
- macOS 10.13 or later
- Internet connection

Copyright © 2024
README_EOF

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_NAME"

# Clean up
rm -rf "$STAGING_DIR"

# Get size
DMG_SIZE=$(du -h "$DMG_NAME" | cut -f1)

echo ""
echo "=========================================="
echo "✨ DMG Created Successfully!"
echo "=========================================="
echo ""
echo "File: $DMG_NAME"
echo "Size: $DMG_SIZE"
echo ""
echo "Users can now:"
echo "1. Download this DMG"
echo "2. Open it"
echo "3. Drag IMDAI to Applications"
echo "4. Run without installing Python!"
echo ""
