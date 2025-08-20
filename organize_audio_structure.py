#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def organize_audio_structure():
    """Organize audio files into proper SD card structure."""
    
    # Base paths
    base_audio = Path("c:/Users/Cypress/Documents/Coding/Buttons/tactile-comm-device/sd/SD_FUTURE_PROOF/audio")
    recordings_source = Path("c:/Users/Cypress/Documents/Coding/Buttons/Recordings")
    backup_generated = Path("D:/Coding_backup/Coding/Button/Audio/expanded_audio")
    backup_human = Path("D:/Coding_backup/Coding/Button/Audio/RecordedWords")
    
    print("Organizing audio structure...")
    
    # Create main directories
    human_dir = base_audio / "human"
    generated_dir = base_audio / "generated"
    
    human_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy generated audio files from backup
    if backup_generated.exists():
        print(f"Copying generated audio from {backup_generated}")
        
        for folder in backup_generated.iterdir():
            if folder.is_dir() and folder.name.isdigit():
                # Map numbered folders to letters (05=A, 06=B, etc.)
                folder_num = int(folder.name)
                if 5 <= folder_num <= 30:  # A-Z mapping
                    letter = chr(ord('A') + folder_num - 5)
                    dest_folder = generated_dir / letter
                    dest_folder.mkdir(exist_ok=True)
                    
                    # Copy all mp3 files
                    for mp3_file in folder.glob("*.mp3"):
                        dest_file = dest_folder / mp3_file.name
                        if backup_generated != generated_dir:  # Only copy if different locations
                            try:
                                shutil.copy2(mp3_file, dest_file)
                                print(f"  Copied {mp3_file.name} to {letter}/")
                            except Exception as e:
                                print(f"  Error copying {mp3_file.name}: {e}")
    
    # Organize human recordings
    sources = [recordings_source, backup_human]
    
    for source in sources:
        if source.exists():
            print(f"Processing human recordings from {source}")
            
            # Letter-based name mappings
            name_mappings = {
                'A': ['Alari.mp3', 'Amer.mp3', 'Amory.mp3'],
                'D': ['Daddy.mp3', 'Deen.mp3'],
                'K': ['Kiyah.mp3', 'Kyan.mp3'],
                'L': ['Lee.mp3'],
                'N': ['Nada.mp3', 'Nadowie.mp3', 'Noah.mp3'],
                'S': ['Susu.mp3'],
                'W': ['Walker.mp3', 'Wheelchair.mp3']
            }
            
            # Special phrases
            phrases = ['Bye.mp3', 'Good Morning.mp3', 'Hello How are You.mp3', 
                      'I Love You.mp3', 'Urgent Care.mp3']
            
            # Copy name-based files
            for letter, files in name_mappings.items():
                letter_dir = human_dir / letter
                letter_dir.mkdir(exist_ok=True)
                
                for i, filename in enumerate(files, 1):
                    source_file = source / filename
                    if source_file.exists():
                        dest_file = letter_dir / f"{i:03d}.mp3"
                        try:
                            shutil.copy2(source_file, dest_file)
                            print(f"  Copied {filename} to {letter}/{i:03d}.mp3")
                        except Exception as e:
                            print(f"  Error copying {filename}: {e}")
            
            # Copy phrase files to special folder
            phrases_dir = human_dir / "PHRASES"
            phrases_dir.mkdir(exist_ok=True)
            
            for i, filename in enumerate(phrases, 1):
                source_file = source / filename
                if source_file.exists():
                    dest_file = phrases_dir / f"{i:03d}.mp3"
                    try:
                        shutil.copy2(source_file, dest_file)
                        print(f"  Copied {filename} to PHRASES/{i:03d}.mp3")
                    except Exception as e:
                        print(f"  Error copying {filename}: {e}")
    
    # Create remaining letter folders for generated content
    print("Creating remaining letter folders...")
    for i in range(26):
        letter = chr(ord('A') + i)
        
        # Generated folder
        gen_folder = generated_dir / letter
        gen_folder.mkdir(exist_ok=True)
        
        # Human folder (if doesn't exist)
        human_folder = human_dir / letter
        human_folder.mkdir(exist_ok=True)
    
    print("Audio structure organization completed!")
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Generated audio: {generated_dir}")
    print(f"Human audio: {human_dir}")
    
    # Count files
    gen_count = sum(len(list(folder.glob("*.mp3"))) for folder in generated_dir.iterdir() if folder.is_dir())
    human_count = sum(len(list(folder.glob("*.mp3"))) for folder in human_dir.iterdir() if folder.is_dir())
    
    print(f"Generated files: {gen_count}")
    print(f"Human files: {human_count}")

if __name__ == "__main__":
    organize_audio_structure()
