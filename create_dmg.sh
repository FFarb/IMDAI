#!/bin/bash

# IMDAI DMG Creator
# This script creates a distributable DMG installer for macOS

set -e  # Exit on error

echo "=========================================="
echo "IMDAI DMG Creator"
echo "=========================================="
echo ""

# Check if IMDAI.app exists
if [ ! -d "dist/IMDAI.app" ]; then
    echo "❌ Error: dist/IMDAI.app not found!"
    echo "Please run ./build_mac_app.sh first"
    exit 1
fi

# Install create-dmg if not present
if ! command -v create-dmg &> /dev/null; then
    echo "Installing create-dmg..."
    brew install create-dmg || {
        echo "⚠️  create-dmg not available via brew"
        echo "Using manual DMG creation method..."
        USE_MANUAL=true
    }
fi

# Set variables
APP_NAME="IMDAI"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
VOLUME_NAME="${APP_NAME} ${VERSION}"
SOURCE_DIR="dist"
DMG_DIR="dmg_build"

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf "$DMG_DIR"
rm -f "$DMG_NAME"

# Create DMG staging directory
echo "Creating DMG staging directory..."
mkdir -p "$DMG_DIR"

# Copy app to staging
echo "Copying application..."
cp -R "$SOURCE_DIR/IMDAI.app" "$DMG_DIR/"

# Create Applications symlink
echo "Creating Applications symlink..."
ln -s /Applications "$DMG_DIR/Applications"

# Create README
cat > "$DMG_DIR/README.txt" << 'README_EOF'
IMDAI - POD Merch Swarm
Version 1.0.0

INSTALLATION INSTRUCTIONS:
1. Drag IMDAI.app to the Applications folder
2. Open IMDAI from your Applications folder
3. On first launch, you'll be prompted to configure your OpenAI API key
4. Edit the configuration file at: ~/Library/Application Support/IMDAI/.env
5. Restart IMDAI

SYSTEM REQUIREMENTS:
- macOS 10.13 (High Sierra) or later
- Internet connection for AI features

SUPPORT:
For issues or questions, please visit our GitHub repository.

Copyright © 2024
README_EOF

if [ "$USE_MANUAL" = true ]; then
    # Manual DMG creation
    echo ""
    echo "Creating DMG manually..."
    
    # Create temporary DMG
    hdiutil create -volname "$VOLUME_NAME" -srcfolder "$DMG_DIR" -ov -format UDRW temp.dmg
    
    # Mount it
    MOUNT_DIR=$(hdiutil attach -readwrite -noverify -noautoopen temp.dmg | grep Volumes | awk '{print $3}')
    
    # Set background and icon positions (optional)
    echo '
    tell application "Finder"
        tell disk "'$VOLUME_NAME'"
            open
            set current view of container window to icon view
            set toolbar visible of container window to false
            set statusbar visible of container window to false
            set the bounds of container window to {100, 100, 700, 500}
            set viewOptions to the icon view options of container window
            set arrangement of viewOptions to not arranged
            set icon size of viewOptions to 128
            set position of item "IMDAI.app" of container window to {150, 150}
            set position of item "Applications" of container window to {450, 150}
            set position of item "README.txt" of container window to {300, 300}
            close
            open
            update without registering applications
            delay 2
        end tell
    end tell
    ' | osascript || true
    
    # Unmount
    hdiutil detach "$MOUNT_DIR"
    
    # Convert to compressed
    hdiutil convert temp.dmg -format UDZO -o "$DMG_NAME"
    rm temp.dmg
    
else
    # Use create-dmg
    echo ""
    echo "Creating DMG with create-dmg..."
    
    create-dmg \
        --volname "$VOLUME_NAME" \
        --volicon "$SOURCE_DIR/IMDAI.app/Contents/Resources/icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 128 \
        --icon "IMDAI.app" 150 150 \
        --hide-extension "IMDAI.app" \
        --app-drop-link 450 150 \
        --text-size 12 \
        "$DMG_NAME" \
        "$DMG_DIR" || {
            echo "⚠️  create-dmg failed, falling back to manual method"
            USE_MANUAL=true
            # Retry with manual method
            hdiutil create -volname "$VOLUME_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_NAME"
        }
fi

# Clean up staging directory
echo "Cleaning up..."
rm -rf "$DMG_DIR"

# Get DMG size
DMG_SIZE=$(du -h "$DMG_NAME" | cut -f1)

echo ""
echo "=========================================="
echo "DMG Created Successfully! ✨"
echo "=========================================="
echo ""
echo "File: $DMG_NAME"
echo "Size: $DMG_SIZE"
echo ""
echo "You can now distribute this DMG file to users."
echo "They can simply drag IMDAI.app to Applications and run it."
echo ""
