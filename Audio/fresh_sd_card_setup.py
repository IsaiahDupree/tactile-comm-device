#!/usr/bin/env python3
"""
Fresh SD Card Setup - Priority System Reversed

NEW PRIORITY SYSTEM:
- 1st Press: Generated TTS (clear, consistent)
- 2nd Press: Personal Recorded Words (familiar voices)
- 3rd+ Press: Additional TTS words

This creates a fresh, clean SD card setup with the improved priority system.
"""

import os
import shutil
import requests
import json
from pathlib import Path

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is required")
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # RILOU voice for clear speech
API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

def create_fresh_sd_structure():
    """Create fresh SD card folder structure"""
    sd_path = "E:\\"
    
    if not os.path.exists(sd_path):
        print(f"Error: SD card not found at {sd_path}")
        return False
    
    print("🗂️ Creating fresh SD card structure...")
    
    # Clear existing audio folders (keep backups and configs)
    for folder_num in range(1, 34):
        folder_path = os.path.join(sd_path, f"{folder_num:02d}")
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
    
    print("✅ Fresh folder structure created")
    return True

def generate_tts_audio(text, output_path, voice_id=VOICE_ID):
    """Generate TTS audio using ElevenLabs API"""
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
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    try:
        response = requests.post(
            API_URL.format(voice_id=voice_id),
            json=data,
            headers=headers,
            stream=True
        )
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            print(f"Error generating TTS: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# NEW BUTTON MAPPING SYSTEM
# Priority 1: Generated TTS (1st press)
# Priority 2: Recorded Words (2nd press) 
# Priority 3+: Additional TTS (3rd+ press)

BUTTON_MAPPINGS = {
    # Special Buttons (Folder 01-04)
    "SPECIAL": {
        1: [  # Folder 01
            ("Yes", "yes"),
            ("No", "no"), 
            ("Water", "water"),
            ("Help", "help")
        ],
        4: [  # Folder 04 - SHIFT button with help system
            ("Shift", "shift"),
            ("Device Help", "This is your tactile communication device. Press any button once for the main word, twice for personal recordings, or three times for additional options. Press SHIFT twice for help.")
        ]
    },
    
    # Letters A-Z (Folders 05-30)
    "LETTERS": {
        "A": {
            "folder": 5,
            "tracks": [
                ("Apple", "apple"),                    # 1st press: TTS
                ("Amer", "recorded"),                  # 2nd press: Recorded
                ("Alari", "recorded"),                 # 3rd press: Recorded  
                ("Arabic", "arabic"),                  # 4th press: TTS
                ("Amory", "recorded")                  # 5th press: Recorded
            ]
        },
        "B": {
            "folder": 6,
            "tracks": [
                ("Ball", "ball"),                      # 1st press: TTS
                ("Bye", "recorded"),                   # 2nd press: Recorded
                ("Bathroom", "bathroom"),              # 3rd press: TTS
                ("Bed", "bed")                         # 4th press: TTS
            ]
        },
        "C": {
            "folder": 7,
            "tracks": [
                ("Cat", "cat"),                        # 1st press: TTS
                ("Chair", "chair"),                    # 2nd press: TTS
                ("Car", "car")                         # 3rd press: TTS
            ]
        },
        "D": {
            "folder": 8,
            "tracks": [
                ("Dog", "dog"),                        # 1st press: TTS
                ("Deen", "recorded"),                  # 2nd press: Recorded
                ("Daddy", "recorded"),                 # 3rd press: Recorded
                ("Doctor", "doctor")                   # 4th press: TTS
            ]
        },
        "E": {
            "folder": 9,
            "tracks": [
                ("Elephant", "elephant")               # 1st press: TTS
            ]
        },
        "F": {
            "folder": 10,
            "tracks": [
                ("Fish", "fish"),                      # 1st press: TTS
                ("FaceTime", "facetime")               # 2nd press: TTS
            ]
        },
        "G": {
            "folder": 11,
            "tracks": [
                ("Go", "go"),                          # 1st press: TTS
                ("Good Morning", "recorded")           # 2nd press: Recorded
            ]
        },
        "H": {
            "folder": 12,
            "tracks": [
                ("House", "house"),                    # 1st press: TTS
                ("Hello", "hello"),                    # 2nd press: TTS
                ("How are you", "how are you")         # 3rd press: TTS
            ]
        },
        "I": {
            "folder": 13,
            "tracks": [
                ("Ice", "ice"),                        # 1st press: TTS
                ("Inside", "inside")                   # 2nd press: TTS
            ]
        },
        "J": {
            "folder": 14,
            "tracks": [
                ("Jump", "jump")                       # 1st press: TTS
            ]
        },
        "K": {
            "folder": 15,
            "tracks": [
                ("Key", "key"),                        # 1st press: TTS
                ("Kiyah", "recorded"),                 # 2nd press: Recorded
                ("Kyan", "recorded"),                  # 3rd press: Recorded
                ("Kleenex", "kleenex")                 # 4th press: TTS
            ]
        },
        "L": {
            "folder": 16,
            "tracks": [
                ("Love", "love"),                      # 1st press: TTS
                ("Lee", "recorded"),                   # 2nd press: Recorded
                ("I love you", "recorded"),            # 3rd press: Recorded
                ("Light", "light")                     # 4th press: TTS
            ]
        },
        "M": {
            "folder": 17,
            "tracks": [
                ("Moon", "moon"),                      # 1st press: TTS
                ("Medicine", "medicine"),              # 2nd press: TTS
                ("Mohammad", "mohammad")               # 3rd press: TTS
            ]
        },
        "N": {
            "folder": 18,
            "tracks": [
                ("Net", "net"),                        # 1st press: TTS
                ("Nadowie", "recorded"),               # 2nd press: Recorded
                ("Noah", "recorded")                   # 3rd press: Recorded
            ]
        },
        "O": {
            "folder": 19,
            "tracks": [
                ("Orange", "orange"),                  # 1st press: TTS
                ("Outside", "outside")                 # 2nd press: TTS
            ]
        },
        "P": {
            "folder": 20,
            "tracks": [
                ("Purple", "purple"),                  # 1st press: TTS
                ("Phone", "phone"),                    # 2nd press: TTS
                ("Pain", "pain")                       # 3rd press: TTS
            ]
        },
        "Q": {
            "folder": 21,
            "tracks": [
                ("Queen", "queen")                     # 1st press: TTS
            ]
        },
        "R": {
            "folder": 22,
            "tracks": [
                ("Red", "red"),                        # 1st press: TTS
                ("Room", "room")                       # 2nd press: TTS
            ]
        },
        "S": {
            "folder": 23,
            "tracks": [
                ("Sun", "sun"),                        # 1st press: TTS
                ("Susu", "recorded"),                  # 2nd press: Recorded
                ("Scarf", "scarf")                     # 3rd press: TTS
            ]
        },
        "T": {
            "folder": 24,
            "tracks": [
                ("Tree", "tree"),                      # 1st press: TTS
                ("TV", "tv")                           # 2nd press: TTS
            ]
        },
        "U": {
            "folder": 25,
            "tracks": [
                ("Up", "up"),                          # 1st press: TTS
                ("Urgent Care", "recorded")            # 2nd press: Recorded
            ]
        },
        "V": {
            "folder": 26,
            "tracks": [
                ("Van", "van")                         # 1st press: TTS
            ]
        },
        "W": {
            "folder": 27,
            "tracks": [
                ("Water", "water"),                    # 1st press: TTS
                ("Walker", "recorded"),                # 2nd press: Recorded
                ("Wheelchair", "recorded"),            # 3rd press: Recorded
                ("Walk", "walk")                       # 4th press: TTS
            ]
        },
        "X": {
            "folder": 28,
            "tracks": [
                ("X-ray", "x ray")                     # 1st press: TTS
            ]
        },
        "Y": {
            "folder": 29,
            "tracks": [
                ("Yellow", "yellow")                   # 1st press: TTS
            ]
        },
        "Z": {
            "folder": 30,
            "tracks": [
                ("Zebra", "zebra")                     # 1st press: TTS
            ]
        }
    },
    
    # Special characters
    "SYMBOLS": {
        31: [("Space", "space")],                      # SPACE
        32: [("Period", "period")],                    # PERIOD
        33: [("Shift", "shift"), ("Device Help", "This is your tactile communication device. Press any button once for the main word, twice for personal recordings, or three times for additional options. Press SHIFT twice for help.")]  # SHIFT with help
    }
}

def copy_recorded_words():
    """Copy recorded words to appropriate track positions (2nd press priority)"""
    recorded_path = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\RecordedWords"
    sd_path = "E:\\"
    
    if not os.path.exists(recorded_path):
        print(f"⚠️ RecordedWords folder not found: {recorded_path}")
        return
    
    print("🎙️ Copying recorded words to 2nd press positions...")
    
    # Define where each recorded file goes (2nd press = track 002.mp3)
    recorded_mappings = {
        "amer.mp3": ("05", "002"),      # A - 2nd press
        "alari.mp3": ("05", "003"),     # A - 3rd press  
        "amory.mp3": ("05", "005"),     # A - 5th press
        "bye.mp3": ("06", "002"),       # B - 2nd press
        "deen.mp3": ("08", "002"),      # D - 2nd press
        "daddy.mp3": ("08", "003"),     # D - 3rd press
        "good_morning.mp3": ("11", "002"), # G - 2nd press
        "kiyah.mp3": ("15", "002"),     # K - 2nd press
        "kyan.mp3": ("15", "003"),      # K - 3rd press
        "lee.mp3": ("16", "002"),       # L - 2nd press
        "i_love_you.mp3": ("16", "003"), # L - 3rd press
        "nadowie.mp3": ("18", "002"),   # N - 2nd press
        "noah.mp3": ("18", "003"),      # N - 3rd press
        "susu.mp3": ("23", "002"),      # S - 2nd press
        "urgent_care.mp3": ("25", "002"), # U - 2nd press
        "walker.mp3": ("27", "002"),    # W - 2nd press
        "wheelchair.mp3": ("27", "003")  # W - 3rd press
    }
    
    for filename, (folder, track) in recorded_mappings.items():
        src_path = os.path.join(recorded_path, filename)
        dst_path = os.path.join(sd_path, folder, f"{track}.mp3")
        
        if os.path.exists(src_path):
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"  📄 Copied: {filename} → Folder {folder}/Track {track}")
        else:
            print(f"  ⚠️ Missing: {filename}")

