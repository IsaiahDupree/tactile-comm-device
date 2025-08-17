#!/usr/bin/env python3
"""
Generate Priority Mode Audio Files for Tactile Communication Device
Creates TTS audio files for "Human first priority" and "Generated first priority" announcements
"""

import requests
import json
import os
import time

# ElevenLabs API configuration
API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is required")
VOICE_ID = "pqHfZKP75CvOlQylNhV4"  # RILOU voice ID
BASE_URL = "https://api.elevenlabs.io/v1"

def generate_tts_audio(text, output_path):
    """Generate TTS audio using ElevenLabs API"""
    
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
            "similarity_boost": 0.8,
            "style": 0.2,
            "use_speaker_boost": True
        }
    }
    
    try:
        print(f"🎧 Generating: {text} → {output_path}")
        
        response = requests.post(
            f"{BASE_URL}/text-to-speech/{VOICE_ID}",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ Saved: {output_path} ({file_size:,} bytes)")
            return True
            
        else:
            print(f"❌ Error generating {text}: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {text}: {e}")
        return False

def main():
    """Generate priority mode announcement audio files"""
    
    print("🎵 PRIORITY MODE AUDIO GENERATOR")
    print("=" * 50)
    
    # Create output directory
    output_dir = "priority_mode_audio/33"
    os.makedirs(output_dir, exist_ok=True)
    
    # Audio files to generate
    audio_files = [
        {
            "text": "Human first priority",
            "filename": "004.mp3",
            "description": "Human-first mode announcement"
        },
        {
            "text": "Generated first priority", 
            "filename": "005.mp3",
            "description": "Generated-first mode announcement"
        }
    ]
    
    success_count = 0
    
    for audio in audio_files:
        output_path = os.path.join(output_dir, audio["filename"])
        
        if generate_tts_audio(audio["text"], output_path):
            success_count += 1
        
        # Rate limiting delay
        time.sleep(1)
        print()
    
    print("=" * 50)
    print(f"🎉 PRIORITY MODE AUDIO GENERATION COMPLETE!")
    print(f"✅ Successfully generated: {success_count}/{len(audio_files)} files")
    print(f"📂 Files created in: {output_dir}")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Copy the priority_mode_audio/33/ folder to your SD card")
    print("2. Upload the updated Arduino code with priority mode system")
    print("3. Test priority mode switching by pressing Period 3 times quickly")
    print("4. The device will announce the current mode when switched")

if __name__ == "__main__":
    main()
