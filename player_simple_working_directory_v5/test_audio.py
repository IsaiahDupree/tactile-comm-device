#!/usr/bin/env python3
"""
Test the priority mode announcement audio files
"""

import os
import sys
import time
import pygame

def main():
    # Initialize pygame mixer
    pygame.mixer.init()
    
    # Path to the audio files
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_announcements", "33")
    
    # Files to test
    test_files = [
        ("001.mp3", "Human first mode"),
        ("002.mp3", "Generated first mode")
    ]
    
    print("Testing priority mode announcement audio files...\n")
    
    for filename, description in test_files:
        file_path = os.path.join(audio_dir, filename)
        
        if os.path.exists(file_path):
            print(f"Playing {filename} - '{description}'...")
            
            try:
                # Load and play the audio file
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                print(f"✅ Successfully played {filename}\n")
            except Exception as e:
                print(f"❌ Error playing {filename}: {str(e)}\n")
        else:
            print(f"❌ File not found: {file_path}\n")
    
    print("Audio test complete!")

if __name__ == "__main__":
    main()
