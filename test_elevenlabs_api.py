#!/usr/bin/env python3
"""
Test ElevenLabs API with the provided key.
"""

import requests
import os
from pathlib import Path

# Set API key directly
API_KEY = "sk_e349c46da16f713a586a3848e96bda3a0f40b1b3f709b7c1"
BASE_URL = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "RILOU7YmBhvwJGDGjNmP"

def test_api_connection():
    """Test basic API connection by listing voices."""
    print("=== Testing ElevenLabs API Connection ===")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    
    url = f"{BASE_URL}/voices"
    headers = {"xi-api-key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            voices = response.json()
            print("✓ API Connection Successful!")
            print(f"Available voices: {len(voices.get('voices', []))}")
            
            # Find our voice
            for voice in voices.get("voices", []):
                if voice['voice_id'] == DEFAULT_VOICE_ID:
                    print(f"✓ Found target voice: {voice['name']} ({voice['voice_id']})")
                    return True
            
            print(f"⚠ Target voice {DEFAULT_VOICE_ID} not found")
            return False
            
        else:
            print(f"✗ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

def test_audio_generation():
    """Test generating a single audio file."""
    print("\n=== Testing Audio Generation ===")
    
    test_text = "Hello, this is a test"
    output_file = Path("test_audio.mp3")
    
    url = f"{BASE_URL}/text-to-speech/{DEFAULT_VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": test_text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75
        }
    }
    
    try:
        print(f"Generating: '{test_text}'")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            file_size = output_file.stat().st_size
            print(f"✓ Audio generated successfully!")
            print(f"File: {output_file}")
            print(f"Size: {file_size} bytes")
            
            # Clean up
            output_file.unlink()
            return True
            
        else:
            print(f"✗ Generation Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Generation Error: {e}")
        return False

def main():
    print("ElevenLabs API Test")
    print("=" * 50)
    
    # Test connection
    if not test_api_connection():
        return 1
    
    # Test generation
    if not test_audio_generation():
        return 1
    
    print("\n✓ All tests passed! API is working correctly.")
    return 0

if __name__ == "__main__":
    exit(main())
