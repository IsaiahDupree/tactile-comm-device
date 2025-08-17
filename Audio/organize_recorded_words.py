#!/usr/bin/env python3
"""
Organize Recorded Words for Tactile Communication Device

This script prioritizes the pre-recorded audio files from the RecordedWords directory
and organizes them into the correct positions for the DFPlayer Mini SD card structure.
"""

import json
import shutil
import os
from pathlib import Path

# Mapping of recorded files to their correct button positions
RECORDED_WORD_MAPPINGS = {
    # Letter A (Folder 02)
    "Amer.mp3": {"button": "A", "folder": 2, "track": 1, "text": "Amer"},
    "Alari.mp3": {"button": "A", "folder": 2, "track": 2, "text": "Alari"},
    
    # Letter B (Folder 03) 
    "Bye.mp3": {"button": "B", "folder": 3, "track": 2, "text": "Bye"},
    
    # Letter D (Folder 05)
    "Deen.mp3": {"button": "D", "folder": 5, "track": 1, "text": "Deen"},
    "Daddy.mp3": {"button": "D", "folder": 5, "track": 2, "text": "Daddy"},
    
    # Letter G (Folder 08)
    "Good Morning.mp3": {"button": "G", "folder": 8, "track": 1, "text": "Good Morning"},
    
    # Letter K (Folder 12)
    "Kiyah.mp3": {"button": "K", "folder": 12, "track": 1, "text": "Kiyah"},
    "Kyan.mp3": {"button": "K", "folder": 12, "track": 2, "text": "Kyan"},
    
    # Letter L (Folder 13)
    "Lee.mp3": {"button": "L", "folder": 13, "track": 1, "text": "Lee"},
    "I Love You.mp3": {"button": "L", "folder": 13, "track": 2, "text": "I love you"},
    
    # Letter N (Folder 15)
    "Nadowie.mp3": {"button": "N", "folder": 15, "track": 2, "text": "Nadowie"},
    "Noah.mp3": {"button": "N", "folder": 15, "track": 3, "text": "Noah"},
    
    # Letter S (Folder 20)
    "Susu.mp3": {"button": "S", "folder": 20, "track": 2, "text": "Susu"},
    
    # Letter U (Folder 22)
    "Urgent Care.mp3": {"button": "U", "folder": 22, "track": 1, "text": "Urgent Care"},
    
    # Letter W (Folder 24)
    "Walker.mp3": {"button": "W", "folder": 24, "track": 2, "text": "Walker"},
    "Wheelchair.mp3": {"button": "W", "folder": 24, "track": 3, "text": "wheelchair"},
    
    # Special Buttons (Folder 01)
    "Hello How are You.mp3": {"button": "AUX", "folder": 1, "track": 4, "text": "Hello How are You"},
    
    # Additional words (might need new mapping)
    "Amory.mp3": {"button": "A", "folder": 2, "track": 5, "text": "Amory"}  # Extra A word
}

def create_sd_structure_with_recorded():
    """Create SD card structure prioritizing recorded words"""
    
    recorded_dir = Path("RecordedWords")
    elevenlabs_dir = Path("11labs") 
    sd_structure_dir = Path("SD_Structure")
    
    if not recorded_dir.exists():
        print(f"❌ RecordedWords directory not found: {recorded_dir}")
        return False
        
    if not elevenlabs_dir.exists():
        print(f"❌ 11labs directory not found: {elevenlabs_dir}")
        return False
    
    # Create SD structure directory
    sd_structure_dir.mkdir(exist_ok=True)
    print(f"Creating SD card structure in: {sd_structure_dir}")
    
    # Create folders 01-28
    for folder_num in range(1, 29):
        folder_path = sd_structure_dir / f"{folder_num:02d}"
        folder_path.mkdir(exist_ok=True)
    
    files_copied = 0
    recorded_used = 0
    
    # First, copy all recorded words to their priority positions
    print("\n=== Copying Recorded Words (PRIORITY) ===")
    for recorded_file, mapping in RECORDED_WORD_MAPPINGS.items():
        src_path = recorded_dir / recorded_file
        dst_folder = sd_structure_dir / f"{mapping['folder']:02d}"
        dst_file = dst_folder / f"{mapping['track']:03d}.mp3"
        
        if src_path.exists():
            shutil.copy2(src_path, dst_file)
            print(f"✓ RECORDED: {mapping['button']} - {mapping['text']} → {dst_file}")
            files_copied += 1
            recorded_used += 1
        else:
            print(f"⚠️  Missing recorded file: {src_path}")
    
    # Then, fill remaining positions with ElevenLabs generated files
    print(f"\n=== Filling Remaining Positions with Generated Audio ===")
    
    # Load the audio index to see what generated files we have
    audio_index_path = elevenlabs_dir / "audio_index.json"
    if audio_index_path.exists():
        with open(audio_index_path, 'r') as f:
            audio_index = json.load(f)
        
        # Process each button's audio files
        for button, audio_files in audio_index["audio_files"].items():
            for audio_file in audio_files:
                # Determine folder number based on button
                folder_num = get_folder_number(button)
                if folder_num == 0:
                    continue
                    
                track_num = audio_file["button_press"]
                
                dst_folder = sd_structure_dir / f"{folder_num:02d}"
                dst_file = dst_folder / f"{track_num:03d}.mp3"
                
                # Only copy if position isn't already filled by recorded word
                if not dst_file.exists():
                    src_file = elevenlabs_dir / audio_file["file"]
                    if src_file.exists():
                        shutil.copy2(src_file, dst_file)
                        print(f"✓ Generated: {button} - {audio_file['text']} → {dst_file}")
                        files_copied += 1
                    else:
                        print(f"⚠️  Missing generated file: {src_file}")
    
    # Create reference mapping file
    create_sd_mapping_reference(sd_structure_dir)
    
    print(f"\n=== SD Structure Complete ===")
    print(f"✓ Used {recorded_used} recorded words (PRIORITY)")
    print(f"✓ Total files copied: {files_copied}")
    print(f"✓ SD structure ready at: {sd_structure_dir}")
    
    return True

