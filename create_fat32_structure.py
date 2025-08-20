#!/usr/bin/env python3
"""
Create FAT32 8.3 compatible folder structure to match what Arduino sees
"""

import os
import shutil
from pathlib import Path

def create_fat32_structure():
    base_path = Path("C:/Users/Cypress/Documents/Coding/Buttons/player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio")
    
    # Create GENERA~1 directory (FAT32 8.3 version of 'generated')
    genera_path = base_path / "GENERA~1"
    genera_path.mkdir(exist_ok=True)
    
    # Copy contents from 'generated' to 'GENERA~1'
    generated_path = base_path / "generated"
    if generated_path.exists():
        print(f"Copying from {generated_path} to {genera_path}")
        
        # Copy all subdirectories and files
        for item in generated_path.iterdir():
            dest = genera_path / item.name
            if item.is_directory():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
                print(f"Copied directory: {item.name}")
            else:
                shutil.copy2(item, dest)
                print(f"Copied file: {item.name}")
    
    # List what we created
    print(f"\nContents of {genera_path}:")
    if genera_path.exists():
        for item in sorted(genera_path.iterdir()):
            if item.is_directory():
                file_count = len(list(item.glob("*")))
                print(f"  {item.name}/ ({file_count} items)")
            else:
                print(f"  {item.name} ({item.stat().st_size} bytes)")
    
    print(f"\n✓ FAT32 8.3 structure created at: {genera_path}")
    print("Arduino will now see: /audio/GENERA~1/ instead of /audio/generated/")

if __name__ == "__main__":
    create_fat32_structure()
