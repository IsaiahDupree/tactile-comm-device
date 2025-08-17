#!/usr/bin/env python3
"""
SD Card Reorganization Script for Label-Based Audio Mapping
This script reorganizes audio files on the SD card to match the new 
label-based audio mapping system used by the VS1053 tactile communicator.
"""

import os
import shutil
from pathlib import Path

# SD card path (adjust as needed)
SD_CARD_PATH = "E:\\"

# New label-based audio mapping (matches Arduino code)
AUDIO_MAPPINGS = {
    # Special buttons
    "YES": {"folder": 1, "tracks": 1},
    "NO": {"folder": 2, "tracks": 1}, 
    "WATER": {"folder": 3, "tracks": 1},
    "AUX": {"folder": 4, "tracks": 4},   # *Hello How are You [RECORDED track 4]
    
    # Letters with recorded word priorities  
    "A": {"folder": 5, "tracks": 5},   # *Amer, *Alari, Apple, Arabic Show, *Amory [RECORDED: tracks 1,2,5]
    "B": {"folder": 6, "tracks": 5},   # Bathroom, *Bye, Bed, Breathe, blanket [RECORDED: track 2]
    "C": {"folder": 7, "tracks": 3},   # Chair, car, Cucumber
    "D": {"folder": 8, "tracks": 4},   # *Deen, *Daddy, Doctor, Door [RECORDED: tracks 1,2]
    "E": {"folder": 9, "tracks": 0},   # No words assigned
    "F": {"folder": 10, "tracks": 2},  # FaceTime, funny
    "G": {"folder": 11, "tracks": 2},  # *Good Morning, Go [RECORDED: track 1]
    "H": {"folder": 12, "tracks": 2},  # How are you, Heartburn
    "I": {"folder": 13, "tracks": 1},  # Inside
    "J": {"folder": 14, "tracks": 0},  # No words assigned
    "K": {"folder": 15, "tracks": 4},  # *Kiyah, *Kyan, Kleenex, Kaiser [RECORDED: tracks 1,2]
    "L": {"folder": 16, "tracks": 4},  # *Lee, *I love you, light down, light up [RECORDED: tracks 1,2]
    "M": {"folder": 17, "tracks": 3},  # Mohammad, Medicine, Medical
    "N": {"folder": 18, "tracks": 3},  # Nada, *Nadowie, *Noah [RECORDED: tracks 2,3]
    "O": {"folder": 19, "tracks": 1},  # Outside
    "P": {"folder": 20, "tracks": 2},  # Pain, Phone
    "Q": {"folder": 21, "tracks": 0},  # No words assigned
    "R": {"folder": 22, "tracks": 1},  # Room
    "S": {"folder": 23, "tracks": 3},  # Scarf, *Susu, Sinemet [RECORDED: track 2]
    "T": {"folder": 24, "tracks": 1},  # TV
    "U": {"folder": 25, "tracks": 1},  # *Urgent Care [RECORDED: track 1]
    "V": {"folder": 26, "tracks": 0},  # No words assigned
    "W": {"folder": 27, "tracks": 4},  # Water, *Walker, *wheelchair, walk [RECORDED: tracks 2,3]
    "X": {"folder": 28, "tracks": 0},  # No words assigned
    "Y": {"folder": 29, "tracks": 0},  # No words assigned
    "Z": {"folder": 30, "tracks": 0},  # No words assigned
    "SPACE": {"folder": 31, "tracks": 1},
    "PERIOD": {"folder": 32, "tracks": 1},
    "SHIFT": {"folder": 33, "tracks": 1}  # Add SHIFT button support
}

# Original button mappings from letter_mappings.json
ORIGINAL_MAPPINGS = {
    # Special buttons (based on old index system)
    "YES": {"old_folder": 1},
    "NO": {"old_folder": 2}, 
    "WATER": {"old_folder": 3},
    "AUX": {"old_folder": 4},
    
    # Letters (based on alphabet order A=folder 5, B=folder 6, etc.)
    "A": {"old_folder": 5},
    "B": {"old_folder": 6},
    "C": {"old_folder": 7},
    "D": {"old_folder": 8},
    "E": {"old_folder": 9},
    "F": {"old_folder": 10},
    "G": {"old_folder": 11},
    "H": {"old_folder": 12},
    "I": {"old_folder": 13},
    "J": {"old_folder": 14},
    "K": {"old_folder": 15},
    "L": {"old_folder": 16},
    "M": {"old_folder": 17},
    "N": {"old_folder": 18},
    "O": {"old_folder": 19},
    "P": {"old_folder": 20},
    "Q": {"old_folder": 21},
    "R": {"old_folder": 22},
    "S": {"old_folder": 23},
    "T": {"old_folder": 24},
    "U": {"old_folder": 25},
    "V": {"old_folder": 26},
    "W": {"old_folder": 27},
    "X": {"old_folder": 28},
    "Y": {"old_folder": 29},
    "Z": {"old_folder": 30},
    "SPACE": {"old_folder": 31},
    "PERIOD": {"old_folder": 32}
}

def backup_sd_card():
    """Create a backup of the current SD card structure"""
    backup_path = Path(SD_CARD_PATH) / "backup_original"
    if backup_path.exists():
        print(f"Backup already exists at {backup_path}")
        return
    
    print("Creating backup of original SD card structure...")
    backup_path.mkdir()
    
    for i in range(1, 33):  # Original folders 01-32
        folder_name = f"{i:02d}"
        src_folder = Path(SD_CARD_PATH) / folder_name
        if src_folder.exists():
            dst_folder = backup_path / folder_name
            shutil.copytree(src_folder, dst_folder)
            print(f"  Backed up folder {folder_name}")

