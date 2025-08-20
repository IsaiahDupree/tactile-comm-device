#!/usr/bin/env python3
"""Simple TTS test to debug the issue."""

import os
from pathlib import Path

def test_basic():
    print("=== Basic Test ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Wordlist exists: {Path('wordlist').exists()}")
    
    # Test .env loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ELEVENLABS_API_KEY')
        print(f"API key loaded: {'Yes' if api_key else 'No'}")
        if api_key:
            print(f"API key starts with: {api_key[:10]}...")
    except ImportError:
        print("dotenv not available, checking direct env...")
        api_key = os.getenv('ELEVENLABS_API_KEY')
        print(f"Direct env API key: {'Yes' if api_key else 'No'}")
    
    # Test generate_audio import
    try:
        from generate_audio import generate_audio, DEFAULT_VOICE_ID
        print(f"generate_audio imported OK, voice: {DEFAULT_VOICE_ID}")
    except Exception as e:
        print(f"generate_audio import failed: {e}")
        return False
    
    return True

def test_single_generation():
    print("\n=== Single TTS Test ===")
    try:
        from generate_audio import generate_audio, DEFAULT_VOICE_ID
        
        # Test with a simple word
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test_apple.mp3"
        
        print(f"Generating: Apple -> {test_file}")
        success = generate_audio("Apple", DEFAULT_VOICE_ID, str(test_file))
        print(f"Result: {'SUCCESS' if success else 'FAILED'}")
        
        if test_file.exists():
            print(f"File created: {test_file} ({test_file.stat().st_size} bytes)")
        else:
            print("File was not created")
            
        return success
        
    except Exception as e:
        print(f"TTS test failed: {e}")
        return False

if __name__ == '__main__':
    if test_basic():
        test_single_generation()
    else:
        print("Basic test failed, skipping TTS test")
