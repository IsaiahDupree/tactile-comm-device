#!/usr/bin/env python3
"""
TTS Vocabulary Update Script
Updates SD card audio files to match the JSON vocabulary specification
Uses ElevenLabs API with the previously used voice ID
"""

import os
import json
import requests
import time
from pathlib import Path

# ElevenLabs Configuration
API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # Previously used voice ID
SD_CARD_PATH = "E:\\"

# Your vocabulary specification
VOCABULARY = {
    "A": ["Alari", "Amer", "Apple", "Arabic Show"],
    "B": ["Bagel", "Bathroom", "Bed", "Blanket", "Breathe", "Bye"],
    "C": ["Call", "Car", "Chair", "Coffee", "Cold", "Cucumber"],
    "D": ["Daddy", "Deen", "Doctor", "Door", "Down"],
    "E": [],
    "F": ["FaceTime", "Funny"],
    "G": ["Garage", "Go", "Good Morning"],
    "H": ["Happy", "Heartburn", "Hot", "How are you", "Hungry"],
    "I": ["Inside", "iPad"],
    "J": [],
    "K": ["Kaiser", "Kiyah", "Kleenex", "Kyan"],
    "L": ["I love you", "Lee", "Light Down", "Light Up"],
    "M": ["Mad", "Medical", "Medicine", "Meditate", "Mohammad"],
    "N": ["Nada", "Nadowie", "No", "Noah"],
    "O": ["Outside"],
    "P": ["Pain", "Period", "Phone", "Purple"],
    "Q": [],
    "R": ["Rest", "Room"],
    "S": ["Sad", "Scarf", "Shoes", "Sinemet", "Sleep", "Socks", "Stop", "Space", "Susu"],
    "T": ["TV", "Togamet", "Tylenol"],
    "U": ["Up", "Urgent Care"],
    "V": [],
    "W": ["Walk", "Walker", "Water", "Wheelchair"],
    "X": [],
    "Y": ["Yes"],
    "Z": []
}

# Button to folder mapping
BUTTON_FOLDERS = {
    "A": 5, "B": 6, "C": 7, "D": 8, "E": 9, "F": 10, "G": 11, "H": 12,
    "I": 13, "J": 14, "K": 15, "L": 16, "M": 17, "N": 18, "O": 19, "P": 20,
    "Q": 21, "R": 22, "S": 23, "T": 24, "U": 25, "V": 26, "W": 27, "X": 28,
    "Y": 29, "Z": 30
}

# Personal recordings (these should NOT be overwritten)
PERSONAL_RECORDINGS = {
    "A": ["Alari"],           # /05/001.mp3
    "D": ["Daddy"],           # /08/001.mp3  
    "L": ["I love you"],      # /16/001.mp3
    "N": ["Nada", "Nadowie", "Noah"],  # /18/001.mp3, /18/002.mp3, /18/003.mp3
    "S": ["Susu"]             # /23/001.mp3
}

def generate_tts_audio(text, output_path, voice_id=VOICE_ID):
    """Generate TTS audio using ElevenLabs API"""
    
    if API_KEY == "your_api_key_here":
        print("❌ Please set your ElevenLabs API key in the script!")
        return False
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        print(f"🎵 Generating TTS: '{text}' -> {output_path}")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Generated: {output_path}")
            return True
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {output_path}: {e}")
        return False

def update_button_vocabulary(button, words):
    """Update TTS files for a specific button"""
    
    if not words:  # Empty vocabulary
        print(f"⏭️  Button {button}: Empty vocabulary, skipping")
        return
        
    folder_num = BUTTON_FOLDERS[button]
    folder_path = os.path.join(SD_CARD_PATH, f"{folder_num:02d}")
    
    print(f"\n📁 Updating Button {button} (Folder {folder_num:02d})")
    print(f"   Vocabulary: {words}")
    
    # Ensure folder exists
    os.makedirs(folder_path, exist_ok=True)
    
    # Determine starting track number (skip personal recordings)
    personal_recs = PERSONAL_RECORDINGS.get(button, [])
    start_track = len(personal_recs) + 1
    
    if personal_recs:
        print(f"   🎙️  Personal recordings (tracks 1-{len(personal_recs)}): {personal_recs}")
        print(f"   🤖 TTS will start at track {start_track}")
    
    # Generate TTS for each word
    track_num = start_track
    for word in words:
        # Skip personal recordings
        if word in personal_recs:
            print(f"   ⏭️  Skipping '{word}' (personal recording)")
            continue
            
        output_file = os.path.join(folder_path, f"{track_num:03d}.mp3")
        
        if generate_tts_audio(word, output_file):
            track_num += 1
            time.sleep(0.5)  # Rate limiting
        else:
            print(f"   ❌ Failed to generate '{word}'")

def create_audio_manifest():
    """Create a manifest file showing what text each audio file contains"""
    
    manifest_path = os.path.join(SD_CARD_PATH, "AUDIO_MANIFEST.json")
    manifest = {}
    
    print(f"\n📋 Creating audio manifest: {manifest_path}")
    
    for button, words in VOCABULARY.items():
        if not words:
            continue
            
        folder_num = BUTTON_FOLDERS[button]
        folder_key = f"{folder_num:02d}"
        manifest[folder_key] = {
            "button": button,
            "folder": f"/{folder_num:02d}/",
            "tracks": {}
        }
        
        # Add personal recordings
        personal_recs = PERSONAL_RECORDINGS.get(button, [])
        for i, word in enumerate(personal_recs, 1):
            manifest[folder_key]["tracks"][f"{i:03d}.mp3"] = {
                "text": word,
                "type": "personal_recording"
            }
        
        # Add TTS tracks
        track_num = len(personal_recs) + 1
        for word in words:
            if word not in personal_recs:
                manifest[folder_key]["tracks"][f"{track_num:03d}.mp3"] = {
                    "text": word,
                    "type": "tts_generated"
                }
                track_num += 1
    
    # Write manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Audio manifest created: {manifest_path}")

def main():
    """Main execution"""
    
    print("🎵 TTS VOCABULARY UPDATE SCRIPT")
    print("=" * 50)
    print(f"Voice ID: {VOICE_ID}")
    print(f"SD Card: {SD_CARD_PATH}")
    
    if not os.path.exists(SD_CARD_PATH):
        print(f"❌ SD card not found at {SD_CARD_PATH}")
        return
    
    # Update each button's vocabulary
    for button in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        words = VOCABULARY.get(button, [])
        if words:  # Only update buttons with vocabulary
            update_button_vocabulary(button, words)
    
    # Create manifest
    create_audio_manifest()
    
    print("\n🎯 VOCABULARY UPDATE COMPLETE!")
    print("Next steps:")
    print("1. Update Arduino code mappings to match new track counts")
    print("2. Test priority mode with updated vocabulary")
    print("3. Check AUDIO_MANIFEST.json for track-to-text mapping")

if __name__ == "__main__":
    main()
