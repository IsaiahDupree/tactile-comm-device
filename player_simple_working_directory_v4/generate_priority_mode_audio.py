#!/usr/bin/env python3
"""
Generate Priority Mode Announcement Audio Files
Creates MP3 files for the tactile device priority mode announcements using ElevenLabs API

Required files:
- /33/001.mp3 - "Human first mode"
- /33/002.mp3 - "Generated first mode"

Usage:
  python generate_priority_mode_audio.py

Output will be saved to ./audio_announcements/33/ directory
"""

import os
import sys
import requests
import json

def generate_with_elevenlabs(text, output_file, api_key, voice_id="RILOU7YmBhvwJGDGjNmP"):
    """
    Generate audio using ElevenLabs API
    Default voice: Rilou (RILOU7YmBhvwJGDGjNmP)
    Fallback: Rachel (21m00Tcm4TlvDq8ikWAM)
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            # If primary voice fails, try fallback
            if voice_id != "21m00Tcm4TlvDq8ikWAM":  # If not already using Rachel
                print("Trying fallback voice (Rachel)...")
                return generate_with_elevenlabs(text, output_file, api_key, "21m00Tcm4TlvDq8ikWAM")
            return False
            
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        return False

def main():
    # Set API key
    api_key = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"  # Using provided key
    
    # Create local directory for output
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_announcements", "33")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    
    # Generate announcements
    announcements = {
        "001.mp3": "Human first mode",
        "002.mp3": "Generated first mode"
    }
    
    print("Generating priority mode announcement files using ElevenLabs...")
    
    for filename, text in announcements.items():
        file_path = os.path.join(output_dir, filename)
        print(f"Creating {file_path} - '{text}'")
        
        # Generate MP3 using ElevenLabs
        success = generate_with_elevenlabs(text, file_path, api_key)
        if success:
            print(f"✅ Successfully generated {filename}")
        else:
            print(f"❌ Failed to generate {filename}")
    
    print("\nAudio generation process complete!")
    print("\nFiles created (if successful):")
    for filename in announcements.keys():
        file_path = os.path.join(output_dir, filename)
        if os.path.exists(file_path):
            print(f"- {file_path} ✅")
        else:
            print(f"- {file_path} ❌ (Failed)")
    
    print("\nNow you can copy these files to your SD card in the /33/ directory")
    print("Then you can use the 'M' serial command or the triple-press")
    print("of the period button to toggle priority modes with announcements.")

if __name__ == "__main__":
    main()
