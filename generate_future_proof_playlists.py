#!/usr/bin/env python3
"""
Generate Future-Proof Playlist System for Tactile Communication Device

This script creates the complete SD card structure with strict human/generated
separation and playlist-enforced ordering for desktop app compatibility.

Based on the existing audio mappings from the Arduino code, this creates:
1. Playlist files for each key (human and generated)
2. Directory structure for audio files
3. Manifest file for desktop app compatibility
4. Migration guide from existing system
"""

import os
import json
from pathlib import Path

# Audio mappings from the existing Arduino code
AUDIO_MAPPINGS = [
    # Format: (label, recFolder, recBase, recCount, ttsFolder, ttsBase, ttsCount, fallbackLabel)
    ("A", 1, 1, 3, 1, 4, 3, "Apple"),
    ("B", 0, 0, 0, 2, 1, 7, "Ball"),
    ("C", 0, 0, 0, 3, 1, 7, "Cat"),
    ("D", 4, 1, 1, 4, 2, 5, "Dog"),
    ("E", 0, 0, 0, 5, 1, 1, "Elephant"),
    ("F", 0, 0, 0, 6, 1, 3, "FaceTime"),
    ("G", 7, 1, 1, 7, 2, 2, "Good"),
    ("H", 8, 1, 2, 8, 3, 5, "Hello"),
    ("I", 0, 0, 0, 9, 1, 3, "Ice"),
    ("J", 0, 0, 0, 10, 1, 1, "Jump"),
    ("K", 11, 1, 2, 11, 3, 3, "Key"),
    ("M", 0, 0, 0, 13, 1, 6, "Mom"),
    ("N", 14, 1, 2, 14, 3, 3, "No"),
    ("O", 0, 0, 0, 15, 1, 2, "Orange"),
    ("P", 0, 0, 0, 16, 1, 4, "Please"),
    ("Q", 0, 0, 0, 17, 1, 1, "Queen"),
    ("R", 0, 0, 0, 18, 1, 3, "Red"),
    ("S", 19, 1, 1, 19, 2, 9, "Susu"),
    ("T", 0, 0, 0, 20, 1, 4, "Thank"),
    ("U", 21, 1, 1, 21, 2, 1, "Up"),
    ("V", 0, 0, 0, 22, 1, 1, "Very"),
    ("W", 23, 1, 2, 23, 3, 2, "Water"),
    ("X", 0, 0, 0, 24, 1, 1, "X-ray"),
    ("Y", 0, 0, 0, 25, 1, 2, "Yes"),
    ("Z", 0, 0, 0, 26, 1, 1, "Zebra"),
    ("SPACE", 0, 0, 0, 35, 1, 1, "Space"),
    (".", 0, 0, 0, 33, 1, 3, "Period"),
]

# Additional keys for expanded vocabulary
ADDITIONAL_KEYS = [
    "Water", "Help", "Yes", "No", "Please", "Thank", "More", "Stop", "Go", "Come",
    "Want", "Need", "Like", "Love", "Happy", "Sad", "Hungry", "Thirsty", "Tired", "Sick",
    "Emergency", "Home", "Work", "School"
]

