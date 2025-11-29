# 🍎 macOS Installer - Quick Reference

## Three Methods Available

### 1️⃣ **Platypus Method** (Easiest - RECOMMENDED)
```bash
# Install Platypus
brew install --cask platypus

# Build
chmod +x build_mac_app_simple.sh create_dmg_simple.sh
./build_mac_app_simple.sh
./create_dmg_simple.sh
```
**Output:** `IMDAI-Installer-1.0.0.dmg` (~1GB)

---

### 2️⃣ **py2app Method** (Native macOS)
```bash
# Install py2app
pip3 install py2app

# Build
chmod +x build_mac_app_py2app.sh create_dmg_py2app.sh
./build_mac_app_py2app.sh
./create_dmg_py2app.sh
```
**Output:** `IMDAI-py2app-1.0.0.dmg` (~800MB)

---

### 3️⃣ **PyInstaller Method** (Most Optimized)
```bash
# Install PyInstaller
pip3 install pyinstaller

# Build
chmod +x build_mac_app.sh create_dmg.sh
./build_mac_app.sh
./create_dmg.sh
```
**Output:** `IMDAI-1.0.0.dmg` (~500MB)

---

## 📊 Which Method Should I Use?

| Method | Difficulty | Build Time | Size | Best For |
|--------|-----------|------------|------|----------|
| **Platypus** | ⭐ Easy | 5 min | 1GB | Quick builds, testing |
| **py2app** | ⭐⭐ Medium | 10 min | 800MB | Native macOS feel |
| **PyInstaller** | ⭐⭐⭐ Hard | 15 min | 500MB | Production, distribution |

**Recommendation:** Start with **Platypus** for testing, use **PyInstaller** for final distribution.

---

## 🚀 What Users Get

After installing your DMG, users get:
- ✅ **No Python installation needed**
- ✅ **No dependency installation needed**
- ✅ **Double-click to run**
- ✅ **Native macOS app**
- ✅ **Automatic browser launch**
- ✅ **Easy API key configuration**

---

## 📦 What's Included in the Package

All methods include:
- Python 3.11+ (embedded)
- FastAPI backend
- React frontend (built)
- All Python packages:
  - openai
  - fastapi
  - langgraph
  - chromadb
  - rembg
  - And all other dependencies

---

## 🎯 One-Line Build (Platypus)

```bash
brew install --cask platypus && chmod +x build_mac_app_simple.sh create_dmg_simple.sh && ./build_mac_app_simple.sh && ./create_dmg_simple.sh
```

---

## 🐛 Common Issues

### "App can't be opened because it is from an unidentified developer"
**Solution:** Right-click → Open → Open

### "Platypus not found"
**Solution:** `brew install --cask platypus`

### "py2app not found"
**Solution:** `pip3 install py2app`

### "Build failed"
**Solution:** 
1. Clean build: `rm -rf dist dist_simple build`
2. Rebuild frontend: `cd frontend && npm install && npm run build && cd ..`
3. Try again

---

## 📝 Before Distribution

- [ ] Test on clean Mac
- [ ] Verify API key setup works
- [ ] Check frontend loads
- [ ] Test backend starts
- [ ] Sign app (optional): `codesign --deep --force --sign "Developer ID" dist/IMDAI.app`
- [ ] Notarize (for macOS 10.15+)

---

## 🎨 Customization

### Add App Icon
1. Create `icon.icns` (512x512 PNG → icns)
2. Place in project root
3. Update build script icon path

### Change Version
Edit in build scripts:
- `VERSION="1.0.0"`
- `CFBundleVersion`

---

## 📚 Full Documentation

See `README_MAC_INSTALLER.md` for complete details.

---

## 💡 Tips

1. **First build?** Use Platypus method
2. **Distributing?** Use PyInstaller method
3. **Testing locally?** Just use `./start_mac.sh`
4. **Need smaller file?** Use PyInstaller
5. **Want fastest build?** Use Platypus

---

## 🆘 Need Help?

1. Check `README_MAC_INSTALLER.md`
2. Review build logs
3. Try rebuilding from scratch
4. Check GitHub issues

---

**Ready to build?** Pick a method above and run the commands! 🚀
