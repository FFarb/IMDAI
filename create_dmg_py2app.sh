#!/bin/bash

# DMG creator for py2app build

set -e

echo "Creating DMG for py2app build..."

if [ ! -d "dist/IMDAI.app" ]; then
    echo "❌ dist/IMDAI.app not found!"
    echo "Run ./build_mac_app_py2app.sh first"
    exit 1
fi

DMG_NAME="IMDAI-py2app-1.0.0.dmg"
STAGING="dmg_py2app"

rm -rf "$STAGING"
rm -f "$DMG_NAME"
mkdir -p "$STAGING"

cp -R "dist/IMDAI.app" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

cat > "$STAGING/README.txt" << 'EOF'
IMDAI - POD Merch Swarm
Built with py2app

INSTALL:
1. Drag IMDAI.app to Applications
2. Launch from Applications
3. Configure API key on first run

All dependencies included!
No Python installation required!

macOS 10.13+ required
EOF

hdiutil create -volname "IMDAI" -srcfolder "$STAGING" -ov -format UDZO "$DMG_NAME"
rm -rf "$STAGING"

echo "✨ Created: $DMG_NAME"
echo "Size: $(du -h "$DMG_NAME" | cut -f1)"