def create_directory_structure(base_path):
    """Create the complete SD card directory structure."""
    directories = [
        "config",
        "mappings/playlists",
        "audio/human",
        "audio/generated",
        "state"
    ]
    
    # Create directories for each key
    all_keys = [mapping[0] for mapping in AUDIO_MAPPINGS] + ADDITIONAL_KEYS
    for key in all_keys:
        directories.extend([
            f"audio/human/{key}",
            f"audio/generated/{key}"
        ])
    
    # Add system directory for announcements
    directories.extend([
        "audio/generated/SYSTEM"
    ])
    
    for directory in directories:
        dir_path = Path(base_path) / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_playlists(base_path):
    """Create playlist files for all keys."""
    playlist_dir = Path(base_path) / "mappings" / "playlists"
    
    # Create playlists for mapped keys
    for label, rec_folder, rec_base, rec_count, tts_folder, tts_base, tts_count, fallback in AUDIO_MAPPINGS:
        # Human playlist
        human_playlist = playlist_dir / f"{label}_human.m3u"
        with open(human_playlist, 'w') as f:
            f.write(f"# Human recordings for {label}\n")
            if rec_count > 0:
                for i in range(rec_count):
                    track_num = rec_base + i
                    f.write(f"audio/human/{label}/{track_num:03d}.mp3\n")
            else:
                f.write(f"# No human recordings defined - add files and update this playlist\n")
        
        # Generated playlist
        generated_playlist = playlist_dir / f"{label}_generated.m3u"
        with open(generated_playlist, 'w') as f:
            f.write(f"# Generated audio for {label} ({fallback})\n")
            if tts_count > 0:
                for i in range(tts_count):
                    track_num = tts_base + i
                    f.write(f"audio/generated/{label}/{track_num:03d}.mp3\n")
            else:
                f.write(f"# No generated audio defined - add files and update this playlist\n")
        
        print(f"Created playlists for {label}")
    
    # Create playlists for additional keys
    for key in ADDITIONAL_KEYS:
        if key not in [mapping[0] for mapping in AUDIO_MAPPINGS]:
            # Human playlist
            human_playlist = playlist_dir / f"{key}_human.m3u"
            with open(human_playlist, 'w') as f:
                f.write(f"# Human recordings for {key}\n")
                f.write(f"audio/human/{key}/001.mp3\n")
                f.write(f"# Add more files as needed\n")
            
            # Generated playlist
            generated_playlist = playlist_dir / f"{key}_generated.m3u"
            with open(generated_playlist, 'w') as f:
                f.write(f"# Generated audio for {key}\n")
                f.write(f"audio/generated/{key}/001.mp3\n")
                f.write(f"# Add more files as needed\n")
            
            print(f"Created template playlists for {key}")

def create_manifest(base_path):
    """Create manifest.json for desktop app compatibility."""
    all_keys = [mapping[0] for mapping in AUDIO_MAPPINGS] + ADDITIONAL_KEYS
    
    manifest = {
        "schema": "tcd-playlists@1",
        "version": "1.0.0",
        "created": "2025-01-15",
        "description": "Future-proof tactile communication device configuration",
        "priority": "HUMAN_FIRST",
        "strict_playlists": True,
        "hardware": {
            "pcf8575_count": 3,
            "gpio_pins": [8, 9, 2, 5],
            "total_capacity": 52
        },
        "keys": []
    }
    
    for key in sorted(set(all_keys)):
        manifest["keys"].append({
            "key": key,
            "human_playlist": f"mappings/playlists/{key}_human.m3u",
            "generated_playlist": f"mappings/playlists/{key}_generated.m3u",
            "human_dir": f"audio/human/{key}",
            "generated_dir": f"audio/generated/{key}"
        })
    
    manifest_path = Path(base_path) / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Created manifest: {manifest_path}")

