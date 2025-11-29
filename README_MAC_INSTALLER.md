# macOS Installer Package Guide

This guide explains how to create a standalone macOS application installer for IMDAI that **does not require users to install Python or any dependencies**.

## 📦 Two Packaging Methods

We provide two methods to create a macOS installer:

### Method 1: Simple (Recommended) - Using Platypus
**Best for:** Quick builds, easier to maintain, smaller file size

### Method 2: Advanced - Using PyInstaller
**Best for:** Fully self-contained single binary, no external dependencies

---

## 🚀 Method 1: Simple Build (Platypus)

### Prerequisites

1. **macOS** (10.13 or later)
2. **Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```
3. **Homebrew** (if not installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
4. **Platypus**
   ```bash
   brew install --cask platypus
   ```
   Or download from: https://sveinbjorn.org/platypus

### Build Steps

1. **Make scripts executable:**
   ```bash
   chmod +x build_mac_app_simple.sh
   chmod +x create_dmg_simple.sh
   ```

2. **Build the app:**
   ```bash
   ./build_mac_app_simple.sh
   ```
   
   This will:
   - Build the React frontend
   - Create a Python virtual environment
   - Install all Python dependencies
   - Package everything into `dist_simple/IMDAI.app`

3. **Create the DMG installer:**
   ```bash
   ./create_dmg_simple.sh
   ```
   
   This creates `IMDAI-Installer-1.0.0.dmg`

### What Gets Packaged

The app bundle includes:
- ✅ Python 3.11+ (embedded in virtual environment)
- ✅ All Python dependencies (FastAPI, OpenAI, LangGraph, etc.)
- ✅ Frontend (built React app)
- ✅ Backend (FastAPI server)
- ✅ All required libraries and tools

### File Size

Expected size: **~500MB - 1GB** (depending on dependencies)

---

## 🔧 Method 2: Advanced Build (PyInstaller)

### Prerequisites

1. **macOS** (10.13 or later)
2. **Python 3.11+**
3. **Node.js 18+**
4. **PyInstaller**
   ```bash
   pip3 install pyinstaller
   ```

### Build Steps

1. **Make scripts executable:**
   ```bash
   chmod +x build_mac_app.sh
   chmod +x create_dmg.sh
   ```

2. **Build the app:**
   ```bash
   ./build_mac_app.sh
   ```
   
   This will:
   - Build the React frontend
   - Use PyInstaller to create a standalone binary
   - Package everything into `dist/IMDAI.app`

3. **Create the DMG installer:**
   ```bash
   ./create_dmg.sh
   ```
   
   This creates `IMDAI-1.0.0.dmg`

### What Gets Packaged

The app bundle includes:
- ✅ Python interpreter (compiled into binary)
- ✅ All Python dependencies (compiled)
- ✅ Frontend (built React app)
- ✅ Backend (compiled binary)

### File Size

Expected size: **~300MB - 800MB** (more optimized than Method 1)

---

## 📱 How Users Install

1. **Download** the DMG file
2. **Open** the DMG
3. **Drag** IMDAI.app to the Applications folder
4. **Launch** IMDAI from Applications
5. **Configure** OpenAI API key on first run

### First Run Experience

When users first launch the app:
1. A dialog appears asking them to configure their OpenAI API key
2. The configuration folder opens automatically
3. They edit `~/.env` file with their API key
4. They restart the app
5. The app launches and opens in their default browser

### User Configuration Location

```
~/Library/Application Support/IMDAI/
├── .env              # API key configuration
└── data/             # Application data
```

---

## 🎨 Customization

### Adding an App Icon

1. Create an `.icns` file (macOS icon format)
2. Place it in the project root as `icon.icns`
3. Update the build script to reference it:

For Platypus method:
```bash
platypus --app-icon icon.icns ...
```

For PyInstaller method:
```python
# In backend_bundle.spec
app = BUNDLE(
    ...
    icon='icon.icns',
    ...
)
```

### Changing App Name or Version

Edit the build scripts and modify:
- `APP_NAME="IMDAI"`
- `VERSION="1.0.0"`
- `bundle_identifier='com.imdai.podmerch'`

### Code Signing (for Distribution)

To distribute outside the App Store, you need to sign the app:

1. **Get a Developer ID Certificate** from Apple
2. **Sign the app:**
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/IMDAI.app
   ```
3. **Notarize the app** (required for macOS 10.15+):
   ```bash
   xcrun notarytool submit IMDAI-1.0.0.dmg --apple-id your@email.com --password app-specific-password --team-id TEAMID
   ```

---

## 🐛 Troubleshooting

### "App is damaged and can't be opened"

This happens when the app isn't signed. Users can bypass this:
```bash
xattr -cr /Applications/IMDAI.app
```

Or right-click the app → Open → Open anyway

### "Python not found" error

The virtual environment might not be properly embedded. Rebuild with:
```bash
rm -rf dist_simple
./build_mac_app_simple.sh
```

### Large file size

To reduce size:
1. Remove unused dependencies from `requirements.txt`
2. Use PyInstaller method instead of Platypus
3. Exclude unnecessary files in the build script

### Backend won't start

Check the logs:
```bash
tail -f ~/Library/Application\ Support/IMDAI/backend.log
```

---

## 📊 Comparison

| Feature | Platypus (Simple) | PyInstaller (Advanced) |
|---------|-------------------|------------------------|
| Build Time | Fast (~5 min) | Slower (~15 min) |
| File Size | Larger (~1GB) | Smaller (~500MB) |
| Complexity | Easy | Moderate |
| Maintenance | Easier | More complex |
| Startup Speed | Fast | Very Fast |
| Dependencies | Virtual env | Compiled binary |

---

## 🚢 Distribution Checklist

Before distributing your DMG:

- [ ] Test the app on a clean macOS installation
- [ ] Verify all dependencies are included
- [ ] Test with a fresh API key configuration
- [ ] Check that the frontend loads correctly
- [ ] Verify the backend starts without errors
- [ ] Test on different macOS versions (10.13+)
- [ ] Sign the app with Developer ID (optional but recommended)
- [ ] Notarize the app (required for macOS 10.15+)
- [ ] Create release notes
- [ ] Upload to distribution platform (GitHub Releases, website, etc.)

---

## 📝 License & Distribution

Make sure to:
1. Include all necessary licenses for bundled dependencies
2. Update copyright information in Info.plist
3. Add a LICENSE file to the DMG
4. Comply with OpenAI's usage policies

---

## 🆘 Support

If you encounter issues:

1. Check the build logs
2. Verify all prerequisites are installed
3. Try rebuilding from scratch
4. Check the GitHub issues page
5. Review the PyInstaller/Platypus documentation

---

## 🎯 Quick Start Summary

**For most users, use Method 1 (Simple):**

```bash
# Install Platypus
brew install --cask platypus

# Build the app
chmod +x build_mac_app_simple.sh create_dmg_simple.sh
./build_mac_app_simple.sh

# Create installer
./create_dmg_simple.sh

# Distribute IMDAI-Installer-1.0.0.dmg
```

That's it! Users can now install and run IMDAI without installing Python or any dependencies! 🎉
