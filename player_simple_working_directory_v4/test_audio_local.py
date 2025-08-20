#!/usr/bin/env python3
"""
Test the priority mode announcement audio files locally
"""

import os
import sys
import time
import subprocess

def main():
    # Path to the audio files
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_announcements", "33")
    
    # Files to test
    test_files = [
        ("001.mp3", "Human first mode"),
        ("002.mp3", "Generated first mode")
    ]
    
    print("Testing priority mode announcement audio files locally...\n")
    
    for filename, description in test_files:
        file_path = os.path.join(audio_dir, filename)
        
        if os.path.exists(file_path):
            print(f"Playing {filename} - '{description}'...")
            
            try:
                # Use default system player to play audio
                os.startfile(file_path)
                
                # Wait for playback to finish (approximate)
                print("Playing... (press Ctrl+C to skip to next file)")
                try:
                    time.sleep(3)  # Wait for ~3 seconds for each announcement
                except KeyboardInterrupt:
                    print("\nSkipped to next file")
                
                print(f"✅ Played {filename}\n")
            except Exception as e:
                print(f"❌ Error playing {filename}: {str(e)}\n")
        else:
            print(f"❌ File not found: {file_path}\n")
    
    print("Audio test complete!")
    print("\nTo manually copy these files to your SD card:")
    print(f"1. Source files are located in: {audio_dir}")
    print("2. Copy 001.mp3 and 002.mp3 to these directories on your SD card:")
    print("   - /33/            (primary location)")
    print("   - / (root)        (fallback location 1)")
    print("   - /audio/         (fallback location 2)")
    print("   - /announcements/ (fallback location 3)")
    print("\nWith the enhanced firmware, any of these locations will work.")

if __name__ == "__main__":
    main()
