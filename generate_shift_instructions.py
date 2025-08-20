#!/usr/bin/env python3
"""
Generate the missing SHIFT button instruction audio files
"""

import os
import requests
import json

def generate_shift_audio():
    """Generate the 3 missing SHIFT instruction audio files"""
    
    # Create the generated audio directory for SHIFT
    shift_dir = "player_simple_working_directory_v4/SD_CARD_STRUCTURE/audio/generated/SHIFT"
    os.makedirs(shift_dir, exist_ok=True)
    
    # SHIFT button audio content from wordlist
    shift_audio = [
        "Shift button. Press Shift twice for instructions.",
        "Welcome to your Tactile Communication Device. The device has four special buttons: Yes, No, Water, and Shift. It also has 26 letter buttons, from A to Z. Each button supports multiple presses to cycle through different words. Press once for the first word, twice for the second, and so on. The device uses text-to-speech and personal recordings stored locally, so it works offline. It runs on rechargeable batteries and charges with a USB-C cable. Press Shift twice to hear these instructions again. Press Shift three times to hear the full word list. Use the Period button, pressed three times, to toggle between Human first mode and Generated first mode.",
        "Word list mapping. A – Alari, Amer, Amory, Apple, Arabic, Arabic Show. B – Bagel, Ball, Bathroom, Bed, Blanket, Breathe, Bye. C – Call, Car, Cat, Chair, Coffee, Cold, Cucumber. D – Daddy, Deen, Doctor, Dog, Door, Down. E – Elephant. F – FaceTime, Fish, Funny. G – Garage, Go, Good Morning. H – Happy, Heartburn, Hello, Hot, House, How are you, Hungry. I – Ice, Inside, iPad. J – Jump. K – Kaiser, Key, Kiyah, Kleenex, Kyan. L – I love you, Lee, Light, Light Down, Light Up, Love. M – Mad, Medical, Medicine, Meditate, Mohammad, Moon. N – Nada, Nadowie, Net, No, Noah. O – Orange, Outside. P – Pain, Period, Phone, Purple. Q – Queen. R – Red, Rest, Room. S – Sad, Scarf, Shoes, Sinemet, Sleep, Socks, Space, Stop, Sun, Susu. T – Togamet, Tree, TV, Tylenol. U – Up, Urgent Care. V – Van. W – Walk, Walker, Water, Wheelchair. X – X-ray. Y – Yes, Yellow. Z – Zebra. Press the same letter multiple times to cycle through words."
    ]
    
    # Create placeholder files with the text content
    for i, text in enumerate(shift_audio, 1):
        filename = f"{i+1:03d}.mp3"  # 002.mp3, 003.mp3, 004.mp3
        txt_file = f"{shift_dir}/{filename.replace('.mp3', '.txt')}"
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"# {filename} should contain:\n{text}\n")
        
        print(f"Created: {txt_file}")
    
    print(f"\nCreated 3 instruction files in {shift_dir}/")
    print("Replace .txt files with actual .mp3 audio using TTS")
    print("\nSHIFT button will now support:")
    print("  Press 1: Human recording (001.mp3)")
    print("  Press 2: Instructions (002.mp3)")  
    print("  Press 3: Full instructions (003.mp3)")
    print("  Press 4: Word list (004.mp3)")

if __name__ == "__main__":
    generate_shift_audio()
