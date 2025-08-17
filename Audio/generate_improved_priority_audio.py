#!/usr/bin/env python3
"""
Generate improved priority mode announcement audio files
More concise and user-friendly than the original versions
"""

import os
import requests
import json

# ElevenLabs API configuration
API_KEY = "sk_3cc9cfbe1d68b95ef0b32bd4d0049082097dfc1f769d21b0"  # Your ElevenLabs API key
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (clear, professional)

# Audio settings for clear, concise announcements
VOICE_SETTINGS = {
    "stability": 0.75,
    "similarity_boost": 0.85,
    "style": 0.2,
    "use_speaker_boost": True
}

def generate_audio(text, filename):
    """Generate audio file using ElevenLabs TTS API"""
    
    if API_KEY == "your_elevenlabs_api_key_here":
        print(f"⚠️  Please set your ElevenLabs API key in the script")
        print(f"📝 Would generate: {filename} - '{text}'")
        return False
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": VOICE_SETTINGS
    }
    
    try:
        print(f"🎤 Generating: {text}")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        # Create output directory
        os.makedirs("priority_audio_improved/33", exist_ok=True)
        
        # Save audio file
        filepath = f"priority_audio_improved/33/{filename}"
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"✅ Generated: {filepath}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating {filename}: {e}")
        return False

def main():
    """Generate improved priority mode announcement audio files"""
    
    print("🎵 GENERATING IMPROVED PRIORITY MODE AUDIO")
    print("=" * 50)
    
    # Improved, more concise and natural announcements
    audio_files = [
        {
            "filename": "004.mp3",
            "text": "Personal voice first",
            "description": "HUMAN_FIRST mode - Personal recordings prioritized"
        },
        {
            "filename": "005.mp3", 
            "text": "Computer voice first",
            "description": "GENERATED_FIRST mode - TTS audio prioritized"
        }
    ]
    
    success_count = 0
    
    for audio in audio_files:
        print(f"\n📢 {audio['description']}")
        if generate_audio(audio["text"], audio["filename"]):
            success_count += 1
    
    print(f"\n🎊 GENERATION COMPLETE!")
    print(f"✅ Successfully generated {success_count}/{len(audio_files)} files")
    
    if success_count > 0:
        print(f"\n📁 Files saved to: priority_audio_improved/33/")
        print(f"📋 Next steps:")
        print(f"   1. Copy files to SD card folder /33/")
        print(f"   2. Upload Arduino code to device")
        print(f"   3. Test priority mode switching with Period button (3x press)")
        print(f"   4. Test manual mode switching with 'M' command")
    
    print(f"\n🎯 IMPROVED ANNOUNCEMENTS:")
    for audio in audio_files:
        print(f"   • {audio['filename']}: '{audio['text']}'")
    
    print(f"\n💡 These announcements are:")
    print(f"   ✅ More concise (2-3 words vs 4-5 words)")
    print(f"   ✅ More natural and conversational")
    print(f"   ✅ Easier to understand quickly")
    print(f"   ✅ Less technical jargon")

if __name__ == "__main__":
    main()
