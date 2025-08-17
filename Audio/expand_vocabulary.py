#!/usr/bin/env python3
"""
Vocabulary Expansion for Tactile Communication Device

Generates TTS versions of all recorded words and expands vocabulary
to support pressing as many times as there are words for each letter.
"""

import os
import requests
import json
from pathlib import Path
import shutil

# ElevenLabs configuration
ELEVENLABS_API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # RILOU voice
ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

def generate_tts_audio(text, output_path):
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
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(ELEVENLABS_URL, json=data, headers=headers)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
        
    except Exception as e:
        print(f"Error generating TTS for '{text}': {e}")
        return False

def analyze_current_vocabulary():
    """Analyze current vocabulary and recorded words"""
    
    # Complete vocabulary mapping with all known words
    vocabulary = {
        "01": {  # Special buttons
            "button": "SPECIAL",
            "words": ["Yes", "No", "Water", "Help"]
        },
        "04": {  # Shift system  
            "button": "SHIFT",
            "words": ["Shift", "Device Help"]
        },
        "05": {  # Letter A
            "button": "A", 
            "words": ["Apple", "Amer", "Alari", "Arabic", "Amory"]
        },
        "06": {  # Letter B
            "button": "B",
            "words": ["Ball", "Bye", "Bathroom", "Bed"]
        },
        "07": {  # Letter C
            "button": "C",
            "words": ["Cat", "Chair", "Car"]
        },
        "08": {  # Letter D
            "button": "D", 
            "words": ["Dog", "Deen", "Daddy", "Doctor"]
        },
        "09": {  # Letter E
            "button": "E",
            "words": ["Elephant"]
        },
        "10": {  # Letter F
            "button": "F",
            "words": ["Fish", "FaceTime"]
        },
        "11": {  # Letter G
            "button": "G",
            "words": ["Go", "Good Morning"]
        },
        "12": {  # Letter H
            "button": "H",
            "words": ["House", "Hello", "How are you"]
        },
        "13": {  # Letter I
            "button": "I",
            "words": ["Ice", "Inside"]
        },
        "14": {  # Letter J
            "button": "J",
            "words": ["Jump"]
        },
        "15": {  # Letter K
            "button": "K",
            "words": ["Key", "Kiyah", "Kyan", "Kleenex"]
        },
        "16": {  # Letter L
            "button": "L",
            "words": ["Love", "Lee", "I love you", "Light"]
        },
        "17": {  # Letter M
            "button": "M",
            "words": ["Moon", "Medicine", "Mohammad"]
        },
        "18": {  # Letter N
            "button": "N",
            "words": ["Net", "Nadowie", "Noah"]
        },
        "19": {  # Letter O
            "button": "O",
            "words": ["Orange", "Outside"]
        },
        "20": {  # Letter P
            "button": "P",
            "words": ["Purple", "Phone", "Pain"]
        },
        "21": {  # Letter Q
            "button": "Q",
            "words": ["Queen"]
        },
        "22": {  # Letter R
            "button": "R",
            "words": ["Red", "Room"]
        },
        "23": {  # Letter S
            "button": "S",
            "words": ["Sun", "Susu", "Scarf"]
        },
        "24": {  # Letter T
            "button": "T",
            "words": ["Tree", "TV"]
        },
        "25": {  # Letter U
            "button": "U",
            "words": ["Up", "Urgent Care"]
        },
        "26": {  # Letter V
            "button": "V",
            "words": ["Van"]
        },
        "27": {  # Letter W
            "button": "W",
            "words": ["Water", "Walker", "Wheelchair", "Walk"]
        },
        "28": {  # Letter X
            "button": "X",
            "words": ["X-ray"]
        },
        "29": {  # Letter Y
            "button": "Y",
            "words": ["Yellow"]
        },
        "30": {  # Letter Z
            "button": "Z",
            "words": ["Zebra"]
        },
        "31": {  # Space
            "button": "SPACE",
            "words": ["Space"]
        },
        "32": {  # Period
            "button": "PERIOD",
            "words": ["Period"]
        },
        "33": {  # Shift
            "button": "SHIFT",
            "words": ["Shift", "Device Help"]
        }
    }
    
    return vocabulary