def generate_all_audio():
    """Generate all TTS audio files"""
    sd_path = "E:\\"
    generated_count = 0
    
    print("🗣️ Generating TTS audio files...")
    
    # Generate special buttons
    for folder, tracks in BUTTON_MAPPINGS["SPECIAL"].items():
        for i, (display_name, tts_text) in enumerate(tracks):
            if tts_text != "recorded":
                track_num = f"{i+1:03d}"
                output_path = os.path.join(sd_path, f"{folder:02d}", f"{track_num}.mp3")
                
                if generate_tts_audio(tts_text, output_path):
                    print(f"  ✅ Generated: {display_name} → {folder:02d}/{track_num}.mp3")
                    generated_count += 1
                else:
                    print(f"  ❌ Failed: {display_name}")
    
    # Generate letter audio
    for letter, data in BUTTON_MAPPINGS["LETTERS"].items():
        folder = data["folder"]
        for i, (display_name, tts_text) in enumerate(data["tracks"]):
            if tts_text != "recorded":
                track_num = f"{i+1:03d}"
                output_path = os.path.join(sd_path, f"{folder:02d}", f"{track_num}.mp3")
                
                if generate_tts_audio(tts_text, output_path):
                    print(f"  ✅ Generated: {letter} - {display_name} → {folder:02d}/{track_num}.mp3")
                    generated_count += 1
                else:
                    print(f"  ❌ Failed: {letter} - {display_name}")
    
    # Generate symbols
    for folder, tracks in BUTTON_MAPPINGS["SYMBOLS"].items():
        for i, (display_name, tts_text) in enumerate(tracks):
            track_num = f"{i+1:03d}"
            output_path = os.path.join(sd_path, f"{folder:02d}", f"{track_num}.mp3")
            
            if generate_tts_audio(tts_text, output_path):
                print(f"  ✅ Generated: {display_name} → {folder:02d}/{track_num}.mp3")
                generated_count += 1
            else:
                print(f"  ❌ Failed: {display_name}")
    
    print(f"🎵 Generated {generated_count} TTS audio files")

