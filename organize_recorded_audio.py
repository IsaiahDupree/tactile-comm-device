#!/usr/bin/env python3
"""
Organize recorded human audio files on SD card for tactile communication device.
This script copies personal recordings to their appropriate folders and tracks on the SD card.
"""

import os
import shutil
import json
from pathlib import Path

# Configuration
RECORDED_FOLDER = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\Recorded"
SD_CARD_DRIVE = "E:\\"
MANIFEST_FILE = os.path.join(SD_CARD_DRIVE, "AUDIO_MANIFEST.json")

# Mapping of recorded files to their button folders and track numbers
# Format: "filename.mp3": {"folder": X, "track": Y, "button": "LABEL", "type": "REC"}
RECORDED_MAPPINGS = {
    # A button - folder 5
    "Alari.mp3": {"folder": 5, "track": 1, "button": "A", "type": "REC"},
    "Amer.mp3": {"folder": 5, "track": 2, "button": "A", "type": "REC"},
    "Amory.mp3": {"folder": 5, "track": 3, "button": "A", "type": "REC"},
    
    # D button - folder 8 (Daddy at track 1, Deen moved to TTS as track 2)
    "Daddy.mp3": {"folder": 8, "track": 1, "button": "D", "type": "REC"},
    
    # G button - folder 11
    "Good Morning.mp3": {"folder": 11, "track": 1, "button": "G", "type": "REC"},
    
    # H button - folder 12
    "Hello How are You.mp3": {"folder": 12, "track": 1, "button": "H", "type": "REC"},
    
    # L button - folder 16
    "I Love You.mp3": {"folder": 16, "track": 1, "button": "L", "type": "REC"},
    
    # K button - folder 15
    "Kiyah.mp3": {"folder": 15, "track": 1, "button": "K", "type": "REC"},
    "Kyan.mp3": {"folder": 15, "track": 2, "button": "K", "type": "REC"},
    
    # L button - folder 16 (additional)
    "Lee.mp3": {"folder": 16, "track": 2, "button": "L", "type": "REC"},
    
    # N button - folder 18
    "Nadowie.mp3": {"folder": 18, "track": 2, "button": "N", "type": "REC"},  # Track 2 after existing Nada
    "Noah.mp3": {"folder": 18, "track": 3, "button": "N", "type": "REC"},
    
    # S button - folder 23
    "Susu.mp3": {"folder": 23, "track": 1, "button": "S", "type": "REC"},
    
    # U button - folder 25
    "Urgent Care.mp3": {"folder": 25, "track": 1, "button": "U", "type": "REC"},
    
    # W button - folder 27
    "Walker.mp3": {"folder": 27, "track": 1, "button": "W", "type": "REC"},
    "Wheelchair.mp3": {"folder": 27, "track": 2, "button": "W", "type": "REC"},
}

def copy_recorded_files():
    """Copy recorded audio files to SD card in organized folders."""
    print("🎵 Organizing recorded human audio files on SD card...")
    
    if not os.path.exists(RECORDED_FOLDER):
        print(f"❌ Recorded folder not found: {RECORDED_FOLDER}")
        return False
    
    if not os.path.exists(SD_CARD_DRIVE):
        print(f"❌ SD card not found at: {SD_CARD_DRIVE}")
        return False
    
    # Load existing manifest if it exists
    manifest = {}
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, 'r') as f:
                manifest = json.load(f)
        except:
            print("⚠️  Could not load existing manifest, creating new one")
    
    copied_count = 0
    
    for filename, mapping in RECORDED_MAPPINGS.items():
        source_path = os.path.join(RECORDED_FOLDER, filename)
        
        if not os.path.exists(source_path):
            print(f"⚠️  File not found: {filename}")
            continue
        
        # Create target folder path
        folder_num = mapping["folder"]
        folder_name = f"{folder_num:02d}"
        target_folder = os.path.join(SD_CARD_DRIVE, folder_name)
        
        # Create folder if it doesn't exist
        os.makedirs(target_folder, exist_ok=True)
        
        # Create target file path
        track_num = mapping["track"]
        target_filename = f"{track_num:03d}.mp3"
        target_path = os.path.join(target_folder, target_filename)
        
        # Copy file
        try:
            shutil.copy2(source_path, target_path)
            print(f"✅ Copied {filename} → /{folder_name}/{target_filename} ({mapping['button']} button)")
            copied_count += 1
            
            # Update manifest
            manifest_key = f"{folder_num:02d}/{track_num:03d}.mp3"
            # Extract clean text from filename (remove .mp3 and clean up)
            clean_text = filename.replace('.mp3', '').replace('_', ' ')
            manifest[manifest_key] = {
                "text": clean_text,
                "type": mapping["type"],
                "button": mapping["button"],
                "source_file": filename
            }
            
        except Exception as e:
            print(f"❌ Error copying {filename}: {e}")
    
    # Save updated manifest
    try:
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        print(f"📝 Updated audio manifest: {MANIFEST_FILE}")
    except Exception as e:
        print(f"⚠️  Could not save manifest: {e}")
    
    print(f"\n🎉 Successfully copied {copied_count} recorded audio files to SD card!")
    return True

