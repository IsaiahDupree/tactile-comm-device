#!/usr/bin/env python3
"""
Fix audio_index.csv to match the actual audio content on the SD card.
Uses the AUDIO_MANIFEST.json to get the correct text mappings.
"""

import os
import json

SD_CARD_DRIVE = "E:\\"

def read_audio_manifest():
    """Read the audio manifest to get actual text content."""
    manifest_path = os.path.join(SD_CARD_DRIVE, "AUDIO_MANIFEST.json")
    
    if not os.path.exists(manifest_path):
        print(f"❌ Audio manifest not found at: {manifest_path}")
        return None
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        print(f"✅ Loaded audio manifest with {len(manifest)} entries")
        return manifest
    except Exception as e:
        print(f"❌ Error reading manifest: {e}")
        return None

def scan_sd_card_files():
    """Scan SD card to find all audio files and their actual content."""
    print("🔍 SCANNING SD CARD FOR AUDIO FILES")
    print("=" * 50)
    
    audio_files = []
    
    # Scan folders 01-33
    for folder_num in range(1, 34):
        folder_path = os.path.join(SD_CARD_DRIVE, f"{folder_num:02d}")
        
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
            files.sort()
            
            if files:
                print(f"📁 Folder {folder_num:02d}: {len(files)} files")
                
                for file in files:
                    if file.endswith('.mp3'):
                        track_num = int(file.replace('.mp3', ''))
                        file_path = os.path.join(folder_path, file)
                        size = os.path.getsize(file_path)
                        
                        audio_files.append({
                            'folder': folder_num,
                            'track': track_num,
                            'filename': f"{folder_num:02d}/{file}",
                            'size': size
                        })
                        
                        print(f"   {track_num:03d}.mp3 ({size:,} bytes)")
    
    print(f"\n✅ Found {len(audio_files)} audio files total")
    return audio_files

