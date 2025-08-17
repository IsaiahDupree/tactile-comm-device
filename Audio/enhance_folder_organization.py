#!/usr/bin/env python3
"""
Enhanced Folder Organization for Tactile Communication Device

Creates better naming convention and documentation while maintaining 
Arduino compatibility with numbered folders.
"""

import os
import json
from pathlib import Path

def create_folder_index():
    """Create comprehensive folder index and documentation"""
    
    # Detailed mapping based on Arduino audioMappings
    folder_mapping = {
        "01": {
            "name": "SPECIAL_BUTTONS",
            "description": "Essential communication buttons",
            "button": "YES/NO/WATER/HELP",
            "tracks": {
                "001.mp3": "Yes (TTS)",
                "002.mp3": "No (TTS)", 
                "003.mp3": "Water (TTS)",
                "004.mp3": "Help (TTS)"
            }
        },
        "04": {
            "name": "SHIFT_SYSTEM",
            "description": "System control and help",
            "button": "SHIFT",
            "tracks": {
                "001.mp3": "Shift (TTS)",
                "002.mp3": "Device Help & Instructions (TTS)"
            }
        },
        "05": {
            "name": "LETTER_A",
            "description": "Letter A words",
            "button": "A",
            "tracks": {
                "001.mp3": "Apple (TTS)",
                "002.mp3": "Amer (Recorded)",
                "003.mp3": "Alari (Recorded)", 
                "004.mp3": "Arabic (TTS)",
                "005.mp3": "Amory (Recorded)"
            }
        },
        "06": {
            "name": "LETTER_B", 
            "description": "Letter B words",
            "button": "B",
            "tracks": {
                "001.mp3": "Ball (TTS)",
                "002.mp3": "Bye (Recorded)",
                "003.mp3": "Bathroom (TTS)",
                "004.mp3": "Bed (TTS)"
            }
        },
        "07": {
            "name": "LETTER_C",
            "description": "Letter C words", 
            "button": "C",
            "tracks": {
                "001.mp3": "Cat (TTS)",
                "002.mp3": "Chair (TTS)",
                "003.mp3": "Car (TTS)"
            }
        },
        "08": {
            "name": "LETTER_D",
            "description": "Letter D words",
            "button": "D", 
            "tracks": {
                "001.mp3": "Dog (TTS)",
                "002.mp3": "Deen (Recorded)",
                "003.mp3": "Daddy (Recorded)",
                "004.mp3": "Doctor (TTS)"
            }
        },
        "09": {
            "name": "LETTER_E",
            "description": "Letter E words",
            "button": "E",
            "tracks": {
                "001.mp3": "Elephant (TTS)"
            }
        },
        "10": {
            "name": "LETTER_F",
            "description": "Letter F words",
            "button": "F",
            "tracks": {
                "001.mp3": "Fish (TTS)",
                "002.mp3": "FaceTime (TTS)"
            }
        },
        "11": {
            "name": "LETTER_G",
            "description": "Letter G words",
            "button": "G",
            "tracks": {
                "001.mp3": "Go (TTS)"
            }
        },
        "12": {
            "name": "LETTER_H",
            "description": "Letter H words",
            "button": "H", 
            "tracks": {
                "001.mp3": "House (TTS)",
                "002.mp3": "Hello (TTS)",
                "003.mp3": "How are you (TTS)"
            }
        },
        "13": {
            "name": "LETTER_I",
            "description": "Letter I words",
            "button": "I",
            "tracks": {
                "001.mp3": "Ice (TTS)",
                "002.mp3": "Inside (TTS)"
            }
        },
        "14": {
            "name": "LETTER_J",
            "description": "Letter J words",
            "button": "J",
            "tracks": {
                "001.mp3": "Jump (TTS)"
            }
        },
        "15": {
            "name": "LETTER_K",
            "description": "Letter K words",
            "button": "K",
            "tracks": {
                "001.mp3": "Key (TTS)",
                "002.mp3": "Kiyah (Recorded)",
                "003.mp3": "Kyan (Recorded)",
                "004.mp3": "Kleenex (TTS)"
            }
        },
        "16": {
            "name": "LETTER_L",
            "description": "Letter L words",
            "button": "L",
            "tracks": {
                "001.mp3": "Love (TTS)",
                "002.mp3": "Lee (Recorded)",
                "003.mp3": "I love you (Recorded)",
                "004.mp3": "Light (TTS)"
            }
        },
        "17": {
            "name": "LETTER_M",
            "description": "Letter M words", 
            "button": "M",
            "tracks": {
                "001.mp3": "Moon (TTS)",
                "002.mp3": "Medicine (TTS)",
                "003.mp3": "Mohammad (TTS)"
            }
        },
        "18": {
            "name": "LETTER_N",
            "description": "Letter N words",
            "button": "N",
            "tracks": {
                "001.mp3": "Net (TTS)",
                "002.mp3": "Nadowie (Recorded)",
                "003.mp3": "Noah (Recorded)"
            }
        },
        "19": {
            "name": "LETTER_O",
            "description": "Letter O words",
            "button": "O",
            "tracks": {
                "001.mp3": "Orange (TTS)",
                "002.mp3": "Outside (TTS)"
            }
        },
        "20": {
            "name": "LETTER_P",
            "description": "Letter P words",
            "button": "P",
            "tracks": {
                "001.mp3": "Purple (TTS)",
                "002.mp3": "Phone (TTS)",
                "003.mp3": "Pain (TTS)"
            }
        },
        "21": {
            "name": "LETTER_Q",
            "description": "Letter Q words",
            "button": "Q",
            "tracks": {
                "001.mp3": "Queen (TTS)"
            }
        },
        "22": {
            "name": "LETTER_R",
            "description": "Letter R words",
            "button": "R",
            "tracks": {
                "001.mp3": "Red (TTS)",
                "002.mp3": "Room (TTS)"
            }
        },
        "23": {
            "name": "LETTER_S",
            "description": "Letter S words",
            "button": "S",
            "tracks": {
                "001.mp3": "Sun (TTS)",
                "002.mp3": "Susu (Recorded)",
                "003.mp3": "Scarf (TTS)"
            }
        },
        "24": {
            "name": "LETTER_T",
            "description": "Letter T words",
            "button": "T",
            "tracks": {
                "001.mp3": "Tree (TTS)",
                "002.mp3": "TV (TTS)"
            }
        },
        "25": {
            "name": "LETTER_U",
            "description": "Letter U words",
            "button": "U",
            "tracks": {
                "001.mp3": "Up (TTS)"
            }
        },
        "26": {
            "name": "LETTER_V",
            "description": "Letter V words",
            "button": "V",
            "tracks": {
                "001.mp3": "Van (TTS)"
            }
        },
        "27": {
            "name": "LETTER_W",
            "description": "Letter W words",
            "button": "W",
            "tracks": {
                "001.mp3": "Water (TTS)",
                "002.mp3": "Walker (Recorded)",
                "003.mp3": "Wheelchair (Recorded)",
                "004.mp3": "Walk (TTS)"
            }
        },
        "28": {
            "name": "LETTER_X",
            "description": "Letter X words",
            "button": "X",
            "tracks": {
                "001.mp3": "X-ray (TTS)"
            }
        },
        "29": {
            "name": "LETTER_Y",
            "description": "Letter Y words",
            "button": "Y",
            "tracks": {
                "001.mp3": "Yellow (TTS)"
            }
        },
        "30": {
            "name": "LETTER_Z",
            "description": "Letter Z words",
            "button": "Z",
            "tracks": {
                "001.mp3": "Zebra (TTS)"
            }
        },
        "31": {
            "name": "SPACE",
            "description": "Space character",
            "button": "SPACE",
            "tracks": {
                "001.mp3": "Space (TTS)"
            }
        },
        "32": {
            "name": "PERIOD",
            "description": "Period punctuation",
            "button": "PERIOD",
            "tracks": {
                "001.mp3": "Period (TTS)"
            }
        },
        "33": {
            "name": "SHIFT",
            "description": "Shift functionality",
            "button": "SHIFT",
            "tracks": {
                "001.mp3": "Shift (TTS)",
                "002.mp3": "Device Help & Instructions (TTS)"
            }
        }
    }
    
    return folder_mapping

