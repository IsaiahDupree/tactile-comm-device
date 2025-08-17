#!/usr/bin/env python3
"""
SD Card Help System Updater
Updates your SD card with the enhanced 3-level SHIFT help system.

Usage:
    python update_sd_card_help_system.py

This script will:
1. Find your SD card drive (E:\ or other)
2. Copy the enhanced help files to /33/ folder
3. Verify all files are properly copied
4. Provide installation confirmation
"""

import os
import shutil
from pathlib import Path
import sys

def find_sd_card():
    """Find the SD card drive letter"""
    common_drives = ['E:', 'F:', 'G:', 'H:', 'D:']
    
    for drive in common_drives:
        drive_path = Path(drive + '\\')
        if drive_path.exists():
            # Check if it looks like our SD card (has numbered folders)
            folder_01 = drive_path / '01'
            folder_33 = drive_path / '33'
            
            if folder_01.exists() or folder_33.exists():
                print(f"📱 Found SD card at: {drive_path}")
                return drive_path
    
    return None

def backup_existing_files(sd_path):
    """Backup existing SHIFT files before replacement"""
    folder_33 = sd_path / '33'
    backup_folder = sd_path / '33_backup'
    
    if not folder_33.exists():
        print(f"⚠️  Creating folder: {folder_33}")
        folder_33.mkdir(exist_ok=True)
        return
    
    # Create backup folder
    backup_folder.mkdir(exist_ok=True)
    
    # Backup existing files
    for file in ['001.mp3', '002.mp3', '003.mp3']:
        source = folder_33 / file
        backup = backup_folder / file
        
        if source.exists():
            print(f"💾 Backing up: {file} → 33_backup/{file}")
            shutil.copy2(source, backup)

def copy_help_files(sd_path):
    """Copy enhanced help system files to SD card"""
    source_folder = Path("SHIFT_Enhanced_Help")
    target_folder = sd_path / '33'
    
    if not source_folder.exists():
        print(f"❌ Error: Source folder not found: {source_folder}")
        print("🔧 Please run 'python generate_enhanced_help_system.py' first!")
        return False
    
    # Ensure target folder exists
    target_folder.mkdir(exist_ok=True)
    
    # Copy all help files
    files_copied = 0
    total_size = 0
    
    for file in ['001.mp3', '002.mp3', '003.mp3']:
        source_file = source_folder / file
        target_file = target_folder / file
        
        if source_file.exists():
            print(f"📁 Copying: {file} → /33/{file}")
            shutil.copy2(source_file, target_file)
            
            file_size = target_file.stat().st_size
            total_size += file_size
            files_copied += 1
            
            print(f"   ✅ {file} ({file_size:,} bytes)")
        else:
            print(f"   ⚠️  Missing: {source_file}")
    
    print(f"\n📊 Total files copied: {files_copied}")
    print(f"📊 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    
    return files_copied == 3

def verify_installation(sd_path):
    """Verify all help files are properly installed"""
    folder_33 = sd_path / '33'
    
    print("\n🔍 VERIFYING INSTALLATION:")
    
    all_good = True
    expected_files = {
        '001.mp3': 'Basic SHIFT functionality',
        '002.mp3': 'Detailed device explanation', 
        '003.mp3': 'Complete word mapping guide'
    }
    
    for filename, description in expected_files.items():
        file_path = folder_33 / filename
        
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"   ✅ {filename}: {description} ({file_size:,} bytes)")
        else:
            print(f"   ❌ {filename}: MISSING!")
            all_good = False
    
    return all_good

def main():
    """Main SD card update function"""
    print("🎙️  SD CARD HELP SYSTEM UPDATER")
    print("=" * 50)
    
    # Find SD card
    sd_path = find_sd_card()
    if not sd_path:
        print("❌ SD card not found!")
        print("🔧 Please:")
        print("   1. Insert your SD card")
        print("   2. Note the drive letter (E:, F:, etc.)")
        print("   3. Run this script again")
        return
    
    print(f"📱 Using SD card: {sd_path}")
    
    # Backup existing files
    print("\n💾 BACKING UP EXISTING FILES:")
    backup_existing_files(sd_path)
    
    # Copy new help files
    print("\n📁 COPYING ENHANCED HELP FILES:")
    if not copy_help_files(sd_path):
        print("❌ File copying failed!")
        return
    
    # Verify installation
    if verify_installation(sd_path):
        print("\n🎉 SD CARD UPDATE COMPLETE!")
        print("✅ All enhanced help files installed successfully")
        
        print("\n🎯 READY TO TEST:")
        print("1. 🔌 Insert SD card back into your device")
        print("2. 🔄 Power cycle your device (turn off/on)")
        print("3. 🎮 Test the enhanced help system:")
        print("   • SHIFT 1x → Basic shift explanation")
        print("   • SHIFT 2x → Detailed device tutorial (~2-3 min)")  
        print("   • SHIFT 3x → Complete word mapping guide (~1-2 min)")
        
        print("\n🚀 Your device now has professional-grade help!")
        
    else:
        print("\n⚠️  Installation verification failed!")
        print("🔧 Please check your SD card and try again.")

if __name__ == "__main__":
    main()
