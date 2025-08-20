#!/usr/bin/env python3
"""
Create audio files for both SHIFT and HELLO_HOW_ARE_YOU buttons with identical content
"""

import os
import shutil

def create_shared_audio_structure():
    """Create identical audio structure for both SHIFT and HELLO_HOW_ARE_YOU"""
    
    # Base directories
    v4_base = "player_simple_working_directory_v4/SD_CARD_STRUCTURE/audio"
    
    # Create directories
    shift_human_dir = f"{v4_base}/human/SHIFT"
    shift_gen_dir = f"{v4_base}/generated/SHIFT"
    hello_human_dir = f"{v4_base}/human/HELLO_HOW_ARE_YOU"
    hello_gen_dir = f"{v4_base}/generated/HELLO_HOW_ARE_YOU"
    
    for dir_path in [shift_human_dir, shift_gen_dir, hello_human_dir, hello_gen_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Audio content from wordlist
    audio_content = {
        "human": ["Hello How are You"],
        "generated": [
            "Shift button. Press Shift twice for instructions.",
            "Welcome to your Tactile Communication Device. The device has four special buttons: Yes, No, Water, and Shift. It also has 26 letter buttons, from A to Z. Each button supports multiple presses to cycle through different words. Press once for the first word, twice for the second, and so on. The device uses text-to-speech and personal recordings stored locally, so it works offline. It runs on rechargeable batteries and charges with a USB-C cable. Press Shift twice to hear these instructions again. Press Shift three times to hear the full word list. Use the Period button, pressed three times, to toggle between Human first mode and Generated first mode.",
            "Word list mapping. A – Alari, Amer, Amory, Apple, Arabic, Arabic Show. B – Bagel, Ball, Bathroom, Bed, Blanket, Breathe, Bye. C – Call, Car, Cat, Chair, Coffee, Cold, Cucumber. D – Daddy, Deen, Doctor, Dog, Door, Down. E – Elephant. F – FaceTime, Fish, Funny. G – Garage, Go, Good Morning. H – Happy, Heartburn, Hello, Hot, House, How are you, Hungry. I – Ice, Inside, iPad. J – Jump. K – Kaiser, Key, Kiyah, Kleenex, Kyan. L – I love you, Lee, Light, Light Down, Light Up, Love. M – Mad, Medical, Medicine, Meditate, Mohammad, Moon. N – Nada, Nadowie, Net, No, Noah. O – Orange, Outside. P – Pain, Period, Phone, Purple. Q – Queen. R – Red, Rest, Room. S – Sad, Scarf, Shoes, Sinemet, Sleep, Socks, Space, Stop, Sun, Susu. T – Togamet, Tree, TV, Tylenol. U – Up, Urgent Care. V – Van. W – Walk, Walker, Water, Wheelchair. X – X-ray. Y – Yes, Yellow. Z – Zebra. Press the same letter multiple times to cycle through words."
        ]
    }
    
    # Create human audio placeholders for both buttons
    for i, text in enumerate(audio_content["human"], 1):
        filename = f"{i:03d}.mp3"
        for dir_path in [shift_human_dir, hello_human_dir]:
            txt_file = f"{dir_path}/{filename.replace('.mp3', '.txt')}"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"# {filename} should contain: {text}\n")
    
    # Create generated audio placeholders for both buttons
    for i, text in enumerate(audio_content["generated"], 1):
        filename = f"{i:03d}.mp3"
        for dir_path in [shift_gen_dir, hello_gen_dir]:
            txt_file = f"{dir_path}/{filename.replace('.mp3', '.txt')}"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"# {filename} should contain: {text}\n")
    
    print("Created identical audio structure for SHIFT and HELLO_HOW_ARE_YOU buttons:")
    print(f"  Human: 1 file (Hello How are You)")
    print(f"  Generated: 3 files (Instructions, Full instructions, Word list)")
    print(f"\nBoth buttons will now have identical 4-press functionality:")
    print(f"  Press 1: Hello How are You (human)")
    print(f"  Press 2: Shift instructions (generated)")
    print(f"  Press 3: Full device instructions (generated)")
    print(f"  Press 4: Complete word list (generated)")
    print(f"\nReplace .txt files with actual .mp3 audio using TTS")

if __name__ == "__main__":
    create_shared_audio_structure()
