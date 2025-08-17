#!/usr/bin/env python3
"""
Fix Button Mappings for Tactile Communication Device
Maps the actual button indices to the correct letters and audio folders
"""

import re
from pathlib import Path

# Configuration
ARDUINO_FILE_PATH = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\tactile_communicator_vs1053\tactile_communicator_vs1053.ino"

# Actual button index to letter mapping from device
BUTTON_INDEX_TO_LETTER = {
    2: "K",
    3: "A", 
    5: "P",
    6: "C",
    7: "R",
    8: "I",
    9: "J",
    10: "Q",
    11: "W",
    13: "V",
    14: "X",
    15: ".",  # Period
    16: "N",
    17: "G",
    18: "F",
    21: "U",
    22: "T",
    23: "M",
    24: "E",
    27: "_",  # Space
    28: "Z",
    29: "S",
    30: "D",
    31: "Y",
    32: "B",
    33: "H",
    35: "O"
}

# Word mappings for each letter
WORD_MAPPINGS = {
    "A": ["Alari", "Amer", "Amory", "Apple", "Arabic", "Arabic Show"],
    "B": ["Bagel", "Ball", "Bathroom", "Bed", "Blanket", "Breathe", "Bye"],
    "C": ["Call", "Car", "Cat", "Chair", "Coffee", "Cold", "Cucumber"],
    "D": ["Daddy", "Deen", "Doctor", "Dog", "Door", "Down"],
    "E": ["Elephant"],
    "F": ["FaceTime", "Fish", "Funny"],
    "G": ["Garage", "Go", "Good Morning"],
    "H": ["Happy", "Heartburn", "Hello", "Hot", "House", "How are you", "Hungry"],
    "I": ["Ice", "Inside", "iPad"],
    "J": ["Jump"],
    "K": ["Kaiser", "Key", "Kiyah", "Kleenex", "Kyan"],
    "L": ["I love you", "Lee", "Light", "Light Down", "Light Up", "Love"],
    "M": ["Mad", "Medical", "Medicine", "Meditate", "Mohammad", "Moon"],
    "N": ["Nada", "Nadowie", "Net", "No", "Noah"],
    "O": ["Orange", "Outside"],
    "P": ["Pain", "Period", "Phone", "Purple"],
    "Q": ["Queen"],
    "R": ["Red", "Rest", "Room"],
    "S": ["Sad", "Scarf", "Shoes", "Sinemet", "Sleep", "Socks", "Space", "Stop", "Sun", "Susu"],
    "T": ["Togamet", "Tree", "TV", "Tylenol"],
    "U": ["Up", "Urgent Care"],
    "V": ["Van"],
    "W": ["Walk", "Walker", "Water", "Wheelchair"],
    "X": ["X-ray"],
    "Y": ["Yes", "Yellow"],
    "Z": ["Zebra"]
}

# Known recorded audio files
RECORDED_FILES = {
    "Alari", "Amer", "Amory", "Daddy", "Good Morning", "Hello", "How are you",
    "I love you", "Kiyah", "Kyan", "Lee", "Nadowie", "Noah", "Susu", 
    "Urgent Care", "Walker", "Wheelchair"
}

def generate_correct_mappings():
    """Generate the correct Arduino mappings based on button indices"""
    print("🔧 GENERATING CORRECT BUTTON MAPPINGS")
    print("=" * 50)
    
    # Create array with 36 entries (indices 0-35) initialized to empty
    mappings_array = [None] * 36
    
    # Map each button index to its corresponding letter and audio setup
    for button_index, letter in BUTTON_INDEX_TO_LETTER.items():
        if letter == ".":
            # Period button - special handling
            mappings_array[button_index] = {
                'label': 'PERIOD',
                'recFolder': 33,
                'recBase': 0,
                'recCount': 0,
                'ttsFolder': 33,
                'ttsBase': 1,
                'ttsCount': 3,
                'fallbackLabel': 'period'
            }
            continue
        elif letter == "_":
            # Space button - special handling  
            mappings_array[button_index] = {
                'label': 'SPACE',
                'recFolder': 35,
                'recBase': 0,
                'recCount': 0,
                'ttsFolder': 35,
                'ttsBase': 1,
                'ttsCount': 1,
                'fallbackLabel': 'space'
            }
            continue
        
        if letter not in WORD_MAPPINGS:
            print(f"⚠️  Warning: No word mapping for letter {letter}")
            continue
            
        words = WORD_MAPPINGS[letter]
        folder_num = ord(letter) - ord('A') + 1  # A=1, B=2, etc.
        
        # Count recorded vs TTS words
        recorded_words = [w for w in words if w in RECORDED_FILES]
        tts_words = [w for w in words if w not in RECORDED_FILES]
        
        rec_count = len(recorded_words)
        tts_count = len(tts_words)
        tts_base = rec_count + 1 if rec_count > 0 else 1
        
        # Primary label (first recorded word if available, otherwise first word)
        primary_label = recorded_words[0] if recorded_words else words[0]
        
        mappings_array[button_index] = {
            'label': letter,
            'recFolder': folder_num,
            'recBase': 1,
            'recCount': rec_count,
            'ttsFolder': folder_num,
            'ttsBase': tts_base,
            'ttsCount': tts_count,
            'fallbackLabel': primary_label
        }
        
        print(f"Button {button_index:2d} -> {letter} (Folder {folder_num:02d}): {len(words)} words ({rec_count} REC, {tts_count} TTS)")
    
    return mappings_array

