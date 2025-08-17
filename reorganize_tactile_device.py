#!/usr/bin/env python3
"""
Tactile Communication Device Reorganization Script
Reorganizes SD card structure and updates Arduino code based on new word mappings
"""

import json
import os
import shutil
import csv
from pathlib import Path

# Configuration
RECORDED_AUDIO_PATH = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\Recorded"
SD_CARD_PATH = r"E:"
ARDUINO_FILE_PATH = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\tactile_communicator_vs1053\tactile_communicator_vs1053.ino"

# New word mappings from user request
WORD_MAPPINGS = {
    "A": ["Alari", "Amer", "Amory", "Apple", "Arabic", "Arabic Show"],
    "B": ["Bagel", "Ball", "Bathroom", "Bed", "Blanket", "Breathe", "Bye"],
    "C": ["Call", "Car", "Cat", "Chair", "Coffee", "Cold", "Cucumber"],
    "D": ["Daddy", "Deen", "Doctor", "Dog", "Door", "Down"],
    "E": ["Elephant"],
    "F": ["FaceTime", "Fish", "Funny"],
    "G": ["Garage", "Go", "Good Morning"],
    "H": ["Happy", "Heartburn", "Hello", "Hot", "House", "How are you", "Hungry"],
    "I": ["Ice", "Inside", "iPad"],
    "J": ["Jump"],
    "K": ["Kaiser", "Key", "Kiyah", "Kleenex", "Kyan"],
    "L": ["I love you", "Lee", "Light", "Light Down", "Light Up", "Love"],
    "M": ["Mad", "Medical", "Medicine", "Meditate", "Mohammad", "Moon"],
    "N": ["Nada", "Nadowie", "Net", "No", "Noah"],
    "O": ["Orange", "Outside"],
    "P": ["Pain", "Period", "Phone", "Purple"],
    "Q": ["Queen"],
    "R": ["Red", "Rest", "Room"],
    "S": ["Sad", "Scarf", "Shoes", "Sinemet", "Sleep", "Socks", "Space", "Stop", "Sun", "Susu"],
    "T": ["Togamet", "Tree", "TV", "Tylenol"],
    "U": ["Up", "Urgent Care"],
    "V": ["Van"],
    "W": ["Walk", "Walker", "Water", "Wheelchair"],
    "X": ["X-ray"],
    "Y": ["Yes", "Yellow"],
    "Z": ["Zebra"]
}

# Known recorded audio files (from directory listing)
RECORDED_FILES = {
    "Alari": "Alari.mp3",
    "Amer": "Amer.mp3", 
    "Amory": "Amory.mp3",
    "Daddy": "Daddy.mp3",
    "Good Morning": "Good Morning.mp3",
    "Hello": "Hello How are You.mp3",  # Maps to "How are you"
    "How are you": "Hello How are You.mp3",
    "I love you": "I Love You.mp3",
    "Kiyah": "Kiyah.mp3",
    "Kyan": "Kyan.mp3", 
    "Lee": "Lee.mp3",
    "Nadowie": "Nadowie.mp3",
    "Noah": "Noah.mp3",
    "Susu": "Susu.mp3",
    "Urgent Care": "Urgent Care.mp3",
    "Walker": "Walker.mp3",
    "Wheelchair": "Wheelchair.mp3"
}

def clean_sd_card():
    """Clean up old SD card structure"""
    print("🧹 Cleaning SD card structure...")
    
    # Remove old REC and TTS folders
    old_rec = Path(SD_CARD_PATH) / "REC"
    old_tts = Path(SD_CARD_PATH) / "TTS"
    
    if old_rec.exists():
        shutil.rmtree(old_rec)
        print("   Removed old REC folder")
    
    if old_tts.exists():
        shutil.rmtree(old_tts)
        print("   Removed old TTS folder")
    
    # Remove backup folders
    backup_folder = Path(SD_CARD_PATH) / "BACKUP_OLD_STRUCTURE"
    if backup_folder.exists():
        shutil.rmtree(backup_folder)
        print("   Removed backup folder")
    
    # Remove old config files
    old_files = ["ARDUINO_MAPPINGS_NEW.txt", "AUDIO_MANIFEST.json", "AUDIO_MANIFEST_NEW.json", 
                 "CONFIG.CSV", "EXPANDED_VOCABULARY.txt", "FRESH_BUTTON_MAPPINGS.txt",
                 "QUICK_REFERENCE.txt", "SD_CARD_INDEX.txt", "folder_mapping.json"]
    
    for file in old_files:
        file_path = Path(SD_CARD_PATH) / file
        if file_path.exists():
            file_path.unlink()
            print(f"   Removed {file}")

