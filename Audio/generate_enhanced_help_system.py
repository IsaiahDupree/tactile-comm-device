#!/usr/bin/env python3
"""
Enhanced Help System Generator for Tactile Communication Device
Generates comprehensive TTS audio for SHIFT button multi-press help system.

Usage:
    python generate_enhanced_help_system.py

Creates:
- 001.mp3: "Shift" (basic functionality)
- 002.mp3: Detailed device explanation (comprehensive overview)
- 003.mp3: Complete word mapping guide (all button assignments)
"""

import os
import requests
import json
from pathlib import Path

# ElevenLabs Configuration
API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # RILOU voice for clear speech
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

# Audio settings for clear, professional speech
TTS_SETTINGS = {
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.85,        # High stability for consistent pronunciation
        "similarity_boost": 0.75, # Good similarity to original voice
        "style": 0.15,           # Slight style for natural speech
        "use_speaker_boost": True # Enhanced clarity
    }
}

def generate_audio(text, filename, max_length=None):
    """Generate TTS audio using ElevenLabs API"""
    
    # Truncate text if too long
    if max_length and len(text) > max_length:
        print(f"⚠️  Text too long ({len(text)} chars), truncating to {max_length} chars")
        text = text[:max_length-3] + "..."
    
    print(f"🎙️  Generating: {filename}")
    print(f"📝  Text ({len(text)} chars): {text[:100]}...")
    
    # Prepare request
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": text,
        **TTS_SETTINGS
    }
    
    try:
        response = requests.post(API_URL, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save audio file
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(filename)
        print(f"✅ Generated: {filename} ({file_size:,} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating {filename}: {e}")
        return False

def create_help_texts():
    """Create comprehensive help system texts"""
    
    # Track 1: Basic Shift functionality
    shift_text = "Shift button. Press multiple times for help system."
    
    # Track 2: Shorter Device Explanation (optimized for VS1053)
    device_explanation = """Welcome to your Tactile Communication Device. You have 74 words across multiple buttons. The device has 4 special buttons: YES, NO, WATER, and HELP, plus 26 letter buttons A through Z. Each button supports multiple presses to cycle through different words. Press once for the primary word, twice for secondary options. The device uses text-to-speech and personal recordings stored locally for offline operation. Use plus key for maximum volume, minus key for moderate volume, or number keys 1 through 9 for precise levels. The device runs on rechargeable battery and requires no internet connection. This device is designed for independence and clear communication."""

    # Track 3: Shorter Word Mapping Guide (optimized for TTS)
    word_mapping = """Word Mapping Guide for your communication device. Special buttons: YES says Yes, NO says No, WATER says Water, HELP says Help. Letter buttons: A for Apple and Amer, B for Ball and Bye, C for Cat and Chair, D for Dog and Daddy, E for Elephant, F for Fish and FaceTime, G for Go and Good Morning, H for House and Hello, I for Ice and Inside, J for Jump, K for Key and Kiyah, L for Love and Lee, M for Moon and Medicine, N for Net and Noah, O for Orange and Outside, P for Purple and Phone, Q for Queen, R for Red and Room, S for Sun and Susu, T for Tree and TV, U for Up and Urgent Care, V for Van, W for Water and Walker, X for X-ray, Y for Yellow, Z for Zebra. Press each button multiple times to cycle through all available words. Press SHIFT twice for device help or three times to repeat this word guide."""

    return {
        '001': shift_text,
        '002': device_explanation, 
        '003': word_mapping
    }

def main():
    """Main function to generate enhanced help system"""
    print("🎙️  ENHANCED HELP SYSTEM GENERATOR")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("SHIFT_Enhanced_Help")
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Generate help texts
    help_texts = create_help_texts()
    
    # Track statistics
    total_generated = 0
    total_failed = 0
    
    # Generate each help audio file
    for track_num, text in help_texts.items():
        filename = output_dir / f"{track_num}.mp3"
        
        # Generate audio (limit to reasonable length for device storage)
        max_length = 4000 if track_num == '001' else 8000  # Longer for detailed help
        
        if generate_audio(text, filename, max_length):
            total_generated += 1
        else:
            total_failed += 1
        
        print("-" * 40)
    
    # Generate summary
    print("\n🎉 ENHANCED HELP SYSTEM GENERATION COMPLETE!")
    print(f"✅ Successfully generated: {total_generated} files")
    if total_failed > 0:
        print(f"❌ Failed to generate: {total_failed} files")
    
    print(f"\n📂 Files created in: {output_dir}")
    print("\n🎯 NEXT STEPS:")
    print("1. Copy all .mp3 files to your SD card folder /33/")
    print("2. Replace existing files: 001.mp3, 002.mp3, and add new 003.mp3")
    print("3. Upload updated Arduino code with SHIFT button supporting 3 tracks")
    print("4. Test the enhanced help system:")
    print("   - SHIFT once: Basic shift function") 
    print("   - SHIFT twice: Detailed device explanation")
    print("   - SHIFT three times: Complete word mapping guide")
    
    # Create installation instructions
    instructions_file = output_dir / "INSTALLATION_INSTRUCTIONS.md"
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write("""# Enhanced Help System Installation

## Files Generated:
- `001.mp3`: Basic shift functionality
- `002.mp3`: Detailed device explanation (comprehensive overview)  
- `003.mp3`: Complete word mapping guide (all button assignments)

## Installation Steps:
1. **Copy to SD Card**: Copy all 3 files to `/33/` folder on your SD card
2. **Replace existing**: Overwrite 001.mp3 and 002.mp3, add new 003.mp3
3. **Arduino Code**: Upload updated code with SHIFT supporting 3 tracks
4. **Test System**: 
   - Press SHIFT once → "Shift button. Press multiple times for help system."
   - Press SHIFT twice → Detailed device explanation (~2-3 minutes)
   - Press SHIFT three times → Complete word mapping guide (~3-4 minutes)

## Features:
✅ Professional TTS using RILOU voice  
✅ Comprehensive device explanation  
✅ Complete button-to-word mapping  
✅ Multi-level help system  
✅ Optimized audio length for device storage  

Your tactile communication device now has a complete, professional help system!
""")
    
    print(f"📋 Installation instructions saved to: {instructions_file}")

if __name__ == "__main__":
    main()
