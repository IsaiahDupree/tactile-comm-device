#!/usr/bin/env python3
"""
Generate all playlist files for strict-mode SD card structure.
Creates M3U playlists for all keys from the calibration session.
"""

import os
from pathlib import Path

# All keys from the calibration session
KEYS = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'WATER', 'YES', 'NO', 'SHIFT', 'SPACE', 'PERIOD'
]

# Special keys with multiple audio files
MULTI_AUDIO_KEYS = {
    'WATER': 3,  # Water, Thirsty, Drink
    'A': 2,      # A, Apple  
    'I': 2,      # I, Ice
    'T': 3,      # TV, Tylenol, Togamet
    'S': 9,      # Multiple S words
    'E': 8,      # Multiple E words
}

def create_playlist_file(key, bank, base_dir):
    """Create a playlist file for the given key and bank."""
    playlist_dir = base_dir / "mappings" / "playlists"
    playlist_file = playlist_dir / f"{key}_{bank}.m3u"
    
    # Determine number of audio files for this key
    num_files = MULTI_AUDIO_KEYS.get(key, 1)
    
    content = [f"# {key} {bank} list"]
    
    for i in range(1, num_files + 1):
        audio_path = f"audio/{bank}/{key}/{i:03d}.mp3"
        content.append(audio_path)
    
    with open(playlist_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(content) + '\n')
    
    print(f"Created: {playlist_file}")

def main():
    """Generate all playlist files."""
    base_dir = Path(__file__).parent / "sd_strict_mode"
    
    if not base_dir.exists():
        print(f"Error: {base_dir} does not exist!")
        return
    
    # Create playlists directory if it doesn't exist
    playlist_dir = base_dir / "mappings" / "playlists"
    playlist_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating playlist files for strict-mode SD structure...")
    print(f"Base directory: {base_dir}")
    print(f"Total keys: {len(KEYS)}")
    
    created_count = 0
    
    for key in KEYS:
        # Skip keys that already have playlists
        human_playlist = playlist_dir / f"{key}_human.m3u"
        generated_playlist = playlist_dir / f"{key}_generated.m3u"
        
        if not human_playlist.exists():
            create_playlist_file(key, "human", base_dir)
            created_count += 1
        else:
            print(f"Skipped: {human_playlist} (already exists)")
            
        if not generated_playlist.exists():
            create_playlist_file(key, "generated", base_dir)
            created_count += 1
        else:
            print(f"Skipped: {generated_playlist} (already exists)")
    
    print(f"\nCompleted! Created {created_count} playlist files.")
    print(f"Total playlist files: {len(list(playlist_dir.glob('*.m3u')))}")
    
    # Validation check
    print("\n=== Validation ===")
    missing_keys = []
    for key in KEYS:
        human_exists = (playlist_dir / f"{key}_human.m3u").exists()
        generated_exists = (playlist_dir / f"{key}_generated.m3u").exists()
        
        if not human_exists and not generated_exists:
            missing_keys.append(key)
        
        status = []
        if human_exists:
            status.append("H")
        if generated_exists:
            status.append("G")
        
        print(f"{key:8} : {'/'.join(status) if status else 'MISSING'}")
    
    if missing_keys:
        print(f"\n⚠️  Keys without any playlists: {missing_keys}")
    else:
        print(f"\n✅ All {len(KEYS)} keys have at least one playlist!")

if __name__ == "__main__":
    main()
