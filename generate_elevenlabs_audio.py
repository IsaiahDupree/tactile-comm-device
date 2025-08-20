#!/usr/bin/env python3
"""
Generate all audio files using ElevenLabs TTS API based on wordlist
"""

import os
import json
import requests
import time

# ElevenLabs API configuration
ELEVENLABS_API_KEY = "sk_c167a8fb150750ebb1cb825a8e4ddfbfd48fc8b9125d6f49"  # Replace with your actual API key
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

def generate_all_audio():
    """Generate all audio files from wordlist"""
    
    # Read the wordlist
    with open('wordlist', 'r') as f:
        wordlist = json.load(f)
    
    base_dir = "player_simple_working_directory_v4/SD_CARD_STRUCTURE/audio"
    
    print("Generating ElevenLabs TTS audio for all wordlist entries...")
    
    total_files = 0
    generated_files = 0
    
    # Process letters A-Z
    for letter, data in wordlist["letters"].items():
        # Generate human audio (if any)
        human_words = data.get("human", [])
        if human_words:
            human_dir = f"{base_dir}/human/{letter}"
            os.makedirs(human_dir, exist_ok=True)
            for i, word in enumerate(human_words, 1):
                filename = f"{i:03d}.mp3"
                output_path = f"{human_dir}/{filename}"
                total_files += 1
                if generate_audio_file(word, output_path):
                    generated_files += 1
                time.sleep(0.5)  # Rate limiting
        
        # Generate generated audio
        gen_words = data.get("generated", [])
        if gen_words:
            gen_dir = f"{base_dir}/generated/{letter}"
            os.makedirs(gen_dir, exist_ok=True)
            for i, word in enumerate(gen_words, 1):
                filename = f"{i:03d}.mp3"
                output_path = f"{gen_dir}/{filename}"
                total_files += 1
                if generate_audio_file(word, output_path):
                    generated_files += 1
                time.sleep(0.5)  # Rate limiting
    
    # Process special phrases
    for phrase, data in wordlist["phrases"].items():
        # Generate human audio (if any)
        human_words = data.get("human", [])
        if human_words:
            human_dir = f"{base_dir}/human/{phrase}"
            os.makedirs(human_dir, exist_ok=True)
            for i, word in enumerate(human_words, 1):
                filename = f"{i:03d}.mp3"
                output_path = f"{human_dir}/{filename}"
                total_files += 1
                if generate_audio_file(word, output_path):
                    generated_files += 1
                time.sleep(0.5)  # Rate limiting
        
        # Generate generated audio
        gen_words = data.get("generated", [])
        if gen_words:
            gen_dir = f"{base_dir}/generated/{phrase}"
            os.makedirs(gen_dir, exist_ok=True)
            for i, word in enumerate(gen_words, 1):
                filename = f"{i:03d}.mp3"
                output_path = f"{gen_dir}/{filename}"
                total_files += 1
                if generate_audio_file(word, output_path):
                    generated_files += 1
                time.sleep(0.5)  # Rate limiting
    
    print(f"\nGeneration complete: {generated_files}/{total_files} files")
    print(f"Copy entire SD_CARD_STRUCTURE to your physical SD card")
    print(f"The device will now match wordlist definitions exactly")

if __name__ == "__main__":
    if ELEVENLABS_API_KEY == "your_api_key_here":
        print("Please set your ElevenLabs API key in the script")
        exit(1)
    
    generate_all_audio()
