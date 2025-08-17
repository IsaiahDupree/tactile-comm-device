#!/usr/bin/env python3
"""
SD Card Folder Scanner

Scans all folders on the SD card and analyzes content to propose better naming conventions.
"""

import os
import glob
from pathlib import Path

def get_file_size_mb(file_path):
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)

def analyze_folder(folder_path):
    """Analyze content of a folder"""
    if not os.path.exists(folder_path):
        return {"exists": False}
    
    mp3_files = glob.glob(os.path.join(folder_path, "*.mp3"))
    mp3_files.sort()
    
    total_size = sum(os.path.getsize(f) for f in mp3_files)
    
    return {
        "exists": True,
        "file_count": len(mp3_files),
        "total_size_kb": total_size / 1024,
        "files": [os.path.basename(f) for f in mp3_files]
    }

def propose_better_names():
    """Propose better folder naming convention"""
    
    # Better naming convention based on function
    proposed_structure = {
        "SPECIAL": {
            "description": "Special communication buttons",
            "folders": {
                "YES_NO_WATER": "Essential needs (Yes, No, Water, Help)",
                "AUX_SHIFT": "System functions (AUX commands, SHIFT help)"
            }
        },
        "LETTERS": {
            "description": "Alphabetic communication",
            "folders": {
                f"LETTER_{chr(65+i)}": f"Letter {chr(65+i)} words" for i in range(26)
            }
        },
        "SYMBOLS": {
            "description": "Punctuation and symbols", 
            "folders": {
                "SPACE": "Space character",
                "PERIOD": "Period punctuation",
                "PUNCTUATION": "Other punctuation marks"
            }
        }
    }
    
    return proposed_structure

def main():
    sd_path = "E:\\"
    
    if not os.path.exists(sd_path):
        print(f"Error: SD card not found at {sd_path}")
        return
    
    print("=== SD CARD FOLDER ANALYSIS ===")
    print(f"SD Card: {sd_path}")
    print()
    
    total_folders = 0
    total_files = 0
    total_size_kb = 0
    empty_folders = []
    
    # Analyze numbered folders 01-33
    for folder_num in range(1, 34):
        folder_name = f"{folder_num:02d}"
        folder_path = os.path.join(sd_path, folder_name)
        
        analysis = analyze_folder(folder_path)
        
        if analysis["exists"]:
            total_folders += 1
            total_files += analysis["file_count"]
            total_size_kb += analysis["total_size_kb"]
            
            if analysis["file_count"] == 0:
                empty_folders.append(folder_name)
                status = "📂 EMPTY"
            else:
                status = f"🎵 {analysis['file_count']} files ({analysis['total_size_kb']:.1f}KB)"
            
            print(f"Folder {folder_name}: {status}")
            
            # Show files in non-empty folders
            if analysis["file_count"] > 0:
                for file in analysis["files"]:
                    print(f"  └── {file}")
        else:
            print(f"Folder {folder_name}: ❌ MISSING")
    
    print()
    print("=== SUMMARY ===")
    print(f"📁 Total folders: {total_folders}")
    print(f"🎵 Total audio files: {total_files}")
    print(f"💾 Total size: {total_size_kb:.1f}KB ({total_size_kb/1024:.1f}MB)")
    
    if empty_folders:
        print(f"📂 Empty folders: {', '.join(empty_folders)}")
    
    print()
    print("=== PROPOSED BETTER NAMING CONVENTION ===")
    
    proposed = propose_better_names()
    
    # Current mapping based on Arduino code
    current_mapping = {
        "01": "YES_NO_WATER_HELP (Special buttons)",
        "04": "SHIFT_HELP (System functions)",
        "05": "LETTER_A (Apple, Amer, Alari, Arabic, Amory)",
        "06": "LETTER_B (Ball, Bye, Bathroom, Bed)",
        "07": "LETTER_C (Cat, Chair, Car)",
        "08": "LETTER_D (Dog, Deen, Daddy, Doctor)",
        "09": "LETTER_E (Elephant)",
        "10": "LETTER_F (Fish, FaceTime)",
        "11": "LETTER_G (Go, Good Morning)",
        "12": "LETTER_H (House, Hello, How are you)",
        "13": "LETTER_I (Ice, Inside)",
        "14": "LETTER_J (Jump)",
        "15": "LETTER_K (Key, Kiyah, Kyan, Kleenex)",
        "16": "LETTER_L (Love, Lee, I love you, Light)",
        "17": "LETTER_M (Moon, Medicine, Mohammad)",
        "18": "LETTER_N (Net, Nadowie, Noah)",
        "19": "LETTER_O (Orange, Outside)",
        "20": "LETTER_P (Purple, Phone, Pain)",
        "21": "LETTER_Q (Queen)",
        "22": "LETTER_R (Red, Room)",
        "23": "LETTER_S (Sun, Susu, Scarf)",
        "24": "LETTER_T (Tree, TV)",
        "25": "LETTER_U (Up, Urgent Care)",
        "26": "LETTER_V (Van)",
        "27": "LETTER_W (Water, Walker, Wheelchair, Walk)",
        "28": "LETTER_X (X-ray)",
        "29": "LETTER_Y (Yellow)",
        "30": "LETTER_Z (Zebra)",
        "31": "SPACE (Space character)",
        "32": "PERIOD (Period punctuation)",
        "33": "SHIFT (Shift, Device Help)"
    }
    
    print("Current → Proposed Better Names:")
    for folder_num in range(1, 34):
        folder_name = f"{folder_num:02d}"
        if folder_name in current_mapping:
            current_desc = current_mapping[folder_name]
            print(f"  {folder_name}/ → {current_desc}")
    
    print()
    print("=== RECOMMENDATIONS ===")
    print("1. 📝 Keep numbered system for Arduino compatibility")
    print("2. 🏷️  Add descriptive README.txt in each folder")
    print("3. 📄 Create FOLDER_INDEX.txt with mapping")
    print("4. 🎵 Add track list files showing what each 001.mp3, 002.mp3 contains")
    print("5. 🗂️  Group related functions in subfolders if needed")

if __name__ == "__main__":
    main()