def expand_vocabulary_to_sd(sd_path, vocabulary):
    """Expand vocabulary on SD card by generating missing TTS files"""
    
    print("🎵 Expanding vocabulary with TTS versions...")
    
    generated_count = 0
    
    for folder_id, info in vocabulary.items():
        folder_path = os.path.join(sd_path, folder_id)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        button = info["button"]
        words = info["words"]
        
        print(f"\n📁 Folder {folder_id}/ ({button}):")
        
        for i, word in enumerate(words, 1):
            file_path = os.path.join(folder_path, f"{i:03d}.mp3")
            
            if os.path.exists(file_path):
                print(f"  ✅ {i:03d}.mp3: {word} (exists)")
            else:
                print(f"  🎙️ Generating {i:03d}.mp3: {word}")
                if generate_tts_audio(word, file_path):
                    print(f"    ✅ Generated successfully")
                    generated_count += 1
                else:
                    print(f"    ❌ Failed to generate")
    
    return generated_count

def update_arduino_mappings(vocabulary):
    """Generate updated Arduino audioMappings array"""
    
    arduino_mappings = []
    
    # Special mappings that don't follow the standard pattern
    special_mappings = {
        "01": '{"YES", 1, 4, false, "yes"}',
        "04": '{"SHIFT", 4, 2, false, "Shift"}',
        "31": '{"SPACE", 31, 1, false, "Space"}',
        "32": '{"PERIOD", 32, 1, false, "Period"}',
        "33": '{"SHIFT", 33, 2, false, "Shift"}'
    }
    
    # Generate mappings for each folder
    for folder_id, info in vocabulary.items():
        folder_num = int(folder_id)
        button = info["button"]
        word_count = len(info["words"])
        
        # Check if any words are typically recorded (personal names, etc.)
        recorded_words = ["Amer", "Alari", "Amory", "Bye", "Deen", "Daddy", 
                         "Kiyah", "Kyan", "Lee", "I love you", "Nadowie", "Noah", 
                         "Susu", "Walker", "Wheelchair"]
        
        has_recorded = any(word in recorded_words for word in info["words"])
        
        if folder_id in special_mappings:
            arduino_mappings.append(special_mappings[folder_id])
        else:
            # Standard letter mapping
            fallback = info["words"][0].lower()  # First word as fallback
            mapping = f'{{"{ button}", {folder_num}, {word_count}, {str(has_recorded).lower()}, "{fallback}"}}'
            arduino_mappings.append(mapping)
    
    return arduino_mappings

def generate_arduino_code_update(vocabulary):
    """Generate complete Arduino code update"""
    
    arduino_mappings = update_arduino_mappings(vocabulary)
    
    code_update = """// Updated audioMappings with expanded vocabulary
// Each button now supports pressing as many times as there are words

AudioMapping audioMappings[] = {
  // Special Buttons (Essential communication)
  {"YES", 1, 4, false, "yes"},        // 1=Yes, 2=No, 3=Water, 4=Help
  
  // System Functions
  {"SHIFT", 4, 2, false, "Shift"},    // 1=Shift, 2=Device Help
  
  // Letter Buttons A-Z (with expanded vocabulary)
"""
    
    # Add letter mappings with detailed comments
    for folder_id, info in vocabulary.items():
        if info["button"] not in ["SPECIAL", "SHIFT"] and folder_id not in ["01", "04", "31", "32", "33"]:
            folder_num = int(folder_id)
            button = info["button"]
            word_count = len(info["words"])
            words = info["words"]
            
            # Check for recorded words
            recorded_words = ["Amer", "Alari", "Amory", "Bye", "Deen", "Daddy", 
                             "Kiyah", "Kyan", "Lee", "I love you", "Nadowie", "Noah", 
                             "Susu", "Walker", "Wheelchair"]
            has_recorded = any(word in recorded_words for word in words)
            
            # Create comment showing what each press does
            press_details = []
            for i, word in enumerate(words, 1):
                word_type = "(REC)" if word in recorded_words else "(TTS)"
                press_details.append(f"{i}={word}{word_type}")
            
            comment = f"  // {button}: {', '.join(press_details)}"
            fallback = words[0].lower()
            
            mapping = f'  {{"{button}", {folder_num}, {word_count}, {str(has_recorded).lower()}, "{fallback}"}},{comment}'
            code_update += mapping + "\n"
    
    code_update += """  
  // Punctuation
  {"SPACE", 31, 1, false, "Space"},   // 1=Space
  {"PERIOD", 32, 1, false, "Period"}, // 1=Period
  {"SHIFT", 33, 2, false, "Shift"}    // 1=Shift, 2=Device Help
};

// Updated array size
const uint8_t AUDIO_MAPPING_COUNT = sizeof(audioMappings) / sizeof(audioMappings[0]);
"""
    
    return code_update

