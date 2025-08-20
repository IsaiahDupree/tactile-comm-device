#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def copy_audio_files():
    """Copy generated audio files from backup to current project structure."""
    
    # Source and destination paths
    source_dir = Path("D:/Coding_backup/Coding/Button/Audio/expanded_audio")
    dest_dir = Path("c:/Users/Cypress/Documents/Coding/Buttons/tactile-comm-device/sd/SD_FUTURE_PROOF/audio/generated")
    
    # Human recordings source and destination
    human_source = Path("D:/Coding_backup/Coding/Button/Audio/RecordedWords")
    human_dest = Path("c:/Users/Cypress/Documents/Coding/Buttons/tactile-comm-device/sd/SD_FUTURE_PROOF/audio/human")
    
    print("Starting audio file copy process...")
    
    # Copy generated audio files
    if source_dir.exists():
        print(f"Copying generated audio from {source_dir} to {dest_dir}")
        
        # Create destination directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy each numbered folder
        for folder in source_dir.iterdir():
            if folder.is_dir() and folder.name.isdigit():
                dest_folder = dest_dir / folder.name
                dest_folder.mkdir(exist_ok=True)
                
                # Copy all mp3 files in the folder
                for mp3_file in folder.glob("*.mp3"):
                    dest_file = dest_folder / mp3_file.name
                    shutil.copy2(mp3_file, dest_file)
                    print(f"  Copied {mp3_file.name} to folder {folder.name}")
    else:
        print(f"Source directory not found: {source_dir}")
    
    # Copy human recordings
    if human_source.exists():
        print(f"\nCopying human recordings from {human_source} to {human_dest}")
        
        # Create human audio directory structure
        human_dest.mkdir(parents=True, exist_ok=True)
        
        # Create letter folders for human audio (A-Z)
        letter_mapping = {
            'A': ['Alari.mp3', 'Amer.mp3', 'Amory.mp3'],
            'D': ['Daddy.mp3', 'Deen.mp3'],
            'K': ['Kiyah.mp3', 'Kyan.mp3'],
            'L': ['Lee.mp3'],
            'N': ['Nada.mp3', 'Nadowie.mp3', 'Noah.mp3'],
            'S': ['Susu.mp3'],
            'W': ['Walker.mp3', 'Wheelchair.mp3'],
            'PHRASES': ['Bye.mp3', 'Good Morning.mp3', 'Hello How are You.mp3', 'I Love You.mp3', 'Urgent Care.mp3']
        }
        
        for letter, files in letter_mapping.items():
            if letter == 'PHRASES':
                # Create special phrases folder
                phrases_folder = human_dest / 'PHRASES'
                phrases_folder.mkdir(exist_ok=True)
                dest_folder = phrases_folder
            else:
                # Create letter folder
                letter_folder = human_dest / letter
                letter_folder.mkdir(exist_ok=True)
                dest_folder = letter_folder
            
            # Copy files with sequential numbering
            for i, filename in enumerate(files, 1):
                source_file = human_source / filename
                if source_file.exists():
                    dest_file = dest_folder / f"{i:03d}.mp3"
                    shutil.copy2(source_file, dest_file)
                    print(f"  Copied {filename} to {letter}/{i:03d}.mp3")
    else:
        print(f"Human recordings directory not found: {human_source}")
    
    print("\nAudio file copy process completed!")

if __name__ == "__main__":
    copy_audio_files()
