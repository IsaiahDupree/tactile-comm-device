#!/usr/bin/env python3
"""
UPDATED Shift Button Help Generator for Tactile Communication Device
Generates TTS files for SHIFT button press levels 2 & 3 (press 1 = recorded hello)
"""

import os
import requests
from pathlib import Path

# ElevenLabs Configuration
API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # Rilou is clear and natural
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

# TTS Settings - SLOWER speech for better comprehension
TTS_SETTINGS = {
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.90,        # Higher stability for clearer pronunciation
        "similarity_boost": 0.80, # Better similarity to original voice
        "style": 0.10,           # Less style for clearer speech
        "use_speaker_boost": True # Enhanced clarity
    }
}

# SLOWER TTS Settings for word mapping (easier to follow)
TTS_SLOW_SETTINGS = {
    "model_id": "eleven_multilingual_v2", 
    "voice_settings": {
        "stability": 0.95,        # Maximum stability for word lists
        "similarity_boost": 0.85, # High similarity
        "style": 0.05,           # Minimal style for clarity
        "use_speaker_boost": True # Enhanced clarity
    }
}

OUTPUT_DIR = Path("output/33")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_tts(text: str, filename: str, max_length: int = 8000, slow_speech: bool = False):
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json", 
        "xi-api-key": API_KEY
    }
    
    # Use slower settings for word mapping
    settings = TTS_SLOW_SETTINGS if slow_speech else TTS_SETTINGS
    data = { "text": text, **settings }

    if len(text) > max_length:
        print(f"⚠️ Truncating text to {max_length} characters")
        text = text[:max_length - 3] + "..."

    speed_note = " (SLOW SPEECH)" if slow_speech else ""
    print(f"🎧 Generating {filename}{speed_note}...")
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        output_path = OUTPUT_DIR / filename
        with open(output_path, "wb") as f:
            f.write(response.content)
        file_size = os.path.getsize(output_path)
        print(f"✅ Saved to {output_path} ({file_size:,} bytes)")
    except Exception as e:
        print(f"❌ Error: {e}")

# ---- Updated Texts ----

# Track 2: Device Instructions (normal speed)
shift_2 = (
    "Welcome to your Tactile Communication Device. "
    "The device has four special buttons: Yes, No, Water, and Shift. "
    "It also has 26 letter buttons, from A to Z. "
    "Each button supports multiple presses to cycle through different words. "
    "Press once for the first word, twice for the second, and so on. "
    "The device uses text-to-speech and personal recordings stored locally, so it works offline. "
    "It runs on rechargeable batteries and charges with a USB-C cable. "
    "Press Shift twice to hear these instructions again. "
    "Press Shift three times to hear the full word list."
)

# Track 3: Word List with SLOWER pacing and clearer pauses
shift_3 = (
    "Word list mapping. Please listen carefully. "
    "Letter A has: Apple, Amer, Alari, Arabic, Amory. "
    "Letter B has: Ball, Bye, Bathroom, Bed. "
    "Letter C has: Cat, Chair, Car. "
    "Letter D has: Dog, Deen, Daddy, Doctor. "
    "Letter E has: Elephant. "
    "Letter F has: Fish, FaceTime. "
    "Letter G has: Go, Good morning. "
    "Letter H has: House, Hello, How are you. "
    "Letter I has: Ice, Inside. "
    "Letter J has: Jump. "
    "Letter K has: Key, Kiyah, Kyan, Kleenex. "
    "Letter L has: Love, Lee, I love you, Light. "
    "Letter M has: Moon, Medicine, Mohammad. "
    "Letter N has: Net, Nadowie, Noah. "
    "Letter O has: Orange, Outside. "
    "Letter P has: Purple, Phone, Pain. "
    "Letter Q has: Queen. "
    "Letter R has: Red, Room. "
    "Letter S has: Sun, Susu, Scarf. "
    "Letter T has: Tree, TV. "
    "Letter U has: Up, Urgent Care. "
    "Letter V has: Van. "
    "Letter W has: Water, Walker, Wheelchair, Walk. "
    "Letter X has: X-ray. "
    "Letter Y has: Yellow. "
    "Letter Z has: Zebra. "
    "Remember: Press the same letter multiple times to cycle through all available words for that letter."
)

# ---- Generate Updated MP3s ----

print("🎙️ UPDATED SHIFT BUTTON HELP GENERATOR")
print("=" * 50)
print("📝 Note: 001.mp3 = Recorded 'Hello How are You' (already copied)")
print()

# Generate 002.mp3 - Device instructions (normal speed)
generate_tts(shift_2, "002.mp3", max_length=8000, slow_speech=False)

# Generate 003.mp3 - Word list (SLOW speech for clarity)
generate_tts(shift_3, "003.mp3", max_length=10000, slow_speech=True)

print("\n📂 Updated audio files:")
print("• 001.mp3 → Personal recorded 'Hello How are You'")
print("• 002.mp3 → TTS device instructions (normal speed)")
print("• 003.mp3 → TTS word list mapping (SLOW speech for clarity)")

print("\n🎮 NEW SHIFT Button Function:")
print("• Press 1x → Personal greeting (recorded)")
print("• Press 2x → Device instructions (~2 min)")
print("• Press 3x → Slower word list (~4 min, easier to follow)")
print("\n🎯 Copy 002.mp3 and 003.mp3 to SD card folder /33/")