def create_folder_structure():
    """Create proper folder structure (01-26 for A-Z, plus special folders)"""
    print("📁 Creating new folder structure...")
    
    # Create folders 01-26 for A-Z
    for i in range(1, 27):
        folder_path = Path(SD_CARD_PATH) / f"{i:02d}"
        folder_path.mkdir(exist_ok=True)
    
    # Create special folders
    special_folders = [32, 33, 34, 35]  # For special buttons
    for folder in special_folders:
        folder_path = Path(SD_CARD_PATH) / f"{folder:02d}"
        folder_path.mkdir(exist_ok=True)
    
    print("   Created folder structure 01-26 + special folders")

def organize_audio_files():
    """Organize audio files into proper folder structure with priority system"""
    print("🎵 Organizing audio files...")
    
    audio_index = []
    
    for letter, words in WORD_MAPPINGS.items():
        folder_num = ord(letter) - ord('A') + 1  # A=1, B=2, etc.
        folder_path = Path(SD_CARD_PATH) / f"{folder_num:02d}"
        
        track_num = 1
        recorded_count = 0
        tts_start = 1
        
        print(f"   Processing {letter}: {words}")
        
        # First pass: Place recorded audio files (REC priority)
        for word in words:
            if word in RECORDED_FILES:
                source_file = Path(RECORDED_AUDIO_PATH) / RECORDED_FILES[word]
                if source_file.exists():
                    dest_file = folder_path / f"{track_num:03d}.mp3"
                    shutil.copy2(source_file, dest_file)
                    
                    audio_index.append({
                        'folder': folder_num,
                        'track': track_num,
                        'text': word,
                        'bank': 'REC'
                    })
                    
                    print(f"     REC: {word} -> /{folder_num:02d}/{track_num:03d}.mp3")
                    track_num += 1
                    recorded_count += 1
        
        # Update TTS start position
        tts_start = track_num
        
        # Second pass: Add TTS placeholders for non-recorded words
        for word in words:
            if word not in RECORDED_FILES:
                audio_index.append({
                    'folder': folder_num,
                    'track': track_num,
                    'text': word,
                    'bank': 'TTS'
                })
                
                print(f"     TTS: {word} -> /{folder_num:02d}/{track_num:03d}.mp3 (placeholder)")
                track_num += 1
        
        # Create folder info
        folder_info = {
            'letter': letter,
            'folder': folder_num,
            'recorded_count': recorded_count,
            'tts_start': tts_start,
            'tts_count': track_num - tts_start,
            'total_tracks': track_num - 1
        }
    
    # Create special button audio index entries
    special_buttons = [
        {'folder': 32, 'track': 1, 'text': 'Yes', 'bank': 'TTS'},
        {'folder': 32, 'track': 2, 'text': 'No', 'bank': 'TTS'},
        {'folder': 33, 'track': 1, 'text': 'Period', 'bank': 'TTS'},
        {'folder': 33, 'track': 4, 'text': 'Human first priority', 'bank': 'TTS'},
        {'folder': 33, 'track': 5, 'text': 'Generated first priority', 'bank': 'TTS'},
        {'folder': 34, 'track': 1, 'text': 'Shift', 'bank': 'TTS'},
        {'folder': 35, 'track': 1, 'text': 'Space', 'bank': 'TTS'}
    ]
    
    audio_index.extend(special_buttons)
    
    return audio_index

def create_audio_index_csv(audio_index):
    """Create audio_index.csv file for SD card configuration"""
    print("📝 Creating audio_index.csv...")
    
    csv_path = Path(SD_CARD_PATH) / "audio_index.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['folder', 'track', 'text', 'bank']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in audio_index:
            writer.writerow(entry)
    
    print(f"   Created audio_index.csv with {len(audio_index)} entries")

def generate_arduino_mappings():
    """Generate new Arduino audioMappings array"""
    print("⚙️ Generating Arduino mappings...")
    
    mappings = []
    
    # Generate mappings for A-Z
    for letter, words in WORD_MAPPINGS.items():
        folder_num = ord(letter) - ord('A') + 1
        
        # Count recorded vs TTS
        recorded_words = [w for w in words if w in RECORDED_FILES]
        tts_words = [w for w in words if w not in RECORDED_FILES]
        
        rec_count = len(recorded_words)
        tts_count = len(tts_words)
        tts_base = rec_count + 1 if rec_count > 0 else 1
        
        # Primary label (first recorded word if available, otherwise first word)
        primary_label = recorded_words[0] if recorded_words else words[0]
        
        mapping = f'  {{"{letter}", /*recFolder*/{folder_num},/*recBase*/1,/*recCount*/{rec_count}, /*ttsFolder*/{folder_num},/*ttsBase*/{tts_base},/*ttsCount*/{tts_count}, "{primary_label}"}}'
        
        # Add comment with word breakdown
        comment = f"  // {letter}: "
        if recorded_words:
            comment += f"REC=1-{rec_count}({','.join(recorded_words[:3])}"
            if len(recorded_words) > 3:
                comment += "..."
            comment += "), "
        if tts_words:
            comment += f"TTS={tts_base}-{tts_base + tts_count - 1}({','.join(tts_words[:3])}"
            if len(tts_words) > 3:
                comment += "..."
            comment += ")"
        
        mappings.append(mapping + ("," if letter != "Z" else ""))
        if len(comment) > 20:  # Only add comment if meaningful
            mappings.append(comment)
    
    # Add special buttons
    special_mappings = [
        '',
        '  // Special Buttons',
        '  {"YES", /*recFolder*/32,/*recBase*/0,/*recCount*/0, /*ttsFolder*/32,/*ttsBase*/1,/*ttsCount*/1, "yes"},',
        '  {"NO", /*recFolder*/32,/*recBase*/0,/*recCount*/0, /*ttsFolder*/32,/*ttsBase*/2,/*ttsCount*/1, "no"},',
        '  {"PERIOD", /*recFolder*/33,/*recBase*/0,/*recCount*/0, /*ttsFolder*/33,/*ttsBase*/1,/*ttsCount*/3, "period"},',
        '  {"SHIFT", /*recFolder*/34,/*recBase*/0,/*recCount*/0, /*ttsFolder*/34,/*ttsBase*/1,/*ttsCount*/1, "shift"},',
        '  {"SPACE", /*recFolder*/35,/*recBase*/0,/*recCount*/0, /*ttsFolder*/35,/*ttsBase*/1,/*ttsCount*/1, "space"}'
    ]
    
    mappings.extend(special_mappings)
    
    return mappings

