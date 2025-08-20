#!/usr/bin/env python3
import requests
import os
import json
import time
import argparse
from pathlib import Path

# Configuration
BASE_URL = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # Preferred user voice

def _load_api_key():
    # 1) Environment variable
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key
    # 2) .env in repo root (same directory as this script)
    try:
        from pathlib import Path
        env_path = Path(__file__).resolve().parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding='utf-8', errors='ignore').splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('ELEVENLABS_API_KEY='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return None

API_KEY = _load_api_key()

# Dictionary mapping for common words per letter
LETTER_WORDS = {
    "A": ["Apple", "Again", "Always", "Around", "About"],
    "B": ["Ball", "Boy", "Book", "Bath", "Blue"],
    "C": ["Cat", "Car", "Cookie", "Chair", "Come"],
    "D": ["Dog", "Door", "Down", "Doctor", "Day"],
    "E": ["Egg", "Eye", "Eat", "End", "Every"],
    "F": ["Fish", "Food", "Friend", "Face", "Father"],
    "G": ["Go", "Good", "Game", "Girl", "Give"],
    "H": ["Hat", "Help", "Home", "Happy", "Hand"],
    "I": ["Ice", "In", "If", "Important", "I"],
    "J": ["Jump", "Juice", "Job", "Join", "Jacket"],
    "K": ["Key", "Kitchen", "Kind", "Keep", "Know"],
    "L": ["Love", "Like", "Look", "Listen", "Light"],
    "M": ["Mom", "Milk", "More", "Make", "Music"],
    "N": ["No", "Name", "Now", "New", "Nice"],
    "O": ["Open", "Out", "Over", "On", "Off"],
    "P": ["Please", "Play", "Person", "Phone", "Put"],
    "Q": ["Question", "Quick", "Quiet", "Queen", "Quit"],
    "R": ["Run", "Red", "Room", "Right", "Read"],
    "S": ["Stop", "Say", "See", "School", "Sleep"],
    "T": ["Time", "Thank", "Today", "Take", "Talk"],
    "U": ["Up", "Under", "Use", "Us", "Understand"],
    "V": ["Very", "Visit", "Voice", "View", "Vacation"],
    "W": ["Water", "Want", "Work", "Walk", "Window"],
    "X": ["X-ray", "Xylophone", "Extra", "Exit", "Excited"],
    "Y": ["Yes", "You", "Your", "Yellow", "Year"],
    "Z": ["Zoo", "Zebra", "Zero", "Zip", "Zone"]
}

def list_voices():
    """List available voices from Eleven Labs."""
    url = f"{BASE_URL}/voices"
    headers = {"xi-api-key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        voices = response.json()
        
        print("Available Voices:")
        for voice in voices.get("voices", []):
            print(f"- {voice['name']}: {voice['voice_id']}")
        
        return voices.get("voices", [])
    except requests.exceptions.RequestException as e:
        print(f"Error listing voices: {e}")
        return []

def generate_audio(text, voice_id, output_file,
                   model_id: str = "eleven_monolingual_v1",
                   stability: float = 0.5,
                   similarity_boost: float = 0.85,
                   style: float | None = None,
                   use_speaker_boost: bool | None = True):
    """Generate audio from text using ElevenLabs API with tunable settings.

    Defaults are tuned for clarity/intelligibility on embedded playback:
    - stability=0.5, similarity_boost=0.85, speaker_boost=True
    - model_id defaults to 'eleven_monolingual_v1'
    """
    url = f"{BASE_URL}/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    voice_settings = {
        "stability": stability,
        "similarity_boost": similarity_boost,
    }
    if style is not None:
        voice_settings["style"] = style
    if use_speaker_boost is not None:
        voice_settings["use_speaker_boost"] = use_speaker_boost

    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings,
    }
    
    response = None
    try:
        print(f"Generating audio for: '{text}'")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        # Save audio content to file
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        print(f"Audio saved to {output_file}")
        return True
    except requests.exceptions.RequestException as e:
        status = getattr(response, 'status_code', None)
        print(f"Error generating audio (status={status}): {e}")
        if status == 401:
            print("[HINT] Check ELEVENLABS_API_KEY in environment or .env")
        if status == 429:
            print("Rate limit exceeded. Waiting before retry...")
            time.sleep(10)
        return False

def generate_letter_audio(letter, voice_id, base_path, count=5):
    """Generate audio files for a specific letter."""
    letter = letter.upper()
    if letter not in LETTER_WORDS:
        print(f"No words defined for letter {letter}")
        return
    
    # Ensure the directory exists
    letter_dir = os.path.join(base_path, letter)
    os.makedirs(letter_dir, exist_ok=True)
    
    # Generate audio for each word
    words = LETTER_WORDS[letter][:count]  # Limit to the requested count
    for i, word in enumerate(words, start=1):
        output_file = os.path.join(letter_dir, f"{i:03d}.mp3")
        if os.path.exists(output_file):
            print(f"File already exists: {output_file}. Skipping.")
            continue
        
        success = generate_audio(word, voice_id, output_file)
        if not success:
            print(f"Failed to generate audio for {word}")
        
        # Sleep to avoid rate limiting
        time.sleep(1.5)

def main():
    parser = argparse.ArgumentParser(description="Generate audio files using ElevenLabs API")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID, help="Voice ID to use")
    parser.add_argument("--model", default="eleven_monolingual_v1", help="Model ID (e.g. eleven_monolingual_v1)")
    parser.add_argument("--stability", type=float, default=0.5, help="Voice stability (0.0-1.0)")
    parser.add_argument("--similarity", type=float, default=0.85, help="Voice similarity boost (0.0-1.0)")
    parser.add_argument("--style", type=float, default=None, help="Optional style (0.0-1.0)")
    parser.add_argument("--speaker-boost", type=int, choices=[0,1], default=1, help="Use speaker boost (1) or not (0)")
    parser.add_argument("--letter", help="Generate audio for specific letter(s) (comma-separated)")
    parser.add_argument("--all", action="store_true", help="Generate audio for all letters")
    parser.add_argument("--base-path", default="c:/Users/Cypress/Documents/Coding/Buttons/tactile-comm-device/sd/SD_FUTURE_PROOF/audio/generated", help="Base path for audio files")
    parser.add_argument("--count", type=int, default=3, help="Number of words per letter")
    
    args = parser.parse_args()
    
    if args.list_voices:
        list_voices()
        return
    
    if args.all:
        for letter in LETTER_WORDS.keys():
            generate_letter_audio(letter, args.voice, args.base_path, args.count)
    elif args.letter:
        letters = [l.strip() for l in args.letter.split(",")]
        for letter in letters:
            generate_letter_audio(letter, args.voice, args.base_path, args.count)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
