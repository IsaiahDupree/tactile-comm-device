# Large Files - To Be Added

## 📁 Files Not Yet Uploaded (Due to Size Limits)

The following directories contain large files that need to be added separately:

### 🎵 Audio Files (~100MB)
**Location:** `../Button/audio/`
- Contains organized MP3 files in numbered folders (01/, 02/, etc.)
- Sample recordings and TTS audio
- **Action needed:** Set up Git LFS or external hosting

### 🎨 3D Model Files (~400MB)
**Location:** `../Button/hardware/3d-models/` and various STL files
- Letter button STL files
- Enclosure designs
- Case models
- **Action needed:** Use Git LFS for large binary files

### 📚 Library Dependencies (~50MB)
**Location:** `../Button/libraries/`
- Adafruit libraries (BusIO, PCF8574, VS1053)
- **Action needed:** Document in README instead of including

## 🔧 How to Add Large Files Later

### Option 1: Git LFS (Recommended)
```bash
# Install Git LFS
git lfs install

# Track large file types
git lfs track "*.stl"
git lfs track "*.mp3"
git lfs track "*.f3d"

# Add and commit
git add .gitattributes
git add hardware/3d-models/
git add audio/
git commit -m "Add 3D models and audio files via Git LFS"
git push
```

### Option 2: External Hosting
- Host STL files on Thingiverse or GitHub Releases
- Host audio samples on separate storage
- Link to downloads in README

### Option 3: Repository Releases
- Create GitHub releases with ZIP attachments
- Include all large files as downloadable assets
- Reference in main README

## ✅ Currently Uploaded (Core Files)

- ✅ Arduino firmware (`firmware/`)
- ✅ Complete documentation (`docs/`)
- ✅ Hardware BOM (`hardware/bom/bom.csv`)
- ✅ Configuration samples (`config/`)
- ✅ GitHub workflows (`.github/`)
- ✅ Project README and licenses

## 🎯 Next Steps

1. **Test current repository** - firmware and docs are functional
2. **Set up Git LFS** for 3D models and audio
3. **Create first release** with downloadable assets
4. **Update README** with links to large file downloads

The core project is now live and functional on GitHub! 🚀
