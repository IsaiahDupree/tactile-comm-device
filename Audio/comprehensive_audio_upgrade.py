#!/usr/bin/env python3
"""
Comprehensive Audio System Upgrade for Tactile Communicator
- Named audio files that match actual words
- High-quality RILOU voice for clear speech  
- Multi-track priority system (Generated TTS + Recorded Words)
- Short, concise audio clips
- Complete alphabet + special button coverage
"""

import os
import requests
import json
from pathlib import Path
import shutil
import argparse

# Configuration
SD_CARD_PATH = "E:\\"
RECORDED_WORDS_PATH = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\RecordedWords"
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is required")
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # Clear, understandable voice

# Complete word mapping with proper track naming
COMPLETE_AUDIO_MAPPING = {
    # Special buttons (Priority 1: Generated TTS, Priority 2: Recorded if available)
    "YES": {
        "folder": 1,
        "tracks": [
            {"file": "yes.mp3", "word": "Yes", "type": "generated", "priority": 1},
            {"file": "yes_recorded.mp3", "word": "Yes", "type": "recorded", "priority": 2}
        ]
    },
    "NO": {
        "folder": 2,
        "tracks": [
            {"file": "no.mp3", "word": "No", "type": "generated", "priority": 1},
            {"file": "no_recorded.mp3", "word": "No", "type": "recorded", "priority": 2}
        ]
    },
    "WATER": {
        "folder": 3,
        "tracks": [
            {"file": "water.mp3", "word": "Water", "type": "generated", "priority": 1},
            {"file": "water_recorded.mp3", "word": "Water", "type": "recorded", "priority": 2}
        ]
    },
    
    # Letters A-Z with clear, simple words
    "A": {
        "folder": 5,
        "tracks": [
            {"file": "apple.mp3", "word": "Apple", "type": "generated", "priority": 1},
            {"file": "amer.mp3", "word": "Amer", "type": "recorded", "priority": 2},
            {"file": "alari.mp3", "word": "Alari", "type": "recorded", "priority": 3}
        ]
    },
    "B": {
        "folder": 6,
        "tracks": [
            {"file": "ball.mp3", "word": "Ball", "type": "generated", "priority": 1},
            {"file": "bye.mp3", "word": "Bye", "type": "recorded", "priority": 2},
            {"file": "bathroom.mp3", "word": "Bathroom", "type": "generated", "priority": 3}
        ]
    },
    "C": {
        "folder": 7,
        "tracks": [
            {"file": "cat.mp3", "word": "Cat", "type": "generated", "priority": 1},
            {"file": "chair.mp3", "word": "Chair", "type": "generated", "priority": 2},
            {"file": "car.mp3", "word": "Car", "type": "generated", "priority": 3}
        ]
    },
    "D": {
        "folder": 8,
        "tracks": [
            {"file": "dog.mp3", "word": "Dog", "type": "generated", "priority": 1},
            {"file": "deen.mp3", "word": "Deen", "type": "recorded", "priority": 2},
            {"file": "daddy.mp3", "word": "Daddy", "type": "recorded", "priority": 3}
        ]
    },
    "E": {
        "folder": 9,
        "tracks": [
            {"file": "elephant.mp3", "word": "Elephant", "type": "generated", "priority": 1}
        ]
    },
    "F": {
        "folder": 10,
        "tracks": [
            {"file": "fish.mp3", "word": "Fish", "type": "generated", "priority": 1},
            {"file": "facetime.mp3", "word": "FaceTime", "type": "generated", "priority": 2}
        ]
    },
    "G": {
        "folder": 11,
        "tracks": [
            {"file": "go.mp3", "word": "Go", "type": "generated", "priority": 1},
            {"file": "good_morning.mp3", "word": "Good Morning", "type": "recorded", "priority": 2}
        ]
    },
    "H": {
        "folder": 12,
        "tracks": [
            {"file": "house.mp3", "word": "House", "type": "generated", "priority": 1},
            {"file": "hello.mp3", "word": "Hello", "type": "generated", "priority": 2}
        ]
    },
    "I": {
        "folder": 13,
        "tracks": [
            {"file": "ice.mp3", "word": "Ice", "type": "generated", "priority": 1},
            {"file": "inside.mp3", "word": "Inside", "type": "generated", "priority": 2}
        ]
    },
    "J": {
        "folder": 14,
        "tracks": [
            {"file": "jump.mp3", "word": "Jump", "type": "generated", "priority": 1}
        ]
    },
    "K": {
        "folder": 15,
        "tracks": [
            {"file": "key.mp3", "word": "Key", "type": "generated", "priority": 1},
            {"file": "kiyah.mp3", "word": "Kiyah", "type": "recorded", "priority": 2},
            {"file": "kyan.mp3", "word": "Kyan", "type": "recorded", "priority": 3}
        ]
    },
    "L": {
        "folder": 16,
        "tracks": [
            {"file": "love.mp3", "word": "Love", "type": "generated", "priority": 1},
            {"file": "lee.mp3", "word": "Lee", "type": "recorded", "priority": 2},
            {"file": "i_love_you.mp3", "word": "I love you", "type": "recorded", "priority": 3}
        ]
    },
    "M": {
        "folder": 17,
        "tracks": [
            {"file": "moon.mp3", "word": "Moon", "type": "generated", "priority": 1},
            {"file": "medicine.mp3", "word": "Medicine", "type": "generated", "priority": 2}
        ]
    },
    "N": {
        "folder": 18,
        "tracks": [
            {"file": "net.mp3", "word": "Net", "type": "generated", "priority": 1},
            {"file": "nadowie.mp3", "word": "Nadowie", "type": "recorded", "priority": 2},
            {"file": "noah.mp3", "word": "Noah", "type": "recorded", "priority": 3}
        ]
    },
    "O": {
        "folder": 19,
        "tracks": [
            {"file": "orange.mp3", "word": "Orange", "type": "generated", "priority": 1},
            {"file": "outside.mp3", "word": "Outside", "type": "generated", "priority": 2}
        ]
    },
    "P": {
        "folder": 20,
        "tracks": [
            {"file": "purple.mp3", "word": "Purple", "type": "generated", "priority": 1},
            {"file": "phone.mp3", "word": "Phone", "type": "generated", "priority": 2}
        ]
    },
    "Q": {
        "folder": 21,
        "tracks": [
            {"file": "queen.mp3", "word": "Queen", "type": "generated", "priority": 1}
        ]
    },
    "R": {
        "folder": 22,
        "tracks": [
            {"file": "red.mp3", "word": "Red", "type": "generated", "priority": 1},
            {"file": "room.mp3", "word": "Room", "type": "generated", "priority": 2}
        ]
    },
    "S": {
        "folder": 23,
        "tracks": [
            {"file": "sun.mp3", "word": "Sun", "type": "generated", "priority": 1},
            {"file": "susu.mp3", "word": "Susu", "type": "recorded", "priority": 2}
        ]
    },
    "T": {
        "folder": 24,
        "tracks": [
            {"file": "tree.mp3", "word": "Tree", "type": "generated", "priority": 1},
            {"file": "tv.mp3", "word": "TV", "type": "generated", "priority": 2}
        ]
    },
    "U": {
        "folder": 25,
        "tracks": [
            {"file": "up.mp3", "word": "Up", "type": "generated", "priority": 1},
            {"file": "urgent_care.mp3", "word": "Urgent Care", "type": "recorded", "priority": 2}
        ]
    },
    "V": {
        "folder": 26,
        "tracks": [
            {"file": "van.mp3", "word": "Van", "type": "generated", "priority": 1}
        ]
    },
    "W": {
        "folder": 27,
        "tracks": [
            {"file": "water.mp3", "word": "Water", "type": "generated", "priority": 1},
            {"file": "walker.mp3", "word": "Walker", "type": "recorded", "priority": 2},
            {"file": "wheelchair.mp3", "word": "Wheelchair", "type": "recorded", "priority": 3}
        ]
    },
    "X": {
        "folder": 28,
        "tracks": [
            {"file": "xray.mp3", "word": "X-ray", "type": "generated", "priority": 1}
        ]
    },
    "Y": {
        "folder": 29,
        "tracks": [
            {"file": "yellow.mp3", "word": "Yellow", "type": "generated", "priority": 1}
        ]
    },
    "Z": {
        "folder": 30,
        "tracks": [
            {"file": "zebra.mp3", "word": "Zebra", "type": "generated", "priority": 1}
        ]
    },
    
    # Special buttons
    "SPACE": {
        "folder": 31,
        "tracks": [
            {"file": "space.mp3", "word": "Space", "type": "generated", "priority": 1}
        ]
    },
    "PERIOD": {
        "folder": 32,
        "tracks": [
            {"file": "period.mp3", "word": "Period", "type": "generated", "priority": 1}
        ]
    },
    "SHIFT": {
        "folder": 33,
        "tracks": [
            {"file": "shift.mp3", "word": "Shift", "type": "generated", "priority": 1}
        ]
    }
}