def create_arduino_mappings_code(mappings_array):
    """Create the Arduino audioMappings array code"""
    print("\n📝 CREATING ARDUINO CODE")
    print("=" * 50)
    
    code_lines = ["AudioMapping audioMappings[] = {"]
    
    for i, mapping in enumerate(mappings_array):
        if mapping is None:
            # Empty slot - use default values
            code_lines.append(f'  {{"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}}, // Index {i} - unused')
        else:
            # Active mapping
            label = mapping['label']
            rec_folder = mapping['recFolder']
            rec_base = mapping['recBase']
            rec_count = mapping['recCount']
            tts_folder = mapping['ttsFolder']
            tts_base = mapping['ttsBase']
            tts_count = mapping['ttsCount']
            fallback = mapping['fallbackLabel']
            
            line = f'  {{"{label}", /*recFolder*/{rec_folder},/*recBase*/{rec_base},/*recCount*/{rec_count}, /*ttsFolder*/{tts_folder},/*ttsBase*/{tts_base},/*ttsCount*/{tts_count}, "{fallback}"}}'
            
            if i < len(mappings_array) - 1:
                line += ","
            
            # Add comment for letter mappings
            if label in WORD_MAPPINGS:
                words = WORD_MAPPINGS[label]
                recorded_words = [w for w in words if w in RECORDED_FILES]
                comment = f" // Index {i} -> {label}: "
                if recorded_words:
                    comment += f"REC=1-{rec_count}({','.join(recorded_words[:2])}{'...' if len(recorded_words) > 2 else ''}), "
                if tts_count > 0:
                    tts_words = [w for w in words if w not in RECORDED_FILES]
                    comment += f"TTS={tts_base}-{tts_base + tts_count - 1}({','.join(tts_words[:2])}{'...' if len(tts_words) > 2 else ''})"
                line += comment
            else:
                line += f" // Index {i} -> {label}"
            
            code_lines.append(line)
    
    code_lines.append("};")
    
    return "\n".join(code_lines)

def update_arduino_file(new_mappings_code):
    """Update the Arduino file with new mappings"""
    print("\n🔧 UPDATING ARDUINO FILE")
    print("=" * 50)
    
    # Read current file
    with open(ARDUINO_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the audioMappings array
    start_marker = "AudioMapping audioMappings[] = {"
    end_marker = "};\n\nconst uint8_t AUDIO_MAPPINGS_COUNT"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("❌ Could not find audioMappings array in Arduino code")
        return False
    
    # Replace the mappings
    new_content = content[:start_idx] + new_mappings_code + "\n\n" + content[end_idx:]
    
    # Write updated content
    with open(ARDUINO_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Arduino file updated successfully")
    return True

def create_button_reference():
    """Create a reference file showing the button mapping"""
    print("\n📋 CREATING BUTTON REFERENCE")
    print("=" * 50)
    
    ref_path = Path(ARDUINO_FILE_PATH).parent / "BUTTON_INDEX_REFERENCE.txt"
    
    with open(ref_path, 'w', encoding='utf-8') as f:
        f.write("TACTILE COMMUNICATION DEVICE - BUTTON INDEX REFERENCE\n")
        f.write("=" * 60 + "\n\n")
        f.write("Physical Button Index -> Letter -> Audio Folder -> Words\n")
        f.write("-" * 60 + "\n\n")
        
        for button_index in sorted(BUTTON_INDEX_TO_LETTER.keys()):
            letter = BUTTON_INDEX_TO_LETTER[button_index]
            
            if letter == ".":
                f.write(f"Button {button_index:2d} -> PERIOD (Folder 33) -> Period, Mode switching\n")
            elif letter == "_":
                f.write(f"Button {button_index:2d} -> SPACE  (Folder 35) -> Space\n")
            elif letter in WORD_MAPPINGS:
                folder_num = ord(letter) - ord('A') + 1
                words = WORD_MAPPINGS[letter]
                recorded_words = [w for w in words if w in RECORDED_FILES]
                
                f.write(f"Button {button_index:2d} -> {letter}      (Folder {folder_num:02d}) -> {', '.join(words)}\n")
                if recorded_words:
                    f.write(f"           🎤 Recorded: {', '.join(recorded_words)}\n")
                f.write("\n")
        
        f.write("\nPRIORITY SYSTEM:\n")
        f.write("- HUMAN_FIRST: Personal recordings play first, then TTS\n")
        f.write("- GENERATED_FIRST: TTS plays first, then personal recordings\n")
        f.write("- Switch modes: Triple-press Period button within 1.2 seconds\n")
    
    print(f"✅ Created reference file: {ref_path}")

def main():
    """Main function"""
    print("🚀 FIXING TACTILE COMMUNICATION DEVICE BUTTON MAPPINGS")
    print("=" * 60)
    
    try:
        # Generate correct mappings
        mappings_array = generate_correct_mappings()
        
        # Create Arduino code
        arduino_code = create_arduino_mappings_code(mappings_array)
        
        # Update Arduino file
        update_arduino_file(arduino_code)
        
        # Create reference file
        create_button_reference()
        
        print("\n" + "=" * 60)
        print("✅ BUTTON MAPPING FIX COMPLETE!")
        print("=" * 60)
        print("Summary:")
        print(f"- Updated Arduino mappings for {len([m for m in mappings_array if m is not None])} active buttons")
        print("- Mapped button indices to correct letters and audio folders")
        print("- Maintained REC/TTS priority system")
        print("- Created button reference file")
        print("\nNext steps:")
        print("1. Compile and upload the updated Arduino code")
        print("2. Test all button mappings")
        print("3. Verify audio playback matches expected words")
        
    except Exception as e:
        print(f"❌ Error fixing button mappings: {e}")
        raise

if __name__ == "__main__":
    main()