def create_documentation_files(sd_path, folder_mapping):
    """Create comprehensive documentation files"""
    
    # Create main index file
    index_content = """# TACTILE COMMUNICATION DEVICE - SD CARD INDEX

## 🎯 PRIORITY SYSTEM
1st Press: Generated TTS (Clear, consistent)  
2nd Press: Personal Recorded Words (Familiar voices)  
3rd+ Press: Additional vocabulary  

## 📁 FOLDER STRUCTURE

| Folder | Name | Button | Description | Tracks |
|--------|------|--------|-------------|--------|
"""
    
    for folder_id, info in folder_mapping.items():
        track_count = len(info["tracks"])
        index_content += f"| {folder_id}/ | {info['name']} | {info['button']} | {info['description']} | {track_count} |\n"
    
    index_content += """
## 🎵 AUDIO DETAILS

### Voice Information:
- TTS Voice: ElevenLabs RILOU (Professional, clear)
- Recorded: Personal family recordings
- Format: MP3, VS1053 compatible
- Quality: 22kHz, 128kbps

### File Naming Convention:
- 001.mp3 = 1st press (Primary TTS)
- 002.mp3 = 2nd press (Personal recording)  
- 003.mp3 = 3rd press (Additional word)
- etc.

## 🔧 SYSTEM FEATURES

### Multi-Press Detection:
- Single press = Primary word (TTS)
- Double press = Personal recording (if available)
- Triple press = Additional vocabulary
- Multi-press window: 1000ms (1 second)

### Special Functions:
- SHIFT double-press = Device help & instructions
- Audio interruption for long clips
- Console logging for debugging

## 📋 USAGE GUIDE

1. **Basic Communication**: Single press any button
2. **Personal Touch**: Double press for recorded words
3. **Extended Vocabulary**: Triple press for more options
4. **Get Help**: Double press SHIFT for instructions
5. **Audio Control**: Press any button to interrupt long audio

Generated: """ + "2025-08-01 21:20 EST" + """
Voice: RILOU (ElevenLabs)
Total Files: 71 MP3 files
Total Size: 1.2MB
"""
    
    with open(os.path.join(sd_path, "SD_CARD_INDEX.txt"), "w", encoding="utf-8") as f:
        f.write(index_content)
    
    # Create individual folder README files
    for folder_id, info in folder_mapping.items():
        folder_path = os.path.join(sd_path, folder_id)
        if os.path.exists(folder_path):
            readme_content = f"""# {info['name']} - {info['description']}

Button: {info['button']}
Folder: {folder_id}/

## Track List:
"""
            for track_file, description in info["tracks"].items():
                readme_content += f"- {track_file}: {description}\n"
            
            readme_content += f"""
## Usage:
- Press {info['button']} once for: {list(info['tracks'].values())[0]}
"""
            if len(info["tracks"]) > 1:
                readme_content += f"- Press {info['button']} twice for: {list(info['tracks'].values())[1]}\n"
            if len(info["tracks"]) > 2:
                readme_content += f"- Press {info['button']} three times for: {list(info['tracks'].values())[2]}\n"
            
            readme_path = os.path.join(folder_path, "README.txt")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)