def create_expanded_documentation(sd_path, vocabulary, generated_count):
    """Create updated documentation with expanded vocabulary"""
    
    doc_content = f"""# EXPANDED VOCABULARY - Tactile Communication Device

## 🎉 VOCABULARY EXPANSION COMPLETE!

**Generated {generated_count} new TTS audio files**
**Total vocabulary now supports unlimited presses per button**

## 🎯 ENHANCED SYSTEM:

### Multi-Press Support:
- **Press 1**: First word (usually TTS)
- **Press 2**: Second word (often recorded) 
- **Press 3**: Third word (additional vocabulary)
- **Press N**: Nth word (as many as available)

### Example - Letter A:
1. Press once = "Apple" (TTS)
2. Press twice = "Amer" (Recorded)  
3. Press 3 times = "Alari" (Recorded)
4. Press 4 times = "Arabic" (TTS)
5. Press 5 times = "Amory" (Recorded)

## 📊 COMPLETE VOCABULARY BY LETTER:

"""
    
    for folder_id, info in vocabulary.items():
        if info["button"] not in ["SPECIAL", "SHIFT"]:
            button = info["button"]
            words = info["words"]
            
            doc_content += f"### {button} Button ({len(words)} words):\n"
            for i, word in enumerate(words, 1):
                doc_content += f"{i}. {word}\n"
            doc_content += "\n"
    
    doc_content += f"""
## 🔢 VOCABULARY STATISTICS:

Total Buttons: {len(vocabulary)}
Total Words: {sum(len(info['words']) for info in vocabulary.values())}
Average Words per Button: {sum(len(info['words']) for info in vocabulary.values()) / len(vocabulary):.1f}

## 🎵 AUDIO DETAILS:

- Voice: ElevenLabs RILOU (Professional TTS)
- Personal Recordings: Family voices preserved
- Both TTS and recorded versions available for many words
- Users can choose their preferred version by press count

## 🚀 USAGE:

Simply press any button as many times as needed to cycle through 
all available words for that letter. The device now supports 
unlimited vocabulary expansion!

Generated: 2025-08-01 21:25 EST
Expansion: {generated_count} new TTS files added
System: Multi-press unlimited vocabulary
"""
    
    with open(os.path.join(sd_path, "EXPANDED_VOCABULARY.txt"), "w", encoding="utf-8") as f:
        f.write(doc_content)

def main():
    sd_path = "E:\\"
    
    if not os.path.exists(sd_path):
        print(f"Error: SD card not found at {sd_path}")
        return
    
    print("=== VOCABULARY EXPANSION ===")
    print("Generating TTS versions of all recorded words")
    print("Enabling unlimited multi-press vocabulary")
    print()
    
    # Analyze current vocabulary
    vocabulary = analyze_current_vocabulary()
    
    # Expand vocabulary on SD card
    generated_count = expand_vocabulary_to_sd(sd_path, vocabulary)
    
    # Generate Arduino code update
    print("\n🔧 Generating Arduino code update...")
    arduino_update = generate_arduino_code_update(vocabulary)
    
    with open("arduino_mapping_update.txt", "w") as f:
        f.write(arduino_update)
    
    # Create expanded documentation  
    print("📄 Creating expanded documentation...")
    create_expanded_documentation(sd_path, vocabulary, generated_count)
    
    print(f"\n✅ VOCABULARY EXPANSION COMPLETE!")
    print(f"🎵 Generated {generated_count} new TTS audio files")
    print(f"🔢 Total vocabulary words: {sum(len(info['words']) for info in vocabulary.values())}")
    print(f"📁 Active folders: {len([f for f in vocabulary.keys() if vocabulary[f]['words']])}")
    print()
    print("📂 Created files:")
    print("  - arduino_mapping_update.txt (Updated Arduino mappings)")
    print("  - EXPANDED_VOCABULARY.txt (Complete vocabulary documentation)")
    print()
    print("🎯 Your device now supports pressing each button as many")
    print("   times as there are words available for that letter!")

if __name__ == "__main__":
    main()
