#!/usr/bin/env python3
"""
Generate Missing Audio Files for Tactile Communicator
Creates TTS audio files for labels that are missing recorded audio
or need additional generated alternatives.

Priority System:
- Priority 1: Human recorded audio (keep existing)
- Priority 2: Generated TTS audio (create for missing)
"""

import os
import requests
import json
from pathlib import Path
import argparse

# Configuration
SD_CARD_PATH = "E:\\"
ELEVENLABS_API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (default ElevenLabs voice)

# Audio files to generate based on our Arduino mapping
MISSING_AUDIO_PRIORITIES = {
    # Letters that need simple phonetic sounds (Priority 2 - Generated)
    "E": {"folder": 9, "word": "Elephant", "explanation": "Simple word starting with E"},
    "F": {"folder": 10, "word": "Fish", "explanation": "Backup for FaceTime/funny"},
    "G": {"folder": 11, "word": "Go", "explanation": "Backup for Good Morning/Go"},
    "H": {"folder": 12, "word": "House", "explanation": "Backup for How are you/Heartburn"},
    "I": {"folder": 13, "word": "Ice", "explanation": "Backup for Inside"},
    "J": {"folder": 14, "word": "Jump", "explanation": "New word for J"},
    "K": {"folder": 15, "word": "Key", "explanation": "Backup for Kiyah/Kyan"},
    "M": {"folder": 17, "word": "Moon", "explanation": "Backup for Mohammad/Medicine"},
    "N": {"folder": 18, "word": "No", "explanation": "Backup for Nada/Nadowie/Noah"}, 
    "O": {"folder": 19, "word": "Orange", "explanation": "Backup for Outside"},
    "P": {"folder": 20, "word": "Purple", "explanation": "Backup for Pain/Phone"},
    "Q": {"folder": 21, "word": "Queen", "explanation": "New word for Q"},
    "R": {"folder": 22, "word": "Red", "explanation": "Backup for Room"},
    "S": {"folder": 23, "word": "Sun", "explanation": "Backup for Scarf/Susu/Sinemet"},
    "T": {"folder": 24, "word": "Tree", "explanation": "Backup for TV"},
    "U": {"folder": 25, "word": "Up", "explanation": "Backup for Urgent Care"},
    "V": {"folder": 26, "word": "Van", "explanation": "New word for V"},
    "W": {"folder": 27, "word": "Water", "explanation": "Backup for Walker/wheelchair/walk"},
    "X": {"folder": 28, "word": "X-ray", "explanation": "New word for X"},
    "Y": {"folder": 29, "word": "Yellow", "explanation": "New word for Y"},
    "Z": {"folder": 30, "word": "Zebra", "explanation": "New word for Z"},
    
    # Special buttons that need TTS
    "SPACE": {"folder": 31, "word": "Space", "explanation": "Space button audio"},
    "PERIOD": {"folder": 32, "word": "Period", "explanation": "Period button audio"},
    "SHIFT": {"folder": 33, "word": "Shift", "explanation": "Shift button audio"},
    
    # Additional helpful words for existing folders
    "C": {"folder": 7, "word": "Cat", "explanation": "Simple C word for backup"},
}

def check_elevenlabs_setup():
    """Check if ElevenLabs API is properly configured"""
    if ELEVENLABS_API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️  ElevenLabs API key not configured!")
        print("   Please update ELEVENLABS_API_KEY in this script")
        return False
        
    if VOICE_ID == "your_voice_id_here":
        print("⚠️  Voice ID not configured!")
        print("   Please update VOICE_ID in this script")
        return False
        
    return True

def generate_audio_file(text, output_path, voice_id=VOICE_ID):
    """Generate audio file using ElevenLabs API"""
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating audio: {e}")
        return False

def check_existing_files():
    """Check which folders already have audio files"""
    existing_files = {}
    
    for label, info in MISSING_AUDIO_PRIORITIES.items():
        folder_num = f"{info['folder']:02d}"
        folder_path = Path(SD_CARD_PATH) / folder_num
        
        if folder_path.exists():
            mp3_files = list(folder_path.glob("*.mp3"))
            existing_files[label] = {
                'folder': folder_num,
                'count': len(mp3_files),
                'files': [f.name for f in mp3_files]
            }
        else:
            existing_files[label] = {
                'folder': folder_num,
                'count': 0,
                'files': []
            }
    
    return existing_files