def get_folder_number(button):
    """Get folder number for a button"""
    folder_map = {
        # Special buttons
        "YES": 1, "NO": 1, "WATER": 1, "AUX": 1,
        
        # Letters A-Z (folders 2-27)
        "A": 2, "B": 3, "C": 4, "D": 5, "E": 6, "F": 7, "G": 8, "H": 9,
        "I": 10, "J": 11, "K": 12, "L": 13, "M": 14, "N": 15, "O": 16,
        "P": 17, "Q": 18, "R": 19, "S": 20, "T": 21, "U": 22, "V": 23,
        "W": 24, "X": 25, "Y": 26, "Z": 27,
        
        # Punctuation
        "SPACE": 28, "PERIOD": 28
    }
    return folder_map.get(button, 0)

def create_sd_mapping_reference(sd_path):
    """Create a reference file showing the final SD card mapping"""
    
    mapping_content = """# SD Card Audio Mapping - WITH RECORDED WORDS PRIORITY
# Generated: Tactile Communication Device

## RECORDED WORDS (Priority Files):
These are pre-recorded personal audio files that take precedence:

### Folder 01 - Special Buttons
004.mp3 - Hello How are You [RECORDED]

### Folder 02 - Letter A  
001.mp3 - Amer [RECORDED]
002.mp3 - Alari [RECORDED]
003.mp3 - Apple [Generated]
004.mp3 - Arabic Show [Generated]
005.mp3 - Amory [RECORDED - Extra]

### Folder 03 - Letter B
001.mp3 - Bathroom [Generated]
002.mp3 - Bye [RECORDED]
003.mp3 - Bed [Generated]
004.mp3 - Breathe [Generated]
005.mp3 - blanket [Generated]

### Folder 05 - Letter D
001.mp3 - Deen [RECORDED]
002.mp3 - Daddy [RECORDED]
003.mp3 - Doctor [Generated]
004.mp3 - Door [Generated]

### Folder 08 - Letter G
001.mp3 - Good Morning [RECORDED]
002.mp3 - Go [Generated]

### Folder 12 - Letter K
001.mp3 - Kiyah [RECORDED]
002.mp3 - Kyan [RECORDED]
003.mp3 - Kleenex [Generated]
004.mp3 - Kaiser [Generated]

### Folder 13 - Letter L
001.mp3 - Lee [RECORDED]
002.mp3 - I love you [RECORDED]
003.mp3 - light down [Generated]
004.mp3 - light up [Generated]

### Folder 15 - Letter N
001.mp3 - Nada [Generated]
002.mp3 - Nadowie [RECORDED]
003.mp3 - Noah [RECORDED]

### Folder 20 - Letter S
001.mp3 - Scarf [Generated]
002.mp3 - Susu [RECORDED]
003.mp3 - Sinemet [Generated]

### Folder 22 - Letter U
001.mp3 - Urgent Care [RECORDED]

### Folder 24 - Letter W
001.mp3 - Water [Generated]
002.mp3 - Walker [RECORDED]
003.mp3 - wheelchair [RECORDED]
004.mp3 - walk [Generated]

## Notes:
- [RECORDED] files are personal recordings (priority)
- [Generated] files are ElevenLabs TTS
- Recorded words provide personal, familiar voices
- Generated words ensure complete coverage
- Arduino code plays tracks in order: 1st press = 001.mp3, 2nd press = 002.mp3, etc.
"""
    
    mapping_file = sd_path / "PRIORITY_MAPPING.txt"
    with open(mapping_file, 'w') as f:
        f.write(mapping_content)
    
    print(f"✓ Created priority mapping reference: {mapping_file}")

def update_arduino_mappings():
    """Update Arduino code with recorded word priorities"""
    
    print("\n=== Arduino Mapping Updates ===")
    print("The following buttons now have recorded words as priority:")
    
    recorded_buttons = {}
    for recorded_file, mapping in RECORDED_WORD_MAPPINGS.items():
        button = mapping['button']
        if button not in recorded_buttons:
            recorded_buttons[button] = []
        recorded_buttons[button].append({
            'track': mapping['track'],
            'text': mapping['text'],
            'file': recorded_file
        })
    
    for button, recordings in recorded_buttons.items():
        print(f"\n📍 Button {button}:")
        for recording in sorted(recordings, key=lambda x: x['track']):
            print(f"   Track {recording['track']}: {recording['text']} [RECORDED: {recording['file']}]")
    
    print(f"\n✓ Total buttons with recorded words: {len(recorded_buttons)}")
    print("✓ Arduino code will automatically use these in track order")

if __name__ == "__main__":
    print("Tactile Communication Device - Recorded Words Organizer")
    print("=" * 60)
    print("Prioritizing pre-recorded personal audio files...")
    
    if create_sd_structure_with_recorded():
        update_arduino_mappings()
        print("\n🎉 Recorded words successfully prioritized!")
        print("📁 Check SD_Structure/ folder for organized files")
        print("🎵 Recorded words will play first on their assigned buttons")
    else:
        print("❌ Failed to organize recorded words")
