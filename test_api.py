#!/usr/bin/env python3
import requests
import json

# Test ElevenLabs API
api_key = "sk_c167a8fb150750ebb1cb825a8e4ddfbfd48fc8b9125d6f49"
voice_id = "21m00Tcm4TlvDq8ikWAM"
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json", 
    "xi-api-key": api_key
}

data = {
    "text": "Test audio generation",
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
    }
}

print("Testing ElevenLabs API...")
try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ API working successfully")
        with open("test_audio.mp3", "wb") as f:
            f.write(response.content)
        print("✓ Test audio file created")
    else:
        print(f"✗ API Error: {response.text}")
        
except Exception as e:
    print(f"✗ Exception: {e}")
