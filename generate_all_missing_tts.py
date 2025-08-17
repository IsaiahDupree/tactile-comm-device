#!/usr/bin/env python3
"""
Generate ALL Missing TTS Audio Files for Tactile Communication Device
Uses ElevenLabs API to generate high-quality TTS audio for all TTS-marked words
"""

import csv
import requests
import os
import json
import time
from pathlib import Path

# ElevenLabs API configuration
API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"  # Replace with your API key
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"  # Replace with your preferred voice ID
SD_CARD_PATH = r"E:"

def load_tts_requirements():
    """Load TTS requirements from audio_index.csv"""
    csv_path = Path(SD_CARD_PATH) / "audio_index.csv"
    tts_files = []
    
    if not csv_path.exists():
        print(f"❌ audio_index.csv not found at {csv_path}")
        return []
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['bank'] == 'TTS':
                tts_files.append({
                    'folder': int(row['folder']),
                    'track': int(row['track']),
                    'text': row['text']
                })
    
    return tts_files

def generate_tts_audio(text, output_path):
    """Generate TTS audio using ElevenLabs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    print(f"   🎵 Generating TTS for: '{text}'")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_path)
            print(f"   ✅ Generated: {output_path.name} ({file_size:,} bytes)")
            return True
        else:
            print(f"   ❌ API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error generating TTS: {e}")
        return False

def generate_all_missing_tts():
    """Generate all missing TTS files."""
    print("🎵 GENERATING ALL MISSING TTS FILES")
    print("=" * 60)
    
    if not API_KEY or API_KEY == "your_elevenlabs_api_key_here":
        print("❌ Please set your ElevenLabs API key in the script")
        return False
    
    if not os.path.exists(SD_CARD_PATH):
        print(f"❌ SD card not found at: {SD_CARD_PATH}")
        return False
    
    # Load TTS requirements
    tts_files = load_tts_requirements()
    if not tts_files:
        print("❌ No TTS files to generate")
        return False
    
    print(f"📋 Found {len(tts_files)} TTS files to generate")
    print()
    
    generated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, file_info in enumerate(tts_files, 1):
        folder = file_info["folder"]
        track = file_info["track"]
        text = file_info["text"]
        
        # Create folder path
        folder_path = Path(SD_CARD_PATH) / f"{folder:02d}"
        folder_path.mkdir(exist_ok=True)
        
        # Create file path
        file_path = folder_path / f"{track:03d}.mp3"
        
        print(f"[{i:2d}/{len(tts_files)}] Folder {folder:02d} - Track {track:03d}")
        print(f"        Text: '{text}'")
        
        # Check if file already exists
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"        ⚠️  Already exists ({size:,} bytes) - skipping")
            skipped_count += 1
            continue
        
        # Generate TTS audio
        if generate_tts_audio(text, file_path):
            generated_count += 1
            
            # Add small delay between API calls to be respectful
            time.sleep(1)
        else:
            failed_count += 1
        
        print()  # Add spacing between files
    
    # Summary
    print("=" * 60)
    print("📊 GENERATION SUMMARY:")
    print(f"   ✅ Generated: {generated_count} files")
    print(f"   ⚠️  Skipped:   {skipped_count} files (already existed)")
    print(f"   ❌ Failed:    {failed_count} files")
    print(f"   📁 Total:     {len(tts_files)} files")
    
    if generated_count > 0:
        print(f"\n🎉 Successfully generated {generated_count} new TTS files!")
        create_generation_report(tts_files, generated_count, skipped_count, failed_count)
    
    if failed_count == 0 and generated_count + skipped_count == len(tts_files):
        print("\n✅ ALL TTS FILES ARE NOW COMPLETE!")
        print("Your tactile communication device is ready to use!")
    
    print("=" * 60)
    return generated_count > 0

def create_generation_report(tts_files, generated, skipped, failed):
    """Create a detailed generation report"""
    report_path = Path(SD_CARD_PATH) / "TTS_GENERATION_REPORT.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("TACTILE COMMUNICATION DEVICE - TTS GENERATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Generation Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total TTS Files Required: {len(tts_files)}\n")
        f.write(f"Generated: {generated}\n")
        f.write(f"Skipped (already existed): {skipped}\n")
        f.write(f"Failed: {failed}\n\n")
        
        f.write("DETAILED FILE LIST:\n")
        f.write("-" * 40 + "\n")
        
        for file_info in tts_files:
            folder = file_info["folder"]
            track = file_info["track"]
            text = file_info["text"]
            file_path = Path(SD_CARD_PATH) / f"{folder:02d}" / f"{track:03d}.mp3"
            
            status = "✅ EXISTS" if file_path.exists() else "❌ MISSING"
            f.write(f"/{folder:02d}/{track:03d}.mp3 - '{text}' - {status}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("End of Report\n")
    
    print(f"📝 Generated report: {report_path}")

def verify_all_files():
    """Verify all required files exist on SD card"""
    print("\n🔍 VERIFYING ALL FILES...")
    
    tts_files = load_tts_requirements()
    missing_files = []
    
    for file_info in tts_files:
        folder = file_info["folder"]
        track = file_info["track"]
        text = file_info["text"]
        file_path = Path(SD_CARD_PATH) / f"{folder:02d}" / f"{track:03d}.mp3"
        
        if not file_path.exists():
            missing_files.append(f"/{folder:02d}/{track:03d}.mp3 - '{text}'")
    
    if missing_files:
        print(f"❌ {len(missing_files)} files still missing:")
        for missing in missing_files:
            print(f"   {missing}")
    else:
        print("✅ All TTS files are present!")
    
    return len(missing_files) == 0

def main():
    """Main function"""
    print("🚀 TACTILE COMMUNICATION DEVICE - TTS GENERATOR")
    print("=" * 60)
    
    try:
        # Generate missing TTS files
        success = generate_all_missing_tts()
        
        # Verify all files
        all_complete = verify_all_files()
        
        if all_complete:
            print("\n🎉 SUCCESS! Your tactile communication device is complete!")
            print("Next steps:")
            print("1. Upload the updated Arduino code to your device")
            print("2. Test all button mappings")
            print("3. Enjoy your fully functional communication device!")
        else:
            print("\n⚠️  Some files are still missing. Check the report for details.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