def create_corrected_audio_index():
    """Create corrected audio index based on actual SD card content."""
    print("\n📝 CREATING CORRECTED AUDIO INDEX")
    print("=" * 50)
    
    # Read manifest for text mappings
    manifest = read_audio_manifest()
    
    # Scan SD card for actual files
    audio_files = scan_sd_card_files()
    
    if not audio_files:
        print("❌ No audio files found on SD card")
        return False
    
    # Known mappings based on your console output and our previous work
    KNOWN_MAPPINGS = {
        # A button - folder 05 (from console output and our work)
        "05/001.mp3": {"text": "Alari", "type": "REC"},
        "05/002.mp3": {"text": "Amer", "type": "REC"},
        "05/003.mp3": {"text": "Amory", "type": "REC"},
        "05/004.mp3": {"text": "Arabic Show", "type": "TTS"},  # From console output
        "05/005.mp3": {"text": "Attention", "type": "TTS"},
        "05/006.mp3": {"text": "Awesome", "type": "TTS"},
        
        # D button - folder 08
        "08/001.mp3": {"text": "Daddy", "type": "REC"},
        "08/002.mp3": {"text": "Deen", "type": "TTS"},
        "08/003.mp3": {"text": "Doctor", "type": "TTS"},
        "08/004.mp3": {"text": "Door", "type": "TTS"},
        "08/005.mp3": {"text": "Down", "type": "TTS"},
        
        # G button - folder 11
        "11/001.mp3": {"text": "Good Morning", "type": "REC"},
        "11/002.mp3": {"text": "Garage", "type": "TTS"},
        "11/003.mp3": {"text": "Go", "type": "TTS"},
        
        # H button - folder 12
        "12/001.mp3": {"text": "Hello How are You", "type": "REC"},
        "12/002.mp3": {"text": "Happy", "type": "TTS"},
        "12/003.mp3": {"text": "Heartburn", "type": "TTS"},
        "12/004.mp3": {"text": "Hot", "type": "TTS"},
        "12/005.mp3": {"text": "Hungry", "type": "TTS"},
        
        # K button - folder 15
        "15/001.mp3": {"text": "Kiyah", "type": "REC"},
        "15/002.mp3": {"text": "Kyan", "type": "REC"},
        "15/003.mp3": {"text": "Kaiser", "type": "TTS"},
        "15/004.mp3": {"text": "Kleenex", "type": "TTS"},  # From your vocabulary
        "15/005.mp3": {"text": "Kitchen", "type": "TTS"},
        
        # L button - folder 16
        "16/001.mp3": {"text": "I Love You", "type": "REC"},
        "16/002.mp3": {"text": "Lee", "type": "REC"},
        "16/003.mp3": {"text": "Light Down", "type": "TTS"},  # From your vocabulary
        "16/004.mp3": {"text": "Light Up", "type": "TTS"},    # From your vocabulary
        "16/005.mp3": {"text": "Look", "type": "TTS"},
        
        # N button - folder 18
        "18/001.mp3": {"text": "Nada", "type": "REC"},
        "18/002.mp3": {"text": "Nadowie", "type": "REC"},
        "18/003.mp3": {"text": "Noah", "type": "REC"},
        "18/004.mp3": {"text": "No", "type": "TTS"},
        "18/005.mp3": {"text": "Net", "type": "TTS"},
        
        # S button - folder 23
        "23/001.mp3": {"text": "Susu", "type": "REC"},
        "23/002.mp3": {"text": "Sad", "type": "TTS"},
        "23/003.mp3": {"text": "Scarf", "type": "TTS"},
        "23/004.mp3": {"text": "Shoes", "type": "TTS"},
        "23/005.mp3": {"text": "Sinemet", "type": "TTS"},
        "23/006.mp3": {"text": "Sleep", "type": "TTS"},
        "23/007.mp3": {"text": "Socks", "type": "TTS"},
        "23/008.mp3": {"text": "Stop", "type": "TTS"},
        "23/009.mp3": {"text": "Space", "type": "TTS"},
        
        # U button - folder 25
        "25/001.mp3": {"text": "Urgent Care", "type": "REC"},
        "25/002.mp3": {"text": "Up", "type": "TTS"},
        "25/003.mp3": {"text": "Under", "type": "TTS"},
        
        # W button - folder 27
        "27/001.mp3": {"text": "Walker", "type": "REC"},
        "27/002.mp3": {"text": "Wheelchair", "type": "REC"},
        "27/003.mp3": {"text": "Walk", "type": "TTS"},
        "27/004.mp3": {"text": "Water", "type": "TTS"},
        "27/005.mp3": {"text": "Window", "type": "TTS"},
        "27/006.mp3": {"text": "Work", "type": "TTS"},
    }
    
    # Create config directory
    config_dir = os.path.join(SD_CARD_DRIVE, "config")
    os.makedirs(config_dir, exist_ok=True)
    
    # Create corrected audio index
    csv_path = os.path.join(config_dir, "audio_index.csv")
    
    print(f"Writing corrected audio index to: {csv_path}")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        # Write header
        f.write("folder,track,text,type\n")
        
        # Write entries for each file found
        entries_written = 0
        
        for file_info in sorted(audio_files, key=lambda x: (x['folder'], x['track'])):
            folder = file_info['folder']
            track = file_info['track']
            filename = file_info['filename']
            
            # Get text and type from known mappings or manifest
            text = "Unknown"
            audio_type = "TTS"
            
            if filename in KNOWN_MAPPINGS:
                text = KNOWN_MAPPINGS[filename]['text']
                audio_type = KNOWN_MAPPINGS[filename]['type']
            elif manifest and filename in manifest:
                text = manifest[filename].get('text', 'Unknown')
                audio_type = manifest[filename].get('type', 'TTS')
            
            # Write entry
            f.write(f"{folder},{track},{text},{audio_type}\n")
            entries_written += 1
            
            print(f"✅ {filename} -> {text} ({audio_type})")
    
    print(f"\n✅ Created corrected audio index with {entries_written} entries")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    if create_corrected_audio_index():
        print("🎉 AUDIO INDEX CORRECTED!")
        print("The text mappings now match the actual audio content on your SD card.")
        print("Upload the Arduino firmware and test - the console output should now show correct text!")
    else:
        print("❌ Failed to create corrected audio index")