def create_updated_audio_index_csv():
    """Create updated audio_index.csv with recorded files included."""
    csv_path = os.path.join(SD_CARD_DRIVE, "config", "audio_index.csv")
    
    # Create config folder if it doesn't exist
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    print(f"📝 Creating updated audio_index.csv...")
    
    # Load manifest to get all audio files
    manifest = {}
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, 'r') as f:
                manifest = json.load(f)
        except:
            print("⚠️  Could not load manifest")
    
    # Create CSV content
    csv_lines = ["folder,track,text,type"]
    
    # Add recorded files from our mapping
    for filename, mapping in RECORDED_MAPPINGS.items():
        folder = mapping["folder"]
        track = mapping["track"]
        button = mapping["button"]
        clean_text = filename.replace('.mp3', '').replace('_', ' ')
        csv_lines.append(f"{folder},{track},{clean_text},REC")
    
    # Write CSV file
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))
        print(f"✅ Created {csv_path}")
        print(f"📊 Added {len(RECORDED_MAPPINGS)} recorded audio entries")
    except Exception as e:
        print(f"❌ Error creating CSV: {e}")

def print_updated_mappings():
    """Print the updated Arduino audioMappings that should be used."""
    print("\n" + "="*60)
    print("📋 UPDATED ARDUINO AUDIOMAPPINGS")
    print("="*60)
    
    # Group by button
    button_mappings = {}
    for filename, mapping in RECORDED_MAPPINGS.items():
        button = mapping["button"]
        if button not in button_mappings:
            button_mappings[button] = {"rec": [], "folder": mapping["folder"]}
        button_mappings[button]["rec"].append({
            "track": mapping["track"],
            "text": filename.replace('.mp3', '').replace('_', ' ')
        })
    
    print("// Updated audioMappings entries with recorded files:")
    for button in sorted(button_mappings.keys()):
        info = button_mappings[button]
        rec_tracks = sorted(info["rec"], key=lambda x: x["track"])
        folder = info["folder"]
        
        rec_count = len(rec_tracks)
        rec_base = rec_tracks[0]["track"] if rec_tracks else 0
        
        print(f"// {button}: REC={rec_base}-{rec_base+rec_count-1} ({', '.join([t['text'] for t in rec_tracks])})")
        fallback_text = rec_tracks[0]["text"] if rec_tracks else button
        print('{{"{}" /*recFolder*/{},/*recBase*/{},/*recCount*/{}, /*ttsFolder*/{},/*ttsBase*/X,/*ttsCount*/Y, "{}"}},'.format(button, folder, rec_base, rec_count, folder, fallback_text))
        print()

if __name__ == "__main__":
    print("🎵 TACTILE COMMUNICATION DEVICE - RECORDED AUDIO ORGANIZER")
    print("="*60)
    
    success = copy_recorded_files()
    if success:
        create_updated_audio_index_csv()
        print_updated_mappings()
        
        print("\n" + "="*60)
        print("✅ NEXT STEPS:")
        print("1. Update Arduino audioMappings array with the printed values above")
        print("2. Upload updated firmware to Arduino")
        print("3. Test priority mode to verify REC vs TTS audio selection")
        print("4. Use serial command 'U' to verify all files exist")
        print("="*60)
    else:
        print("❌ Failed to organize recorded files")
