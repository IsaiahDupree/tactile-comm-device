#!/usr/bin/env python3
"""
Setup script for copying strict-mode SD card structure to actual SD card.
Validates structure and provides setup instructions.
"""

import os
import shutil
from pathlib import Path
import json

def validate_structure(base_dir):
    """Validate the strict-mode SD card structure."""
    print("🔍 Validating SD card structure...")
    
    errors = []
    warnings = []
    
    # Check required directories
    required_dirs = [
        "config",
        "mappings/playlists", 
        "audio/human",
        "audio/generated",
        "state",
        "_staging",
        "_rollback"
    ]
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            errors.append(f"Missing directory: {dir_path}")
    
    # Check required config files
    config_files = ["config/mode.cfg", "config/buttons.csv"]
    for config_file in config_files:
        full_path = base_dir / config_file
        if not full_path.exists():
            errors.append(f"Missing config file: {config_file}")
    
    # Check playlist files
    playlist_dir = base_dir / "mappings" / "playlists"
    if playlist_dir.exists():
        playlists = list(playlist_dir.glob("*.m3u"))
        print(f"Found {len(playlists)} playlist files")
        
        # Validate playlist content
        for playlist in playlists:
            with open(playlist, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Check if referenced audio file path is valid format
                        if not line.startswith('audio/'):
                            warnings.append(f"{playlist.name}:{line_num} - Path should start with 'audio/'")
    
    # Check buttons.csv format
    buttons_file = base_dir / "config" / "buttons.csv"
    if buttons_file.exists():
        with open(buttons_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if ',' not in line:
                        errors.append(f"buttons.csv:{line_num} - Invalid format, missing comma")
    
    # Report results
    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print(f"  • {error}")
        return False
    
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
    
    print("✅ Structure validation passed!")
    return True

def copy_to_sd_card(source_dir, target_drive):
    """Copy the structure to SD card."""
    print(f"📁 Copying structure to {target_drive}...")
    
    if not Path(target_drive).exists():
        print(f"❌ Target drive {target_drive} does not exist!")
        return False
    
    try:
        # Copy entire structure
        for item in source_dir.iterdir():
            target_path = Path(target_drive) / item.name
            
            if item.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(item, target_path)
                print(f"  📂 Copied directory: {item.name}")
            else:
                shutil.copy2(item, target_path)
                print(f"  📄 Copied file: {item.name}")
        
        print("✅ Copy completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Copy failed: {e}")
        return False

def show_setup_instructions():
    """Show setup instructions."""
    print("""
🚀 SD Card Setup Instructions:

1. **Format SD Card**:
   - Use FAT32 format
   - Recommended: 8GB or larger
   - Quick format is fine

2. **Copy Structure**:
   - Run this script with your SD card drive letter
   - Example: python setup_sd_card.py E:

3. **Add Audio Files**:
   - Place your MP3 files in /audio/human/<KEY>/ folders
   - Place TTS MP3 files in /audio/generated/<KEY>/ folders
   - Follow the naming convention: 001.mp3, 002.mp3, etc.

4. **Update Playlists**:
   - Edit M3U files to match your actual audio files
   - Ensure paths are correct and files exist

5. **Test Configuration**:
   - Insert SD card into device
   - Use serial commands to verify setup:
     - 'L' to load configuration
     - 'P' to print current mappings
     - 'T' to test all buttons

📋 Quick Checklist:
□ SD card formatted as FAT32
□ All directories copied
□ Audio files added to correct folders
□ Playlists updated to reference real files
□ Configuration tested on device

🎵 Audio File Organization:
/audio/human/A/001.mp3      ← Your recorded "A" sound
/audio/generated/A/001.mp3  ← TTS "A" sound
/audio/generated/A/002.mp3  ← TTS "Apple"
/audio/generated/A/003.mp3  ← TTS "Airplane"
...

💡 Pro Tips:
- Use consistent 001.mp3, 002.mp3 numbering
- Keep filenames short and simple
- Test one key at a time during setup
- Use 'U' command to verify all files exist
""")

def main():
    """Main setup function."""
    import sys
    
    print("🎛️  Tactile Communication Device - SD Card Setup")
    print("=" * 50)
    
    base_dir = Path(__file__).parent / "sd_strict_mode"
    
    if not base_dir.exists():
        print(f"❌ Source directory not found: {base_dir}")
        print("Run generate_strict_playlists.py first!")
        return
    
    # Validate structure
    if not validate_structure(base_dir):
        print("❌ Please fix validation errors before proceeding.")
        return
    
    # Check if target drive specified
    if len(sys.argv) > 1:
        target_drive = sys.argv[1]
        print(f"🎯 Target drive: {target_drive}")
        
        # Confirm before copying
        response = input(f"Copy structure to {target_drive}? This will overwrite existing files! (y/N): ")
        if response.lower() == 'y':
            if copy_to_sd_card(base_dir, target_drive):
                print(f"🎉 SD card setup complete! Insert into device and test.")
            else:
                print("❌ Setup failed. Please check errors above.")
        else:
            print("❌ Copy cancelled.")
    else:
        print("ℹ️  No target drive specified.")
        show_setup_instructions()
        print(f"\n📁 Source structure ready at: {base_dir}")
        print("Usage: python setup_sd_card.py <drive_letter>")
        print("Example: python setup_sd_card.py E:")

if __name__ == "__main__":
    main()
