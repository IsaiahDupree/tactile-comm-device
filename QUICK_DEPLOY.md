# Quick Repository Deployment

## 🚨 Repository Size Issue Detected

The repository is 556MB due to large 3D model files and audio samples. GitHub has upload limits.

## ✅ Solution: Deploy Core Files First

### Step 1: Create Essential Files Repository

```bash
# Create a new directory with just essential files
mkdir tactile-comm-device-core
cd tactile-comm-device-core

# Copy essential files
cp ../README.md .
cp ../LICENSE .
cp ../CONTRIBUTING.md .
cp ../.gitignore .
cp -r ../firmware .
cp -r ../docs .
cp -r ../config .
cp -r ../.github .
```

### Step 2: Create Hardware BOM Only
```bash
mkdir hardware
mkdir hardware/bom
cp ../hardware/bom/bom.csv hardware/bom/
```

### Step 3: Create Audio Structure Guide
```bash
mkdir audio
cp ../audio/ORGANIZATION.md audio/
# Add just a few sample MP3s instead of all audio files
```

### Step 4: Upload Core Repository
```bash
git init
git add .
git commit -m "Core tactile communication device files"
git remote add origin https://github.com/IsaiahDupree/tactile-comm-device.git
git branch -M main
git push -u origin main --force
```

### Step 5: Add Large Files Separately
- Use Git LFS for 3D models
- Host audio files on separate storage
- Link to external downloads in README

## 📋 Files Successfully Ready for Upload

✅ **Essential Files (< 10MB)**:
- Arduino firmware
- Complete documentation
- BOM and parts list
- GitHub workflows
- Setup and troubleshooting guides

⚠️ **Large Files to Handle Separately**:
- 3D model STL files (400MB+)
- Audio sample files (100MB+)
- Library dependencies (50MB+)

## 🎯 Recommended Action

1. Upload core files first (firmware + docs)
2. Add large files via Git LFS later
3. Create releases for downloadable assets
4. Link to external audio samples

This approach gives you a functional repository immediately while handling large files properly.
