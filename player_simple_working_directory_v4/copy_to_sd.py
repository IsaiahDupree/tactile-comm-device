#!/usr/bin/env python3
"""
Copy Priority Mode Announcement Files to SD Card
This script helps copy the generated ElevenLabs announcement files to an SD card

Usage:
  python copy_to_sd.py <sd_card_drive_letter>
  
Example:
  python copy_to_sd.py E:
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Error: Please provide the SD card drive letter")
        print("Usage: python copy_to_sd.py <sd_card_drive_letter>")
        print("Example: python copy_to_sd.py E:")
        
        # List available drives
        print("\nAvailable drives:")
        import win32api
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        for i, drive in enumerate(drives):
            try:
                drive_type = win32api.GetDriveType(drive)
                type_name = {
                    0: "Unknown",
                    1: "No Root Directory",
                    2: "Removable",
                    3: "Fixed",
                    4: "Network",
                    5: "CD-ROM",
                    6: "RAM Disk"
                }.get(drive_type, "Unknown")
                
                print(f"{i+1}. {drive} - {type_name}")
            except:
                print(f"{i+1}. {drive} - Error reading drive type")
        return
    
    sd_path = sys.argv[1]
    
    # Check if SD card exists
    if not os.path.exists(sd_path):
        print(f"Error: Drive {sd_path} not found")
        return
    
    # Source directory with announcement files
    source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_announcements", "33")
    
    # Files to copy
    files_to_copy = [
        ("001.mp3", "Human first mode"),
        ("002.mp3", "Generated first mode")
    ]
    
    # Make sure the source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Source directory not found: {source_dir}")
        print("Please run generate_priority_mode_audio.py first")
        return
    
    # Create target directory structure on SD card
    target_dir = os.path.join(sd_path, "33")
    alt_target_dirs = [
        sd_path,                      # Root directory
        os.path.join(sd_path, "audio"), # /audio directory
        os.path.join(sd_path, "announcements")  # /announcements directory
    ]
    
    try:
        os.makedirs(target_dir, exist_ok=True)
        print(f"Created directory: {target_dir}")
        
        # Also create alternate directories
        for alt_dir in alt_target_dirs:
            if alt_dir != sd_path:  # Skip root directory
                os.makedirs(alt_dir, exist_ok=True)
                print(f"Created alternate directory: {alt_dir}")
                
    except Exception as e:
        print(f"Error creating directories: {str(e)}")
        return
    
    # Copy each file
    for filename, description in files_to_copy:
        source_file = os.path.join(source_dir, filename)
        target_file = os.path.join(target_dir, filename)
        
        if not os.path.exists(source_file):
            print(f"Warning: Source file not found: {source_file}")
            continue
        
        try:
            shutil.copy2(source_file, target_file)
            print(f"✅ Copied '{description}' to {target_file}")
            
            # Also copy to alternate locations for redundancy
            for alt_dir in alt_target_dirs:
                alt_file = os.path.join(alt_dir, filename)
                shutil.copy2(source_file, alt_file)
                print(f"✅ Redundant copy: {alt_file}")
                
        except Exception as e:
            print(f"❌ Error copying {filename}: {str(e)}")
    
    print("\nFiles successfully copied to SD card!")
    print("\nYou can now insert the SD card into your device and")
    print("use the 'M' serial command or triple-press of the period button")
    print("to toggle priority modes with announcements.")

if __name__ == "__main__":
    main()