def update_arduino_code(mappings):
    """Update Arduino code with new mappings"""
    print("🔧 Updating Arduino code...")
    
    # Read current Arduino file
    with open(ARDUINO_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the audioMappings array
    start_marker = "AudioMapping audioMappings[] = {"
    end_marker = "};\n\nconst uint8_t AUDIO_MAPPINGS_COUNT"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("   ❌ Could not find audioMappings array in Arduino code")
        return False
    
    # Replace the mappings
    new_mappings_str = start_marker + "\n" + "\n".join(mappings) + "\n"
    
    new_content = content[:start_idx] + new_mappings_str + content[end_idx:]
    
    # Write updated content
    with open(ARDUINO_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("   ✅ Arduino code updated successfully")
    return True

def create_reference_files():
    """Create reference files for the new structure"""
    print("📋 Creating reference files...")
    
    # Create quick reference
    ref_content = "TACTILE COMMUNICATION DEVICE - UPDATED MAPPINGS\n"
    ref_content += "=" * 50 + "\n\n"
    
    for letter, words in WORD_MAPPINGS.items():
        folder_num = ord(letter) - ord('A') + 1
        ref_content += f"{letter} (Folder {folder_num:02d}): {', '.join(words)}\n"
        
        # Show which are recorded
        recorded = [w for w in words if w in RECORDED_FILES]
        if recorded:
            ref_content += f"   🎤 Recorded: {', '.join(recorded)}\n"
        ref_content += "\n"
    
    ref_content += "\nSPECIAL BUTTONS:\n"
    ref_content += "YES (32), NO (32), PERIOD (33), SHIFT (34), SPACE (35)\n\n"
    ref_content += "PRIORITY MODES:\n"
    ref_content += "- HUMAN_FIRST: Personal recordings play first, then TTS\n"
    ref_content += "- GENERATED_FIRST: TTS plays first, then personal recordings\n"
    ref_content += "- Switch modes: Triple-press Period button within 1.2 seconds\n"
    
    with open(Path(SD_CARD_PATH) / "DEVICE_REFERENCE.txt", 'w', encoding='utf-8') as f:
        f.write(ref_content)
    
    print("   Created DEVICE_REFERENCE.txt")

def main():
    """Main reorganization process"""
    print("🚀 Starting Tactile Communication Device Reorganization")
    print("=" * 60)
    
    try:
        # Step 1: Clean SD card
        clean_sd_card()
        
        # Step 2: Create folder structure
        create_folder_structure()
        
        # Step 3: Organize audio files
        audio_index = organize_audio_files()
        
        # Step 4: Create audio index CSV
        create_audio_index_csv(audio_index)
        
        # Step 5: Generate Arduino mappings
        mappings = generate_arduino_mappings()
        
        # Step 6: Update Arduino code
        update_arduino_code(mappings)
        
        # Step 7: Create reference files
        create_reference_files()
        
        print("\n✅ REORGANIZATION COMPLETE!")
        print("=" * 60)
        print("Summary:")
        print(f"- Organized {len([w for words in WORD_MAPPINGS.values() for w in words])} total words")
        print(f"- {len(RECORDED_FILES)} recorded audio files")
        print(f"- {len(audio_index)} audio index entries")
        print("- Arduino code updated with new mappings")
        print("- SD card structure reorganized (folders 01-26 + specials)")
        print("\nNext steps:")
        print("1. Generate missing TTS audio files for non-recorded words")
        print("2. Upload updated Arduino code to device")
        print("3. Test all button mappings")
        
    except Exception as e:
        print(f"❌ Error during reorganization: {e}")
        raise

if __name__ == "__main__":
    main()
