#!/usr/bin/env python3
"""
Generate the 4 missing TTS files for the tactile communication device.
Uses ElevenLabs API to generate high-quality TTS audio.
"""

import requests
import os
import json
import time

# ElevenLabs API configuration
API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"
SD_CARD_PATH = "E:\\"

# Missing TTS files to generate
MISSING_FILES = [
    {"folder": 15, "track": 5, "text": "Kitchen", "button": "K"},
    {"folder": 25, "track": 3, "text": "Under", "button": "U"},
    {"folder": 27, "track": 5, "text": "Window", "button": "W"},
    {"folder": 27, "track": 6, "text": "Work", "button": "W"},
]

def generate_tts_audio(text, output_path):
    """Generate TTS audio using ElevenLabs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
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
    
    print(f"🎵 Generating TTS for: '{text}'")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_path)
            print(f"✅ Generated: {output_path} ({file_size:,} bytes)")
            return True
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating TTS: {e}")
        return False

def generate_missing_tts_files():
    """Generate all missing TTS files."""
    print("🎵 GENERATING MISSING TTS FILES")
    print("=" * 50)
    
    if not API_KEY or API_KEY == "your_elevenlabs_api_key_here":
        print("❌ Please set your ElevenLabs API key in the script")
        return False
    
    if not os.path.exists(SD_CARD_PATH):
        print(f"❌ SD card not found at: {SD_CARD_PATH}")
        return False
    
    generated_count = 0
    
    for file_info in MISSING_FILES:
        folder = file_info["folder"]
        track = file_info["track"]
        text = file_info["text"]
        button = file_info["button"]
        
        # Create folder path
        folder_path = os.path.join(SD_CARD_PATH, f"{folder:02d}")
        os.makedirs(folder_path, exist_ok=True)
        
        # Create file path
        file_path = os.path.join(folder_path, f"{track:03d}.mp3")
        
        print(f"\n📁 {button} Button - Folder {folder:02d}")
        print(f"   Target: /{folder:02d}/{track:03d}.mp3")
        print(f"   Text: '{text}'")
        
        # Check if file already exists
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ⚠️  File already exists ({size:,} bytes) - skipping")
            continue
        
        # Generate TTS audio
        if generate_tts_audio(text, file_path):
            generated_count += 1
            
            # Add small delay between API calls to be respectful
            time.sleep(1)
        else:
            print(f"   ❌ Failed to generate TTS for '{text}'")
    
    print("\n" + "=" * 50)
    if generated_count > 0:
        print(f"🎉 Successfully generated {generated_count} TTS files!")
        
        # Update audio manifest
        update_audio_manifest()
        
        print("\n✅ ALL MISSING TTS FILES GENERATED!")
        print("Your tactile communication device is now complete!")
    else:
        print("ℹ️  No new files were generated (all files already exist)")
    
    print("=" * 50)
    return generated_count > 0

def update_audio_manifest():
    """Update the audio manifest with new TTS files."""
    manifest_path = os.path.join(SD_CARD_PATH, "AUDIO_MANIFEST.json")
    
    try:
        # Load existing manifest
        manifest = {}
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        
        # Add new entries
        for file_info in MISSING_FILES:
            folder = file_info["folder"]
            track = file_info["track"]
            text = file_info["text"]
            button = file_info["button"]
            
            key = f"{folder:02d}/{track:03d}.mp3"
            manifest[key] = {
                "text": text,
                "type": "TTS",
                "button": button,
                "generated": True
            }
        
        # Save updated manifest
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        
        print("📝 Updated audio manifest")
        
    except Exception as e:
        print(f"⚠️  Could not update manifest: {e}")

if __name__ == "__main__":
    generate_missing_tts_files()