def generate_audio_file(text, output_path, voice_id=VOICE_ID):
    """Generate audio file using ElevenLabs API with RILOU voice"""
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    # Optimized settings for clear, concise speech
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",  # Better quality model
        "voice_settings": {
            "stability": 0.7,        # Higher stability for clarity
            "similarity_boost": 0.8,  # Higher similarity for consistency
            "style": 0.2,            # Low style for neutral speech
            "use_speaker_boost": True,
            "optimize_streaming_latency": 0,  # Best quality
            "output_format": "mp3_22050_32"  # Compact but clear format
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        # Check file size (warn if > 100KB for a single word)
        file_size = os.path.getsize(output_path)
        if file_size > 100000:  # 100KB
            print(f"  ⚠️ Large file: {file_size/1024:.1f}KB")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating audio: {e}")
        return False

def copy_recorded_files():
    """Copy recorded files from RecordedWords folder if they exist"""
    recorded_path = Path(RECORDED_WORDS_PATH)
    
    if not recorded_path.exists():
        print(f"📁 Creating RecordedWords folder: {recorded_path}")
        recorded_path.mkdir(parents=True, exist_ok=True)
        return {}
    
    copied_files = {}
    
    for label, mapping in COMPLETE_AUDIO_MAPPING.items():
        folder_num = f"{mapping['folder']:02d}"
        sd_folder = Path(SD_CARD_PATH) / folder_num
        
        for track in mapping['tracks']:
            if track['type'] == 'recorded':
                recorded_file = recorded_path / track['file']
                sd_file = sd_folder / track['file']
                
                if recorded_file.exists():
                    sd_folder.mkdir(exist_ok=True)
                    shutil.copy2(recorded_file, sd_file)
                    copied_files[track['file']] = str(sd_file)
                    print(f"  📄 Copied: {track['file']} → Folder {folder_num}")
    
    return copied_files

def generate_complete_audio_system(dry_run=False):
    """Generate complete audio system with named files"""
    
    print("=== COMPREHENSIVE AUDIO SYSTEM UPGRADE ===")
    print(f"Voice: RILOU (Clear & Understandable)")
    print(f"SD Card: {SD_CARD_PATH}")
    print(f"Recorded Words: {RECORDED_WORDS_PATH}")
    print(f"Dry Run: {dry_run}")
    print()
    
    # First, copy any existing recorded files
    print("🎵 Copying recorded audio files...")
    copied_files = copy_recorded_files()
    print(f"  ✅ Copied {len(copied_files)} recorded files")
    
    # Generate list of files to create
    files_to_generate = []
    
    for label, mapping in COMPLETE_AUDIO_MAPPING.items():
        folder_num = f"{mapping['folder']:02d}"
        folder_path = Path(SD_CARD_PATH) / folder_num
        
        print(f"📁 Folder {folder_num} ({label}):")
        
        for track in mapping['tracks']:
            if track['type'] == 'generated':
                files_to_generate.append({
                    'label': label,
                    'folder_num': folder_num,
                    'folder_path': folder_path,
                    'filename': track['file'],
                    'word': track['word'],
                    'priority': track['priority']
                })
                print(f"  → Generate: {track['file']} = '{track['word']}'")
            elif track['type'] == 'recorded':
                recorded_file = Path(RECORDED_WORDS_PATH) / track['file']
                if recorded_file.exists():
                    print(f"  ✅ Recorded: {track['file']} (from RecordedWords folder)")
                else:
                    print(f"  ⚠️ Missing recorded: {track['file']} (will skip)")
    
    print(f"\n📋 Total files to generate: {len(files_to_generate)}")
    
    if dry_run:
        print("\\n🔍 DRY RUN - No files will be created")
        return
    
    response = input(f"\nGenerate {len(files_to_generate)} TTS audio files? (y/N): ")
    if response.lower() != 'y':
        print("Generation cancelled.")
        return
    
    # Generate the files
    success_count = 0
    total_size = 0
    
    for i, item in enumerate(files_to_generate, 1):
        print(f"\n[{i}/{len(files_to_generate)}] {item['label']}: {item['filename']}")
        
        # Create folder if it doesn't exist
        item['folder_path'].mkdir(exist_ok=True)
        
        # Generate audio file
        output_path = item['folder_path'] / item['filename']
        
        if generate_audio_file(item['word'], output_path):
            file_size = os.path.getsize(output_path)
            total_size += file_size
            print(f"  ✅ Created: {output_path} ({file_size/1024:.1f}KB)")
            success_count += 1
        else:
            print(f"  ❌ Failed: {output_path}")
    
    print(f"\n=== GENERATION COMPLETE ===")
    print(f"✅ Successfully generated: {success_count}/{len(files_to_generate)} files")
    print(f"📦 Total size: {total_size/1024/1024:.1f}MB")
    print(f"📄 Average file size: {total_size/success_count/1024:.1f}KB per file")
    
    if success_count < len(files_to_generate):
        print(f"⚠️ Failed: {len(files_to_generate) - success_count} files")

def create_arduino_mapping_header():
    """Create Arduino header file with the new audio mappings"""
    header_path = Path(SD_CARD_PATH) / "audio_mapping.h"
    
    with open(header_path, 'w') as f:
        f.write("// Auto-generated audio mapping for tactile communicator\n")
        f.write("// DO NOT EDIT MANUALLY - Generated by comprehensive_audio_upgrade.py\n\n")
        
        f.write("struct TrackInfo {\n")
        f.write("  const char* filename;\n")
        f.write("  const char* word;\n")
        f.write("  uint8_t priority;\n")
        f.write("};\n\n")
        
        f.write("struct AudioMapping {\n")
        f.write("  const char* label;\n")
        f.write("  uint8_t folder;\n")
        f.write("  uint8_t trackCount;\n")
        f.write("  TrackInfo tracks[4];  // Max 4 tracks per label\n")
        f.write("};\n\n")
        
        f.write("const AudioMapping audioMappings[] = {\n")
        
        for label, mapping in COMPLETE_AUDIO_MAPPING.items():
            f.write(f'  {{"{label}", {mapping["folder"]}, {len(mapping["tracks"])}, {{')
            
            track_strings = []
            for track in mapping["tracks"][:4]:  # Limit to 4 tracks
                track_strings.append(f'{{"{track["file"]}", "{track["word"]}", {track["priority"]}}}')
            
            f.write(", ".join(track_strings))
            f.write("}},\n")
        
        f.write("};\n\n")
        f.write(f"const uint8_t AUDIO_MAPPINGS_COUNT = {len(COMPLETE_AUDIO_MAPPING)};\n")
    
    print(f"📄 Created Arduino mapping: {header_path}")

def main():
    parser = argparse.ArgumentParser(description="Comprehensive audio system upgrade")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--copy-only", action="store_true", help="Only copy recorded files")
    
    args = parser.parse_args()
    
    if not Path(SD_CARD_PATH).exists():
        print(f"❌ SD card not found at {SD_CARD_PATH}")
        return
    
    if args.copy_only:
        copy_recorded_files()
        return
    
    generate_complete_audio_system(dry_run=args.dry_run)
    
    if not args.dry_run:
        create_arduino_mapping_header()

if __name__ == "__main__":
    main()
