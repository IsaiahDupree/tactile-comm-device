#!/usr/bin/env python3
"""
Reorganize SD card structure:
1. Create all letter folders A-Z in both HUMAN and GENERA~1 directories
2. Move named folders to corresponding letter directories
"""

import os
import shutil

def main():
    # Base paths
    human_path = r'c:\Users\Cypress\Documents\Coding\Buttons\player_simple_working_directory_v6\SD_CARD_STRUCTURE\AUDIO\HUMAN'
    genera_path = r'c:\Users\Cypress\Documents\Coding\Buttons\player_simple_working_directory_v6\SD_CARD_STRUCTURE\AUDIO\GENERA~1'

    print("=== SD Card Structure Reorganization ===")
    
    # Step 1: Create all letter folders A-Z in both directories
    print("\n1. Creating letter folders A-Z...")
    letters = [chr(i) for i in range(65, 91)]  # A-Z
    for letter in letters:
        human_letter_path = os.path.join(human_path, letter)
        genera_letter_path = os.path.join(genera_path, letter)
        
        os.makedirs(human_letter_path, exist_ok=True)
        os.makedirs(genera_letter_path, exist_ok=True)
        print(f'   Created: {letter}/')

    # Step 2: Move named folders to corresponding letters
    print("\n2. Moving named folders to letter directories...")
    
    moves = [
        ('BYE', 'B'),
        ('GOOD', 'G'), 
        ('HELLO_HO', 'H'),
        ('WHEELCHA', 'W'),
        ('URGENT', 'U')
    ]
    
    for old_name, new_letter in moves:
        old_path = os.path.join(human_path, old_name)
        new_path = os.path.join(human_path, new_letter)
        
        if os.path.exists(old_path):
            print(f"   Moving {old_name}/ contents to {new_letter}/")
            
            # Move all files from old folder to new letter folder
            for item in os.listdir(old_path):
                src = os.path.join(old_path, item)
                dst = os.path.join(new_path, item)
                
                if os.path.isfile(src):
                    shutil.move(src, dst)
                    print(f"     Moved: {item}")
            
            # Remove empty old folder
            try:
                os.rmdir(old_path)
                print(f"     Deleted empty folder: {old_name}/")
            except OSError as e:
                print(f"     Warning: Could not delete {old_name}/: {e}")
        else:
            print(f"   Folder {old_name}/ not found, skipping...")

    print("\n=== Reorganization Complete ===")
    print("All letter folders A-Z now exist in both HUMAN and GENERA~1 directories")
    print("Named folders have been moved to their corresponding letter directories")

if __name__ == "__main__":
    main()
