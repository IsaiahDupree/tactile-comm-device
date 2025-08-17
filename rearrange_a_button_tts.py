#!/usr/bin/env python3
"""
Rearrange A button TTS files to put Arabic Show last:
Track 4: Apple (already done)
Track 5: Attention (keep as is)
Track 6: Arabic Show (move from backup to track 6, replacing Awesome)
"""

import os
import shutil

SD_CARD_DRIVE = "E:\\"

def rearrange_a_button_tts():
    """Rearrange A button TTS to put Arabic Show last."""
    print("🔄 REARRANGING A BUTTON TTS ORDER")
    print("=" * 50)
    
    folder_path = os.path.join(SD_CARD_DRIVE, "05")
    
    # File paths
    track4_file = os.path.join(folder_path, "004.mp3")  # Apple (already correct)
    track5_file = os.path.join(folder_path, "005.mp3")  # Attention (keep as is)
    track6_file = os.path.join(folder_path, "006.mp3")  # Currently Awesome, will become Arabic Show
    backup_file = os.path.join(folder_path, "004_arabic_show_backup.mp3")  # Arabic Show backup
    
    print("Current A button TTS layout:")
    print("  Track 4: Apple ✅")
    print("  Track 5: Attention ✅")
    print("  Track 6: Awesome (will be replaced)")
    print()
    
    # Check if backup exists
    if not os.path.exists(backup_file):
        print(f"❌ Arabic Show backup not found: {backup_file}")
        return False
    
    # Check current files
    for track, file_path in [(4, track4_file), (5, track5_file), (6, track6_file)]:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"📁 Track {track}: {os.path.basename(file_path)} ({size:,} bytes)")
        else:
            print(f"❌ Track {track}: Missing!")
    
    backup_size = os.path.getsize(backup_file)
    print(f"📁 Backup: Arabic Show ({backup_size:,} bytes)")
    print()
    
    try:
        # Step 1: Backup current track 6 (Awesome) in case we need it
        awesome_backup = os.path.join(folder_path, "006_awesome_backup.mp3")
        print(f"📁 Backing up Awesome to: {awesome_backup}")
        shutil.copy2(track6_file, awesome_backup)
        
        # Step 2: Replace track 6 with Arabic Show
        print(f"🔄 Moving Arabic Show to track 6...")
        shutil.copy2(backup_file, track6_file)
        
        # Verify the change
        new_size = os.path.getsize(track6_file)
        print(f"✅ Track 6 now contains Arabic Show ({new_size:,} bytes)")
        
        # Update audio index
        update_audio_index()
        
        print("\n🎯 NEW A BUTTON TTS ORDER:")
        print("  Track 4: Apple (first TTS option)")
        print("  Track 5: Attention (second TTS option)")
        print("  Track 6: Arabic Show (last TTS option)")
        print()
        print("📁 Backups created:")
        print(f"  - Awesome: {awesome_backup}")
        print(f"  - Arabic Show: {backup_file} (can be deleted)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error rearranging files: {e}")
        return False

def update_audio_index():
    """Update audio index to reflect new arrangement."""
    csv_path = os.path.join(SD_CARD_DRIVE, "config", "audio_index.csv")
    
    if not os.path.exists(csv_path):
        print("⚠️  Audio index not found, skipping update")
        return
    
    try:
        # Read current CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the line for 05,6 (track 6)
        updated_lines = []
        for line in lines:
            if line.startswith('5,6,'):
                # Replace Awesome with Arabic Show
                updated_lines.append('5,6,Arabic Show,TTS\n')
                print("📝 Updated audio index: 5,6,Arabic Show,TTS")
            else:
                updated_lines.append(line)
        
        # Write back
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print("✅ Audio index updated")
        
    except Exception as e:
        print(f"⚠️  Could not update audio index: {e}")

if __name__ == "__main__":
    if rearrange_a_button_tts():
        print("\n🎉 SUCCESS!")
        print("A button TTS order rearranged successfully.")
        print("Arabic Show is now the last TTS option as requested!")
        print("\n🎯 READY TO TEST!")
        print("Upload Arduino firmware and test A button priority modes.")
    else:
        print("\n❌ Failed to rearrange A button TTS order")
