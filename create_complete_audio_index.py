#!/usr/bin/env python3
"""
Create complete audio_index.csv with both REC and TTS entries.
"""

import os

SD_CARD_DRIVE = "E:\\"

# Complete audio index based on actual SD card contents and Arduino expectations
COMPLETE_AUDIO_INDEX = [
    # A button - folder 05
    (5, 1, "Alari", "REC"),
    (5, 2, "Amer", "REC"), 
    (5, 3, "Amory", "REC"),
    (5, 4, "Apple", "TTS"),
    (5, 5, "Attention", "TTS"),
    (5, 6, "Awesome", "TTS"),
    
    # D button - folder 08  
    (8, 1, "Daddy", "REC"),
    (8, 2, "Deen", "TTS"),
    (8, 3, "Doctor", "TTS"),
    (8, 4, "Door", "TTS"),
    (8, 5, "Down", "TTS"),
    
    # G button - folder 11
    (11, 1, "Good Morning", "REC"),
    (11, 2, "Garage", "TTS"),
    (11, 3, "Go", "TTS"),
    
    # H button - folder 12
    (12, 1, "Hello How are You", "REC"),
    (12, 2, "Happy", "TTS"),
    (12, 3, "Heartburn", "TTS"),
    (12, 4, "Hot", "TTS"),
    (12, 5, "Hungry", "TTS"),
    
    # K button - folder 15
    (15, 1, "Kiyah", "REC"),
    (15, 2, "Kyan", "REC"),
    (15, 3, "Kaiser", "TTS"),
    (15, 4, "Key", "TTS"),
    (15, 5, "Kitchen", "TTS"),
    
    # L button - folder 16
    (16, 1, "I Love You", "REC"),
    (16, 2, "Lee", "REC"),
    (16, 3, "Light", "TTS"),
    (16, 4, "Listen", "TTS"),
    (16, 5, "Look", "TTS"),
    
    # N button - folder 18
    (18, 1, "Nada", "REC"),
    (18, 2, "Nadowie", "REC"),
    (18, 3, "Noah", "REC"),
    (18, 4, "Net", "TTS"),
    (18, 5, "No", "TTS"),
    
    # S button - folder 23
    (23, 1, "Susu", "REC"),
    (23, 2, "Sad", "TTS"),
    (23, 3, "Scarf", "TTS"),
    (23, 4, "Shoes", "TTS"),
    (23, 5, "Sinemet", "TTS"),
    (23, 6, "Sleep", "TTS"),
    (23, 7, "Socks", "TTS"),
    (23, 8, "Stop", "TTS"),
    (23, 9, "Space", "TTS"),
    
    # U button - folder 25
    (25, 1, "Urgent Care", "REC"),
    (25, 2, "Up", "TTS"),
    (25, 3, "Under", "TTS"),
    
    # W button - folder 27
    (27, 1, "Walker", "REC"),
    (27, 2, "Wheelchair", "REC"),
    (27, 3, "Walk", "TTS"),
    (27, 4, "Water", "TTS"),
    (27, 5, "Window", "TTS"),
    (27, 6, "Work", "TTS"),
]

def create_complete_audio_index():
    """Create complete audio_index.csv with both REC and TTS entries."""
    print("📝 CREATING COMPLETE AUDIO INDEX")
    print("=" * 50)
    
    config_dir = os.path.join(SD_CARD_DRIVE, "config")
    os.makedirs(config_dir, exist_ok=True)
    
    csv_path = os.path.join(config_dir, "audio_index.csv")
    
    print(f"Writing to: {csv_path}")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        # Write header
        f.write("folder,track,text,type\n")
        
        # Write all entries
        for folder, track, text, audio_type in COMPLETE_AUDIO_INDEX:
            f.write(f"{folder},{track},{text},{audio_type}\n")
    
    print(f"✅ Created complete audio index with {len(COMPLETE_AUDIO_INDEX)} entries")
    
    # Verify files exist
    print("\n🔍 VERIFYING FILES EXIST:")
    missing_files = []
    
    for folder, track, text, audio_type in COMPLETE_AUDIO_INDEX:
        file_path = os.path.join(SD_CARD_DRIVE, f"{folder:02d}", f"{track:03d}.mp3")
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ /{folder:02d}/{track:03d}.mp3 -> {text} ({audio_type}) ({size:,} bytes)")
        else:
            print(f"❌ MISSING: /{folder:02d}/{track:03d}.mp3 -> {text} ({audio_type})")
            missing_files.append(f"/{folder:02d}/{track:03d}.mp3")
    
    if missing_files:
        print(f"\n⚠️  {len(missing_files)} files are missing from SD card:")
        for file in missing_files:
            print(f"   {file}")
        print("These files need to be generated or copied to SD card.")
    else:
        print(f"\n🎉 All {len(COMPLETE_AUDIO_INDEX)} audio files are present on SD card!")
    
    print("=" * 50)

if __name__ == "__main__":
    create_complete_audio_index()
