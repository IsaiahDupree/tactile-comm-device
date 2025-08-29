#!/usr/bin/env python3
"""
Generate WiFi toggle audio announcements using ElevenLabs TTS API
"""

import os
import requests
import time

# ElevenLabs API configuration (from existing project)
ELEVENLABS_API_KEY = "sk_c167a8fb150750ebb1cb825a8e4ddfbfd48fc8b9125d6f49"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # User's preferred voice
BASE_URL = "https://api.elevenlabs.io/v1"

def generate_audio_file(text, output_path):
    """Generate a single audio file using ElevenLabs TTS"""
    
    url = f"{BASE_URL}/text-to-speech/{VOICE_ID}"
    
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
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ Generated: {output_path}")
            return True
        else:
            print(f"✗ Failed: {output_path} - {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {output_path} - {e}")
        return False

def generate_wifi_audio():
    """Generate WiFi toggle audio files"""
    
    # Create output directory in v7 SD structure
    output_dir = "player_simple_working_directory_v7/SD_CARD_STRUCTURE/ANNOUNCE"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate WiFi on/off announcements
    wifi_phrases = [
        ("WiFi on", f"{output_dir}/WIFI_ON.MP3"),
        ("WiFi off", f"{output_dir}/WIFI_OFF.MP3")
    ]
    
    print("Generating WiFi toggle audio announcements...")
    
    for text, output_path in wifi_phrases:
        print(f"Generating: {text}")
        if generate_audio_file(text, output_path):
            print(f"✓ Created: {output_path}")
        else:
            print(f"✗ Failed: {output_path}")
        time.sleep(0.5)  # Rate limiting
    
    print(f"\nWiFi audio generation complete!")
    print(f"Files saved to: {output_dir}")
    print(f"Copy to SD card /ANNOUNCE/ directory for device use")

if __name__ == "__main__":
    generate_wifi_audio()