def create_documentation():
    """Create comprehensive documentation"""
    sd_path = "E:\\"
    
    # Create button mapping documentation
    doc_content = """# Fresh SD Card - Button Mapping Documentation

## NEW PRIORITY SYSTEM ✨

### 1st Press: Generated TTS (Clear & Consistent)
- Primary communication
- Always available
- Professional quality

### 2nd Press: Personal Recorded Words (Familiar Voices)  
- Your personal recordings
- Natural family pronunciations
- Emotional connection

### 3rd+ Press: Additional Words
- Extended vocabulary
- Context-specific terms

## SPECIAL BUTTONS

### SHIFT Button (Double Press = Help)
- **Single Press**: "Shift"
- **Double Press**: Device introduction and help

## LETTER MAPPINGS

"""
    
    for letter, data in BUTTON_MAPPINGS["LETTERS"].items():
        doc_content += f"### {letter} Button (Folder {data['folder']:02d})\n"
        for i, (display_name, tts_text) in enumerate(data["tracks"]):
            press_num = i + 1
            status = "🎙️ RECORDED" if tts_text == "recorded" else "🗣️ TTS"
            doc_content += f"- **Press {press_num}**: {display_name} {status}\n"
        doc_content += "\n"
    
    # Write documentation
    with open(os.path.join(sd_path, "FRESH_BUTTON_MAPPINGS.txt"), "w") as f:
        f.write(doc_content)
    
    print("📄 Created button mapping documentation")

def main():
    print("=== FRESH SD CARD SETUP ===")
    print("NEW Priority System:")
    print("1st Press: Generated TTS")
    print("2nd Press: Recorded Words") 
    print("3rd+ Press: Additional TTS")
    print()
    
    if not create_fresh_sd_structure():
        return
    
    # Copy recorded words to 2nd press positions
    copy_recorded_words()
    
    # Generate all TTS audio
    print()
    response = input("Generate all TTS audio files? (y/N): ")
    if response.lower() == 'y':
        generate_all_audio()
    
    # Create documentation
    create_documentation()
    
    print()
    print("=== FRESH SD CARD SETUP COMPLETE ===")
    print("✅ Priority system: TTS first, Recorded second")
    print("✅ Clear button mappings documented")
    print("✅ SHIFT double-press help system ready")
    print("📁 SD Card: E:\\")
    print("🎙️ Voice: RILOU (ElevenLabs)")

if __name__ == "__main__":
    main()