def generate_missing_files(dry_run=False):
    """Generate missing audio files"""
    
    if not check_elevenlabs_setup():
        return
    
    print("=== GENERATING MISSING TTS AUDIO FILES ===")
    print(f"SD Card Path: {SD_CARD_PATH}")
    print(f"Dry Run: {dry_run}")
    print()
    
    existing_files = check_existing_files()
    
    files_to_generate = []
    
    for label, info in MISSING_AUDIO_PRIORITIES.items():
        folder_num = f"{info['folder']:02d}"
        folder_path = Path(SD_CARD_PATH) / folder_num
        existing = existing_files[label]
        
        print(f"📁 Folder {folder_num} ({label}): {existing['count']} files")
        
        if existing['count'] == 0:
            # No files exist, need to create 001.mp3
            files_to_generate.append({
                'label': label,
                'folder': folder_num,
                'folder_path': folder_path,
                'filename': '001.mp3',
                'text': info['word'],
                'reason': 'Missing primary audio file'
            })
            print(f"  → Will generate: 001.mp3 ('{info['word']}')")
        else:
            print(f"  ✓ Has files: {', '.join(existing['files'])}")
    
    if not files_to_generate:
        print("\n✅ All required audio files already exist!")
        return
    
    print(f"\n📋 Total files to generate: {len(files_to_generate)}")
    
    if dry_run:
        print("\n🔍 DRY RUN - No files will be created")
        for item in files_to_generate:
            print(f"  Would create: {item['folder']}/{item['filename']} = '{item['text']}'")
        return
    
    response = input(f"\nGenerate {len(files_to_generate)} TTS audio files? (y/N): ")
    if response.lower() != 'y':
        print("Generation cancelled.")
        return
    
    # Generate the files
    success_count = 0
    for i, item in enumerate(files_to_generate, 1):
        print(f"\n[{i}/{len(files_to_generate)}] Generating {item['label']}: {item['filename']}")
        
        # Create folder if it doesn't exist
        item['folder_path'].mkdir(exist_ok=True)
        
        # Generate audio file
        output_path = item['folder_path'] / item['filename']
        
        if generate_audio_file(item['text'], output_path):
            print(f"  ✅ Created: {output_path}")
            success_count += 1
        else:
            print(f"  ❌ Failed: {output_path}")
    
    print(f"\n=== GENERATION COMPLETE ===")
    print(f"✅ Successfully generated: {success_count}/{len(files_to_generate)} files")
    
    if success_count < len(files_to_generate):
        print(f"⚠️  Failed to generate: {len(files_to_generate) - success_count} files")
        print("   Check your API key and network connection")

def create_generation_summary():
    """Create a summary of what was generated"""
    summary_path = Path(SD_CARD_PATH) / "GENERATED_AUDIO_SUMMARY.txt"
    
    with open(summary_path, 'w') as f:
        f.write("TACTILE COMMUNICATOR - GENERATED AUDIO SUMMARY\n")
        f.write("============================================\n\n")
        f.write("Priority-Based Audio System:\n")
        f.write("- Priority 1: Human recorded audio (preserved)\n")
        f.write("- Priority 2: Generated TTS audio (created)\n\n")
        
        f.write("Generated TTS Audio Files:\n")
        for label, info in MISSING_AUDIO_PRIORITIES.items():
            folder_num = f"{info['folder']:02d}"
            f.write(f"Folder {folder_num}: {label} → '{info['word']}' ({info['explanation']})\n")
        
        f.write(f"\nTotal labels with TTS: {len(MISSING_AUDIO_PRIORITIES)}\n")
        f.write("Generated by: generate_missing_audio.py\n")
    
    print(f"📄 Summary created: {summary_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate missing TTS audio for tactile communicator")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without creating files")
    parser.add_argument("--check-only", action="store_true", help="Only check existing files, don't generate")
    
    args = parser.parse_args()
    
    if not Path(SD_CARD_PATH).exists():
        print(f"❌ SD card not found at {SD_CARD_PATH}")
        print("Please update SD_CARD_PATH variable to match your SD card drive")
        return
    
    if args.check_only:
        print("=== CHECKING EXISTING AUDIO FILES ===")
        existing_files = check_existing_files()
        for label, info in existing_files.items():
            status = "✅" if info['count'] > 0 else "❌"
            print(f"{status} {label} (Folder {info['folder']}): {info['count']} files")
        return
    
    generate_missing_files(dry_run=args.dry_run)
    
    if not args.dry_run:
        create_generation_summary()

if __name__ == "__main__":
    main()
