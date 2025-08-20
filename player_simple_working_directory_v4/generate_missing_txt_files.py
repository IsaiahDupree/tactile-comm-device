#!/usr/bin/env python3
"""
Generate missing .txt files for all .mp3 files in the SD structure.
This ensures the firmware's [CONTENT] About to say: ... logging works.
"""

import os
from pathlib import Path

def generate_txt_files(base_dir):
    """Generate .txt files for all .mp3 files that don't have them."""
    
    audio_dir = base_dir / "SD_CARD_STRUCTURE" / "audio"
    
    # Key-to-description mapping for better text content
    key_descriptions = {
        'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H',
        'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P',
        'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X',
        'Y': 'Y', 'Z': 'Z',
        'SHIFT': 'Shift',
        'PERIOD': 'Period',
        'SPACE': 'Space',
        'YES': 'Yes',
        'NO': 'No',
        'WATER': 'Water',
        'HELLO_HOW_ARE_YOU': 'Hello, how are you?',
        'BYE': 'Bye',
        'GOOD': 'Good morning',
        'URGENT': 'Urgent care',
        'WHEELCHAIR': 'Wheelchair'
    }
    
    # Name-based descriptions for loose files
    name_descriptions = {
        'Alari.mp3': 'Alari',
        'Amer.mp3': 'Amer', 
        'Amory.mp3': 'Amory',
        'Bye.mp3': 'Bye',
        'Daddy.mp3': 'Daddy',
        'Deen.mp3': 'Deen',
        'Good Morning.mp3': 'Good morning',
        'Hello How are You.mp3': 'Hello, how are you?',
        'I Love You.mp3': 'I love you',
        'Kiyah.mp3': 'Kiyah',
        'Kyan.mp3': 'Kyan',
        'Lee.mp3': 'Lee',
        'Nada.mp3': 'Nada',
        'Nadowie.mp3': 'Nadowie',
        'Noah.mp3': 'Noah',
        'Susu.mp3': 'Susu',
        'Urgent Care.mp3': 'Urgent care',
        'Walker.mp3': 'Walker',
        'Wheelchair.mp3': 'Wheelchair'
    }
    
    created_count = 0
    
    # Process both human and generated audio directories
    for audio_type in ['human', 'generated']:
        type_dir = audio_dir / audio_type
        if not type_dir.exists():
            continue
            
        print(f"\n🔍 Processing {audio_type} audio files...")
        
        # Find all .mp3 files recursively
        for mp3_file in type_dir.rglob("*.mp3"):
            txt_file = mp3_file.with_suffix('.txt')
            
            if txt_file.exists():
                continue  # Skip if .txt already exists
            
            # Determine content based on file location and name
            relative_path = mp3_file.relative_to(type_dir)
            parts = relative_path.parts
            
            if len(parts) == 2:  # KEY/001.mp3 format
                key = parts[0]
                filename = parts[1]
                content = key_descriptions.get(key, key)
                
                # Add sequence info for numbered files
                if filename.startswith(('001', '002', '003')):
                    if filename == '002.mp3':
                        content = f"{content} (variation 2)"
                    elif filename == '003.mp3':
                        content = f"{content} (variation 3)"
                        
            else:  # Loose file in root
                filename = mp3_file.name
                content = name_descriptions.get(filename, mp3_file.stem)
            
            # Create the .txt file
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"# {mp3_file.name} should contain: {content}\n")
            
            print(f"  ✅ Created: {txt_file.relative_to(base_dir)}")
            created_count += 1
    
    print(f"\n🎉 Created {created_count} missing .txt files")
    return created_count

def main():
    base_dir = Path(__file__).parent
    print("🎵 Generating missing .txt files for audio content logging...")
    
    count = generate_txt_files(base_dir)
    
    if count > 0:
        print(f"\n✅ Generated {count} .txt files")
        print("📋 Next steps:")
        print("  1. Copy the updated SD_CARD_STRUCTURE to your physical SD card")
        print("  2. Upload firmware and test - you should now see [CONTENT] About to say: ... messages")
    else:
        print("✅ All .txt files already exist!")

if __name__ == "__main__":
    main()
