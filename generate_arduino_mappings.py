#!/usr/bin/env python3
"""
Generate correct Arduino audioMappings array based on actual SD card content.
"""

import os
import json

SD_CARD_DRIVE = "E:\\"

# Button to folder mapping (from your Arduino code)
BUTTON_FOLDERS = {
    "A": 5, "B": 6, "C": 7, "D": 8, "E": 9, "F": 10, "G": 11, "H": 12,
    "I": 13, "J": 14, "K": 15, "L": 16, "M": 17, "N": 18, "O": 19, "P": 20,
    "Q": 21, "R": 22, "S": 23, "T": 24, "U": 25, "V": 26, "W": 27, "X": 28,
    "Y": 29, "Z": 30
}

def analyze_sd_card_content():
    """Analyze SD card to determine REC vs TTS ranges for each button."""
    print("🔍 ANALYZING SD CARD CONTENT")
    print("=" * 50)
    
    button_analysis = {}
    
    # Read the corrected audio index
    csv_path = os.path.join(SD_CARD_DRIVE, "config", "audio_index.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ Audio index not found: {csv_path}")
        return None
    
    # Parse CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]  # Skip header
    
    # Group by folder
    folder_data = {}
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            folder = int(parts[0])
            track = int(parts[1])
            text = parts[2]
            audio_type = parts[3]
            
            if folder not in folder_data:
                folder_data[folder] = []
            
            folder_data[folder].append({
                'track': track,
                'text': text,
                'type': audio_type
            })
    
    # Analyze each button
    for button, folder in BUTTON_FOLDERS.items():
        if folder in folder_data:
            tracks = sorted(folder_data[folder], key=lambda x: x['track'])
            
            rec_tracks = [t for t in tracks if t['type'] == 'REC']
            tts_tracks = [t for t in tracks if t['type'] == 'TTS']
            
            # Determine ranges
            rec_base = rec_tracks[0]['track'] if rec_tracks else 0
            rec_count = len(rec_tracks)
            
            tts_base = tts_tracks[0]['track'] if tts_tracks else 0
            tts_count = len(tts_tracks)
            
            # Get fallback label (first REC or first TTS)
            fallback = rec_tracks[0]['text'] if rec_tracks else (tts_tracks[0]['text'] if tts_tracks else button)
            
            button_analysis[button] = {
                'folder': folder,
                'rec_base': rec_base,
                'rec_count': rec_count,
                'tts_base': tts_base,
                'tts_count': tts_count,
                'fallback': fallback[:11],  # Max 11 chars for Arduino
                'rec_tracks': [t['text'] for t in rec_tracks],
                'tts_tracks': [t['text'] for t in tts_tracks],
                'total_tracks': len(tracks)
            }
            
            print(f"📁 {button} (folder {folder:02d}): {rec_count} REC + {tts_count} TTS = {len(tracks)} total")
            if rec_tracks:
                print(f"   REC: {', '.join([t['text'] for t in rec_tracks])}")
            if tts_tracks:
                print(f"   TTS: {', '.join([t['text'] for t in tts_tracks])}")
    
    return button_analysis

def generate_arduino_code(button_analysis):
    """Generate Arduino audioMappings array code."""
    print("\n📝 GENERATING ARDUINO CODE")
    print("=" * 50)
    
    arduino_code = []
    arduino_code.append("// Generated audioMappings based on actual SD card content")
    arduino_code.append("AudioMapping audioMappings[] = {")
    
    for button in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if button in button_analysis:
            data = button_analysis[button]
            
            # Create comment with track details
            comment_parts = []
            if data['rec_count'] > 0:
                rec_range = f"{data['rec_base']}-{data['rec_base'] + data['rec_count'] - 1}" if data['rec_count'] > 1 else str(data['rec_base'])
                comment_parts.append(f"REC={rec_range}({','.join(data['rec_tracks'])})")
            
            if data['tts_count'] > 0:
                tts_range = f"{data['tts_base']}-{data['tts_base'] + data['tts_count'] - 1}" if data['tts_count'] > 1 else str(data['tts_base'])
                comment_parts.append(f"TTS={tts_range}({','.join(data['tts_tracks'])})")
            
            comment = f"  // {button}: {', '.join(comment_parts)}"
            arduino_code.append(comment)
            
            # Create mapping entry
            mapping = f'  {{"{button}", /*recFolder*/{data["folder"]},/*recBase*/{data["rec_base"]},/*recCount*/{data["rec_count"]}, /*ttsFolder*/{data["folder"]},/*ttsBase*/{data["tts_base"]},/*ttsCount*/{data["tts_count"]}, "{data["fallback"]}"}}'
            
            # Add comma except for last entry
            if button != "Z" or any(b in button_analysis for b in "ABCDEFGHIJKLMNOPQRSTUVWXY"[ord(button)-ord("A")+1:]):
                mapping += ","
            
            arduino_code.append(mapping)
        else:
            # Empty button
            arduino_code.append(f'  // {button}: No audio files')
            arduino_code.append(f'  {{"{button}", /*recFolder*/0,/*recBase*/0,/*recCount*/0, /*ttsFolder*/0,/*ttsBase*/0,/*ttsCount*/0, "{button}"}},')
    
    # Remove trailing comma from last entry
    if arduino_code[-1].endswith(','):
        arduino_code[-1] = arduino_code[-1][:-1]
    
    arduino_code.append("};")
    arduino_code.append("")
    arduino_code.append(f"const uint8_t AUDIO_MAPPINGS_COUNT = sizeof(audioMappings) / sizeof(audioMappings[0]);")
    
    return arduino_code

def main():
    """Main function to generate Arduino mappings."""
    print("🎵 GENERATING ARDUINO AUDIO MAPPINGS")
    print("=" * 60)
    
    # Analyze SD card content
    button_analysis = analyze_sd_card_content()
    
    if not button_analysis:
        print("❌ Failed to analyze SD card content")
        return
    
    # Generate Arduino code
    arduino_code = generate_arduino_code(button_analysis)
    
    # Save to file
    output_file = "arduino_audio_mappings.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(arduino_code))
    
    # Display the code
    print("\n🎯 GENERATED ARDUINO CODE:")
    print("=" * 60)
    for line in arduino_code:
        print(line)
    
    print(f"\n✅ Arduino code saved to: {output_file}")
    print("\n📋 NEXT STEPS:")
    print("1. Copy the generated audioMappings array")
    print("2. Replace the existing audioMappings in your Arduino code")
    print("3. Upload the updated firmware")
    print("4. Test the priority modes - they should now work correctly!")
    
    # Summary
    active_buttons = len(button_analysis)
    total_files = sum(data['total_tracks'] for data in button_analysis.values())
    total_rec = sum(data['rec_count'] for data in button_analysis.values())
    total_tts = sum(data['tts_count'] for data in button_analysis.values())
    
    print(f"\n📊 SUMMARY:")
    print(f"   Active buttons: {active_buttons}")
    print(f"   Total audio files: {total_files}")
    print(f"   Personal recordings (REC): {total_rec}")
    print(f"   Generated TTS files: {total_tts}")
    print("=" * 60)

if __name__ == "__main__":
    main()
