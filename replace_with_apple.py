#!/usr/bin/env python3
"""
Replace /05/004.mp3 with "Apple" TTS to make Apple the first TTS option for A button.
"""

import requests
import os
import json

# ElevenLabs API configuration
API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"
SD_CARD_PATH = "E:\\"

def generate_apple_tts():
    """Generate Apple TTS audio."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": "Apple",
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    print("🍎 Generating TTS for: 'Apple'")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating TTS: {e}")
        return None

def replace_arabic_show_with_apple():
    """Replace /05/004.mp3 (Arabic Show) with Apple TTS."""
    print("🍎 REPLACING ARABIC SHOW WITH APPLE")
    print("=" * 50)
    
    # Target file path
    target_file = os.path.join(SD_CARD_PATH, "05", "004.mp3")
    
    print(f"Target file: {target_file}")
    
    # Check if file exists
    if not os.path.exists(target_file):
        print(f"❌ File not found: {target_file}")
        return False
    
    # Show current file info
    current_size = os.path.getsize(target_file)
    print(f"Current file: 004.mp3 ({current_size:,} bytes) - 'Arabic Show'")
    
    # Generate Apple TTS
    apple_audio = generate_apple_tts()
    
    if not apple_audio:
        print("❌ Failed to generate Apple TTS")
        return False
    
    # Backup current file
    backup_file = target_file.replace(".mp3", "_arabic_show_backup.mp3")
    print(f"📁 Creating backup: {backup_file}")
    
    try:
        # Create backup
        with open(target_file, 'rb') as src, open(backup_file, 'wb') as dst:
            dst.write(src.read())
        
        # Replace with Apple
        with open(target_file, 'wb') as f:
            f.write(apple_audio)
        
        new_size = os.path.getsize(target_file)
        print(f"✅ Replaced with Apple TTS ({new_size:,} bytes)")
        
        # Update audio index
        update_audio_index()
        
        print("\n🍎 SUCCESS!")
        print("A button TTS order is now:")
        print("  Track 4: Apple (NEW)")
        print("  Track 5: Attention")
        print("  Track 6: Awesome")
        print("\nArabic Show backed up as: 004_arabic_show_backup.mp3")
        
        return True
        
    except Exception as e:
        print(f"❌ Error replacing file: {e}")
        return False

def update_audio_index():
    """Update audio index to reflect Apple instead of Arabic Show."""
    csv_path = os.path.join(SD_CARD_PATH, "config", "audio_index.csv")
    
    if not os.path.exists(csv_path):
        print("⚠️  Audio index not found, skipping update")
        return
    
    try:
        # Read current CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the line for 05,4
        updated_lines = []
        for line in lines:
            if line.startswith('5,4,'):
                # Replace Arabic Show with Apple
                updated_lines.append('5,4,Apple,TTS\n')
                print("📝 Updated audio index: 5,4,Apple,TTS")
            else:
                updated_lines.append(line)
        
        # Write back
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print("✅ Audio index updated")
        
    except Exception as e:
        print(f"⚠️  Could not update audio index: {e}")

if __name__ == "__main__":
    if replace_arabic_show_with_apple():
        print("\n🎯 READY TO TEST!")
        print("Upload Arduino firmware and test A button.")
        print("In GENERATED_FIRST mode, first press should now play 'Apple'!")
    else:
        print("\n❌ Failed to replace Arabic Show with Apple")