def create_migration_guide(base_path):
    """Create migration guide from existing system."""
    guide_path = Path(base_path) / "MIGRATION_GUIDE.md"
    
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write("""# Migration Guide: Legacy to Future-Proof System

## Overview
This guide helps you migrate from the existing folder-based system to the new future-proof playlist-based system.

## Key Changes

### 1. Directory Structure
**OLD:** `/01/`, `/02/`, etc. with mixed human/generated content
**NEW:** `/audio/human/{KEY}/` and `/audio/generated/{KEY}/` with strict separation

### 2. Hardware Mapping
**OLD:** Hardcoded GPIO -> label mappings in Arduino code
**NEW:** `/config/buttons.csv` defines all hardware mappings

### 3. Audio Selection
**OLD:** Folder scanning with hardcoded track ranges
**NEW:** Playlist-enforced ordering via `.m3u` files

## Migration Steps

### Step 1: Copy Audio Files
For each existing folder (01-35), copy files to the new structure:

```bash
# Example for folder 01 (A button)
# Human recordings (REC bank)
cp /01/001.mp3 /audio/human/A/001.mp3
cp /01/002.mp3 /audio/human/A/002.mp3
cp /01/003.mp3 /audio/human/A/003.mp3

# Generated audio (TTS bank)
cp /01/004.mp3 /audio/generated/A/001.mp3
cp /01/005.mp3 /audio/generated/A/002.mp3
cp /01/006.mp3 /audio/generated/A/003.mp3
```

### Step 2: Update Playlists
Edit the `.m3u` files in `/mappings/playlists/` to reflect your actual audio files.

### Step 3: Configure Hardware
Update `/config/buttons.csv` to match your physical button layout.

### Step 4: Test System
Use the new firmware's test commands:
- `T` - Test all buttons
- `U` - Verify audio files
- `P` - Print current mappings

## Mapping Reference

""")
        
        # Add mapping reference
        for label, rec_folder, rec_base, rec_count, tts_folder, tts_base, tts_count, fallback in AUDIO_MAPPINGS:
            f.write(f"### {label} ({fallback})\n")
            f.write(f"- **Legacy:** Folder {rec_folder} (REC: {rec_base}-{rec_base+rec_count-1 if rec_count > 0 else 'none'}), ")
            f.write(f"Folder {tts_folder} (TTS: {tts_base}-{tts_base+tts_count-1 if tts_count > 0 else 'none'})\n")
            f.write(f"- **New:** `/audio/human/{label}/` and `/audio/generated/{label}/`\n\n")
        
        f.write("""
## Benefits of New System

1. **Hardware Independence:** Change GPIO pins without code changes
2. **Desktop App Ready:** Standard playlists work with any audio tool
3. **Strict Separation:** Human and generated audio never mixed
4. **Future Proof:** Easy to add new keys, hardware, or features
5. **Version Control:** Manifest tracks system changes
6. **Cross Platform:** Works on Windows, Mac, Linux

## Troubleshooting

- **No audio plays:** Check playlist files point to existing audio files
- **Wrong button mapping:** Update `/config/buttons.csv`
- **Priority not working:** Verify `/config/mode.cfg` settings
- **Missing playlists:** Use `U` command to verify all required files exist

For more help, see the main README.md file.
""")
    
    print(f"Created migration guide: {guide_path}")

def create_system_audio_files(base_path):
    """Create placeholder system audio files."""
    system_dir = Path(base_path) / "audio" / "generated" / "SYSTEM"
    
    # Create placeholder files for priority announcements
    placeholders = [
        "human_first.mp3",
        "generated_first.mp3",
        "system_ready.mp3",
        "calibration_mode.mp3"
    ]
    
    for placeholder in placeholders:
        placeholder_path = system_dir / placeholder
        with open(placeholder_path, 'w') as f:
            f.write(f"# Placeholder for {placeholder}\n")
            f.write("# Replace with actual MP3 file\n")
        print(f"Created placeholder: {placeholder_path}")

def main():
    """Generate the complete future-proof system."""
    base_path = "SD_FUTURE_PROOF"
    
    print("=== GENERATING FUTURE-PROOF TACTILE COMMUNICATION SYSTEM ===")
    print(f"Target directory: {base_path}")
    print()
    
    # Create directory structure
    print("1. Creating directory structure...")
    create_directory_structure(base_path)
    print()
    
    # Create playlists
    print("2. Creating playlist files...")
    create_playlists(base_path)
    print()
    
    # Create manifest
    print("3. Creating manifest file...")
    create_manifest(base_path)
    print()
    
    # Create migration guide
    print("4. Creating migration guide...")
    create_migration_guide(base_path)
    print()
    
    # Create system audio placeholders
    print("5. Creating system audio placeholders...")
    create_system_audio_files(base_path)
    print()
    
    print("=== GENERATION COMPLETE ===")
    print()
    print("Next steps:")
    print("1. Copy your existing audio files using the migration guide")
    print("2. Update playlist files to match your actual audio content")
    print("3. Configure buttons.csv for your hardware layout")
    print("4. Upload the new firmware to your device")
    print("5. Copy the SD_FUTURE_PROOF contents to your SD card")
    print()
    print("The system is now ready for desktop app integration!")

if __name__ == "__main__":
    main()
