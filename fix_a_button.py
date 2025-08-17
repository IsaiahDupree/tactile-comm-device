#!/usr/bin/env python3
"""
Fix A button folder organization on SD card.
The recorded files were placed incorrectly.
"""

import os
import shutil
import json

SD_CARD_DRIVE = "E:\\"
RECORDED_FOLDER = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\Recorded"

def fix_a_button():
    """Fix the A button folder organization."""
    print("🔧 FIXING A BUTTON FOLDER ORGANIZATION")
    print("=" * 50)
    
    folder_05 = os.path.join(SD_CARD_DRIVE, "05")
    
    # Expected final layout:
    # 001.mp3 = Alari (REC)
    # 002.mp3 = Amer (REC) 
    # 003.mp3 = Amory (REC)
    # 004.mp3 = Apple (TTS)
    # 005.mp3 = Attention (TTS)
    # 006.mp3 = Awesome (TTS)
    
    print("📁 Current files in /05/:")
    for file in sorted(os.listdir(folder_05)):
        if file.endswith('.mp3'):
            size = os.path.getsize(os.path.join(folder_05, file))
            print(f"   {file} ({size:,} bytes)")
    
    # The recorded files should be:
    # 001.mp3 = Alari (16,843 bytes) ✅ Already correct
    # 002.mp3 = Amer (12,617 bytes) - currently in wrong place
    # 003.mp3 = Amory (15,746 bytes) - currently in wrong place
    
    # Copy the correct recorded files
    recorded_files = {
        "Amer.mp3": "002.mp3",
        "Amory.mp3": "003.mp3"
    }
    
    print("\n🎵 Copying recorded files to correct positions:")
    for source_file, target_file in recorded_files.items():
        source_path = os.path.join(RECORDED_FOLDER, source_file)
        target_path = os.path.join(folder_05, target_file)
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            size = os.path.getsize(target_path)
            print(f"✅ Copied {source_file} → /05/{target_file} ({size:,} bytes)")
        else:
            print(f"❌ Source file not found: {source_file}")
    
    print("\n📁 Updated files in /05/:")
    for file in sorted(os.listdir(folder_05)):
        if file.endswith('.mp3'):
            size = os.path.getsize(os.path.join(folder_05, file))
            print(f"   {file} ({size:,} bytes)")
    
    # Update the audio manifest
    manifest_path = os.path.join(SD_CARD_DRIVE, "AUDIO_MANIFEST.json")
    print(f"\n📝 Updating audio manifest...")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Update the entries for folder 05
        manifest["05/001.mp3"] = {
            "button": "A",
            "source_file": "Alari.mp3", 
            "text": "Alari",
            "type": "REC"
        }
        manifest["05/002.mp3"] = {
            "button": "A",
            "source_file": "Amer.mp3",
            "text": "Amer", 
            "type": "REC"
        }
        manifest["05/003.mp3"] = {
            "button": "A",
            "source_file": "Amory.mp3",
            "text": "Amory",
            "type": "REC"
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        
        print("✅ Audio manifest updated")
        
    except Exception as e:
        print(f"⚠️  Could not update manifest: {e}")
    
    print("\n" + "=" * 50)
    print("✅ A BUTTON FOLDER FIXED!")
    print("Expected layout:")
    print("  001.mp3 = Alari (REC)")
    print("  002.mp3 = Amer (REC)")  
    print("  003.mp3 = Amory (REC)")
    print("  004.mp3 = Apple (TTS)")
    print("  005.mp3 = Attention (TTS)")
    print("  006.mp3 = Awesome (TTS)")
    print("=" * 50)

if __name__ == "__main__":
    fix_a_button()
