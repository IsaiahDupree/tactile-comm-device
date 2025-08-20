#!/usr/bin/env python3
"""
Organize generated TTS audio and human recordings into proper SD card structure.
Creates numbered MP3 files (001.mp3, 002.mp3, etc.) and playlists for each key.
"""

import json
import shutil
from pathlib import Path
import os


def load_wordlist():
    """Load the wordlist to understand the audio organization."""
    wordlist_path = Path("wordlist")
    if not wordlist_path.exists():
        raise FileNotFoundError("wordlist file not found")
    
    with open(wordlist_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_playlist(audio_files, playlist_path):
    """Create a playlist.m3u file with the given audio files."""
    playlist_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(playlist_path, 'w', encoding='utf-8') as f:
        for audio_file in audio_files:
            f.write(f"{audio_file}\n")
    
    print(f"  Created playlist: {playlist_path.name} ({len(audio_files)} entries)")


def organize_letter_audio(letter, wordlist_data, sd_audio_dir, generated_audio_dir, recordings_dir):
    """Organize audio files for a single letter."""
    print(f"\n=== Organizing letter {letter} ===")
    
    letter_data = wordlist_data["letters"][letter]
    human_words = letter_data["human"]
    generated_words = letter_data["generated"]
    
    # Organize human audio
    if human_words:
        human_dir = sd_audio_dir / "human" / letter
        human_dir.mkdir(parents=True, exist_ok=True)
        
        human_files = []
        for i, word in enumerate(human_words, 1):
            # Find matching recording file
            recording_file = None
            for ext in ['.mp3', '.wav', '.m4a']:
                potential_file = recordings_dir / f"{word}{ext}"
                if potential_file.exists():
                    recording_file = potential_file
                    break
            
            if recording_file:
                target_file = human_dir / f"{i:03d}.mp3"
                shutil.copy2(recording_file, target_file)
                human_files.append(f"{i:03d}.mp3")
                print(f"  [HUMAN] {word} → {target_file.name}")
            else:
                print(f"  [WARN] Human recording not found: {word}")
        
        # Create human playlist
        if human_files:
            create_playlist(human_files, human_dir / "playlist.m3u")
    
    # Organize generated audio
    if generated_words:
        generated_dir = sd_audio_dir / "generated" / letter
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        for i, word in enumerate(generated_words, 1):
            # Find matching generated TTS file
            source_file = generated_audio_dir / "letters" / letter / f"{i:03d}_{word.replace('/', '_').replace(':', '_')}.mp3"
            
            # Try alternative naming patterns if exact match not found
            if not source_file.exists():
                # Look for any file starting with the number
                pattern_files = list((generated_audio_dir / "letters" / letter).glob(f"{i:03d}_*.mp3"))
                if pattern_files:
                    source_file = pattern_files[0]
            
            if source_file.exists():
                target_file = generated_dir / f"{i:03d}.mp3"
                shutil.copy2(source_file, target_file)
                generated_files.append(f"{i:03d}.mp3")
                print(f"  [GEN] {word} → {target_file.name}")
            else:
                print(f"  [WARN] Generated audio not found: {word}")
        
        # Create generated playlist
        if generated_files:
            create_playlist(generated_files, generated_dir / "playlist.m3u")


def organize_phrase_audio(phrase_key, wordlist_data, sd_audio_dir, generated_audio_dir, recordings_dir):
    """Organize audio files for phrase keys (SPACE, PERIOD, HELLO_HOW_ARE_YOU)."""
    print(f"\n=== Organizing phrase {phrase_key} ===")
    
    phrase_data = wordlist_data["phrases"][phrase_key]
    human_texts = phrase_data["human"]
    generated_texts = phrase_data["generated"]
    
    # Map phrase keys to SD card key names
    key_mapping = {
        "SPACE": "SPACE",
        "PERIOD": "PERIOD", 
        "HELLO_HOW_ARE_YOU": "SHIFT"  # SHIFT button uses HELLO_HOW_ARE_YOU phrase
    }
    
    sd_key = key_mapping[phrase_key]
    
    # Organize human audio
    if human_texts:
        human_dir = sd_audio_dir / "human" / sd_key
        human_dir.mkdir(parents=True, exist_ok=True)
        
        human_files = []
        for i, text in enumerate(human_texts, 1):
            # For HELLO_HOW_ARE_YOU, look for "Hello How are You.mp3" recording
            if phrase_key == "HELLO_HOW_ARE_YOU" and text == "Hello How are You":
                recording_file = recordings_dir / "Hello How are You.mp3"
                if recording_file.exists():
                    target_file = human_dir / f"{i:03d}.mp3"
                    shutil.copy2(recording_file, target_file)
                    human_files.append(f"{i:03d}.mp3")
                    print(f"  [HUMAN] {text} → {target_file.name}")
                else:
                    print(f"  [WARN] Human recording not found: {text}")
        
        # Create human playlist
        if human_files:
            create_playlist(human_files, human_dir / "playlist.m3u")
    
    # Organize generated audio
    if generated_texts:
        generated_dir = sd_audio_dir / "generated" / sd_key
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        for i, text in enumerate(generated_texts, 1):
            # Find matching generated TTS file
            source_file = generated_audio_dir / "phrases" / phrase_key / f"{i:03d}_{text[:50].replace('/', '_').replace(':', '_')}.mp3"
            
            # Try finding any file starting with the number
            if not source_file.exists():
                pattern_files = list((generated_audio_dir / "phrases" / phrase_key).glob(f"{i:03d}_*.mp3"))
                if pattern_files:
                    source_file = pattern_files[0]
            
            if source_file.exists():
                target_file = generated_dir / f"{i:03d}.mp3"
                shutil.copy2(source_file, target_file)
                generated_files.append(f"{i:03d}.mp3")
                print(f"  [GEN] {text[:30]}... → {target_file.name}")
            else:
                print(f"  [WARN] Generated audio not found: {text[:30]}...")
        
        # Create generated playlist
        if generated_files:
            create_playlist(generated_files, generated_dir / "playlist.m3u")


def main():
    # Paths
    wordlist_data = load_wordlist()
    sd_structure_dir = Path("player_simple_working_directory_v3/SD_CARD_STRUCTURE")
    sd_audio_dir = sd_structure_dir / "audio"
    generated_audio_dir = Path("Generated_Audio")
    recordings_dir = Path("Recordings")
    
    print("=== SD Card Audio Organization ===")
    print(f"SD structure: {sd_structure_dir}")
    print(f"Generated audio: {generated_audio_dir}")
    print(f"Recordings: {recordings_dir}")
    
    # Create base audio directories
    (sd_audio_dir / "human").mkdir(parents=True, exist_ok=True)
    (sd_audio_dir / "generated").mkdir(parents=True, exist_ok=True)
    
    # Organize letter audio (A-Z)
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if letter in wordlist_data["letters"]:
            organize_letter_audio(letter, wordlist_data, sd_audio_dir, generated_audio_dir, recordings_dir)
    
    # Organize phrase audio
    for phrase_key in wordlist_data["phrases"]:
        organize_phrase_audio(phrase_key, wordlist_data, sd_audio_dir, generated_audio_dir, recordings_dir)
    
    print(f"\n=== Organization Complete ===")
    print(f"SD card audio structure created at: {sd_audio_dir}")
    print("Structure:")
    print("  audio/")
    print("    human/[KEY]/001.mp3, 002.mp3, ..., playlist.m3u")
    print("    generated/[KEY]/001.mp3, 002.mp3, ..., playlist.m3u")
    
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