def create_quick_reference_card(sd_path, folder_mapping):
    """Create a quick reference card for caregivers"""
    
    quick_ref = """# QUICK REFERENCE CARD - Tactile Communication Device

## 🚀 HOW TO USE
1. **Single Press** = Main word (TTS voice)
2. **Double Press** = Personal recording (family voice)  
3. **Triple Press** = Additional words
4. **SHIFT + SHIFT** = Help & instructions

## 🔤 LETTER BUTTONS (A-Z)
"""
    
    for folder_id, info in folder_mapping.items():
        if info["name"].startswith("LETTER_"):
            letter = info["button"]
            main_word = list(info["tracks"].values())[0].replace(" (TTS)", "").replace(" (Recorded)", "")
            quick_ref += f"**{letter}** = {main_word}"
            if len(info["tracks"]) > 1:
                second_word = list(info["tracks"].values())[1].replace(" (TTS)", "").replace(" (Recorded)", "")
                quick_ref += f" / {second_word}"
            quick_ref += "\n"
    
    quick_ref += """
## ⭐ SPECIAL BUTTONS
**YES** = Yes  
**NO** = No  
**WATER** = Water  
**HELP** = Help  
**SHIFT** = System control (double-press for help)  
**SPACE** = Space character  
**PERIOD** = Period punctuation  

## 💡 TIPS
- Wait 1 second between presses for multi-press detection
- Press any button to stop long audio clips
- Check console output for detailed button press logs
- Personal recordings play on second press when available

Device ready! Start communicating! 🎉
"""
    
    with open(os.path.join(sd_path, "QUICK_REFERENCE.txt"), "w", encoding="utf-8") as f:
        f.write(quick_ref)

def main():
    sd_path = "E:\\"
    
    if not os.path.exists(sd_path):
        print(f"Error: SD card not found at {sd_path}")
        return
    
    print("=== ENHANCING FOLDER ORGANIZATION ===")
    print(f"SD Card: {sd_path}")
    
    # Get folder mapping
    folder_mapping = create_folder_index()
    
    print("🏷️  Creating documentation files...")
    create_documentation_files(sd_path, folder_mapping)
    
    print("📋 Creating quick reference card...")
    create_quick_reference_card(sd_path, folder_mapping)
    
    print("📄 Creating JSON mapping for developers...")
    json_mapping = {
        "metadata": {
            "created": "2025-08-01T21:20:00-04:00",
            "voice": "RILOU (ElevenLabs)",
            "total_files": 71,
            "total_folders": 31,
            "priority_system": "TTS first, recorded second"
        },
        "folders": folder_mapping
    }
    
    with open(os.path.join(sd_path, "folder_mapping.json"), "w", encoding="utf-8") as f:
        json.dump(json_mapping, f, indent=2)
    
    print("✅ Enhanced folder organization complete!")
    print()
    print("📂 Created files:")
    print("  - SD_CARD_INDEX.txt (Comprehensive folder listing)")
    print("  - QUICK_REFERENCE.txt (Caregiver guide)")
    print("  - folder_mapping.json (Developer reference)")
    print("  - README.txt in each active folder")
    print()
    print("🎯 Folders now have clear naming and documentation")
    print("   while maintaining Arduino compatibility!")

if __name__ == "__main__":
    main()
