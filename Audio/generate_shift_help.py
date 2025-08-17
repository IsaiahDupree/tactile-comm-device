#!/usr/bin/env python3
"""
Shift Button Help Generator for Tactile Communication Device
Generates TTS files for 3 Shift button press levels using ElevenLabs API.
"""

import os
import requests
from pathlib import Path

# ElevenLabs Configuration
API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # Rilou is clear and natural
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

TTS_SETTINGS = {
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.85,
        "similarity_boost": 0.75,
        "style": 0.15,
        "use_speaker_boost": True
    }
}

OUTPUT_DIR = Path("output/33")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_tts(text: str, filename: str, max_length: int = 8000):
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    data = { "text": text, **TTS_SETTINGS }

    if len(text) > max_length:
        print(f"⚠️ Truncating text to {max_length} characters")
        text = text[:max_length - 3] + "..."

    print(f"🎧 Generating {filename}...")
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

# ---- Texts ----

shift_1 = "Shift button. Press Shift twice for instructions."

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

shift_3 = (
    "Word list mapping. "
    "A – Apple, Amer, Alari, Arabic, Amory. "
    "B – Ball, Bye, Bathroom, Bed. "
    "C – Cat, Chair, Car. "
    "D – Dog, Deen, Daddy, Doctor. "
    "E – Elephant. "
    "F – Fish, FaceTime. "
    "G – Go, Good morning. "
    "H – House, Hello, How are you. "
    "I – Ice, Inside. "
    "J – Jump. "
    "K – Key, Kiyah, Kyan, Kleenex. "
    "L – Love, Lee, I love you, Light. "
    "M – Moon, Medicine, Mohammad. "
    "N – Net, Nadowie, Noah. "
    "O – Orange, Outside. "
    "P – Purple, Phone, Pain. "
    "Q – Queen. "
    "R – Red, Room. "
    "S – Sun, Susu, Scarf. "
    "T – Tree, TV. "
    "U – Up, Urgent Care. "
    "V – Van. "
    "W – Water, Walker, Wheelchair, Walk. "
    "X – X-ray. "
    "Y – Yellow. "
    "Z – Zebra. "
    "Press the same letter multiple times to cycle through words."
)

# ---- Generate MP3s ----

print("🎙️ SHIFT BUTTON HELP GENERATOR")
print("=" * 50)

generate_tts(shift_1, "001.mp3", max_length=2000)
generate_tts(shift_2, "002.mp3", max_length=8000)
generate_tts(shift_3, "003.mp3", max_length=8000)

print("\n📂 All audio files saved to /output/33/")
print("🎯 Copy them to the SD card folder /33/")
print("\n🎮 SHIFT Button Function:")
print("• Press 1x → Basic shift prompt")
print("• Press 2x → Device instructions (~2 min)")
print("• Press 3x → Complete word list (~3 min)")