def create_new_folder_structure():
    """Create new folder structure based on label mappings"""
    print("\nCreating new folder structure...")
    
    # Create temporary folder for reorganization
    temp_path = Path(SD_CARD_PATH) / "temp_reorganize"
    if temp_path.exists():
        shutil.rmtree(temp_path)
    temp_path.mkdir()
    
    # Create all new folders
    for label, mapping in AUDIO_MAPPINGS.items():
        if mapping["tracks"] > 0:  # Only create folders for labels with audio
            folder_name = f"{mapping['folder']:02d}"
            new_folder = temp_path / folder_name
            new_folder.mkdir(exist_ok=True)
            print(f"  Created folder {folder_name} for {label}")

def move_audio_files():
    """Move audio files from old structure to new structure"""
    print("\nMoving audio files to new structure...")
    
    temp_path = Path(SD_CARD_PATH) / "temp_reorganize"
    
    for label, new_mapping in AUDIO_MAPPINGS.items():
        if new_mapping["tracks"] == 0:
            continue  # Skip labels with no audio
            
        # Find old folder location
        old_mapping = ORIGINAL_MAPPINGS.get(label)
        if not old_mapping:
            print(f"  Warning: No old mapping found for {label}")
            continue
            
        old_folder_name = f"{old_mapping['old_folder']:02d}"
        new_folder_name = f"{new_mapping['folder']:02d}"
        
        old_folder = Path(SD_CARD_PATH) / old_folder_name
        new_folder = temp_path / new_folder_name
        
        if not old_folder.exists():
            print(f"  Warning: Old folder {old_folder_name} not found for {label}")
            continue
            
        # Copy all mp3 files from old to new location
        files_moved = 0
        for mp3_file in old_folder.glob("*.mp3"):
            dst_file = new_folder / mp3_file.name
            shutil.copy2(mp3_file, dst_file)
            files_moved += 1
            
        print(f"  Moved {files_moved} files: {old_folder_name} → {new_folder_name} ({label})")

def finalize_reorganization():
    """Replace old structure with new structure"""
    print("\nFinalizing reorganization...")
    
    temp_path = Path(SD_CARD_PATH) / "temp_reorganize"
    
    # Remove old numbered folders (keep backup folder)
    for i in range(1, 35):  # Remove folders 01-34 to be safe
        folder_name = f"{i:02d}"
        old_folder = Path(SD_CARD_PATH) / folder_name
        if old_folder.exists():
            shutil.rmtree(old_folder)
            
    # Move new folders from temp to root
    for folder in temp_path.iterdir():
        if folder.is_dir():
            dst_folder = Path(SD_CARD_PATH) / folder.name
            shutil.move(str(folder), str(dst_folder))
            print(f"  Finalized folder {folder.name}")
            
    # Remove temp folder
    shutil.rmtree(temp_path)

def create_mapping_documentation():
    """Create documentation of the new folder structure"""
    print("\nCreating mapping documentation...")
    
    doc_path = Path(SD_CARD_PATH) / "FOLDER_MAPPING.txt"
    with open(doc_path, 'w') as f:
        f.write("TACTILE COMMUNICATOR - AUDIO FOLDER MAPPING\n")
        f.write("==========================================\n\n")
        f.write("Label-Based Audio System\n")
        f.write("Generated by: reorganize_sd_card.py\n\n")
        
        for label, mapping in AUDIO_MAPPINGS.items():
            folder_num = f"{mapping['folder']:02d}"
            track_count = mapping['tracks']
            if track_count > 0:
                f.write(f"Folder {folder_num}: {label} ({track_count} tracks)\n")
            else:
                f.write(f"Folder {folder_num}: {label} (no audio)\n")
                
        f.write(f"\nTotal folders: {len([m for m in AUDIO_MAPPINGS.values() if m['tracks'] > 0])}\n")
        f.write("Total audio files: varies by label\n")
        
    print(f"  Created documentation: {doc_path}")

def main():
    """Main reorganization process"""
    if not Path(SD_CARD_PATH).exists():
        print(f"Error: SD card not found at {SD_CARD_PATH}")
        print("Please update SD_CARD_PATH variable to match your SD card drive")
        return
        
    print("=== SD CARD REORGANIZATION FOR LABEL-BASED AUDIO ===")
    print(f"SD Card Path: {SD_CARD_PATH}")
    print(f"Total Labels: {len(AUDIO_MAPPINGS)}")
    print(f"Labels with Audio: {len([m for m in AUDIO_MAPPINGS.values() if m['tracks'] > 0])}")
    
    response = input("\nProceed with reorganization? (y/N): ")
    if response.lower() != 'y':
        print("Reorganization cancelled.")
        return
        
    try:
        backup_sd_card()
        create_new_folder_structure()
        move_audio_files()
        finalize_reorganization()
        create_mapping_documentation()
        
        print("\n=== REORGANIZATION COMPLETE ===")
        print("✅ SD card successfully reorganized for label-based audio system")
        print("✅ Original files backed up in 'backup_original' folder")
        print("✅ New folder structure matches Arduino audio mappings")
        print("✅ Documentation created: FOLDER_MAPPING.txt")
        print("\nYour tactile communicator is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error during reorganization: {e}")
        print("Check the backup_original folder to restore if needed")

if __name__ == "__main__":
    main()
